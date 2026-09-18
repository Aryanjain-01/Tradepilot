from fastapi import APIRouter
from app.schemas.risk import RiskRequest, RiskResponse
from app.services.risk_manager import risk_manager_service

router = APIRouter(
    prefix="/api/risk",
    tags=["risk"],
)

@router.post("/calculate", response_model=RiskResponse)
def calculate_risk(req: RiskRequest):
    return risk_manager_service.calculate(req)
