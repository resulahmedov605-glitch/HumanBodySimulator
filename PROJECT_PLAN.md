# Human Body Simulator — project plan

Direction selected by the user: **3D human body model**.
Language: Python. Platform: native desktop application.
Product language: **English throughout**, including interface, organ content,
messages, documentation, and the future presentation.

## Stage 1 — Interactive 3D anatomy atlas

- Native Python / PySide6 window with a VTK 3D viewport.
- Licensed offline BodyParts3D meshes for body surface, skeleton, and organs.
- Rotation, zoom, and four standard camera directions.
- Selection from the 3D model and the structure list.
- English names and descriptions, with Latin anatomical names for reference.
- Primary function and location for each structure.
- Search and filtering across five organ systems.
- Body-surface and skeleton opacity controls.
- Hide, isolate, focus, and restore actions.
- PNG export for presentation images.
- Persistent dark/light appearance for the interface and 3D scene.
- A two-second welcome screen with background model loading and smooth fades.
- Consistent control spacing and context-aware cursors.

The first version includes 14 selectable structures across five systems.
This stage provides a static anatomical reference.
The included geometry is an adult male reference. Female anatomy is an
optional later expansion that requires a separate licensed dataset.

## Stage 2 — Physiological processes

After reviewing the 3D atlas, add heartbeat and breathing animations.
Connect a simplified educational model to rest, walking, and running scenarios.
Make simulated indicators and their assumptions clear in the interface.

## Stage 3 — Learning and demonstration

Add guided explanations, optional knowledge-check questions, and a concise
demonstration sequence. Refine usability using feedback on the working app.

## Stage 4 — Verification and distribution

Verify search, selection, layers, camera controls, and mesh integrity.
Test on the operating system used for the presentation and prepare the
appropriate desktop application package. The current source-run entry point
is `python main.py`.

## Stage 5 — Presentation in English

1. Project purpose and intended users.
2. Working features and application screenshots.
3. Why Python, PySide6, and VTK were selected.
4. How anatomical content connects to the 3D scene.
5. Model source and license attribution.
6. Live demo: rotate, select, focus, and adjust anatomical layers.
7. Results and future improvements.

## Technical references

- Qt for Python: https://www.qt.io/development/qt-framework/python-bindings
- VTK / Qt: https://docs.vtk.org/en/latest/api/python/vtkmodules/vtkmodules.qt.QVTKRenderWindowInteractor.html
- Anatomical geometry: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- Model license: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
