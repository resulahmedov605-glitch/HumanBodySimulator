"""English learning content and BodyParts3D representation identifiers.

Geometry is provided by DBCLS. Text is a brief educational overview, rather
than a clinical model. Left and right always refer to the subject's body.
"""

from dataclasses import dataclass
from pathlib import Path
import sys
import unicodedata


@dataclass(frozen=True)
class Structure:
    key: str
    name: str
    latin: str
    system: str
    representation: str
    color: str
    summary: str
    function: str
    location: str


STRUCTURES = (
    Structure(
        'brain', 'Brain', 'Encephalon', 'Nervous system', 'BP6687', '#e9b5ac',
        'The brain is the main control center of the nervous system. It processes sensory information and coordinates activities throughout the body.',
        'Supports thought, memory, sensation, and the control of movement.',
        'Inside the cranial cavity of the skull.',
    ),
    Structure(
        'heart', 'Heart', 'Cor', 'Cardiovascular system', 'BP9305', '#e96978',
        'The heart is a muscular organ that pumps blood through the circulatory system. Its right and left sides serve the pulmonary and systemic circulations.',
        'Keeps blood circulating to transport oxygen, nutrients, and waste products.',
        'In the chest, between the lungs.',
    ),
    Structure(
        'aorta', 'Aorta', 'Aorta', 'Cardiovascular system', 'BP10374', '#ee8a78',
        'The aorta is the main artery leaving the left ventricle of the heart. Its branches supply blood to different regions of the body.',
        'Carries oxygen-rich blood from the heart into the systemic circulation.',
        'Passes through the chest and abdomen.',
    ),
    Structure(
        'right_lung', 'Right lung', 'Pulmo dexter', 'Respiratory system', 'BP9359', '#75b7d5',
        'The right lung has three lobes. Its tiny air sacs, called alveoli, provide a surface for gas exchange between air and blood.',
        'Transfers oxygen into the blood and helps remove carbon dioxide.',
        'On the right side of the chest.',
    ),
    Structure(
        'left_lung', 'Left lung', 'Pulmo sinister', 'Respiratory system', 'BP9417', '#75b7d5',
        'The left lung has two lobes and a cardiac notch that accommodates the heart. It participates in gas exchange during breathing.',
        'Exchanges oxygen and carbon dioxide between air and blood.',
        'On the left side of the chest.',
    ),
    Structure(
        'trachea', 'Trachea', 'Trachea', 'Respiratory system', 'BP9373', '#a7d3df',
        'The trachea, or windpipe, connects the larynx to the main bronchi. Cartilage rings help keep this airway open.',
        'Conducts air toward and away from the lungs.',
        'Extends from the neck into the chest.',
    ),
    Structure(
        'liver', 'Liver', 'Hepar', 'Digestive system', 'BP9334', '#b97762',
        'The liver is a large organ involved in metabolism. It processes nutrients, produces bile, and modifies substances carried in the blood.',
        'Produces bile, stores selected nutrients, and processes substances in the blood.',
        'In the upper right abdomen, beneath the diaphragm.',
    ),
    Structure(
        'stomach', 'Stomach', 'Gaster', 'Digestive system', 'BP9480', '#e9aa93',
        'The stomach is a muscular organ between the esophagus and small intestine. It mixes food with digestive juices.',
        'Temporarily stores food and helps break it down for further digestion.',
        'In the upper left abdomen.',
    ),
    Structure(
        'pancreas', 'Pancreas', 'Pancreas', 'Digestive system', 'BP9653', '#e6c987',
        'The pancreas produces digestive enzymes and hormones, including insulin. It has roles in both digestion and blood glucose regulation.',
        'Supplies digestive enzymes and helps regulate blood glucose.',
        'Behind the stomach.',
    ),
    Structure(
        'small_intestine', 'Small intestine', 'Intestinum tenue', 'Digestive system', 'BP9352', '#d99ba3',
        'The small intestine is a long section of the digestive tract after the stomach. Its inner surface provides a large area for nutrient absorption.',
        'Performs much of digestion and absorbs most nutrients.',
        'In the central and lower abdomen.',
    ),
    Structure(
        'large_intestine', 'Large intestine', 'Intestinum crassum', 'Digestive system', 'BP9747', '#c6aa88',
        'The large intestine receives material from the small intestine. It absorbs water and electrolytes from the remaining contents.',
        'Absorbs water and helps form and transport stool.',
        'Runs around much of the small intestine in the abdomen.',
    ),
    Structure(
        'right_kidney', 'Right kidney', 'Ren dexter', 'Urinary system', 'BP10046', '#bd829e',
        'The right kidney is one of two organs that filter blood and produce urine. The kidneys help maintain fluid and electrolyte balance.',
        'Removes waste products and excess fluid from the blood.',
        'At the back of the abdomen, to the right of the spine.',
    ),
    Structure(
        'left_kidney', 'Left kidney', 'Ren sinister', 'Urinary system', 'BP10234', '#bd829e',
        'The left kidney works with the right kidney to filter blood. Together they support the balance of fluids and dissolved substances in the body.',
        'Produces urine and helps maintain fluid and electrolyte balance.',
        'At the back of the abdomen, to the left of the spine.',
    ),
    Structure(
        'bladder', 'Urinary bladder', 'Vesica urinaria', 'Urinary system', 'BP9803', '#dac18c',
        'The urinary bladder is a hollow muscular organ. It collects urine produced by the kidneys and delivered through the ureters.',
        'Temporarily stores urine until it is released from the body.',
        'In the pelvis.',
    ),
)

BY_KEY = {structure.key: structure for structure in STRUCTURES}
SYSTEMS = tuple(dict.fromkeys(structure.system for structure in STRUCTURES))
CONTEXT_MESHES = {"skin": "BP10155", "skeleton": "BP9343"}
ATTRIBUTION = "BodyParts3D, © The Database Center for Life Science · CC BY 4.0"


def asset_directory() -> Path:
    """Support source runs and a future PyInstaller application bundle."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "assets" / "anatomy"


def normalize_search(value: str) -> str:
    value = value.casefold()
    return "".join(char for char in unicodedata.normalize("NFKD", value)
                   if not unicodedata.combining(char))


def matching_structures(query: str = "", system: str | None = None) -> list[Structure]:
    query = normalize_search(query.strip())
    return [structure for structure in STRUCTURES
            if (not system or structure.system == system)
            and query in normalize_search(f"{structure.name} {structure.latin} {structure.system}")]
