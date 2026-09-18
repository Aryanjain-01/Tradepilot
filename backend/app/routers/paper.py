from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.paper import Order, Position, Trade
from app.schemas.paper import OrderRequest, OrderResponse, PositionResponse, AccountResponse, MarketPriceUpdate, TradeResponse
from app.services.paper_execution import paper_engine

router = APIRouter(
    prefix="/api/paper",
    tags=["paper"],
)

@router.post("/orders", response_model=OrderResponse)
def submit_paper_order(req: OrderRequest, db: Session = Depends(get_db)):
    return paper_engine.submit_order(db, req)

@router.get("/orders", response_model=List[OrderResponse])
def get_recent_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.created_at.desc()).limit(50).all()

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_paper_order(order_id: str, db: Session = Depends(get_db)):
    return paper_engine.cancel_order(db, order_id)

@router.get("/positions", response_model=List[PositionResponse])
def get_all_positions(db: Session = Depends(get_db)):
    return db.query(Position).filter(Position.status == "OPEN").all()

@router.get("/positions/{symbol}", response_model=PositionResponse)
def get_symbol_position(symbol: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    position = db.query(Position).filter(Position.symbol == symbol, Position.status == "OPEN").first()
    if not position:
        raise HTTPException(status_code=404, detail="Open position not found for symbol")
    return position

@router.get("/trades", response_model=List[TradeResponse])
def get_recent_trades(db: Session = Depends(get_db)):
    return db.query(Trade).order_by(Trade.id.desc()).limit(50).all()

@router.post("/positions/{symbol}/close", response_model=OrderResponse)
def close_position_manually(symbol: str, db: Session = Depends(get_db)):
    return paper_engine.close_position(db, symbol)

@router.get("/account", response_model=AccountResponse)
def get_account_summary(db: Session = Depends(get_db)):
    return paper_engine._get_account(db)

@router.post("/market-price")
def simulate_market_price(req: MarketPriceUpdate, db: Session = Depends(get_db)):
    return paper_engine.update_market_price(db, req)
