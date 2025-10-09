from fastapi import FastAPI, Depends, HTTPException, status, Query, WebSocket, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse
from typing import List, Annotated, Dict
from contextlib import asynccontextmanager
from pydantic import EmailStr, BaseModel
from datetime import timedelta
from ai_agent import ai_query, ai_stream_generator, ai_websocket_generator
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # 종료 시 정리 작업 (필요한 경우)

app = FastAPI(
    title="Users API with OAuth Token",
    description="FastAPI + Claude AI Agent SDK",
    version="2.0.0",
    lifespan=lifespan,
    debug=True
)
# static 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# templates 폴더 설정
templates = Jinja2Templates(directory="templates")

@app.get("/sse", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("sse_client.html", {
        "request": request,
        "title": "AI Query Client (SSE)",
    })

@app.get("/web-socket", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    return templates.TemplateResponse("websocket_client.html", {
        "request": request,
        "title": "AI Query Client (WebSocket)",
    }) 

# AI Query
# @app.get("/api/mcp/query", response_model=List[str], tags=["AI"])
# def query_ai(query: str):
#     """AI 로부터 query를 수행한다."""
#     return asyncio.run(ai_query(query))
#     #return ai_query(query)

# 활성 WebSocket 연결 관리
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    try:
        while True:
            await websocket.receive_text()  # 연결 유지
    except:
        del active_connections[client_id]
        
# AI Query
# @app.get("/api/mcp/ai-query", response_model=List[str], tags=["AI"])
# def query_ai(query: str):
#     """AI 로부터 query를 수행한다."""
#     return asyncio.run(ai_query(query))




# AI Query - 백그라운드 태스크 + WebSocket

# Request Body 모델 정의
class QueryRequest(BaseModel):
    query: str
    client_id: str
    
@app.post("/api/mcp/query-websocket")
async def query_websocket(request: QueryRequest, background_tasks: BackgroundTasks):
    """쿼리를 받아서 백그라운드에서 처리"""
    print(f"Received query: {request.query} from {request.client_id}")
    background_tasks.add_task(ai_websocket_generator, request.query, request.client_id, active_connections)
    return {
        "message": "쿼리가 접수되었습니다", 
        "client_id": request.client_id,
        "query": request.query
    }
        
@app.post("/api/mcp/query-websocket2", include_in_schema=False)
async def query_websocket2(query: str, client_id: str, background_tasks: BackgroundTasks):
    print(f"query_websocket called with query: {query}, client_id: {client_id}")
    """쿼리를 받아서 백그라운드에서 처리"""
    background_tasks.add_task(ai_websocket_generator, query, client_id, active_connections)
    return {"message": "쿼리가 접수되었습니다", "client_id": client_id}
    
# AI Query - Server-Sent Events (SSE)
@app.get("/api/mcp/query-sse", response_model=List[str], tags=["AI"])
async def query_stream(query: str):
    """AI 로부터 Server-Sent Events (SSE) 방식으로 query를 수행한다."""
    return StreamingResponse(
        ai_stream_generator(query),
        media_type="text/event-stream"
    ) 

# ==================== MAIN ====================
if __name__ == "__main__":
    print("Starting FastAPI Server...")
    print("API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )