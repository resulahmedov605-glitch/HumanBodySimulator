"""Consistent pointer feedback and balanced busy cursors."""

from contextlib import contextmanager

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QAbstractButton, QApplication, QComboBox, QLineEdit, QListWidget, QSlider


@contextmanager
def busy_cursor():
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


class InteractionFeedback(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.list_viewports = {}
        for widget in window.findChildren(QAbstractButton) + window.findChildren(QComboBox):
            widget.setCursor(Qt.CursorShape.PointingHandCursor)
            widget.installEventFilter(self)
        for widget in window.findChildren(QLineEdit):
            widget.setCursor(Qt.CursorShape.IBeamCursor)
        for combo in window.findChildren(QComboBox):
            combo.view().viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        for slider in window.findChildren(QSlider):
            slider.setCursor(Qt.CursorShape.OpenHandCursor)
            slider.sliderPressed.connect(lambda target=slider: target.setCursor(Qt.CursorShape.ClosedHandCursor))
            slider.sliderReleased.connect(lambda target=slider: target.setCursor(Qt.CursorShape.OpenHandCursor))
        for listing in window.findChildren(QListWidget):
            viewport = listing.viewport()
            viewport.setMouseTracking(True)
            viewport.installEventFilter(self)
            self.list_viewports[viewport] = listing

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.EnabledChange:
            watched.setCursor(Qt.CursorShape.PointingHandCursor if watched.isEnabled() else Qt.CursorShape.ArrowCursor)
        elif event.type() == QEvent.Type.MouseMove and watched in self.list_viewports:
            listing = self.list_viewports[watched]
            shape = Qt.CursorShape.PointingHandCursor if listing.itemAt(event.position().toPoint()) else Qt.CursorShape.ArrowCursor
            watched.setCursor(shape)
        return False
