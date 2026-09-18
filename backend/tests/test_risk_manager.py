import pytest
from fastapi import HTTPException
from app.schemas.risk import RiskRequest
from app.services.risk_manager import risk_manager_service

def test_risk_manager_long_valid():
    req = RiskRequest(
        capital=100000,
        risk_percentage=1,
        entry_price=500,
        stop_loss=480,
        target=560,
        direction="LONG"
    )
    res = risk_manager_service.calculate(req)
    
    assert res.maximum_risk == 1000
    assert res.risk_per_share == 20
    assert res.position_size == 50
    assert res.potential_loss == 1000
    assert res.potential_profit == 3000
    assert res.risk_reward_ratio == "1:3.0"

def test_risk_manager_short_valid():
    req = RiskRequest(
        capital=50000,
        risk_percentage=2,
        entry_price=100,
        stop_loss=110,
        target=80,
        direction="SHORT"
    )
    res = risk_manager_service.calculate(req)
    
    assert res.maximum_risk == 1000
    assert res.risk_per_share == 10
    assert res.position_size == 100
    assert res.potential_loss == 1000
    assert res.potential_profit == 2000
    assert res.risk_reward_ratio == "1:2.0"

def test_risk_manager_long_invalid_setup():
    req = RiskRequest(
        capital=100000,
        risk_percentage=1,
        entry_price=500,
        stop_loss=520, # Stop loss above entry for LONG
        target=560,
        direction="LONG"
    )
    with pytest.raises(HTTPException) as exc_info:
        risk_manager_service.calculate(req)
    assert exc_info.value.status_code == 400
    assert "Invalid LONG setup" in exc_info.value.detail

def test_risk_manager_short_invalid_setup():
    req = RiskRequest(
        capital=50000,
        risk_percentage=2,
        entry_price=100,
        stop_loss=110,
        target=120, # Target above entry for SHORT
        direction="SHORT"
    )
    with pytest.raises(HTTPException) as exc_info:
        risk_manager_service.calculate(req)
    assert exc_info.value.status_code == 400
    assert "Invalid SHORT setup" in exc_info.value.detail

def test_risk_manager_zero_risk_per_share():
    req = RiskRequest(
        capital=10000,
        risk_percentage=1,
        entry_price=500,
        stop_loss=500, # Same as entry
        target=600,
        direction="LONG"
    )
    with pytest.raises(HTTPException) as exc_info:
        risk_manager_service.calculate(req)
    assert exc_info.value.status_code == 400
    assert "Invalid LONG setup" in exc_info.value.detail # It will fail the < check first
