"""Two-second welcome screen with background asset loading and a crossfade."""

import math

from PySide6.QtCore import (
    QEasingCurve, QElapsedTimer, QObject, QPointF, QPropertyAnimation,
    QSettings, QThread, QTimer, Qt, Signal, Slot,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMessageBox, QProgressBar,
    QVBoxLayout, QWidget,
)

from .interaction import busy_cursor
from .theme import PALETTES, qt_palette, saved_theme, stylesheet


class AtlasMark(QWidget):
    def __init__(self, theme_name, parent=None):
        super().__init__(parent)
        self.colors = PALETTES[theme_name]
        self.setFixedSize(126, 126)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(63, 63)
        accent = QColor(self.colors["accent"])
        orbit = QColor(accent)
        orbit.setAlpha(65)
        painter.setPen(QPen(orbit, 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, 55, 55)
        painter.drawEllipse(center, 41, 41)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(38, 38, 50, 50, 15, 15)
        painter.setBrush(QColor(self.colors["accent_text"]))
        painter.drawRoundedRect(59, 48, 8, 30, 2, 2)
        painter.drawRoundedRect(48, 59, 30, 8, 2, 2)
        painter.setBrush(accent)
        for angle in (-40, 95, 205):
            radians = math.radians(angle)
            point = center + QPointF(55*math.cos(radians), 55*math.sin(radians))
            painter.drawEllipse(point, 4, 4)


class WelcomeWindow(QWidget):
    def __init__(self, theme_name):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("WelcomeWindow")
        self.setWindowTitle("Welcome to HumanBody")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(710, 430)
        self.setCursor(Qt.CursorShape.BusyCursor)
        colors = PALETTES[theme_name]
        self.setStyleSheet(stylesheet(theme_name) + f"""
            QWidget#WelcomeWindow {{ background: transparent; }}
            QFrame#WelcomeSurface {{ background: {colors['window']};
                border: 1px solid {colors['selected_border']}; border-radius: 20px; }}
            QLabel#WelcomeTitle {{ font-size: 31px; font-weight: 600; }}
            QLabel#WelcomeSubtitle {{ font-size: 14px; color: {colors['body']}; }}
            QProgressBar {{ border: 0; background: {colors['track']}; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {colors['accent']}; border-radius: 3px; }}
        """)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(5, 5, 5, 5)
        surface = QFrame()
        surface.setObjectName("WelcomeSurface")
        outer.addWidget(surface)
        column = QVBoxLayout(surface)
        column.setContentsMargins(40, 28, 40, 32)
        column.setSpacing(14)
        top = QHBoxLayout()
        top.setSpacing(20)
        identity = QVBoxLayout()
        identity.setSpacing(8)
        brand = QLabel("HUMANBODY")
        brand.setObjectName("Brand")
        identity.addWidget(brand)
        subtitle = QLabel("3D ANATOMY ATLAS")
        subtitle.setObjectName("Subbrand")
        identity.addWidget(subtitle)
        top.addLayout(identity)
        top.addStretch()
        top.addWidget(AtlasMark(theme_name))
        column.addLayout(top)
        title = QLabel("Welcome to HumanBody")
        title.setObjectName("WelcomeTitle")
        column.addWidget(title)
        description = QLabel("Explore organs, systems, and the connections within.")
        description.setObjectName("WelcomeSubtitle")
        description.setWordWrap(True)
        column.addWidget(description)
        column.addStretch()
        features = QLabel("14 structures  ·  5 systems  ·  Offline discovery")
        features.setObjectName("Muted")
        column.addWidget(features)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        column.addWidget(self.progress)
        footer = QHBoxLayout()
        footer.setSpacing(16)
        self.status = QLabel("Preparing your atlas…")
        self.status.setObjectName("Muted")
        footer.addWidget(self.status)
        footer.addStretch()
        model = QLabel("Adult male reference")
        model.setObjectName("Muted")
        footer.addWidget(model)
        column.addLayout(footer)
        screen = QApplication.primaryScreen()
        if screen:
            self.move(screen.availableGeometry().center() - self.rect().center())
        self.progress_animation = QPropertyAnimation(self.progress, b"value", self)
        self.progress_animation.setStartValue(0)
        self.progress_animation.setEndValue(100)
        self.progress_animation.setDuration(2000)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade = QPropertyAnimation(self, b"windowOpacity", self)

    def start(self):
        self.setWindowOpacity(0)
        self.show()
        self.fade.setDuration(280)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade.start()
        self.progress_animation.start()


class ModelLoader(QThread):
    loaded = Signal(object)
    failed = Signal(str)

    def run(self):
        try:
            from .model_assets import load_models
            self.loaded.emit(load_models())
        except Exception as error:
            self.failed.emit(str(error))


class StartupController(QObject):
    ready = Signal(object)

    def __init__(self, *, settings=None, interactive=True):
        super().__init__()
        self.interactive = interactive
        self.settings = settings if settings is not None else QSettings()
        self.window = None
        self.intro_elapsed = False
        self.reveal_started_ms = None
        self.clock = QElapsedTimer()
        self.welcome = WelcomeWindow(saved_theme(self.settings))
        QApplication.instance().setPalette(qt_palette(saved_theme(self.settings)))
        self.loader = ModelLoader(self)
        self.loader.loaded.connect(self._models_ready)
        self.loader.failed.connect(self._failed)
        self.intro_timer = QTimer(self)
        self.intro_timer.setSingleShot(True)
        self.intro_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.intro_timer.setInterval(2000)
        self.intro_timer.timeout.connect(self._intro_finished)
        self.main_fade = None

    def start(self):
        self.clock.start()
        self.welcome.start()
        self.intro_timer.start()
        self.loader.start()

    @Slot(object)
    def _models_ready(self, models):
        try:
            # Only data is read by the worker. Qt widgets and every OpenGL
            # operation stay on the application thread.
            from .window import MainWindow
            with busy_cursor():
                self.window = MainWindow(models=models, settings=self.settings)
            self.welcome.status.setText("Your atlas is ready")
            self.welcome.setCursor(Qt.CursorShape.ArrowCursor)
            self._try_reveal()
        except Exception as error:
            self._failed(str(error))

    @Slot()
    def _intro_finished(self):
        self.intro_elapsed = True
        self._try_reveal()

    def _try_reveal(self):
        if not self.intro_elapsed or self.window is None or self.main_fade is not None:
            return
        self.reveal_started_ms = self.clock.elapsed()
        self.window.setWindowOpacity(0)
        self.window.show()
        self.window.raise_()
        self.main_fade = QPropertyAnimation(self.window, b"windowOpacity", self)
        self.main_fade.setDuration(380)
        self.main_fade.setStartValue(0.0)
        self.main_fade.setEndValue(1.0)
        self.main_fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.main_fade.finished.connect(self._revealed)
        self.welcome.fade.stop()
        self.welcome.fade.setDuration(240)
        self.welcome.fade.setStartValue(self.welcome.windowOpacity())
        self.welcome.fade.setEndValue(0.0)
        self.welcome.fade.finished.connect(self.welcome.close)
        self.welcome.fade.start()
        self.main_fade.start()

    def _revealed(self):
        self.window.setWindowOpacity(1)
        self.welcome.hide()
        self.window.activateWindow()
        self.ready.emit(self.window)

    @Slot(str)
    def _failed(self, message):
        self.intro_timer.stop()
        print(f"Startup failed: {message}", flush=True)
        if self.interactive:
            QMessageBox.critical(self.welcome, "Could not open atlas", message)
        self.welcome.close()
        QApplication.instance().exit(1)

    def shutdown(self):
        self.intro_timer.stop()
        self.loader.wait()
        if self.main_fade:
            self.main_fade.stop()
        self.welcome.fade.stop()
        self.welcome.hide()
        if self.window:
            self.window.close()
