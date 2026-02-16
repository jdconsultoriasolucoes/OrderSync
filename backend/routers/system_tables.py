from fastapi import APIRouter

router = APIRouter(prefix="/system_tables", tags=["System Tables"])

@router.get("/")
def get_system_tables():
    return {"message": "System tables placeholder"}
