from abc import ABC, abstractmethod
from typing import Dict, List, Any

class DataSource(ABC):
    @abstractmethod
    def find_awb(self, awb: str) -> Dict:
        """AWB arama metodu"""
        pass

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_all_data(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass
