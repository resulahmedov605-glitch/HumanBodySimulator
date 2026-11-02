# Human Body Simulator

An English-language desktop 3D anatomy atlas built with Python, PySide6, and VTK.
Explore a real human-body mesh, select organs, and learn about their functions.

## Run on this computer

The project already contains its virtual environment and offline model files:

```bash
.venv/bin/python main.py
```

## Set up on another computer

Use Python 3.11 or later. On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On Windows, using PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

Copy the `assets/anatomy/` directory with the source code. After installation,
the application works offline. Windows and Linux require their own runtime
verification before distribution.

## Features

- Real BodyParts3D geometry for the body surface, skeleton, and 14 structures.
- Selectable brain, heart, aorta, right and left lungs, trachea, liver, stomach,
  pancreas, small and large intestines, right and left kidneys, and urinary bladder.
- Five system filters: nervous, cardiovascular, respiratory, digestive, and urinary.
- Search by English or Latin name, with case-insensitive matching.
- A description, primary function, and location for each structure.
- Mouse rotation, zoom, and direct selection in the 3D scene.
- Front, back, left, and right camera views.
- Separate opacity controls for the body surface and skeleton.
- Focus, isolate, hide, and restore structures.
- Automatic rotation and PNG image export.
- English interface, tooltips, learning content, and application messages.
- Dark and light appearance for the interface and 3D scene; your choice is remembered.
- A welcome screen with a two-second introduction and a smooth transition to the atlas.
- Background model loading, spaced controls, and context-aware mouse cursors.

## Controls

| Action | Control |
| --- | --- |
| Rotate the model | Drag with the left mouse button |
| Zoom in or out | Scroll wheel or + / − buttons |
| Select a structure | Click it in the model or choose it from the list |
| Reset the atlas | R |
| Focus on the selected structure | F |
| Search structures | Ctrl+F |
| Save the 3D view | Ctrl+S |
| Switch between light and dark mode | Header appearance button or Ctrl+T |

Left and right refer to the subject's own body. In the front view, the subject's
right side appears on the left of the screen. Unselected lungs are partly
transparent so the heart remains visible. Search filters the list; a system
filter affects both the list and the 3D scene.

Buttons use a pointing hand, search uses a text cursor, and draggable sliders
and the 3D viewport use open/closed hands. Hovering over a selectable organ
shows a pointing hand. Model preparation and image export show busy cursors.
Appearance is stored in the operating system's application preferences.
You can also choose an initial theme with `python main.py --theme light`.

The welcome screen fades in while geometry loads in the background. After
two seconds, the main window fades in once the model is ready.

## Project structure

```text
main.py                  Application entry point
app/anatomy.py           English organ content, search, and model identifiers
app/scene.py             VTK scene, camera controls, and picking
app/window.py            Native PySide6 desktop interface
app/theme.py             Shared dark/light styles and scene colors
app/startup.py           Animated welcome screen and startup controller
app/model_assets.py      Geometry loading without GUI or OpenGL operations
app/interaction.py       Mouse feedback and busy-cursor cleanup
assets/anatomy/          Offline meshes and provenance manifest
assets/ATTRIBUTION.md    Data source, license, and geometry changes
tests/test_anatomy.py    Search, integrity, and shared-coordinate checks
tools/build_anatomy.py   Rebuilds VTP assets from official OBJ geometry
tools/smoke_check.py     Integration checks in a real application window
PROJECT_PLAN.md          Project scope and development stages
```

## Verification

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python main.py --smoke-test --screenshot screenshots/preview.png
```

The second command opens the welcome and atlas windows, checks interaction
behavior, both themes, preference persistence, spacing, cursors, and VTK
selection, saves previews, and closes the application. Test settings use a
temporary file and do not overwrite your appearance preference.
For Qt platform-plugin diagnostics, add `--debug-qt`.

The project pins PySide6 6.9.3 because the native VTK widget has a known
macOS paint/render loop with Qt 6.10 and later. See the
[upstream VTK discussion](https://discourse.vtk.org/t/issue-with-qvtkrenderwindowinteractor-and-pyside6-6-10-1-on-macos/16225).

## Rebuild the model assets

The prepared VTP files are included. To regenerate them, download these files
from the [official BodyParts3D archive](https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html):

1. `partof_BP3D_4.0_obj_99.zip`
2. `partof_parts_list_e.txt`
3. `partof_element_parts.txt`

Then run:

```bash
.venv/bin/python tools/build_anatomy.py \
  --archive /path/to/partof_BP3D_4.0_obj_99.zip \
  --parts-list /path/to/partof_parts_list_e.txt \
  --elements-list /path/to/partof_element_parts.txt
```

## Model source and scope

BodyParts3D, © The Database Center for Life Science licensed under
CC Attribution 4.0 International. See [the attribution notes](assets/ATTRIBUTION.md).

The geometry represents the dataset's adult male anatomy. The interface and
welcome identify it as an adult male reference model. A female model would
require its own geometry and organ content; a sex selector is deferred until
that dataset is available. Version 0.2 is a
static anatomy atlas. Heartbeat, breathing, and responses to physical activity
are planned for the physiology stage. The presentation will be prepared after
the application's final features are complete.
