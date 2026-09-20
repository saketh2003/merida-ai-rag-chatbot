from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.deps import get_db
from app.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        version="1.0.0"
    )
