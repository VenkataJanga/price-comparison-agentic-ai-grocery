from abc import ABC, abstractmethod

class PlatformClient(ABC):
    @abstractmethod
    def search(self, q: str):
        raise NotImplementedError
