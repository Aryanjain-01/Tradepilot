from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import market, indicators, strategy, risk, broker, paper, trading, backtest
import app.models.paper  # Ensure models are registered

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TradePilot API")

# Configure CORS so the frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

app.include_router(market.router)
app.include_router(indicators.router)
app.include_router(strategy.router)
app.include_router(risk.router)
app.include_router(broker.router)
app.include_router(paper.router)
app.include_router(trading.router)
app.include_router(backtest.router)




