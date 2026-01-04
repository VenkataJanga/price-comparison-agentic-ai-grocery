from fastapi import FastAPI
app = FastAPI(title="Grocery Price Compare API")

@app.get("/")
async def root():
    return {"status": "ok"}
