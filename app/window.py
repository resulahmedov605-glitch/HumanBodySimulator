"""Native Qt desktop interface for the anatomy atlas."""

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QSettings, Qt, QSize, QVariantAnimation
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from .anatomy import ATTRIBUTION, BY_KEY, STRUCTURES, SYSTEMS, matching_structures
from .scene import AnatomyScene
from .interaction import InteractionFeedback, busy_cursor
from .theme import PALETTES, STYLESHEET, blend_colors, palette_for_colors, saved_theme




def label(text: str, style: str = "", wrap: bool = False) -> QLabel:
    widget = QLabel(text)
    if style:
        widget.setObjectName(style)
    widget.setWordWrap(wrap)
    if wrap:
        widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


def divider() -> QFrame:
    frame = QFrame()
    frame.setObjectName("Divider")
    return frame


def dot_icon(color: str) -> QIcon:
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawEllipse(4, 4, 10, 10)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self, *, models=None, settings=None):
        super().__init__()
        self.setWindowTitle("Human Body Simulator · 3D Anatomy")
        self.resize(1380, 900)
        self.setMinimumSize(1100, 740)
        self.selected_key = "heart"
        self.settings = settings if settings is not None else QSettings()
        self.theme_name = saved_theme(self.settings)
        self._display_colors = PALETTES[self.theme_name].copy()
        self._theme_lightness = float(self.theme_name == "light")
        self.theme_animation = QVariantAnimation(self)
        self.theme_animation.setDuration(520)
        self.theme_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.theme_animation.valueChanged.connect(self._theme_frame)
        self.theme_animation.finished.connect(self._theme_finished)
        self.save_alert = None
        self.scene = AnatomyScene(self, models=models)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._header())
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar())
        body.addWidget(self._viewport(), 1)
        body.addWidget(self._details())
        root.addLayout(body, 1)

        status_credit = label(ATTRIBUTION, "Credit")
        self.statusBar().addWidget(status_credit)
        self.status_text = label("14 structures · 5 systems · offline")
        self.statusBar().addPermanentWidget(self.status_text)

        self.scene.structure_selected.connect(self.select_structure)
        self.scene.visibility_changed.connect(self._sync_visibility)
        self._populate_list()
        self.select_structure("heart")
        self._sync_visibility()
        self.feedback = InteractionFeedback(self)
        self.set_theme(self.theme_name, persist=False)
        self._shortcuts = []
        for key, callback in [("R", self.reset_all), ("F", self.scene.focus_selected),
                              ("Ctrl+S", self.export_image), ("Ctrl+F", self.search.setFocus),
                              ("Ctrl+T", self.toggle_theme)]:
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
            self._shortcuts.append(shortcut)

    def _header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(84)
        row = QHBoxLayout(header)
        row.setSpacing(12)
        row.setContentsMargins(24, 14, 24, 14)
        brand_stack = QVBoxLayout()
        brand_stack.setSpacing(2)
        brand_stack.addWidget(label("HUMANBODY", "Brand"))
        brand_stack.addWidget(label("3D ANATOMY ATLAS", "Subbrand"))
        row.addLayout(brand_stack)
        row.addSpacing(30)
        row.addWidget(label("Explore. Select. Discover.", "Muted"))
        row.addStretch()
        row.addWidget(label("LEARNING LAB", "Badge"))
        row.addSpacing(16)
        self.theme_button = QPushButton("Light mode")
        self.theme_button.setObjectName("Small")
        self.theme_button.clicked.connect(self.toggle_theme)
        row.addWidget(self.theme_button)
        export = QPushButton("Save image")
        export.setObjectName("Small")
        export.setToolTip("Save the 3D view as PNG · Ctrl+S")
        export.clicked.connect(self.export_image)
        row.addWidget(export)
        about = QPushButton("About")
        about.setObjectName("Small")
        about.clicked.connect(self.show_about)
        row.addWidget(about)
        return header

    def _sidebar(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Sidebar")
        panel.setFixedWidth(250)
        column = QVBoxLayout(panel)
        column.setContentsMargins(18, 24, 18, 18)
        column.setSpacing(12)
        column.addWidget(label("STRUCTURES", "Section"))
        column.addWidget(label("Explore the body", "PanelTitle"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search structures…")
        self.search.setClearButtonEnabled(True)
        self.search.setToolTip("Search by English or Latin name · Ctrl+F")
        self.search.textChanged.connect(self._populate_list)
        column.addWidget(self.search)
        self.system_combo = QComboBox()
        self.system_combo.addItem("All systems", None)
        for system in SYSTEMS:
            self.system_combo.addItem(system, system)
        self.system_combo.currentIndexChanged.connect(self._system_changed)
        column.addWidget(self.system_combo)
        self.result_count = label("14 structures", "Count")
        column.addWidget(self.result_count)
        self.organ_list = QListWidget()
        self.organ_list.setIconSize(QSize(18, 18))
        self.organ_list.currentItemChanged.connect(self._list_selection_changed)
        column.addWidget(self.organ_list, 1)
        column.addWidget(divider())
        column.addWidget(label("ANATOMICAL LAYERS", "Section"))
        self.skin_slider = self._opacity_control(column, "Body surface", "skin", 9)
        self.skeleton_slider = self._opacity_control(column, "Skeleton", "skeleton", 16)
        self.rotation = QCheckBox("Auto-rotate")
        self.rotation.toggled.connect(self.scene.set_rotating)
        column.addWidget(self.rotation)
        self.reset_button = QPushButton("Reset view")
        self.reset_button.setObjectName("Small")
        self.reset_button.setToolTip("Restore all structures and the default camera · R")
        self.reset_button.clicked.connect(self.reset_all)
        column.addWidget(self.reset_button)
        return panel

    def _opacity_control(self, layout: QVBoxLayout, title: str, key: str, initial: int) -> QSlider:
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(label(title, "Muted"))
        row.addStretch()
        percent = label(f"{initial}%", "Muted")
        row.addWidget(percent)
        layout.addLayout(row)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(initial)
        slider.setAccessibleName(f"{title} opacity")
        slider.valueChanged.connect(lambda value: percent.setText(f"{value}%"))
        slider.valueChanged.connect(lambda value: self.scene.set_context_opacity(key, value))
        layout.addWidget(slider)
        return slider

    def _viewport(self) -> QWidget:
        panel = QWidget()
        column = QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        toolbar.setContentsMargins(18, 15, 18, 13)
        toolbar.addWidget(label("INTERACTIVE 3D MODEL", "Section"))
        toolbar.addStretch()
        self.camera_buttons = []
        for title, direction in [("Front", "front"), ("Back", "back"), ("Left", "left"), ("Right", "right")]:
            button = QPushButton(title)
            button.setObjectName("Camera")
            button.clicked.connect(lambda _checked=False, view=direction: self.scene.reset_camera(view))
            toolbar.addWidget(button)
            self.camera_buttons.append(button)
        column.addLayout(toolbar)
        column.addWidget(self.scene, 1)
        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        bottom.setContentsMargins(18, 10, 18, 12)
        self.visible_label = label("14 / 14 structures visible", "Muted")
        bottom.addWidget(self.visible_label)
        bottom.addStretch()
        self.zoom_buttons = []
        for text, factor in [("−", 1/1.2), ("+", 1.2)]:
            button = QPushButton(text)
            button.setObjectName("Zoom")
            button.setFixedWidth(38)
            button.setToolTip("Zoom out" if factor < 1 else "Zoom in")
            button.clicked.connect(lambda _checked=False, zoom=factor: self.scene.zoom(zoom))
            bottom.addWidget(button)
            self.zoom_buttons.append(button)
        column.addLayout(bottom)
        hint = label("Rotate: drag  ·  Zoom: scroll  ·  Select: click a structure", "Muted", True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setContentsMargins(14, 0, 14, 14)
        column.addWidget(hint)
        return panel

    def _details(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Details")
        panel.setFixedWidth(300)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contents = QWidget()
        column = QVBoxLayout(contents)
        column.setContentsMargins(22, 26, 22, 22)
        column.setSpacing(14)
        column.addWidget(label("SELECTED STRUCTURE", "Section"))
        self.organ_title = label("Heart", "OrganTitle", True)
        column.addWidget(self.organ_title)
        self.latin = label("Cor", "Latin")
        column.addWidget(self.latin)
        self.system_tag = label("Cardiovascular system", "SystemTag")
        self.system_tag.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        column.addWidget(self.system_tag)
        column.addSpacing(3)
        column.addWidget(divider())
        self.summary = label("", "BodyText", True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.summary.setCursor(Qt.CursorShape.IBeamCursor)
        column.addWidget(self.summary)
        self.function_text = label("", "BodyText", True)
        column.addWidget(self._detail_card("PRIMARY FUNCTION", self.function_text))
        self.location_text = label("", "BodyText", True)
        column.addWidget(self._detail_card("LOCATION", self.location_text))
        self.focus_button = QPushButton("Focus on structure")
        self.focus_button.setObjectName("Primary")
        self.focus_button.setToolTip("Focus the camera on the selected structure · F")
        self.focus_button.clicked.connect(self.scene.focus_selected)
        column.addWidget(self.focus_button)
        self.isolate_button = QPushButton("Isolate structure")
        self.isolate_button.setCheckable(True)
        self.isolate_button.toggled.connect(self.scene.set_isolated)
        column.addWidget(self.isolate_button)
        self.hide_button = QPushButton("Hide structure")
        self.hide_button.clicked.connect(lambda: self.scene.toggle_hidden(self.selected_key))
        column.addWidget(self.hide_button)
        column.addStretch(1)
        column.addWidget(label("ABOUT THE MODEL", "Section"))
        column.addWidget(label("Adult male reference model", "SystemTag"))
        column.addWidget(label("BodyParts3D anatomy. Left and right refer to the subject’s own body.", "Muted", True))
        column.addWidget(label("Static anatomy model for learning", "Muted", True))
        scroll.setWidget(contents)
        outer.addWidget(scroll)
        return panel

    def _detail_card(self, title: str, content: QLabel) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        column = QVBoxLayout(card)
        column.setContentsMargins(14, 14, 14, 14)
        column.setSpacing(9)
        column.addWidget(label(title, "Section"))
        column.addWidget(content)
        return card

    def _populate_list(self, *_):
        matches = matching_structures(self.search.text(), self.system_combo.currentData())
        self.organ_list.blockSignals(True)
        self.organ_list.clear()
        for structure in matches:
            item = QListWidgetItem(dot_icon(structure.color), structure.name)
            item.setData(Qt.ItemDataRole.UserRole, structure.key)
            item.setToolTip(f"{structure.latin} · {structure.system}")
            self.organ_list.addItem(item)
            if structure.key == self.selected_key:
                self.organ_list.setCurrentItem(item)
        self.organ_list.blockSignals(False)
        noun = "structure" if len(matches) == 1 else "structures"
        self.result_count.setText(f"{len(matches)} {noun}" if matches else "No structures found")

    def _list_selection_changed(self, current, _previous):
        if current:
            self.select_structure(current.data(Qt.ItemDataRole.UserRole))

    def _system_changed(self, *_):
        system = self.system_combo.currentData()
        self.scene.set_system(system)
        self.isolate_button.blockSignals(True)
        self.isolate_button.setChecked(False)
        self.isolate_button.blockSignals(False)
        self._populate_list()
        if system and BY_KEY[self.selected_key].system != system:
            available = matching_structures(system=system)
            if available:
                self.select_structure(available[0].key)

    def select_structure(self, key: str):
        structure = BY_KEY[key]
        # A 3D pick outside the current sidebar search must still be represented.
        current_system = self.system_combo.currentData()
        if current_system and current_system != structure.system:
            self.system_combo.blockSignals(True)
            self.system_combo.setCurrentIndex(0)
            self.system_combo.blockSignals(False)
            self.scene.set_system(None)
        self.selected_key = key
        self.organ_title.setText(structure.name)
        self._update_title_color()
        self.latin.setText(structure.latin)
        self.system_tag.setText(structure.system)
        self.summary.setText(structure.summary)
        self.function_text.setText(structure.function)
        self.location_text.setText(structure.location)
        self.scene.select(key)
        if key not in {s.key for s in matching_structures(self.search.text(), current_system)}:
            self.search.blockSignals(True)
            self.search.clear()
            self.search.blockSignals(False)
        self._populate_list()
        self._sync_visibility()

    def _update_title_color(self):
        color = QColor(BY_KEY[self.selected_key].color)
        color = color.darker(round(100 + 55*self._theme_lightness))
        self.organ_title.setStyleSheet(f"color: {color.name()};")

    def set_theme(self, name: str, *, persist: bool = True, animate: bool = False):
        if name not in ("dark", "light"):
            raise ValueError(f"Unknown theme: {name}")
        self.theme_animation.stop()
        self.theme_name = name
        target = "Light" if name == "dark" else "Dark"
        self.theme_button.setText(f"{target} mode")
        self.theme_button.setToolTip(f"Switch to {target.lower()} mode · Ctrl+T")
        if animate and self.isVisible():
            self._theme_from = self._display_colors.copy()
            self._theme_to = PALETTES[name].copy()
            self._theme_from_lightness = self._theme_lightness
            self._theme_to_lightness = float(name == "light")
            self.theme_animation.setStartValue(0.0)
            self.theme_animation.setEndValue(1.0)
            self.theme_animation.start()
        else:
            self._theme_lightness = float(name == "light")
            self._apply_theme_colors(PALETTES[name].copy())
        if persist:
            self.settings.setValue("appearance/theme", name)
            self.settings.sync()

    def toggle_theme(self):
        self.set_theme("light" if self.theme_name == "dark" else "dark", animate=True)

    def _apply_theme_colors(self, colors):
        self._display_colors = colors
        QApplication.instance().setPalette(palette_for_colors(colors))
        self.setStyleSheet(STYLESHEET.substitute(colors))
        self.scene.set_colors(colors)
        self._update_title_color()

    def _theme_frame(self, progress):
        self._theme_lightness = self._theme_from_lightness + (
            self._theme_to_lightness - self._theme_from_lightness) * progress
        self._apply_theme_colors(blend_colors(self._theme_from, self._theme_to, progress))

    def _theme_finished(self):
        self._theme_lightness = float(self.theme_name == "light")
        self._apply_theme_colors(PALETTES[self.theme_name].copy())

    def _sync_visibility(self):
        self.visible_label.setText(f"{self.scene.visible_count()} / {len(STRUCTURES)} structures visible")
        self.hide_button.setText("Show structure" if self.selected_key in self.scene.hidden_keys else "Hide structure")

    def reset_all(self):
        self.rotation.setChecked(False)
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.system_combo.blockSignals(True)
        self.system_combo.setCurrentIndex(0)
        self.system_combo.blockSignals(False)
        self.isolate_button.blockSignals(True)
        self.isolate_button.setChecked(False)
        self.isolate_button.blockSignals(False)
        self.scene.restore()
        self.skin_slider.setValue(9)
        self.skeleton_slider.setValue(16)
        self.select_structure("heart")

    def export_image(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save 3D view", "humanbody.png", "PNG image (*.png)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if filename:
            if not filename.lower().endswith(".png"):
                filename += ".png"
            try:
                with busy_cursor():
                    self.scene.save_image(filename)
            except (OSError, RuntimeError) as error:
                QMessageBox.warning(self, "Could not save image", str(error))
                return
            self.statusBar().showMessage(f"Image saved: {filename}", 6000)
            self._show_saved_alert(filename)

    def _show_saved_alert(self, filename):
        alert = QMessageBox(self)
        alert.setWindowTitle("Image saved")
        alert.setIcon(QMessageBox.Icon.Information)
        alert.setText("Image saved successfully.")
        alert.setInformativeText(f"Saved as {Path(filename).name}")
        alert.setStandardButtons(QMessageBox.StandardButton.Ok)
        alert.setWindowModality(Qt.WindowModality.WindowModal)
        for button in alert.buttons():
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_alert = alert
        alert.finished.connect(lambda _result: self._clear_save_alert(alert))
        alert.finished.connect(alert.deleteLater)
        alert.open()

    def _clear_save_alert(self, alert):
        if self.save_alert is alert:
            self.save_alert = None

    def show_about(self):
        QMessageBox.about(
            self, "About Human Body Simulator",
            "<h2>Human Body Simulator</h2><p>An interactive 3D anatomy atlas built with Python.</p>"
            "<p>14 structures · 5 organ systems · offline access</p>"
            "<p>Interface: PySide6 / Qt<br>3D engine: VTK</p>"
            "<p>BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.</p>"
            '<p><a href="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html">Model source and license</a></p>'
            "<p>Version 0.2 · light and dark appearance · static anatomy module</p>",
        )

    def closeEvent(self, event):
        self.theme_animation.stop()
        self.scene.shutdown()
        super().closeEvent(event)
