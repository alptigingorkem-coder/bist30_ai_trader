
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import yfinance as yf
import pandas as pd
import random
import threading
import uuid

# Add project root to path to import backend modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dynamic backtest module
from core.dynamic_backtest import run_dynamic_backtest, validate_dates

app = FastAPI()

# Backtest job storage (in-memory)
backtest_jobs: Dict[str, Dict] = {}

# CORS Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class BacktestRequest(BaseModel):
    train_start: str = "2015-01-01"
    train_end: str = "2021-01-01"
    test_end: str = "2024-12-31"
    initial_capital: float = 100000

class BacktestStatus(BaseModel):
    job_id: str
    status: str  # 'pending', 'running', 'completed', 'error'
    progress: int = 0
    message: str = ""
    result: Optional[Dict] = None

@app.get("/")
async def root():
    return {"message": "BIST30 AI Trader API çalışıyor", "docs": "/docs"}

# Configuration
PORTFOLIO_STATE_FILE = "../logs/paper_trading/portfolio_state.json"
# BIST 30 ve Tier-1 Hisseleri
TICKERS = [
    "AKBNK.IS", "ALARK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS",
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS",
    "GUBRF.IS", "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KONTR.IS",
    "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS",
    "TCELL.IS", "THYAO.IS", "TOASO.IS", "TSKB.IS", "TTKOM.IS",
    "TUPRS.IS", "YKBNK.IS"
]

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# ---------------------------------------------------------
# Backtest Functions
# ---------------------------------------------------------

def run_backtest_job(job_id: str, request: BacktestRequest):
    """
    Background'da backtest çalıştır.
    """
    global backtest_jobs
    
    try:
        backtest_jobs[job_id]["status"] = "running"
        backtest_jobs[job_id]["message"] = "Model eğitiliyor..."
        
        def progress_callback(step: str, pct: int):
            backtest_jobs[job_id]["progress"] = pct
            backtest_jobs[job_id]["message"] = step
        
        result = run_dynamic_backtest(
            train_start=request.train_start,
            train_end=request.train_end,
            test_end=request.test_end,
            initial_capital=request.initial_capital,
            progress_callback=progress_callback
        )
        
        if result["success"]:
            backtest_jobs[job_id]["status"] = "completed"
            backtest_jobs[job_id]["progress"] = 100
            backtest_jobs[job_id]["message"] = "Tamamlandı!"
            backtest_jobs[job_id]["result"] = result
        else:
            backtest_jobs[job_id]["status"] = "error"
            backtest_jobs[job_id]["message"] = result.get("error", "Bilinmeyen hata")
            
    except Exception as e:
        import traceback
        traceback.print_exc() # Hatanın detayını konsola bas
        backtest_jobs[job_id]["status"] = "error"
        backtest_jobs[job_id]["message"] = str(e)


@app.post("/api/backtest/run")
async def start_backtest(request: BacktestRequest):
    """
    Dinamik backtest başlat.
    Backtest arka planda çalışır, job_id döner.
    """
    # Validasyon
    validation = validate_dates(request.train_start, request.train_end, request.test_end)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    # Job oluştur
    job_id = str(uuid.uuid4())
    backtest_jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "message": "Kuyrukta...",
        "result": None
    }
    
    # Background thread başlat
    thread = threading.Thread(target=run_backtest_job, args=(job_id, request))
    thread.start()
    
    return {"success": True, "job_id": job_id}


@app.get("/api/backtest/status/{job_id}")
async def get_backtest_status(job_id: str):
    """
    Backtest job durumunu sorgula.
    """
    if job_id not in backtest_jobs:
        return {"success": False, "error": "Job bulunamadı"}
    
    job = backtest_jobs[job_id]
    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "result": job["result"]
    }


@app.post("/api/backtest/validate")
async def validate_backtest_params(request: BacktestRequest):
    """
    Backtest parametrelerini validate et (çalıştırmadan).
    """
    validation = validate_dates(request.train_start, request.train_end, request.test_end)
    return validation


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def load_portfolio_state():
    """Load portfolio state from JSON file generated by paper trading engine."""
    if os.path.exists(PORTFOLIO_STATE_FILE):
        try:
            with open(PORTFOLIO_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading portfolio state: {e}")
            return None
    return None

from core.live_data_engine import live_engine, DataUnavailabilityError

async def fetch_market_data():
    """Fetch real-time data using Robust LiveDataEngine."""
    data = []
    
    try:
        # Fallback zinciri ile veri çek (YFinance -> Stooq -> Cache)
        # Tickers listesi config.py'den geliyor olmalı ama burada global var.
        # LiveDataEngine yf.download formatı (MultiIndex) döner.
        
        # Unpack tuple (data_dict, source_str)
        result = live_engine.fetch_live_data(TICKERS)
        
        # Eğer result tuple değilse (eski versiyon engine kaldıysa)
        if isinstance(result, tuple):
             raw_data, source = result
        else:
             raw_data = result
             source = "Unknown"
        
        # Process data for UI
        # raw_data: { 'AKBNK.IS': DataFrame(OHLCV...), ... } dict formatında döner
        
        for symbol, df_t in raw_data.items():
            try:
                if df_t.empty: continue
                
                # Son veriyi al
                latest = df_t.iloc[-1] # Series
                
                # Prev Close Handling
                if len(df_t) > 1:
                    prev_close = df_t.iloc[-2]['Close']
                else:
                    prev_close = df_t.iloc[-1]['Open'] # Fallback
                
                current_price = latest['Close']
                volume = latest['Volume']
                
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                
                clean_symbol = symbol.replace(".IS", "")
                
                data.append({
                    "symbol": clean_symbol,
                    "price": round(float(current_price), 2),
                    "change": round(float(change_pct), 2),
                    "volume": f"{float(volume)/1_000_000:.1f} Milyon",
                    "volume_raw": float(volume),
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                continue
                
    except DataUnavailabilityError as e:
        print(f"⚠️ [CRITICAL] {e}")
        return {"status": "CRITICAL", "source": "None", "error": str(e), "data": []}
        
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return {"status": "ERROR", "source": "None", "error": str(e), "data": []}
        
    print(f"Returning {len(data)} items from LiveEngine (Source: {source}).")
    return {"status": "OK", "source": source, "data": data}

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/api/portfolio")
async def get_portfolio():
    state = load_portfolio_state()
    if state:
        return state
    # Return empty structure if no state found
    return {
        "cash": 100000,
        "positions": {},
        "realized_pnl": 0,
        "history": []
    }

@app.get("/api/market-data/{symbol}")
async def get_history(symbol: str):
    """Get historical data for charts."""
    # Ensure symbol has .IS suffix
    yf_symbol = f"{symbol}.IS" if not symbol.endswith(".IS") else symbol
    
    try:
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1mo", interval="1d")
        
        # Format for lightweight-charts
        chart_data = []
        for date, row in hist.iterrows():
            chart_data.append({
                "time": date.strftime("%Y-%m-%d"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"]
            })
        return chart_data
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/predictions/{symbol}")
async def get_predictions(symbol: str):
    """
    Get AI predictions and signals for plotting.
    Currently mocks data based on latest price to demonstrate UI features.
    """
    # 1. Get current price context
    chart_data = await get_history(symbol)
    if isinstance(chart_data, dict) and "error" in chart_data:
        return []
        
    last_candle = chart_data[-1]
    last_price = last_candle['close']
    last_date = datetime.strptime(last_candle['time'], "%Y-%m-%d")

    # 2. Generate Future Projections (Next 5 days)
    forecast = []
    current_price = last_price
    
    for i in range(1, 6):
        next_date = last_date + timedelta(days=i)
        # Random walk for demo
        change = random.uniform(-0.02, 0.02)
        current_price = current_price * (1 + change)
        
        upper_bound = current_price * 1.03
        lower_bound = current_price * 0.97
        
        forecast.append({
            "time": next_date.strftime("%Y-%m-%d"),
            "value": current_price, 
            "upper": upper_bound,
            "lower": lower_bound
        })

    # 3. Generate Historical Signals (Last 30 days)
    signals = []
    for i in range(len(chart_data) - 10, len(chart_data)):
        # Randomly place signal
        if random.random() > 0.8:
            candle = chart_data[i]
            signal_type = "sell" if random.random() > 0.5 else "buy"
            signals.append({
                "time": candle['time'],
                "position": "aboveBar" if signal_type == "sell" else "belowBar",
                "color": "#ef5350" if signal_type == "sell" else "#00c853",
                "shape": "arrowDown" if signal_type == "sell" else "arrowUp",
                "text": f"AI {signal_type.upper()}"
            })

    return {
        "forecast": forecast,
        "signals": signals
    }

# ---------------------------------------------------------
# WebSocket Loop
# ---------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_updates():
    """
    Main loop to broadcast:
    1. Real market data prices
    2. Portfolio state file updates
    """
    last_portfolio_state = None
    
    while True:
        # 1. Market Data Update
        market_result = await fetch_market_data()
        
        # market_result artık bir dict: {status, source, data}
        if market_result and market_result.get("data"):
            await manager.broadcast(json.dumps({
                "type": "MARKET_UPDATE",
                "status": market_result.get("status"),
                "source": market_result.get("source"),
                "data": market_result.get("data")
            }))
        elif market_result and market_result.get("status") == "CRITICAL":
             # Kritik hata durumunda da yayın yap, UI kilitlensin
             await manager.broadcast(json.dumps({
                "type": "MARKET_CRITICAL_ERROR",
                "error": market_result.get("error")
            }))
            
        # 2. Portfolio State Update
        current_state = load_portfolio_state()
        
        # Check if state has changed (simple equality check or check timestamp)
        # For simplicity, we just broadcast if it's not None. Client handles diffs?
        # Better: compare strict string dumps
        current_state_str = json.dumps(current_state, sort_keys=True) if current_state else ""
        last_state_str = json.dumps(last_portfolio_state, sort_keys=True) if last_portfolio_state else ""
        
            
        if current_state and current_state_str != last_state_str:
            await manager.broadcast(json.dumps({
                "type": "PORTFOLIO_UPDATE",
                "data": current_state
            }))
            last_portfolio_state = current_state
            
        await asyncio.sleep(15) # Update every 15 seconds to avoid API limits and file I/O spam

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())

if __name__ == "__main__":
    import uvicorn
    # Important: host 0.0.0.0 for external access if needed, but localhost is fine
    uvicorn.run(app, host="0.0.0.0", port=8000)
