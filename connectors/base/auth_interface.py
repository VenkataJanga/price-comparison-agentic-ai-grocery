from abc import ABC, abstractmethod

class AuthInterface(ABC):
    @abstractmethod
    def login(self, credentials: dict):
        pass

    @abstractmethod
    def request_otp(self, phone: str):
        pass

    @abstractmethod
    def submit_otp(self, phone: str, otp: str):
        pass
