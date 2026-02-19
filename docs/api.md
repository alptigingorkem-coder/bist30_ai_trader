# API Documentation

## Overview

BIST30 AI Trader provides a FastAPI-based REST API and WebSocket interface for real-time trading operations and data access.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. This will be added in future versions.

## REST Endpoints

### Health Check

```http
GET /
```

Returns API status.

**Response:**
```json
{
  "status": "ok",
  "service": "BIST30 AI Trader API"
}
```

### Market Data

```http
GET /api/market-data/{symbol}?limit=500
```

Fetch historical candle data for a symbol.

**Parameters:**
- `symbol` (path): Stock symbol (e.g., "THYAO")
- `limit` (query): Number of candles to return (default: 500)

**Response:**
```json
[
  {
    "time": "2023-01-01",
    "open": 100.0,
    "high": 105.0,
    "low": 99.0,
    "close": 103.0,
    "volume": 1000000.0
  }
]
```

### Portfolio

```http
GET /api/portfolio
```

Get current portfolio status.

**Response:**
```json
{
  "cash": 10000.0,
  "equity": 10000.0,
  "positions": []
}
```

### Backtest Job

```http
POST /api/backtest
```

Submit a backtest job.

**Request Body:**
```json
{
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 100000,
  "model": "lightgbm"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

```http
GET /api/backtest/{job_id}
```

Get backtest job status and results.

## WebSocket

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Messages

**Subscribe to market updates:**
```json
{
  "action": "subscribe",
  "symbols": ["THYAO", "GARAN"]
}
```

**Market update (server → client):**
```json
{
  "type": "MARKET_UPDATE",
  "data": {
    "symbol": "THYAO",
    "price": 103.5,
    "volume": 1000000,
    "timestamp": "2023-01-01T10:00:00Z"
  }
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Currently no rate limiting. Will be added in future versions.

## Examples

### Python

```python
import requests

# Get market data
response = requests.get("http://localhost:8000/api/market-data/THYAO?limit=100")
data = response.json()

# Submit backtest
backtest_config = {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000
}
response = requests.post("http://localhost:8000/api/backtest", json=backtest_config)
job = response.json()
```

### JavaScript

```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['THYAO', 'GARAN']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Market update:', data);
};
```

## Running the API Server

```bash
# Development
uvicorn api.server:app --reload

# Production
uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

## Related Documentation

- [Main README](../README.md)
- [Architecture](architecture.md)
- [Deployment Guide](deployment.md)
