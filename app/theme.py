"""Shared dark and light palettes for widgets, startup, and the 3D scene."""

from string import Template

from PySide6.QtGui import QColor, QPalette


PALETTES = {
    "dark": {
        "window": "#111b25", "header": "#14212d", "text": "#e4ebf1",
        "muted": "#91a6b7", "body": "#c0ced9", "border": "#2a3946",
        "card": "#192735", "input": "#1a2835", "input_border": "#304353",
        "hover": "#1d2e3d", "selected": "#203d40", "selected_border": "#3f6a65",
        "selected_text": "#dcf5eb", "accent": "#91d3bd", "accent_text": "#112c2a",
        "accent_hover": "#b0e8d2", "tag": "#193637", "tag_text": "#9adbc6",
        "button": "#203140", "button_border": "#344959", "button_hover": "#2b4454",
        "button_pressed": "#31565c", "disabled": "#6c8292", "track": "#304553",
        "handle": "#c5e9df", "tooltip": "#243c48", "scroll": "#3b5261",
        "scene_bottom": "#101e2b", "scene_top": "#1b3040",
        "skin": "#98c9d4", "skeleton": "#d6cfbd",
    },
    "light": {
        "window": "#f3f7fa", "header": "#ffffff", "text": "#203440",
        "muted": "#5c7180", "body": "#425966", "border": "#d5e0e7",
        "card": "#ffffff", "input": "#ffffff", "input_border": "#bfced9",
        "hover": "#e6eef3", "selected": "#daeee6", "selected_border": "#8bb9a9",
        "selected_text": "#154e43", "accent": "#176d5d", "accent_text": "#ffffff",
        "accent_hover": "#105746", "tag": "#e0f0e9", "tag_text": "#276d5b",
        "button": "#ffffff", "button_border": "#c5d4de", "button_hover": "#e4eef2",
        "button_pressed": "#cce4dc", "disabled": "#91a1ad", "track": "#cfdee6",
        "handle": "#237e6c", "tooltip": "#ffffff", "scroll": "#afc3cf",
        "scene_bottom": "#e2ecf4", "scene_top": "#f9fbfd",
        "skin": "#506e83", "skeleton": "#9e835b",
    },
}


STYLESHEET = Template("""
QWidget { background: $window; color: $text; font-size: 13px; }
QMainWindow { background: $window; }
QFrame#Header { background: $header; border-bottom: 1px solid $border; }
QLabel { background: transparent; }
QLabel#Brand { font-size: 22px; font-weight: 700; letter-spacing: 2px; }
QLabel#Subbrand { color: $muted; font-size: 11px; letter-spacing: 2px; }
QLabel#Badge { background: $tag; color: $tag_text; border: 1px solid $selected_border;
              border-radius: 11px; padding: 5px 12px; font-size: 10px; font-weight: 600; }
QLabel#Section { color: $muted; font-size: 10px; font-weight: 600; letter-spacing: 1.6px; }
QLabel#PanelTitle { font-size: 18px; font-weight: 600; }
QLabel#OrganTitle { font-size: 29px; font-weight: 600; }
QLabel#Latin { color: $muted; font-size: 14px; font-style: italic; }
QLabel#BodyText { color: $body; font-size: 13px; }
QLabel#Muted, QLabel#Count { color: $muted; font-size: 11px; }
QLabel#Credit { color: $muted; font-size: 10px; padding: 3px 10px; }
QLabel#SystemTag { color: $tag_text; background: $tag; border-radius: 6px; padding: 6px 9px; font-size: 11px; }
QFrame#Sidebar { border-right: 1px solid $border; }
QFrame#Details { border-left: 1px solid $border; }
QFrame#Card { background: $card; border: 1px solid $border; border-radius: 10px; }
QFrame#Divider { background: $border; max-height: 1px; min-height: 1px; border: 0; }
QLineEdit { background: $input; border: 1px solid $input_border; border-radius: 8px; padding: 10px 12px; }
QLineEdit:focus { border-color: $accent; }
QComboBox { background: $input; border: 1px solid $input_border; border-radius: 7px; padding: 8px 10px; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView { background: $input; color: $text; selection-background-color: $selected; selection-color: $selected_text; }
QListWidget { background: transparent; border: 0; outline: 0; }
QListWidget::item { border: 1px solid transparent; border-radius: 8px; padding: 10px 8px; margin: 2px 0; }
QListWidget::item:hover { background: $hover; }
QListWidget::item:selected { background: $selected; border-color: $selected_border; color: $selected_text; }
QPushButton { background: $button; border: 1px solid $button_border; border-radius: 7px;
              padding: 9px 12px; font-weight: 500; }
QPushButton:hover { background: $button_hover; border-color: $selected_border; }
QPushButton:pressed { background: $button_pressed; }
QPushButton:checked { background: $selected; border-color: $selected_border; color: $selected_text; }
QPushButton:disabled { color: $disabled; background: $window; border-color: $border; }
QPushButton#Primary { background: $accent; color: $accent_text; border-color: $accent; font-weight: 600; }
QPushButton#Primary:hover { background: $accent_hover; }
QPushButton#Small { padding: 7px 10px; font-size: 11px; }
QPushButton#Camera { padding: 6px 12px; font-size: 11px; }
QPushButton#Zoom { font-size: 18px; padding: 3px 10px; }
QSlider::groove:horizontal { height: 4px; background: $track; border-radius: 2px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 2px; }
QSlider::handle:horizontal { background: $handle; width: 12px; margin: -5px 0; border-radius: 6px; }
QCheckBox { spacing: 8px; color: $body; }
QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid $input_border; border-radius: 4px; background: $input; }
QCheckBox::indicator:checked { background: $accent; border: 3px solid $selected_border; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: $scroll; border-radius: 3px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: $tooltip; color: $text; border: 1px solid $border; padding: 7px; }
QStatusBar { border-top: 1px solid $border; color: $muted; font-size: 10px; }
QStatusBar::item { border: 0; }
""")


def saved_theme(settings) -> str:
    name = settings.value("appearance/theme", "dark")
    return name if name in PALETTES else "dark"


def stylesheet(name: str) -> str:
    return STYLESHEET.substitute(PALETTES[name])


def qt_palette(name: str) -> QPalette:
    return palette_for_colors(PALETTES[name])


def blend_colors(start: dict, end: dict, progress: float) -> dict:
    progress = min(1.0, max(0.0, progress))
    result = {}
    for key in start:
        first, last = QColor(start[key]), QColor(end[key])
        result[key] = QColor.fromRgbF(
            first.redF() + (last.redF() - first.redF()) * progress,
            first.greenF() + (last.greenF() - first.greenF()) * progress,
            first.blueF() + (last.blueF() - first.blueF()) * progress,
        ).name()
    return result


def palette_for_colors(colors: dict) -> QPalette:
    palette = QPalette()
    for role, key in {
        QPalette.ColorRole.Window: "window", QPalette.ColorRole.WindowText: "text",
        QPalette.ColorRole.Base: "input", QPalette.ColorRole.AlternateBase: "card",
        QPalette.ColorRole.Text: "text", QPalette.ColorRole.Button: "button",
        QPalette.ColorRole.ButtonText: "text", QPalette.ColorRole.Highlight: "selected",
        QPalette.ColorRole.HighlightedText: "selected_text",
        QPalette.ColorRole.ToolTipBase: "tooltip", QPalette.ColorRole.ToolTipText: "text",
        QPalette.ColorRole.PlaceholderText: "muted",
    }.items():
        palette.setColor(role, QColor(colors[key]))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(colors["disabled"]))
    return palette
