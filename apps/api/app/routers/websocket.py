import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.events import case_channel, redis_client


router = APIRouter(tags=["websocket"])


@router.websocket("/api/v1/cases/{case_id}/stream")
async def case_stream(websocket: WebSocket, case_id: str):
    await websocket.accept()
    pubsub = redis_client().pubsub()
    pubsub.subscribe(case_channel(case_id))
    try:
        await websocket.send_json({"event_type": "stream.connected", "case_id": case_id})
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("data"):
                await websocket.send_json(json.loads(message["data"]))
    except WebSocketDisconnect:
        return
    finally:
        pubsub.unsubscribe(case_channel(case_id))
        pubsub.close()

