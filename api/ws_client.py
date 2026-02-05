
import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send ping
            # await websocket.send("ping")
            
            print("Waiting for messages...")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    data = json.loads(message)
                    print(f"Received message type: {data.get('type')}")
                    if data.get('type') == 'MARKET_UPDATE':
                        print(f"Market Data Count: {len(data.get('data', []))}")
                        print("Sample:", data.get('data')[0])
                        break
                except asyncio.TimeoutError:
                    print("Timeout waiting for message (20s).")
                    break
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
