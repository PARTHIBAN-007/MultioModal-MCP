import shutil
from enum import Enum
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager


from fastapi import FastAPI, BackgroundTasks , File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastmcp.client import Client
from loguru import logger


from config import get_settings
from models import (
    AssistantMessageResponse,
    ProcessVideoRequest,
    ProcessVideoResponse,
    ResetMemoryResponse,
    UserMessageRequest,
    VideoUploadResponse,
)

settings = get_settings()

class TaskStatus(str,Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_FOUND = "not_found"

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # app.state.agent = GroqAgent(
#     #     name ="agent",
#     #     mcp_server = settings.MCP_SERVER,
#     #     disable_tools = ["process_video"],
#     # )
#     # app.state.bg_task_states = dict()
#     # yield
#     # app.state.agent.reset_memory()
#     pass

app = FastAPI(
    title = "MultioModal MCP",
    docs_url="/docs",
    # lifespan=lifespan,

)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methos = ["*"],
    allow_headers = ["*"]
)