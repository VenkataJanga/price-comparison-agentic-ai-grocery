from pydantic import BaseModel
class AuthState(BaseModel):
    phone: str
    otp_pending: bool = True
