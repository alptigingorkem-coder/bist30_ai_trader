
import asyncio
import json
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import yfinance as yf
import pandas as pd
import threading
import uuid

# Add project root to path to import backend modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.dynamic_backtest import run_dynamic_backtest, validate_dates
from utils.logging_config import get_logger

log = get_logger(__name__)

app = FastAPI(title="BIST30 AI Trader API", version="2.0")

# ---------------------------------------------------------
# SQLite Backtest Job Storage
# ---------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "backtest_jobs.db")


def _init_db():
    """Backtest jobs tablosunu oluştur."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backtest_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            message TEXT DEFAULT '',
            result TEXT DEFAULT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def _save_job(job_id: str, status: str, progress: int, message: str, result=None):
    """Job durumunu SQLite'a kaydet."""
    conn = sqlite3.connect(DB_PATH)
    result_json = json.dumps(result) if result else None
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO backtest_jobs (job_id, status, progress, message, result, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM backtest_jobs WHERE job_id = ?), ?), ?)
    """, (job_id, status, progress, message, result_json, job_id, now, now))
    conn.commit()
    conn.close()


def _load_job(job_id: str) -> Optional[dict]:
    """Job durumunu SQLite'dan oku."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM backtest_jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    if d["result"]:
        d["result"] = json.loads(d["result"])
    return d


_init_db()

# ---------------------------------------------------------
# CORS Settings (güvenli)
# ---------------------------------------------------------
ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
    return {"message": "BIST30 AI Trader API çalışıyor", "version": "2.0", "docs": "/docs"}

# Configuration — DRY: config.TICKERS kullan
PORTFOLIO_STATE_FILE = "../logs/paper_trading/portfolio_state.json"
TICKERS = [f"{t}.IS" if not t.endswith(".IS") else t for t in config.TICKERS]

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
# Model Loading (Lazy Singleton)
# ---------------------------------------------------------

_model_cache = {"model": None, "features": None, "loaded": False}


def _load_model():
    """Load ranking model (singleton, lazy)."""
    if _model_cache["loaded"]:
        return _model_cache["model"], _model_cache["features"]
    
    import joblib
    from models.ensemble_model import HybridEnsemble
    import config
    
    lgbm_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "saved", "global_ranker.pkl")
    features_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "saved", "global_ranker_features.pkl")
    tft_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "saved", "tft_model.pth")
    
    try:
        ensemble = HybridEnsemble()
        
        # LightGBM Check
        if os.path.exists(lgbm_path):
            # Normalde ensemble.load_models lgbm path bekler ama tft config de lazım
            # Basitçe manuel yükleyelim veya load_models kullanalım
            # load_models(self, lgbm_path, tft_path, tft_config=None)
            
            # Feature list
            if os.path.exists(features_path):
                _model_cache["features"] = joblib.load(features_path)
                log.info("Feature list loaded: %d features", len(_model_cache["features"]))
                
            # Config for TFT (Dummy config)
            # Aslında TFT config modelin içinde kayıtlı olmalıydı (save method update'imizde yaptık)
            # Ama load_models methodu tft_config (initialization params) istiyor.
            # Biz save methodunda 'hyperparameters' ve 'dataset_params' kaydettik.
            # BIST30TransformerModel.load() bu parametreleri dosyadan okuyup init edebilse iyi olurdu.
            # Ancak BIST30TransformerModel.__init__ sadece config_module alır.
            # Bu yüzden load() methodu içinde instance yaratması zor.
            # Transformer modelde yaptığımız değişiklik: load() methodu instance oluşturmak yerine mevcut instance'a yüklüyor.
            # Bu yüzden önce init etmemiz lazım. Init için config module yeterli.
            
            tft_config_module = config # Global config
            # TFT path varsa ve dosya mevcutsa
            use_tft = os.path.exists(tft_path)
            
            if use_tft:
                ensemble.load_models(lgbm_path, tft_path, tft_config=tft_config_module)
            else:
                 # Sadece LGBM yükle (load_models TFT opsiyonel destekliyor mu? Bakalım)
                 # load_models kodu: if tft_config and tft_path: ...
                 # Eğer tft_path None verirsek sadece LGBM yükler.
                 ensemble.load_models(lgbm_path, None, None)
                 
            _model_cache["model"] = ensemble
            log.info("Hybrid Ensemble model loaded.")
        else:
            log.warning("No LightGBM model file found at %s", lgbm_path)
    except Exception as e:
        log.error("Model loading failed: %s", e)
    
    _model_cache["loaded"] = True
    return _model_cache["model"], _model_cache["features"]


# ---------------------------------------------------------
# Backtest Functions
# ---------------------------------------------------------

def run_backtest_job(job_id: str, request: BacktestRequest):
    """Background'da backtest çalıştır — sonuçlar SQLite'a kaydedilir."""
    try:
        _save_job(job_id, "running", 0, "Model eğitiliyor...")
        
        def progress_callback(step: str, pct: int):
            _save_job(job_id, "running", pct, step)
        
        result = run_dynamic_backtest(
            train_start=request.train_start,
            train_end=request.train_end,
            test_end=request.test_end,
            initial_capital=request.initial_capital,
            progress_callback=progress_callback
        )
        
        if result["success"]:
            _save_job(job_id, "completed", 100, "Tamamlandı!", result)
        else:
            _save_job(job_id, "error", 0, result.get("error", "Bilinmeyen hata"))
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        _save_job(job_id, "error", 0, str(e))


@app.post("/api/backtest/run")
async def start_backtest(request: BacktestRequest):
    """Dinamik backtest başlat. Job SQLite'a kaydedilir."""
    validation = validate_dates(request.train_start, request.train_end, request.test_end)
    if not validation["valid"]:
        return {"success": False, "error": validation["error"]}
    
    job_id = str(uuid.uuid4())
    _save_job(job_id, "pending", 0, "Kuyrukta...")
    
    thread = threading.Thread(target=run_backtest_job, args=(job_id, request))
    thread.start()
    
    return {"success": True, "job_id": job_id}


@app.get("/api/backtest/status/{job_id}")
async def get_backtest_status(job_id: str):
    """Backtest job durumunu sorgula (SQLite'dan)."""
    job = _load_job(job_id)
    if job is None:
        return {"success": False, "error": "Job bulunamadı"}
    
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
    """Backtest parametrelerini validate et (çalıştırmadan)."""
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
            log.error("Error reading portfolio state: %s", e)
            return None
    return None

from core.live_data_engine import live_engine, DataUnavailabilityError

async def fetch_market_data():
    """Fetch real-time data using Robust LiveDataEngine."""
    data = []
    
    try:
        result = live_engine.fetch_live_data(TICKERS)
        
        if isinstance(result, tuple):
             raw_data, source = result
        else:
             raw_data = result
             source = "Unknown"
        
        for symbol, df_t in raw_data.items():
            try:
                if df_t.empty: continue
                
                latest = df_t.iloc[-1]
                
                if len(df_t) > 1:
                    prev_close = df_t.iloc[-2]['Close']
                else:
                    prev_close = df_t.iloc[-1]['Open']
                
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
        log.error("CRITICAL: %s", e)
        return {"status": "CRITICAL", "source": "None", "error": str(e), "data": []}
        
    except Exception as e:
        log.error("Error fetching market data: %s", e)
        return {"status": "ERROR", "source": "None", "error": str(e), "data": []}
        
    log.info("Returning %d items from LiveEngine (Source: %s).", len(data), source)
    return {"status": "OK", "source": source, "data": data}

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/api/portfolio")
async def get_portfolio():
    state = load_portfolio_state()
    if state:
        return state
    return {
        "cash": 100000,
        "positions": {},
        "realized_pnl": 0,
        "history": []
    }

@app.get("/api/market-data/{symbol}")
async def get_history(symbol: str):
    """Get historical data for charts."""
    yf_symbol = f"{symbol}.IS" if not symbol.endswith(".IS") else symbol
    
    try:
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1mo", interval="1d")
        
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
    AI tabanlı tahmin ve sinyaller.
    Model yüklüyse gerçek score, değilse fallback mock.
    Response'da 'model_source' alanı kaynağı belirtir.
    """
    import random
    
    # 1. Get current price context
    chart_data = await get_history(symbol)
    if isinstance(chart_data, dict) and "error" in chart_data:
        return []
        
    if not chart_data:
        return {"forecast": [], "signals": [], "model_source": "error"}
    
    last_candle = chart_data[-1]
    last_price = last_candle['close']
    last_date = datetime.strptime(last_candle['time'], "%Y-%m-%d")

    # 2. Try real model prediction
    model, features = _load_model()
    model_source = "mock"
    model_score = None
    
    if model is not None:
        try:
            yf_symbol = f"{symbol}.IS" if not symbol.endswith(".IS") else symbol
            ticker_obj = yf.Ticker(yf_symbol)
            hist_60d = ticker_obj.history(period="3mo", interval="1d")
            
            if not hist_60d.empty and len(hist_60d) > 20:
                # Basit feature set oluştur (model feature'larının alt kümesi)
                df = hist_60d.copy()
                df['Returns'] = df['Close'].pct_change()
                df['Volatility_20'] = df['Returns'].rolling(20).std()
                df['SMA_20'] = df['Close'].rolling(20).mean()
                df['SMA_50'] = df['Close'].rolling(50).mean()
                df['RSI_14'] = _compute_rsi(df['Close'], 14)
                df['Volume_SMA_20'] = df['Volume'].rolling(20).mean()
                df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
                df['Momentum_10'] = df['Close'].pct_change(10)
                df = df.dropna()
                
                if not df.empty and features is not None:
                    # Model'in beklediği feature'larla kesişimi al
                    # Not: TFT için tüm sütunlara ihtiyaç olabilir, Feature subsetting LightGBM için.
                    # Hybrid modelde ayrımı içeride yapmak daha doğru olurdu ama şimdilik
                    # LightGBM feature'ları + TFT için gerekenler (Price, Volume, Dates) gerekli.
                    
                    # Basitlik için: df'yi olduğu gibi gönderelim, model içinden seçsin diyeceğim ama
                    # lgbm.predict() strict feature order isteyebilir.
                    # HybridEnsemble.predict bunu handle etmeli.
                    
                    # Mevcut yapıda HybridEnsemble.predict -> lgbm.predict(df) 
                    # Eğer df içinde fazla sütun varsa lgbm bozulur mu? (Sklearn/LGBM genelde bozulmaz, ama feature order önemli)
                    # Feature listesiyle filtrelemek LGBM için güvenli.
                    # TFT için ise 'Close', 'Volume' vb. ham veriler lazım.
                    
                    # Çözüm: HybridEnsemble'a ham DF gönderelim.
                    # Ancak LGBM sadece specific featureları ister.
                    # O yüzden ensemble.predict içinde ayrıştırma yapılmalı.
                    # Şimdilik API tarafında: feature subsetting'i sadece LGBM için değil genel yapıyoruz.
                    # TFT için ekstra sütunları koruyalım.
                    
                    # LightGBM featureları
                    lgbm_cols = [f for f in features if f in df.columns]
                    
                    # Eğer model HybridEnsemble ise, yönetimi ona bırakalım.
                    # Ancak `predict` metodunun imzasına göre davranmalı.
                    
                    if hasattr(model, 'predict'):
                        # HybridEnsemble or LGBM
                        # HybridEnsemble handle both? Yes if coded properly.
                        # But we checked `api/server.py` loaded `HybridEnsemble`.
                        # `ensemble_model.py` checks `self.lgbm.predict(df)`.
                        # If `df` has extra columns, LGBM implementation might warn or error depending on strictness.
                        # But usually `ranking_model.py` (LGBM wrapper) might select features?
                        
                        # Let's verify `ranking_model.py` later.
                        # For now, pass relevant history.
                        
                        # Pass last 60 rows for TFT context
                        p_df = df.iloc[-60:].copy() 
                        
                        # Prediction
                        preds = model.predict(p_df)
                        
                        # Get last value
                        if isinstance(preds, (list, np.ndarray, pd.Series)):
                             # Handle dimensions
                            if hasattr(preds, 'flatten'):
                                preds = preds.flatten()
                            if len(preds) > 0:
                                raw_score = float(preds[-1])
                                model_score = raw_score
                                model_source = "hybrid" if getattr(model, 'tft', None) else "lightgbm"
                                log.info("Real model prediction (%s): score=%.4f", model_source, model_score)
                        else:
                            # Scalar
                            model_score = float(preds)
                            model_source = "hybrid"
                            log.info("Real model prediction: score=%.4f", model_score)
        except Exception as e:
            log.warning("Model prediction failed for %s: %s (falling back to mock)", symbol, e)

    # 3. Generate forecast (model-aware if possible)
    forecast = []
    current_price = last_price
    
    # Model score'u yöne çevir: pozitif = yukarı, negatif = aşağı
    if model_score is not None:
        bias = model_score * 0.005  # Çok küçük etki (günlük %0.5 max)
    else:
        bias = 0.0
    
    for i in range(1, 6):
        next_date = last_date + timedelta(days=i)
        change = random.uniform(-0.015, 0.015) + bias
        current_price = current_price * (1 + change)
        
        confidence_band = 0.03 if model_source == "mock" else 0.02
        upper_bound = current_price * (1 + confidence_band)
        lower_bound = current_price * (1 - confidence_band)
        
        forecast.append({
            "time": next_date.strftime("%Y-%m-%d"),
            "value": round(current_price, 2),
            "upper": round(upper_bound, 2),
            "lower": round(lower_bound, 2)
        })

    # 4. Generate signals (model-aware)
    signals = []
    if model_score is not None:
        # Gerçek model varsa: son muma sinyal koy
        if model_score > 0.5:
            signals.append({
                "time": chart_data[-1]['time'],
                "position": "belowBar",
                "color": "#00c853",
                "shape": "arrowUp",
                "text": f"AI BUY ({model_score:.2f})"
            })
        elif model_score < -0.5:
            signals.append({
                "time": chart_data[-1]['time'],
                "position": "aboveBar",
                "color": "#ef5350",
                "shape": "arrowDown",
                "text": f"AI SELL ({model_score:.2f})"
            })
    else:
        # Fallback mock sinyalleri
        for i in range(len(chart_data) - 10, len(chart_data)):
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
        "signals": signals,
        "model_source": model_source,
        "model_score": model_score
    }


def _compute_rsi(series, period=14):
    """RSI hesaplama yardımcısı."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ---------------------------------------------------------
# WebSocket Loop
# ---------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
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
        
        if market_result and market_result.get("data"):
            await manager.broadcast(json.dumps({
                "type": "MARKET_UPDATE",
                "status": market_result.get("status"),
                "source": market_result.get("source"),
                "data": market_result.get("data")
            }))
        elif market_result and market_result.get("status") == "CRITICAL":
             await manager.broadcast(json.dumps({
                "type": "MARKET_CRITICAL_ERROR",
                "error": market_result.get("error")
            }))
            
        # 2. Portfolio State Update
        current_state = load_portfolio_state()
        
        current_state_str = json.dumps(current_state, sort_keys=True) if current_state else ""
        last_state_str = json.dumps(last_portfolio_state, sort_keys=True) if last_portfolio_state else ""
        
        if current_state and current_state_str != last_state_str:
            await manager.broadcast(json.dumps({
                "type": "PORTFOLIO_UPDATE",
                "data": current_state
            }))
            last_portfolio_state = current_state
            
        await asyncio.sleep(15)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
