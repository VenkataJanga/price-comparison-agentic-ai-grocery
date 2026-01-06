from fastapi import APIRouter, Request


from connectors.worker.client import WorkerClient

router = APIRouter()

@router.get("/status")
async def platforms_status():
    return {"platforms": {"jiomart": "ok", "bigbasket": "degraded"}}



@router.get("/platforms/worker/health")
def worker_health(request: Request):
    client = WorkerClient(env="dev")
    if not client.enabled:
        return {"status": "disabled"}
    try:
        resp = client.health(correlation_id=request.headers.get("X-Correlation-ID"))
        return resp.model_dump()
    except Exception as e:
        return {"status": "down", "message": str(e)}