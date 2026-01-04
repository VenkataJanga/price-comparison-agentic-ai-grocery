from pydantic import BaseModel
class UserContext(BaseModel):
    pincode: str
    prefs: dict = {}
