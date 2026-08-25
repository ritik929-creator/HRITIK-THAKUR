import os
import httpx
from fastapi import FastAPI, Request, Response

TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8001")
app = FastAPI(title="Task Management API Gateway", version="1.0.0")

@app.get("/health")
def health():
    return {"service": "api-gateway", "status": "healthy"}

@app.api_route("/api/tasks", methods=["GET", "POST"])
@app.api_route("/api/tasks/{path:path}", methods=["GET", "PATCH", "DELETE"])
async def proxy(request: Request, path: str = ""):
    target = f"{TASK_SERVICE_URL}/tasks" + (f"/{path}" if path else "")
    async with httpx.AsyncClient(timeout=15) as client:
        upstream = await client.request(
            request.method, target,
            params=request.query_params,
            content=await request.body(),
            headers={"content-type": request.headers.get("content-type", "application/json")},
        )
    return Response(content=upstream.content, status_code=upstream.status_code,
                    media_type=upstream.headers.get("content-type"))
