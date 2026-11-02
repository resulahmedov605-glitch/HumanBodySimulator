"""Read geometry without touching Qt widgets or OpenGL, including in a worker."""

from .anatomy import CONTEXT_MESHES, STRUCTURES, asset_directory


def load_models() -> dict:
    from vtkmodules.vtkIOXML import vtkXMLPolyDataReader

    directory = asset_directory()
    expected = [structure.key for structure in STRUCTURES] + list(CONTEXT_MESHES)
    missing = [key for key in expected if not (directory / f"{key}.vtp").is_file()]
    if missing:
        raise FileNotFoundError("Missing 3D model files: " + ", ".join(missing)
                                + "\nSee README.md for setup instructions.")
    models = {}
    for key in expected:
        reader = vtkXMLPolyDataReader()
        reader.SetFileName(str(directory / f"{key}.vtp"))
        reader.Update()
        data = reader.GetOutput()
        if not data.GetNumberOfPoints():
            raise ValueError(f"3D model is empty or unreadable: {key}")
        models[key] = data
    return models
