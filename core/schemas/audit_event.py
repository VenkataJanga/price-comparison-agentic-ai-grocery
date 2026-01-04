from pydantic import BaseModel
class AuditEvent(BaseModel):
    event: str
    data: dict = {}
