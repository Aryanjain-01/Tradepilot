import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

from sqlalchemy.pool import StaticPool

# Create a test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

import app.models.paper # Ensure models are registered for tests

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_paper_buy_order_and_sell_order():
    # 1. Buy 10 shares of RELIANCE at 1420
    response = client.post("/api/paper/orders", json={
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 10,
        "order_type": "LIMIT",
        "price": 1420.0
    })
    assert response.status_code == 200
    assert response.json()["status"] == "FILLED"
    
    # 2. Check Account Cash decreased by 14200
    account_res = client.get("/api/paper/account")
    assert account_res.status_code == 200
    account = account_res.json()
    assert account["available_cash"] == 100000.0 - 14200.0
    
    # 3. Check Position is LONG
    pos_res = client.get("/api/paper/positions")
    positions = pos_res.json()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "RELIANCE"
    assert positions[0]["side"] == "LONG"
    assert positions[0]["quantity"] == 10
    
    # 4. Simulate Market Price Change
    client.post("/api/paper/market-price", json={
        "symbol": "RELIANCE",
        "price": 1435.0
    })
    
    # 5. Check Unrealized P&L
    pos_res2 = client.get("/api/paper/positions/RELIANCE")
    assert pos_res2.status_code == 200
    pos2 = pos_res2.json()
    assert pos2["unrealized_pnl"] == 150.0  # (1435 - 1420) * 10
    
    # 6. Sell 10 shares at 1435
    response2 = client.post("/api/paper/orders", json={
        "symbol": "RELIANCE",
        "side": "SELL",
        "quantity": 10,
        "order_type": "LIMIT",
        "price": 1435.0
    })
    assert response2.status_code == 200
    assert response2.json()["status"] == "FILLED"
    
    # 7. Check Realized P&L and available cash
    account_res2 = client.get("/api/paper/account")
    account2 = account_res2.json()
    assert account2["realized_pnl"] == 150.0
    assert account2["available_cash"] == 100000.0 + 150.0 # 100,150

def test_paper_buy_insufficient_cash():
    response = client.post("/api/paper/orders", json={
        "symbol": "RELIANCE",
        "side": "BUY",
        "quantity": 100,
        "order_type": "LIMIT",
        "price": 2000.0 # Cost = 200,000 > 100,000
    })
    assert response.status_code == 400
    assert "Insufficient available cash" in response.json()["detail"]

def test_paper_stop_loss_hit():
    # Buy at 100, SL at 90
    client.post("/api/paper/orders", json={
        "symbol": "TCS",
        "side": "BUY",
        "quantity": 10,
        "order_type": "LIMIT",
        "price": 100.0,
        "stop_loss": 90.0
    })
    
    # Simulate price drop to 85
    res = client.post("/api/paper/market-price", json={
        "symbol": "TCS",
        "price": 85.0
    })
    assert res.json()["message"] == "Position automatically closed: STOPPED_OUT"
    
    # Verify account realized P&L is -150
    account_res = client.get("/api/paper/account")
    account = account_res.json()
    assert account["realized_pnl"] == -150.0
