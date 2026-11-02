"""UI integration checks against a real running Qt / VTK window."""

from pathlib import Path
import tempfile

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFrame, QPushButton, QStyle, QStyleOptionSlider

from app.interaction import busy_cursor
from app.theme import PALETTES, saved_theme


def save_preview(window, filename: Path):
    filename.parent.mkdir(parents=True, exist_ok=True)
    scene_file = filename.with_name(f"{filename.stem}-scene.png")
    window.scene.save_image(scene_file)
    # QWidget.grab cannot capture a native VTK child window on macOS.
    preview = window.grab()
    painter = QPainter(preview)
    vtk_widget = window.scene.vtk_widget
    target = QRect(vtk_widget.mapTo(window, QPoint(0, 0)), vtk_widget.size())
    painter.drawImage(target, QImage(str(scene_file)))
    painter.end()
    return preview.save(str(filename))


def check_window(window, screenshot: Path | None = None, *, startup=None) -> dict:
    checks = []

    def check(condition, description):
        if not condition:
            raise AssertionError(description)
        checks.append(description)
        print(f"  PASS: {description}", flush=True)

    initial_theme = window.theme_name
    if startup:
        check(startup.reveal_started_ms >= 2000 and startup.reveal_started_ms < 4000,
              "Welcome stays for two seconds before the main-window transition")
        check(not startup.welcome.isVisible() and window.windowOpacity() > 0.99,
              "Welcome and main-window fades complete")
    check(all(button.cursor().shape() == Qt.CursorShape.PointingHandCursor
              for button in window.findChildren(QPushButton)), "Buttons use a pointing-hand cursor")
    check(window.search.cursor().shape() == Qt.CursorShape.IBeamCursor,
          "Search uses a text cursor")
    slider_options = QStyleOptionSlider()
    window.skin_slider.initStyleOption(slider_options)
    slider_point = window.skin_slider.style().subControlRect(
        QStyle.ComplexControl.CC_Slider, slider_options,
        QStyle.SubControl.SC_SliderHandle, window.skin_slider).center()
    QTest.mousePress(window.skin_slider, Qt.MouseButton.LeftButton, pos=slider_point)
    check(window.skin_slider.cursor().shape() == Qt.CursorShape.ClosedHandCursor,
          "Dragging an opacity slider uses a closed hand")
    QTest.mouseRelease(window.skin_slider, Qt.MouseButton.LeftButton, pos=slider_point)
    check(window.skin_slider.cursor().shape() == Qt.CursorShape.OpenHandCursor,
          "Releasing an opacity slider restores its open hand")
    background_point = QPoint(8, 8)
    QTest.mousePress(window.scene.vtk_widget, Qt.MouseButton.LeftButton, pos=background_point)
    check(window.scene.vtk_widget.cursor().shape() == Qt.CursorShape.ClosedHandCursor,
          "Dragging the 3D viewport uses a closed hand")
    QTest.mouseRelease(window.scene.vtk_widget, Qt.MouseButton.LeftButton, pos=background_point)
    check(window.scene.vtk_widget.cursor().shape() == Qt.CursorShape.OpenHandCursor,
          "Releasing the 3D viewport restores its open hand")
    try:
        with busy_cursor():
            check(QApplication.overrideCursor().shape() == Qt.CursorShape.WaitCursor,
                  "Long operations show a wait cursor")
            raise RuntimeError("Intentional cursor-cleanup check")
    except RuntimeError:
        pass
    check(QApplication.overrideCursor() is None, "Busy cursor restores even after a failed operation")
    window.reset_all()

    for name in ("light", "dark"):
        if window.theme_name != name:
            QTest.mouseClick(window.theme_button, Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        actual = window.scene.renderer.GetBackground()
        expected = QColor(PALETTES[name]["scene_bottom"])
        check(window.theme_name == name and abs(actual[0] - expected.redF()) < 0.001,
              f"{name.title()} mode updates both interface and 3D scene")
        persisted = QSettings(window.settings.fileName(), window.settings.format())
        check(saved_theme(persisted) == name, f"{name.title()} preference survives a new settings read")
        check(window.scene.visible_count() == 14 and window.selected_key == "heart",
              f"{name.title()} mode preserves anatomical selection and visibility")
        if screenshot:
            check(save_preview(window, screenshot.with_name(f"{screenshot.stem}-{name}.png")),
                  f"{name.title()} preview saved")
    for buttons in (window.camera_buttons, window.zoom_buttons,
                    window.findChild(QFrame, "Header").findChildren(QPushButton)):
        ordered = sorted(buttons, key=lambda button: button.x())
        check(all(second.x() - (first.x() + first.width()) >= 8
                  for first, second in zip(ordered, ordered[1:])), "Adjacent controls have visible horizontal gaps")
    check(window.isolate_button.y() - (window.focus_button.y() + window.focus_button.height()) >= 10
          and window.hide_button.y() - (window.isolate_button.y() + window.isolate_button.height()) >= 10,
          "Structure action buttons have visible vertical gaps")
    window.set_theme(initial_theme)

    check(window.scene.visible_count() == 14, "14 anatomical structures loaded")
    check(window.organ_title.text() == "Heart", "Initial selection is reflected in the information panel")
    window.system_combo.setCurrentText("Respiratory system")
    check(window.organ_list.count() == 3 and window.scene.visible_count() == 3,
          "System filtering updates both list and scene")
    window.system_combo.setCurrentIndex(0)
    window.search.setText("KIDNEY")
    check(window.organ_list.count() == 2, "Case-insensitive English organ search")
    window.organ_list.setCurrentRow(1)
    check(window.selected_key == "left_kidney" and window.organ_title.text() == "Left kidney",
          "List selection updates anatomy details")
    window.search.setText("no-such-organ")
    check(window.organ_list.count() == 0 and window.result_count.text() == "No structures found",
          "Empty search results handled")
    window.search.clear()
    QTest.mouseClick(window.isolate_button, Qt.MouseButton.LeftButton)
    check(window.scene.visible_count() == 1 and not window.scene.actors["skin"].GetVisibility(),
          "Isolation hides other organs and context layers")
    QTest.mouseClick(window.hide_button, Qt.MouseButton.LeftButton)
    check(window.scene.visible_count() == 0 and window.hide_button.text() == "Show structure",
          "Selected organ can be hidden")
    QTest.mouseClick(window.hide_button, Qt.MouseButton.LeftButton)
    check(window.scene.visible_count() == 1, "Hidden organ can be restored")
    QTest.mouseClick(window.isolate_button, Qt.MouseButton.LeftButton)
    window.skin_slider.setValue(0)
    check(not window.scene.actors["skin"].GetVisibility(), "Zero skin opacity removes body surface")
    window.skeleton_slider.setValue(55)
    check(abs(window.scene.actors["skeleton"].GetProperty().GetOpacity() - 0.55) < 0.001,
          "Skeleton opacity updates")
    original_scale = window.scene.renderer.GetActiveCamera().GetParallelScale()
    QTest.mouseClick(window.focus_button, Qt.MouseButton.LeftButton)
    check(window.scene.renderer.GetActiveCamera().GetParallelScale() < original_scale,
          "Focus button zooms to selected structure")
    window.rotation.setChecked(True)
    check(window.scene.rotation_timer.isActive(), "Automatic rotation starts")
    window.rotation.setChecked(False)
    check(not window.scene.rotation_timer.isActive(), "Automatic rotation stops")
    window.reset_all()
    check(window.scene.visible_count() == 14 and window.selected_key == "heart"
          and window.skin_slider.value() == 9 and window.skeleton_slider.value() == 16
          and not window.isolate_button.isChecked(), "Reset restores the complete atlas")

    # Test actual VTK surface picking by projecting an isolated organ's points.
    window.select_structure("heart")
    window.isolate_button.setChecked(True)
    window.scene.focus_selected()
    QApplication.processEvents()
    actor = window.scene.actors["heart"]
    data = actor.GetMapper().GetInput()
    renderer = window.scene.renderer
    picked = False
    candidates = [actor.GetCenter()] + [data.GetPoint(index) for index in
        range(0, data.GetNumberOfPoints(), max(1, data.GetNumberOfPoints()//100))]
    for point in candidates:
        renderer.SetWorldPoint(*point, 1)
        renderer.WorldToDisplay()
        x, y, _ = renderer.GetDisplayPoint()
        if window.scene.picker.Pick(x, y, 0, renderer) and window.scene.picker.GetActor() == actor:
            picked = True
            break
    check(picked, "VTK surface picking finds the heart geometry")
    selected_by_click = []
    window.scene.structure_selected.connect(selected_by_click.append)
    vtk_widget = window.scene.vtk_widget
    render_width, render_height = vtk_widget.GetRenderWindow().GetSize()
    click_point = QPoint(round(x * vtk_widget.width() / render_width),
                         round((render_height - y - 1) * vtk_widget.height() / render_height))
    QTest.qWait(90)
    # Deliver a real Qt move event directly; Cocoa's QTest.mouseMove relies
    # on moving the desktop cursor, which is unreliable in unattended runs.
    move = QMouseEvent(QEvent.Type.MouseMove, QPointF(click_point),
                       QPointF(vtk_widget.mapToGlobal(click_point)),
                       Qt.MouseButton.NoButton, Qt.MouseButton.NoButton,
                       Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(vtk_widget, move)
    QTest.qWait(60)
    if vtk_widget.cursor().shape() != Qt.CursorShape.PointingHandCursor:
        print({"projected": (x, y), "click": (click_point.x(), click_point.y()),
               "render_size": (render_width, render_height),
               "event_position": vtk_widget.GetEventPosition(),
               "dragging": window.scene._dragging,
               "hover_pending": window.scene._hover_timer.isActive()}, flush=True)
    check(vtk_widget.cursor().shape() == Qt.CursorShape.PointingHandCursor,
          "Hovering a selectable organ uses a pointing hand")
    QTest.mouseClick(vtk_widget, Qt.MouseButton.LeftButton, pos=click_point)
    check(selected_by_click == ["heart"] and window.organ_title.text() == "Heart",
          "A real viewport click selects the heart and updates its details")
    window.scene.structure_selected.disconnect(selected_by_click.append)
    window.reset_all()
    QApplication.processEvents()

    with tempfile.TemporaryDirectory() as directory:
        exported = Path(directory) / "scene.png"
        window.scene.save_image(exported)
        check(exported.is_file() and exported.stat().st_size > 10_000,
              "PNG export produces a rendered 3D image")

    if screenshot:
        check(save_preview(window, screenshot), "Window preview saved")
    return {"passed": len(checks), "checks": checks}
