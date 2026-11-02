# 3D anatomical model attribution

**BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International.**

- Publisher: Database Center for Life Science (DBCLS), Japan.
- Dataset: BodyParts3D 4.0, PART-OF tree, 99% polygon-reduction archive.
- Download page: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- Publisher's current license page (updated 2025-02-27): https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- License: https://creativecommons.org/licenses/by/4.0/
- Original archive: https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_BP3D_4.0_obj_99.zip
- Concept / representation mapping: https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_parts_list_e.txt
- Concept / element mapping: https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/partof_element_parts.txt

Changes made for this application: constituent meshes were grouped by organ,
triangulated, merged, cleaned, simplified where needed, and converted to
compressed VTK XML PolyData (`.vtp`). Vertex coordinates remain in the source
coordinate system so that organs keep their anatomical positions. Display
colors and transparency are application styling. Provenance and file hashes
are recorded in `anatomy/manifest.json`.

The model represents the dataset's adult male subject; it is not personalized
to the person using the application. Model geometry is a static educational
reference. The application does not simulate clinical physiology.

Earlier copies and third-party mirrors may display an older license. This
application obtains data directly from the official archive and records the
publisher's current CC BY 4.0 terms above.

Reference publication: Mitsuhashi et al. (2009), *BodyParts3D: 3D structure
database for anatomical concepts*, Nucleic Acids Research 37, D782–D785.
https://doi.org/10.1093/nar/gkn613
