import os
import threading
import time
import redis
from fastapi import FastAPI

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
rdb = redis.from_url(REDIS_URL, decode_responses=True)
notifications = []
app = FastAPI(title="Notification Service", version="1.0.0")

@app.get("/health")
def health():
    return {"service": "notification-service", "status": "healthy", "events_received": len(notifications)}

@app.get("/notifications")
def get_notifications():
    return notifications[-100:]

def consume():
    while True:
        try:
            pubsub = rdb.pubsub()
            pubsub.subscribe("task-events")
            for message in pubsub.listen():
                if message.get("type") == "message":
                    notifications.append(message["data"])
        except Exception:
            time.sleep(3)

threading.Thread(target=consume, daemon=True).start()
