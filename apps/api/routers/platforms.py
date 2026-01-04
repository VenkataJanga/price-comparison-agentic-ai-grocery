from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def platforms_status():
    return {"platforms": {"jiomart": "ok", "bigbasket": "degraded"}}
