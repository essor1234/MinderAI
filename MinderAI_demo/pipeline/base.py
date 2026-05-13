"""Base Pipeline Abstract Class"""

from abc import ABC, abstractmethod
from typing import Dict


class BasePipeline(ABC):
    """Abstract base class defining pipeline interface"""

    @abstractmethod
    def run_synchronous_phases(self, worker_input: str) -> Dict:
        """Run Phases 1-5: parse, score, normalize, select, and respond synchronously"""
        pass

    @abstractmethod
    def run_asynchronous_phases(self, context: Dict) -> Dict:
        """Run Phases 6-7: reflect and plan asynchronously"""
        pass
