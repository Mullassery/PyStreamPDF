"""OKF Entity Extraction Profiles for PyStreamPDF.

Entity type confidence scores, extraction accuracy by domain,
and hallucination risk profiles for document intelligence.
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
from dataclasses import dataclass


@dataclass
class EntityProfile:
    """Entity extraction confidence profile."""

    entity_type: str  # person, organization, location, date, etc.
    domain: str
    extraction_accuracy: float  # 0-100%
    hallucination_risk: float  # 0-100%
    false_positive_rate: float
    samples: int


class OKFEntityProfiles:
    """Manage entity extraction profiles."""

    def __init__(self, profiles_dir: Path = None):
        self.profiles_dir = profiles_dir or Path.cwd() / "entity_profiles"
        self.profiles_dir.mkdir(exist_ok=True)

    def save_profile(self, profile: EntityProfile) -> None:
        """Save entity profile."""
        filename = f"{profile.entity_type}_{profile.domain}.json"
        with open(self.profiles_dir / filename, 'w') as f:
            json.dump({
                'entity_type': profile.entity_type,
                'domain': profile.domain,
                'extraction_accuracy': profile.extraction_accuracy,
                'hallucination_risk': profile.hallucination_risk,
                'false_positive_rate': profile.false_positive_rate,
                'samples': profile.samples
            }, f, indent=2)

    def get_profile(self, entity_type: str, domain: str) -> Optional[EntityProfile]:
        """Get entity profile."""
        filename = f"{entity_type}_{domain}.json"
        filepath = self.profiles_dir / filename

        if not filepath.exists():
            return None

        with open(filepath) as f:
            data = json.load(f)
            return EntityProfile(**data)

    def rank_entities_by_confidence(self, domain: str) -> List[Dict]:
        """Rank entities by extraction confidence."""
        entities = {}

        for f in self.profiles_dir.glob(f"*_{domain}.json"):
            with open(f) as fp:
                data = json.load(fp)
                entity_type = data['entity_type']
                confidence = data['extraction_accuracy'] * (1 - data['hallucination_risk'] / 100)
                entities[entity_type] = confidence

        return sorted(
            [{'entity': k, 'confidence': v} for k, v in entities.items()],
            key=lambda x: x['confidence'],
            reverse=True
        )

    def is_safe_to_extract(self, entity_type: str, domain: str,
                          confidence_threshold: float = 85.0) -> bool:
        """Check if entity extraction is reliable."""
        profile = self.get_profile(entity_type, domain)
        if not profile:
            return False

        return profile.extraction_accuracy >= confidence_threshold and \
               profile.hallucination_risk < (100 - confidence_threshold)
