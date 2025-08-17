import json
import uuid
from datetime import datetime
from typing import Optional,Dict,List,Any

import instructor
import opik
from loguru import logger
from opik import Attachment,opik_context
from groq import Groq
from src.config import get_settings
from src.tools import tools
from src.agent.base_agent import BaseAgent
from src.agent.groq.groq_tool import transform_tool_defintion
from src.agent.memory import Memory , MemoryRecord
from src.models import (
    AssistantmessageResponse,
    GeneralResponseModel,
    RoutingResponseModel,
    VideoClipResponseModel
)

logger.bind(name = "Groq Agent")

settings = get_settings()


class GroqAgent(BaseAgent):
    def __init__(
            self,
            name:str,
            mcp_server:str,
            memory:Optional[Memory] = None,
            disable_tools: list = None,
    )
        super.__init__(name,mcp_server,memory,disable_tools)

        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.instructor = instructor.from_groq(self.client,mode = instructor.Mode.JSON)
        self.thread_id = str(uuid.uuid4())


    async def _get_tools(self)-> List[Dict[str,Any]]:
        tools = await self.discover_tools()
        return [transform_tool_defintion(tool) for tool in tools]
    
    @opik.trac(name = "Build Chat History")
    def _build_chat_history(
        self,
        system_prompt:str,
        user_message:str,
        image_base64: Optional[str] = None,
        n:int = settings.AGENT_MEMORY_SIZE,
    )-> List[Dict[str,Any]]:
        history = [
            {"role":"system",
             "content":system_prompt}
        ]
        history += [{"role": record.role, "content": record.content} for record in self.memory.get_latest(n)]

        user_content = (
            [
                {"type":"text","text":user_message},
                {
                    "type":"image_url",
                    "image_url": { "url":f"data:image/jpeg;base64,{image_base64}"},
                },
            ]
            if image_base64
            else user_message
        )
        history.append(
            {
                "role":"user",
                "content":user_content
            }
        )

        return history
    
    @opik.track(name="router",type="llm")
    def _should_use_tool(self,message:str)->bool:
        messages = [
            {"role":"system","content":self.routing_system_prompt},
            {"role":"user","content":message},
        ]

        response = self.instructor_client.chat.completions.create(
            model = settings.GROQ_ROUTING_MODEL,
            response_model = RoutingResponseModel,
            messages = messages,
            max_completion_tokens = 20
        )

        return response.tool_use
    

    async def _execute_tool_call(self,tool_call:Any,video_path:str,image_base64:str|None)->str:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        function_args["video_path"] = video_path
        if function_name=="get_video_clip_from_images":
            function_args["user_image"] = image_base64
        logger.info(f"Executing tool : {function_name}")

        try:
            return await self.call_tool(function_name,function_args)
        except Exception as e:
            logger.error(f"Error Executing tool {function_name}: {str(e)}")
            return f"Error Executing tool {function_name}: {str(e)}"
    
