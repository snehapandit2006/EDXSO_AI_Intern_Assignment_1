from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DiscoverySource(ABC):
    """Abstract base class for creator discovery source adapters."""

    def __init__(self, source_name: str, source_url: str, extraction_method: str):
        self.source_name = source_name
        self.source_url = source_url
        self.extraction_method = extraction_method

    @abstractmethod
    def fetch_creators(self, target_count: int = 50) -> List[Dict[str, Any]]:
        """Fetch raw creator records from the discovery source."""
        pass
