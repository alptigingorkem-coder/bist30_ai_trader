import os
import json
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from utils.db_manager import DBManager
from utils.logging_config import get_logger

log = get_logger("API")

app = FastAPI(title="BIST30 AI Trader API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
db = DBManager()

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                log.error(f"WS Broadcast error: {e}")

manager = ConnectionManager()

# --- Models ---
class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float

# --- Routes ---

@app.get("/")
def read_root():
    return {"status": "ok", "service": "BIST30 AI Trader API"}

@app.get("/api/market-data/{symbol}", response_model=List[Candle])
def get_market_data(symbol: str, limit: int = 500):
    """Fetches historical candles from TimescaleDB."""
    try:
        conn = db.get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="DB connection failed")
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT time, open, high, low, close, volume
                    FROM market_data
                    WHERE symbol = %s
                    ORDER BY time DESC
                    LIMIT %s
                """, (symbol, limit))
                rows = cur.fetchall()
        finally:
            db.return_connection(conn)
        
        if not rows:
            return []
        
        # Reverse to chronological order and convert
        candles = []
        for row in reversed(rows):
            candles.append({
                "time": str(row[0].date()) if hasattr(row[0], 'date') else str(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]) if row[5] else 0.0
            })
            
        return candles
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"API Error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
def get_portfolio():
    # Placeholder for portfolio data
    # Ideally fetch from a 'portfolio' table in DB
    return {
        "cash": 10000.0,
        "equity": 10000.0,
        "positions": []
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages (e.g., subscription requests)
            data = await websocket.receive_text()
            
            # Simple Echo or Command processing
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Background Task for Real-time Updates ---
# In a real app, this would consume a Redis Stream or Queue.
# Here, we simulate a ticker update or poll DB every minute.

import asyncio

async def mock_market_update():
    """Periodically pushes updates to UI."""
    while True:
        await asyncio.sleep(5)
        # Todo: Fetch real latest price from DB and broadcast
        # await manager.broadcast({"type": "MARKET_UPDATE", "data": ...})

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(mock_market_update())
