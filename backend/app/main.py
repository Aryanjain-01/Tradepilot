import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Serve React Frontend
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Serve index.html for all unrecognized paths to let React Router handle them
        # or just serve it if path doesn't map to a static file.
        # But we only mounted /assets. We also need to serve root files like favicon.
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))




