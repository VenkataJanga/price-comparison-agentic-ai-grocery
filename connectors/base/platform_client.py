from abc import ABC, abstractmethod

class PlatformClient(ABC):
    @abstractmethod
    def search(self, query: str):
        raise NotImplementedError
