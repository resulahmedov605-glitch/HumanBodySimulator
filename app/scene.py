"""VTK scene, selection, and camera controls embedded in a Qt widget."""

import math
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout

# Importing Qt before QVTK makes VTK select the PySide6 binding.
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonDataModel import vtkStaticCellLocator
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import (
    vtkActor, vtkCellPicker, vtkLight, vtkPolyDataMapper, vtkRenderer,
    vtkWindowToImageFilter,
)
from vtkmodules.vtkIOImage import vtkPNGWriter
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401 — register OpenGL backend

from .anatomy import ATTRIBUTION, BY_KEY, CONTEXT_MESHES, STRUCTURES
from .model_assets import load_models
from .theme import PALETTES


def rgb(hex_color: str) -> tuple[float, float, float]:
    color = QColor(hex_color)
    return color.redF(), color.greenF(), color.blueF()


class AtlasInteractor(QVTKRenderWindowInteractor):
    """Keep application cursor hints when VTK requests its default arrow."""

    pointer_pressed = Signal(object)
    pointer_released = Signal(object)
    pointer_moved = Signal()

    def __init__(self, parent=None):
        self.interaction_cursor = Qt.CursorShape.OpenHandCursor
        super().__init__(parent)
        self.ShowCursor()

    def set_interaction_cursor(self, shape):
        self.interaction_cursor = shape
        self.ShowCursor()

    def ShowCursor(self):
        self.setCursor(self.interaction_cursor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.pointer_pressed.emit(event.button())

    def mouseReleaseEvent(self, event):
        # VTK's camera style grabs interactor focus while dragging, so its
        # release event does not reliably reach separate VTK observers.
        super().mouseReleaseEvent(event)
        self.pointer_released.emit(event.button())

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.pointer_moved.emit()


class AnatomyScene(QWidget):
    structure_selected = Signal(str)
    visibility_changed = Signal()

    def __init__(self, parent=None, *, models=None):
        super().__init__(parent)
        self.setMinimumSize(360, 440)
        self.actors: dict[str, vtkActor] = {}
        self.selected_key: str | None = None
        self.hidden_keys: set[str] = set()
        self.isolated = False
        self.skin_opacity = 0.09
        self.skeleton_opacity = 0.16
        self.active_system: str | None = None
        self._press_position = (0, 0)
        self._rotating = False
        self._closed = False
        self._dragging = False
        self._locators = []
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(35)
        self._hover_timer.timeout.connect(self._update_hover)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.vtk_widget = AtlasInteractor(self)
        self.vtk_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.vtk_widget)
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(*rgb("#101e2b"))
        self.renderer.SetBackground2(*rgb("#1b3040"))
        self.renderer.GradientBackgroundOn()
        window = self.vtk_widget.GetRenderWindow()
        window.AddRenderer(self.renderer)
        window.SetMultiSamples(0)
        window.SetAlphaBitPlanes(1)
        # Use standard blending for broad graphics-driver compatibility.
        self.renderer.SetUseDepthPeeling(False)

        style = vtkInteractorStyleTrackballCamera()
        self.vtk_widget.SetInteractorStyle(style)
        self.vtk_widget.pointer_pressed.connect(self._pointer_pressed)
        self.vtk_widget.pointer_released.connect(self._pointer_released)
        self.vtk_widget.pointer_moved.connect(self._mouse_hover)
        self.picker = vtkCellPicker()
        self.picker.SetTolerance(0.003)
        self.picker.PickFromListOn()
        self._load_models(models if models is not None else load_models())
        self._add_lighting()
        self.vtk_widget.Initialize()
        self.reset_camera()

        self.rotation_timer = QTimer(self)
        self.rotation_timer.setInterval(33)
        self.rotation_timer.timeout.connect(self._rotate_step)
        self._update_visibility()

    def _load_models(self, models):
        expected = [structure.key for structure in STRUCTURES] + list(CONTEXT_MESHES)
        for key in expected:
            data = models[key]
            mapper = vtkPolyDataMapper()
            mapper.SetInputData(data)
            mapper.ScalarVisibilityOff()
            actor = vtkActor()
            actor.SetMapper(mapper)
            prop = actor.GetProperty()
            prop.SetInterpolationToPhong()
            prop.SetAmbient(0.25)
            prop.SetDiffuse(0.72)
            prop.SetSpecular(0.25)
            prop.SetSpecularPower(32)
            if key in BY_KEY:
                prop.SetColor(*rgb(BY_KEY[key].color))
                self.picker.AddPickList(actor)
                locator = vtkStaticCellLocator()
                locator.SetDataSet(data)
                locator.BuildLocator()
                self.picker.AddLocator(locator)
                self._locators.append(locator)
            else:
                prop.SetColor(*rgb("#98c9d4" if key == "skin" else "#d6cfbd"))
                actor.PickableOff()
            # Keep animation scale centred on the mesh, rather than world origin.
            actor.SetOrigin(*data.GetCenter())
            self.actors[key] = actor
            self.renderer.AddActor(actor)
        self.bounds = self.actors["skin"].GetBounds()
        self.center = tuple((self.bounds[2*i] + self.bounds[2*i+1]) / 2 for i in range(3))
        self.height = self.bounds[5] - self.bounds[4]

    def _add_lighting(self):
        for position, intensity, color in [
            ((-600, -900, 1800), 0.85, "#fff0e5"),
            ((700, -300, 1300), 0.5, "#c6e6ff"),
            ((0, 500, 1600), 0.65, "#b9dbe4"),
        ]:
            light = vtkLight()
            light.SetLightTypeToSceneLight()
            light.SetPosition(*position)
            light.SetFocalPoint(*self.center)
            light.SetColor(*rgb(color))
            light.SetIntensity(intensity)
            self.renderer.AddLight(light)

    def _pointer_pressed(self, button):
        if button == Qt.MouseButton.LeftButton:
            self._press_position = self.vtk_widget.GetEventPosition()
        self._drag_begin()

    def _pointer_released(self, button):
        if button == Qt.MouseButton.LeftButton:
            self._mouse_up()
        else:
            self._drag_end()

    def _drag_begin(self, *_):
        self._dragging = True
        self._hover_timer.stop()
        self.vtk_widget.set_interaction_cursor(Qt.CursorShape.ClosedHandCursor)

    def _drag_end(self, *_):
        self._dragging = False
        self.vtk_widget.set_interaction_cursor(Qt.CursorShape.OpenHandCursor)

    def _mouse_hover(self, *_):
        if not self._dragging and not self._hover_timer.isActive():
            self._hover_timer.start()

    def _update_hover(self):
        # A trailing update also handles a pointer that stops on an organ
        # before the next frame, without picking on every mouse event.
        if self._dragging or self._closed or not self.isVisible():
            return
        x, y = self.vtk_widget.GetEventPosition()
        hit = self.picker.Pick(x, y, 0, self.renderer)
        self.vtk_widget.set_interaction_cursor(
            Qt.CursorShape.PointingHandCursor if hit else Qt.CursorShape.OpenHandCursor)

    def _mouse_up(self):
        self._drag_end()
        x, y = self.vtk_widget.GetEventPosition()
        if math.dist(self._press_position, (x, y)) > 5:
            return
        if self.picker.Pick(x, y, 0, self.renderer):
            self.vtk_widget.set_interaction_cursor(Qt.CursorShape.PointingHandCursor)
            actor = self.picker.GetActor()
            for key, candidate in self.actors.items():
                if candidate == actor and key in BY_KEY:
                    self.structure_selected.emit(key)
                    break

    def set_theme(self, name: str):
        self.set_colors(PALETTES[name])

    def set_colors(self, colors: dict):
        self.renderer.SetBackground(*rgb(colors["scene_bottom"]))
        self.renderer.SetBackground2(*rgb(colors["scene_top"]))
        for key in CONTEXT_MESHES:
            self.actors[key].GetProperty().SetColor(*rgb(colors[key]))
        self.render()

    def select(self, key: str):
        if key not in BY_KEY:
            raise KeyError(key)
        self.selected_key = key
        self.hidden_keys.discard(key)
        self._update_visibility()

    def set_system(self, system: str | None):
        self.active_system = system
        if self.isolated:
            self.isolated = False
        self._update_visibility()

    def set_context_opacity(self, key: str, value: int):
        value = min(100, max(0, value)) / 100
        if key == "skin":
            self.skin_opacity = value
        elif key == "skeleton":
            self.skeleton_opacity = value
        else:
            raise KeyError(key)
        self._update_visibility()

    def toggle_hidden(self, key: str):
        if key in self.hidden_keys:
            self.hidden_keys.remove(key)
        else:
            self.hidden_keys.add(key)
        self._update_visibility()

    def set_isolated(self, enabled: bool):
        self.isolated = enabled and self.selected_key is not None
        self._update_visibility()

    def restore(self):
        self.hidden_keys.clear()
        self.isolated = False
        self.active_system = None
        self.skin_opacity = 0.09
        self.skeleton_opacity = 0.16
        self._update_visibility()
        self.reset_camera()

    def _update_visibility(self):
        for key, actor in self.actors.items():
            prop = actor.GetProperty()
            if key in CONTEXT_MESHES:
                opacity = self.skin_opacity if key == "skin" else self.skeleton_opacity
                actor.SetVisibility(not self.isolated and opacity > 0)
                prop.SetOpacity(opacity)
                continue
            structure = BY_KEY[key]
            visible = key not in self.hidden_keys
            if self.isolated:
                visible = visible and key == self.selected_key
            elif self.active_system:
                visible = visible and structure.system == self.active_system
            actor.SetVisibility(visible)
            selected = key == self.selected_key
            base_color = QColor(structure.color)
            if selected:
                base_color = base_color.lighter(112)
            prop.SetColor(*rgb(base_color.name()))
            prop.SetAmbient(0.36 if selected else 0.25)
            prop.SetSpecular(0.38 if selected else 0.22)
            # Lungs are translucent to make the heart visible from the front.
            prop.SetOpacity(0.62 if "lung" in key and not selected and not self.isolated else 1.0)
        self.render()
        self.visibility_changed.emit()

    def visible_count(self) -> int:
        return sum(bool(self.actors[structure.key].GetVisibility()) for structure in STRUCTURES)

    def reset_camera(self, direction: str = "front"):
        camera = self.renderer.GetActiveCamera()
        cx, cy, cz = self.center
        distance = self.height * 2.0
        vectors = {"front": (0, -1, 0), "back": (0, 1, 0),
                   "left": (1, 0, 0), "right": (-1, 0, 0)}
        dx, dy, dz = vectors.get(direction, vectors["front"])
        camera.SetFocalPoint(cx, cy, cz)
        camera.SetPosition(cx + dx*distance, cy + dy*distance, cz + dz*distance)
        camera.SetViewUp(0, 0, 1)
        camera.ParallelProjectionOn()
        camera.SetParallelScale(self.height * 0.55)
        self.renderer.ResetCameraClippingRange()
        self.render()

    def focus_selected(self):
        if self.selected_key is None:
            return
        actor = self.actors[self.selected_key]
        center = actor.GetCenter()
        bounds = actor.GetBounds()
        span = max(bounds[2*i+1] - bounds[2*i] for i in range(3))
        camera = self.renderer.GetActiveCamera()
        old_direction = camera.GetDirectionOfProjection()
        distance = self.height * 1.4
        camera.SetFocalPoint(*center)
        camera.SetPosition(*(center[i] - old_direction[i]*distance for i in range(3)))
        camera.SetParallelScale(max(span * 0.85, 40))
        self.renderer.ResetCameraClippingRange()
        self.render()

    def zoom(self, factor: float):
        camera = self.renderer.GetActiveCamera()
        camera.SetParallelScale(min(self.height*2, max(12, camera.GetParallelScale()/factor)))
        self.renderer.ResetCameraClippingRange()
        self.render()

    def set_rotating(self, enabled: bool):
        self._rotating = enabled
        if enabled:
            self.rotation_timer.start()
        else:
            self.rotation_timer.stop()

    def _rotate_step(self):
        if not self.isVisible():
            return
        self.renderer.GetActiveCamera().Azimuth(0.45)
        self.renderer.ResetCameraClippingRange()
        self.render()

    def save_image(self, filename: str | Path):
        self.render()
        capture = vtkWindowToImageFilter()
        capture.SetInput(self.vtk_widget.GetRenderWindow())
        capture.ReadFrontBufferOff()
        capture.Update()
        writer = vtkPNGWriter()
        writer.SetFileName(str(filename))
        writer.AddText("Title", "Human Body Simulator - 3D Anatomy")
        writer.AddText("Copyright", ATTRIBUTION)
        writer.SetInputConnection(capture.GetOutputPort())
        writer.Write()
        if writer.GetErrorCode() or not Path(filename).is_file():
            raise OSError(f"Could not write image: {filename}")

    def render(self):
        if not self._closed:
            self.vtk_widget.GetRenderWindow().Render()

    def shutdown(self):
        if not self._closed:
            self._hover_timer.stop()
            self.rotation_timer.stop()
            self._closed = True
            self.vtk_widget.Finalize()
