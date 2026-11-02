"""Convert an official BodyParts3D 4.0 archive to compact offline VTK meshes.

See assets/ATTRIBUTION.md for source URLs and licensing. This script reads only
named OBJ members; it does not extract archive paths onto the filesystem.
"""

import argparse
import csv
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.anatomy import CONTEXT_MESHES, STRUCTURES, asset_directory
from vtkmodules.vtkFiltersCore import (
    vtkAppendPolyData, vtkCleanPolyData, vtkPolyDataNormals,
    vtkQuadricDecimation, vtkTriangleFilter,
)
from vtkmodules.vtkIOGeometry import vtkOBJReader
from vtkmodules.vtkIOXML import vtkXMLPolyDataWriter


def build(archive_path: Path, parts_path: Path, elements_path: Path):
    representations = {}
    with parts_path.open(encoding="utf-8-sig") as stream:
        for row in list(csv.reader(stream, delimiter="\t"))[1:]:
            if len(row) >= 3:
                representations[row[1]] = (row[0], row[2])
    elements = defaultdict(list)
    with elements_path.open(encoding="utf-8-sig") as stream:
        for row in list(csv.reader(stream, delimiter="\t"))[1:]:
            if len(row) >= 3:
                elements[row[0]].append(row[2])

    targets = {structure.key: structure.representation for structure in STRUCTURES}
    targets.update(CONTEXT_MESHES)
    destination = asset_directory()
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "BodyParts3D 4.0, Database Center for Life Science (DBCLS)",
        "license": "CC BY 4.0",
        "license_url": "https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html",
        "archive_url": "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_BP3D_4.0_obj_99.zip",
        "changes": "PART-OF elements grouped by organ; triangulated, merged, cleaned, decimated and converted to VTK XML PolyData. Original shared coordinates preserved.",
        "meshes": {},
    }

    with zipfile.ZipFile(archive_path) as archive, tempfile.TemporaryDirectory() as temp:
        members = {Path(name).stem: name for name in archive.namelist() if name.endswith(".obj")}
        for key, representation in targets.items():
            concept, source_name = representations[representation]
            components = sorted(set(elements[concept]))
            if not components:
                raise ValueError(f"No element mapping for {key} / {concept}")
            missing = set(components) - members.keys()
            if missing:
                raise ValueError(f"Missing components for {key}: {sorted(missing)}")
            append = vtkAppendPolyData()
            for component in components:
                obj_path = Path(temp) / f"{component}.obj"
                obj_path.write_bytes(archive.read(members[component]))
                reader = vtkOBJReader()
                reader.SetFileName(str(obj_path))
                reader.Update()
                mesh = reader.GetOutput()
                if not mesh.GetNumberOfPoints():
                    raise ValueError(f"Empty component: {component}")
                append.AddInputData(mesh)
            triangles = vtkTriangleFilter()
            triangles.SetInputConnection(append.GetOutputPort())
            clean = vtkCleanPolyData()
            clean.SetInputConnection(triangles.GetOutputPort())
            clean.Update()
            original_cells = clean.GetOutput().GetNumberOfCells()
            budget = 100_000 if key == "skeleton" else 45_000
            decimate = vtkQuadricDecimation()
            decimate.SetInputConnection(clean.GetOutputPort())
            decimate.SetTargetReduction(max(0, 1 - budget / max(original_cells, 1)))
            normals = vtkPolyDataNormals()
            normals.SetInputConnection(decimate.GetOutputPort())
            normals.SplittingOff()
            normals.ConsistencyOn()
            normals.Update()
            output = destination / f"{key}.vtp"
            writer = vtkXMLPolyDataWriter()
            writer.SetFileName(str(output))
            writer.SetInputConnection(normals.GetOutputPort())
            writer.SetDataModeToBinary()
            writer.SetCompressorTypeToZLib()
            if writer.Write() != 1:
                raise OSError(f"Could not write {output}")
            data = normals.GetOutput()
            manifest["meshes"][key] = {
                "file": output.name,
                "representation": representation,
                "concept": concept,
                "source_name": source_name,
                "elements": components,
                "points": data.GetNumberOfPoints(),
                "triangles": data.GetNumberOfCells(),
                "bounds": list(data.GetBounds()),
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            }
            print(f"{key}: {len(components)} elements, {data.GetNumberOfCells():,} triangles", flush=True)
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--parts-list", required=True, type=Path)
    parser.add_argument("--elements-list", required=True, type=Path)
    args = parser.parse_args()
    build(args.archive, args.parts_list, args.elements_list)
