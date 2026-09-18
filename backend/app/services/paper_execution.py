import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.paper import PaperAccount, Order, Position, Trade
from app.schemas.paper import OrderRequest, MarketPriceUpdate

class PaperExecutionEngine:
    
    def _get_account(self, db: Session) -> PaperAccount:
        account = db.query(PaperAccount).first()
        if not account:
            account = PaperAccount(
                initial_capital=100000.0,
                available_cash=100000.0,
                used_capital=0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                total_pnl=0.0,
                equity=100000.0
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        return account

    def _update_account_totals(self, db: Session, account: PaperAccount):
        open_positions = db.query(Position).filter(Position.status == "OPEN").all()
        
        unrealized = 0.0
        used_cap = 0.0
        
        for p in open_positions:
            if p.side == "LONG":
                p.unrealized_pnl = (p.current_price - p.entry_price) * p.quantity
            else:
                p.unrealized_pnl = (p.entry_price - p.current_price) * p.quantity
                
            unrealized += p.unrealized_pnl
            used_cap += (p.entry_price * p.quantity) # Margin requirement proxy
            
        account.unrealized_pnl = unrealized
        account.used_capital = used_cap
        account.total_pnl = account.realized_pnl + account.unrealized_pnl
        account.equity = account.initial_capital + account.total_pnl
        db.commit()

    def submit_order(self, db: Session, req: OrderRequest):
        account = self._get_account(db)
        
        if req.order_type == "MARKET" and not req.price:
            from app.services.market_data import market_data_service
            latest = market_data_service.get_latest(req.symbol)
            if not latest or "close" not in latest:
                raise HTTPException(status_code=400, detail="Market price not available for MARKET order")
            req.price = latest["close"]
        elif req.order_type == "LIMIT" and not req.price:
            raise HTTPException(status_code=400, detail="Price is required for LIMIT order")
        
        # Validation for SL/Target
        if req.side == "BUY":
            if req.stop_loss and req.stop_loss >= req.price:
                raise HTTPException(status_code=400, detail="For BUY orders, Stop Loss must be less than Entry Price")
            if req.target and req.target <= req.price:
                raise HTTPException(status_code=400, detail="For BUY orders, Target must be greater than Entry Price")
        elif req.side == "SELL":
            if req.stop_loss and req.stop_loss <= req.price:
                raise HTTPException(status_code=400, detail="For SELL orders, Stop Loss must be greater than Entry Price")
            if req.target and req.target >= req.price:
                raise HTTPException(status_code=400, detail="For SELL orders, Target must be less than Entry Price")

        cost = req.price * req.quantity
        position = db.query(Position).filter(Position.symbol == req.symbol, Position.status == "OPEN").first()

        # Handle crossing sides - Reject per requirements
        if position:
            if req.side == "SELL" and position.side == "LONG" and req.quantity > position.quantity:
                raise HTTPException(status_code=400, detail="Selling more than available LONG quantity is not allowed. Close position first.")
            if req.side == "BUY" and position.side == "SHORT" and req.quantity > position.quantity:
                raise HTTPException(status_code=400, detail="Buying more than available SHORT quantity is not allowed. Close position first.")

        # Cash validation for OPENING positions
        if req.side == "BUY" and (not position or position.side == "LONG"):
            if account.available_cash < cost:
                raise HTTPException(status_code=400, detail="Insufficient available cash")
        elif req.side == "SELL" and (not position or position.side == "SHORT"):
            if account.available_cash < cost: # Assuming 1x margin for shorts
                raise HTTPException(status_code=400, detail="Insufficient available cash for short selling")

        # Create Order
        order = Order(
            order_id=f"TP-{uuid.uuid4().hex[:6].upper()}",
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            requested_price=req.price,
            status="FILLED",
            filled_price=req.price,
            filled_at=datetime.utcnow()
        )
        db.add(order)
        db.commit()

        if req.side == "BUY":
            if position and position.side == "SHORT":
                # Close/Reduce SHORT
                realized_pnl = (position.entry_price - req.price) * req.quantity
                account.realized_pnl += realized_pnl
                account.available_cash += (position.entry_price * req.quantity) + realized_pnl
                
                trade = Trade(
                    trade_id=f"TR-{uuid.uuid4().hex[:6].upper()}",
                    order_id=order.order_id,
                    symbol=req.symbol,
                    side="BUY",
                    quantity=req.quantity,
                    entry_price=position.entry_price,
                    exit_price=req.price,
                    realized_pnl=realized_pnl,
                    opened_at=position.opened_at
                )
                db.add(trade)
                
                position.quantity -= req.quantity
                if position.quantity == 0:
                    position.status = "CLOSED"
                    position.closed_at = datetime.utcnow()
                    position.unrealized_pnl = 0
            else:
                # Open/Increase LONG
                account.available_cash -= cost
                if position:
                    total_qty = position.quantity + req.quantity
                    new_avg = ((position.entry_price * position.quantity) + (req.price * req.quantity)) / total_qty
                    position.quantity = total_qty
                    position.entry_price = new_avg
                    position.current_price = req.price
                    if req.stop_loss: position.stop_loss = req.stop_loss
                    if req.target: position.target = req.target
                else:
                    position = Position(
                        symbol=req.symbol,
                        side="LONG",
                        quantity=req.quantity,
                        entry_price=req.price,
                        current_price=req.price,
                        stop_loss=req.stop_loss,
                        target=req.target,
                        status="OPEN"
                    )
                    db.add(position)
                    
        elif req.side == "SELL":
            if position and position.side == "LONG":
                # Close/Reduce LONG
                realized_pnl = (req.price - position.entry_price) * req.quantity
                account.realized_pnl += realized_pnl
                account.available_cash += (position.entry_price * req.quantity) + realized_pnl
                
                trade = Trade(
                    trade_id=f"TR-{uuid.uuid4().hex[:6].upper()}",
                    order_id=order.order_id,
                    symbol=req.symbol,
                    side="SELL",
                    quantity=req.quantity,
                    entry_price=position.entry_price,
                    exit_price=req.price,
                    realized_pnl=realized_pnl,
                    opened_at=position.opened_at
                )
                db.add(trade)
                
                position.quantity -= req.quantity
                if position.quantity == 0:
                    position.status = "CLOSED"
                    position.closed_at = datetime.utcnow()
                    position.unrealized_pnl = 0
            else:
                # Open/Increase SHORT
                account.available_cash -= cost
                if position:
                    total_qty = position.quantity + req.quantity
                    new_avg = ((position.entry_price * position.quantity) + (req.price * req.quantity)) / total_qty
                    position.quantity = total_qty
                    position.entry_price = new_avg
                    position.current_price = req.price
                    if req.stop_loss: position.stop_loss = req.stop_loss
                    if req.target: position.target = req.target
                else:
                    position = Position(
                        symbol=req.symbol,
                        side="SHORT",
                        quantity=req.quantity,
                        entry_price=req.price,
                        current_price=req.price,
                        stop_loss=req.stop_loss,
                        target=req.target,
                        status="OPEN"
                    )
                    db.add(position)
                    
        db.commit()
        self._update_account_totals(db, account)
        return order

    def update_market_price(self, db: Session, update: MarketPriceUpdate):
        account = self._get_account(db)
        
        position = db.query(Position).filter(Position.symbol == update.symbol, Position.status == "OPEN").first()
        if not position:
            return {"message": "No open position to update"}
            
        position.current_price = update.price
        db.commit()
        self._update_account_totals(db, account)
        
        # Check targets and stops
        status_update = None
        if position.side == "LONG":
            if position.stop_loss and position.current_price <= position.stop_loss:
                status_update = "STOPPED_OUT"
            elif position.target and position.current_price >= position.target:
                status_update = "TARGET_HIT"
        else: # SHORT
            if position.stop_loss and position.current_price >= position.stop_loss:
                status_update = "STOPPED_OUT"
            elif position.target and position.current_price <= position.target:
                status_update = "TARGET_HIT"
            
        if status_update:
            # Auto-close position
            if position.side == "LONG":
                realized_pnl = (position.current_price - position.entry_price) * position.quantity
                exit_side = "SELL"
            else:
                realized_pnl = (position.entry_price - position.current_price) * position.quantity
                exit_side = "BUY"
                
            account.realized_pnl += realized_pnl
            account.available_cash += (position.entry_price * position.quantity) + realized_pnl
            
            trade = Trade(
                trade_id=f"TR-{uuid.uuid4().hex[:6].upper()}",
                order_id="AUTO-CLOSE",
                symbol=position.symbol,
                side=exit_side,
                quantity=position.quantity,
                entry_price=position.entry_price,
                exit_price=position.current_price,
                realized_pnl=realized_pnl,
                opened_at=position.opened_at
            )
            db.add(trade)
            
            position.status = status_update
            position.closed_at = datetime.utcnow()
            position.unrealized_pnl = 0
            position.quantity = 0
            
            db.commit()
            self._update_account_totals(db, account)
            return {"message": f"Position automatically closed: {status_update}"}
            
        return {"message": "Price updated successfully"}

    def cancel_order(self, db: Session, order_id: str):
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.status == "FILLED":
            raise HTTPException(status_code=400, detail="Cannot cancel a FILLED order")
            
        order.status = "CANCELLED"
        db.commit()
        return order

    def close_position(self, db: Session, symbol: str):
        position = db.query(Position).filter(Position.symbol == symbol, Position.status == "OPEN").first()
        if not position:
            raise HTTPException(status_code=404, detail="Open position not found")
            
        close_side = "SELL" if position.side == "LONG" else "BUY"
            
        # Simulate market order at current price
        return self.submit_order(db, OrderRequest(
            symbol=symbol,
            side=close_side,
            quantity=position.quantity,
            order_type="LIMIT",
            price=position.current_price
        ))

paper_engine = PaperExecutionEngine()
