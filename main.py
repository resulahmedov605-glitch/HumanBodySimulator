"""Launch the Python desktop application: python main.py."""

import argparse
import json
import os
from pathlib import Path
import stat
import sys


def prepare_qt_plugins(plugin_root: Path) -> None:
    """Make pip-installed Qt plugins discoverable on affected macOS installs.

    Some macOS installations mark wheel contents UF_HIDDEN. Qt's plugin
    scanner excludes those files even though Python can read them. Clear
    only that Finder visibility flag inside this Qt plugin directory.
    """
    if sys.platform != "darwin":
        return
    for path in (plugin_root, *plugin_root.rglob("*")):
        if path.is_symlink():
            continue
        flags = path.stat().st_flags
        if flags & stat.UF_HIDDEN:
            os.chflags(path, flags & ~stat.UF_HIDDEN)


def main() -> int:
    parser = argparse.ArgumentParser(description="Human Body Simulator · 3D Anatomy")
    parser.add_argument("--smoke-test", action="store_true", help="Run UI integration checks and exit")
    parser.add_argument("--screenshot", type=Path, help="Save a window screenshot during the smoke test")
    parser.add_argument("--debug-qt", action="store_true", help="Log Qt plugin loading diagnostics")
    parser.add_argument("--theme", choices=("dark", "light"), help="Start with the chosen appearance")
    args = parser.parse_args()
    if args.debug_qt:
        os.environ["QT_DEBUG_PLUGINS"] = "1"
    if args.smoke_test:
        import faulthandler
        faulthandler.dump_traceback_later(60, exit=True)
        print("Loading desktop and 3D modules…", flush=True)
    try:
        from PySide6.QtCore import QCoreApplication, QLibraryInfo, QLocale, QSettings, QTimer
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QApplication
    except ImportError as error:
        print(f"Missing dependency: {error}\nFirst run: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1

    if args.smoke_test:
        print("Creating Qt application…", flush=True)
    plugin_root = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))
    prepare_qt_plugins(plugin_root)
    QCoreApplication.addLibraryPath(str(plugin_root))
    app = QApplication(sys.argv[:1])
    QLocale.setDefault(QLocale(QLocale.Language.English))
    app.setApplicationName("Human Body Simulator")
    app.setOrganizationName("HumanBody")
    app.setStyle("Fusion")
    app.setFont(QFont("Avenir Next" if sys.platform == "darwin" else "Segoe UI", 12))
    # Initialize Cocoa before VTK. Geometry is loaded in the background while
    # a responsive welcome window is shown; OpenGL stays on the GUI thread.
    from app.startup import StartupController
    test_directory = None
    if args.smoke_test:
        import tempfile
        test_directory = tempfile.TemporaryDirectory()
        settings = QSettings(str(Path(test_directory.name) / "settings.ini"), QSettings.Format.IniFormat)
    else:
        settings = QSettings()
    if args.theme:
        settings.setValue("appearance/theme", args.theme)
    startup = StartupController(settings=settings, interactive=not args.smoke_test)

    if args.smoke_test:
        from tools.smoke_check import check_window

        def verify(window):
            try:
                result = check_window(window, args.screenshot, startup=startup)
                faulthandler.cancel_dump_traceback_later()
                print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
            except Exception:
                import traceback
                traceback.print_exc()
                window.close()
                app.exit(1)
                return
            window.close()
            app.exit(0)

        startup.ready.connect(lambda window: QTimer.singleShot(150, lambda: verify(window)))
        if args.screenshot:
            def capture_welcome():
                args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                path = args.screenshot.with_name(f"{args.screenshot.stem}-welcome.png")
                if not startup.welcome.grab().save(str(path)):
                    print("Could not save welcome preview", file=sys.stderr)
            QTimer.singleShot(600, capture_welcome)
    startup.start()
    try:
        return app.exec()
    finally:
        startup.shutdown()
        if test_directory:
            test_directory.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
