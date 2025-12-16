import uuid
from pathlib import Path
from typing import TYPE_CHECKING , Optional


import pixeltable as pxt
from loguru import logger
from pixeltable.functions import gemini
from pixeltable.functions.huggingface import clip
from pixeltable.functions.gemini import embeddings, vision # Need to verify
from pixeltable.functions.video import extract_audio
from pixeltable.iterators import AudioSplitter
from pixeltable.iterators.video import FrameIterator


import agent_mcp.video.ingestion.registry as registry
from agent_mcp.config import get_settings
from agent_mcp.video.ingestion.functions import extract_text_from_chunk, resize_image
from agent_mcp.video.ingestion.tools import re_encode_video


if TYPE_CHECKING:
    from agent_mcp.video.ingestion.models import CachedTable


logger = logger.bind(name =" Video Processor")

settings = get_settings()

class VideoProcessor:
    def __init__(self):
        self._pxt_cache : Optional[str] = None
        self._video_table = None
        self._frames_view =  None
        self._audio_chunks = None
        self._video_mapping_idx = Optional[str] = None

        logger.info(
            "VideoProcessor initialized",
            f"\n Split FPS: {settings.SPLIT_FRAMES_COUNT}",
            f"\n Audio Chunk: {settings.AUDIO_CHUNK_LENGTH} seconds",
        )

    
