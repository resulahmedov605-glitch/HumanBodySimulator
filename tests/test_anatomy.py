"""Validate asset provenance and useful search behavior without opening a GUI."""

import hashlib
import json
import unittest

from app.anatomy import CONTEXT_MESHES, STRUCTURES, asset_directory, matching_structures


class AnatomyDataTests(unittest.TestCase):
    def test_english_and_latin_search(self):
        self.assertEqual(len(matching_structures("KIDNEY")), 2)
        self.assertEqual(len(matching_structures("brain")), 1)
        self.assertEqual(len(matching_structures("lung")), 2)
        self.assertEqual(len(matching_structures("pulmo")), 2)
        self.assertEqual([s.key for s in matching_structures("cor", "Cardiovascular system")], ["heart"])
        self.assertEqual(matching_structures("unknown-organ"), [])

    def test_assets_match_manifest(self):
        directory = asset_directory()
        manifest = json.loads((directory / "manifest.json").read_text())
        self.assertEqual(set(manifest["meshes"]), {s.key for s in STRUCTURES} | set(CONTEXT_MESHES))
        for key, info in manifest["meshes"].items():
            with self.subTest(mesh=key):
                data = (directory / info["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), info["sha256"])
                self.assertGreater(info["points"], 0)
                self.assertGreater(info["triangles"], 0)

    def test_organs_use_shared_body_coordinates(self):
        # Catches accidentally recentering each mesh during conversion.
        manifest = json.loads((asset_directory() / "manifest.json").read_text())
        meshes = manifest["meshes"]
        brain_z = sum(meshes["brain"]["bounds"][4:6]) / 2
        heart_z = sum(meshes["heart"]["bounds"][4:6]) / 2
        bladder_z = sum(meshes["bladder"]["bounds"][4:6]) / 2
        self.assertGreater(brain_z, heart_z)
        self.assertGreater(heart_z, bladder_z)


if __name__ == "__main__":
    unittest.main()
