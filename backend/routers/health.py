from fastapi import APIRouter

router = APIRouter()

@router.head("/healthz", tags=["health"])
@router.get("/healthz", tags=["health"])
def healthz():
    return {"status": "up"}


from fastapi import APIRouter

router = APIRouter()

