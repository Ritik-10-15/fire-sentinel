import asyncio
import websockets

async def main():
    try:
        async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
            print("CONNECTED SUCCESSFULLY")
            await asyncio.sleep(3)
    except Exception as e:
        print("FAILED:", e)

asyncio.run(main())
