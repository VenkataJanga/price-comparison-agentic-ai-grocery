from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def price_history():
    return {"history": []}
