from fastapi import APIRouter

router = APIRouter()

@router.get("/healthz")
@router.head("/healthz")
async def health_check():
    return {"status": "ok"}
