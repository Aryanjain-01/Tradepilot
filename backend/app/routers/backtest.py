from fastapi import APIRouter
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.services.backtester import backtest_engine
import logging

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
logger = logging.getLogger(__name__)

@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest):
    logger.info(f"Running backtest for {req.symbol} with Capital={req.initial_capital}, Risk={req.risk_percentage}%")
    result = backtest_engine.run(req)
    logger.info(f"Backtest complete: {result.total_trades} trades, Return={result.return_percentage}%")
    return result
