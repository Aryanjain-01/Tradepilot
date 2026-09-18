from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.schemas.trading import PipelineRequest, PipelineResponse
from app.services.market_data import market_data_service
from app.services.indicators import indicator_service
from app.services.strategy import strategy_service
from app.services.risk_manager import risk_manager_service
from app.services.paper_execution import paper_engine
from app.schemas.risk import RiskRequest
from app.schemas.paper import OrderRequest

class TradingPipelineService:
    def analyze_and_execute(self, db: Session, req: PipelineRequest) -> PipelineResponse:
        symbol = req.symbol
        
        # 1. Market Data
        latest_data = market_data_service.get_latest(symbol)
        if not latest_data or "close" not in latest_data:
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                reason="Market data unavailable"
            )
            
        current_price = latest_data["close"]

        # 2. Strategy & Indicators
        # The strategy service automatically fetches indicators from indicator_service
        strategy_result = strategy_service.evaluate(symbol)
        if not strategy_result:
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                reason="Strategy evaluation failed or insufficient data"
            )
            
        signal = strategy_result.get("signal", "HOLD")
        
        conditions = strategy_result.get("conditions", {})
        cond_str = ", ".join([f"{k.upper()}: {v}" for k, v in conditions.items()])
        
        if signal == "HOLD":
            return PipelineResponse(
                symbol=symbol,
                status="NO_TRADE",
                current_price=current_price,
                signal="HOLD",
                strategy_reason=f"Conditions: {cond_str}",
                reason="Strategy returned HOLD"
            )

        # 3. Check Existing Position
        # The prompt says: "Check whether there is already an active position for the same symbol and direction. If an existing position is present: Do not create another order..."
        # We can just prevent ANY existing position for simplicity as per requirement.
        from app.models.paper import Position
        existing_positions = db.query(Position).filter(Position.status == "OPEN").all()
        if any(p.symbol == symbol for p in existing_positions):
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                current_price=current_price,
                signal=signal,
                strategy_reason=f"Conditions: {cond_str}",
                reason="Existing position already open for this symbol"
            )

        # 4. Risk Validation & Sizing
        account = paper_engine._get_account(db)
        capital = account.available_cash
        
        # If SL and Target are not provided, we can't size properly.
        # But wait, we need SL and Target for RiskRequest.
        sl = req.stop_loss
        tg = req.target
        
        if not sl or not tg:
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                current_price=current_price,
                signal=signal,
                strategy_reason=f"Conditions: {cond_str}",
                reason="Stop loss and target are required for risk sizing"
            )
            
        # Direction for Risk Calculation
        direction = "LONG" if signal == "BUY" else "SHORT"
        
        risk_req = RiskRequest(
            capital=capital,
            risk_percentage=req.risk_percentage,
            entry_price=current_price,
            stop_loss=sl,
            target=tg,
            direction=direction
        )
        
        try:
            risk_resp = risk_manager_service.calculate(risk_req)
        except HTTPException as e:
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                current_price=current_price,
                signal=signal,
                strategy_reason=f"Conditions: {cond_str}",
                reason=e.detail
            )
            
        if risk_resp.position_size <= 0:
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                current_price=current_price,
                signal=signal,
                strategy_reason=f"Conditions: {cond_str}",
                risk=risk_resp.model_dump(),
                reason="Calculated position size is 0 (Risk too low or Capital too small)"
            )
            
        # 5. Paper Order Execution
        order_req = OrderRequest(
            symbol=symbol,
            side=signal,
            quantity=risk_resp.position_size,
            order_type="MARKET",
            price=current_price, # Provide current price as fallback, though engine fetches it
            stop_loss=sl,
            target=tg
        )
        
        try:
            order_resp = paper_engine.submit_order(db, order_req)
        except HTTPException as e:
            return PipelineResponse(
                symbol=symbol,
                status="REJECTED",
                current_price=current_price,
                signal=signal,
                strategy_reason=f"Conditions: {cond_str}",
                risk=risk_resp.model_dump(),
                reason=f"Paper execution failed: {e.detail}"
            )
            
        # 6. Fetch New Position State
        all_pos = db.query(Position).filter(Position.status == "OPEN").all()
        new_pos = next((p for p in all_pos if p.symbol == symbol), None)
        
        pos_dict = {
            "symbol": new_pos.symbol,
            "side": new_pos.side,
            "quantity": new_pos.quantity,
            "entry_price": new_pos.entry_price,
            "status": new_pos.status
        } if new_pos else None
        
        return PipelineResponse(
            symbol=symbol,
            status="FILLED",
            current_price=current_price,
            signal=signal,
            strategy_reason=f"Conditions: {cond_str}",
            risk=risk_resp.model_dump(),
            execution={
                "order_id": order_resp.order_id,
                "side": order_resp.side,
                "quantity": order_resp.quantity,
                "price": order_resp.filled_price,
                "status": order_resp.status
            },
            position=pos_dict
        )

trading_pipeline_service = TradingPipelineService()
