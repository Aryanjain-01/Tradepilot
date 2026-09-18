from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.trading import PipelineRequest, PipelineResponse
from app.services.trading_pipeline import trading_pipeline_service
import logging

router = APIRouter(prefix="/api/trading", tags=["trading"])
logger = logging.getLogger(__name__)

@router.post("/analyze-and-execute", response_model=PipelineResponse)
def analyze_and_execute(req: PipelineRequest, db: Session = Depends(get_db)):
    logger.info(f"Pipeline started for symbol: {req.symbol}")
    result = trading_pipeline_service.analyze_and_execute(db, req)
    
    logger.info(f"Pipeline result for {req.symbol}: Status={result.status}, Signal={result.signal}, Reason={result.reason}")
    if result.status == "FILLED" and result.execution:
        logger.info(f"Execution successful. Order ID: {result.execution.get('order_id')}, Quantity: {result.execution.get('quantity')}")
        
    return result
