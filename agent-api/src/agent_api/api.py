import shutil
from enum import Enum
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager

import click
from fastapi import FastAPI, BackgroundTasks , File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastmcp.client import Client
from loguru import logger


from agent_api.config import get_settings
from agent_api.models import (
    AssistantMessageResponse,
    ProcessVideoRequest,
    ProcessVideoResponse,
    ResetMemoryResponse,
    UserMessageRequest,
    VideoUploadResponse,
)
from agent_api.agent import GroqAgent
settings = get_settings()

class TaskStatus(str,Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_FOUND = "not_found"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = GroqAgent(
        name ="agent",
        mcp_server = settings.MCP_SERVER,
        disable_tools = ["process_video"],
    )
    app.state.bg_task_states = dict()
    yield
    app.state.agent.reset_memory()
    pass

app = FastAPI(
    title = "MultioModal MCP",
    docs_url="/docs",
    lifespan=lifespan,

)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)


@app.post("/")
async def read():
    return {"message":"Welcome to Agent API.Visit /docs for documentation"}


@app.post("/tast-status/{task_id}")
async def get_task_status(task_id: str, fastapi_request: Request):
    status = fastapi_request.app.state.bg_task_states.get(task_id,TaskStatus.NOT_FOUND)
    return {"task_id": task_id, "status": status}

@app.post("/process-video")
async def process_video(request: ProcessVideoRequest, bg_tasks: BackgroundTasks, fastapi_request: Request):
    """
    Process a video and return the results
    """
    task_id = str(uuid4())
    bg_task_states = fastapi_request.app.state.bg_task_states

    async def backgroung_process_video(video_path:str, task_id:str):
        """
        background process to process the video
        """

        bg_task_states[task_id] = TaskStatus.IN_PROGRESS

        if not Path(video_path).exists():
            bg_task_states[task_id] = TaskStatus.FAILED
            raise HTTPException(status_code= 404, detail ="Video file not found")
        try:
            mcp_client = Client(settings.MCP_SERVER)
            async with mcp_client:
                _ = await mcp_client.call_tool("process_video", {"video_path": request.video_path})
        except Exception as e:
            logger.error(f"Error processing video {video_path}: {e}")
            bg_task_states[task_id] = TaskStatus.FAILED
            raise HTTPException(status_code= 500, detail= str(e))
        bg_task_states[task_id] = TaskStatus.COMPLETED

    bg_tasks.add_task(backgroung_process_video, request.video_path,task_id)
    return ProcessVideoResponse(message = "Task enquered for processing ", task_id= task_id)

@app.post("/chat", response_model= AssistantMessageResponse)
async def chat(request: UserMessageRequest, fastapi_request: Request):
    """Chat with an AI Request"""
    agent = fastapi_request.app.state.agent
    await agent.setup()

    try:
        response = await agent.chat(request.message,request.video_path,request.image_base64)
        return response
    except Exception as e:
        raise  HTTPException(status_code= 500, detail= str(e))
    
@app.post("/reset-memory")
async def reset_memory(fastapi_request: Request):
    """Reset the memory of the agent"""
    agent = fastapi_request.app.state.agent
    agent.reset_memory()
    return ResetMemoryResponse(message = "Memory reset successfully")

@app.post("/upload-video",response_model= VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload a video and return the path"""
    if not file.filename:
        raise HTTPException(status_code= 400, detail=" no file uploaded")
    
    try:
        shared_media_dir = Path("shared_media")
        shared_media_dir.mkdir(exist_ok=True)

        video_path = Path(shared_media_dir/ file.filename)

        if not video_path.exists():
            with open(video_path,"wb") as f:
                shutil.copyfileobj(file.file,f)

        return VideoUploadResponse(message = "Video Uploaded Successfully")
    except Exception as e:
        logger.error(f"Error Uploading Video: {e}")
        raise HTTPException(status_code= 500, detail= str(e))

@app.get("/media/{filepath:path}")
async def serve_media(file_path: str):
    """
    serve media files from the shared media directory
    """
    try:
        clean_path = Path(file_path).name
        media_file = Path("shared_media") / clean_path

        if not media_file.exists():
            raise HTTPException(status_code= 404, detail= "File not Found")
    
        return FileResponse(str(media_file))
    except Exception as e:
        logger.error(f"Error Serving media files {file_path}: {e}")
        raise HTTPException(status_code=500, detail= str(e))

@click.command()
@click.option("--port", default=8080, help="FastAPI server port")
@click.option("--host", default="0.0.0.0", help="FastAPI server host")


def run_api(port, host):
    import uvicorn

    uvicorn.run("api:app", host=host, port=port, loop="asyncio")


if __name__ == "__main__":
    run_api()