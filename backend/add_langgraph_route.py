from assistant_stream import create_run, RunController
from assistant_stream.serialization import DataStreamResponse
from langchain_core.messages import (
    HumanMessage,
    AIMessageChunk,
    AIMessage,
    ToolMessage,
    SystemMessage,
    BaseMessage,
)
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal, Union, Optional, Any
import json
import asyncio

class LanguageModelTextPart(BaseModel):
    type: Literal["text"]
    text: str
    providerMetadata: Optional[Any] = None


class LanguageModelImagePart(BaseModel):
    type: Literal["image"]
    image: str  # Will handle URL or base64 string
    mimeType: Optional[str] = None
    providerMetadata: Optional[Any] = None


class LanguageModelFilePart(BaseModel):
    type: Literal["file"]
    data: str  # URL or base64 string
    mimeType: str
    providerMetadata: Optional[Any] = None


class LanguageModelToolCallPart(BaseModel):
    type: Literal["tool-call"]
    toolCallId: str
    toolName: str
    args: Any
    providerMetadata: Optional[Any] = None


class LanguageModelToolResultContentPart(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    data: Optional[str] = None
    mimeType: Optional[str] = None


class LanguageModelToolResultPart(BaseModel):
    type: Literal["tool-result"]
    toolCallId: str
    toolName: str
    result: Any
    isError: Optional[bool] = None
    content: Optional[List[LanguageModelToolResultContentPart]] = None
    providerMetadata: Optional[Any] = None


class LanguageModelSystemMessage(BaseModel):
    role: Literal["system"]
    content: str


class LanguageModelUserMessage(BaseModel):
    role: Literal["user"]
    content: List[
        Union[LanguageModelTextPart, LanguageModelImagePart, LanguageModelFilePart]
    ]


class LanguageModelAssistantMessage(BaseModel):
    role: Literal["assistant"]
    content: List[Union[LanguageModelTextPart, LanguageModelToolCallPart]]


class LanguageModelToolMessage(BaseModel):
    role: Literal["tool"]
    content: List[LanguageModelToolResultPart]


LanguageModelV1Message = Union[
    LanguageModelSystemMessage,
    LanguageModelUserMessage,
    LanguageModelAssistantMessage,
    LanguageModelToolMessage,
]


def convert_to_langchain_messages(
    messages: List[LanguageModelV1Message],
) -> List[BaseMessage]:
    result = []
    for msg in messages:
        if msg.role == "system":
            result.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            content = []
            for p in msg.content:
                if isinstance(p, LanguageModelTextPart):
                    content.append({"type": "text", "text": p.text})
                elif isinstance(p, LanguageModelImagePart):
                    content.append({"type": "image_url", "image_url": p.image})
            result.append(HumanMessage(content=content))
        elif msg.role == "assistant":
            # handle both text and tool calls
            text_parts = [
                p for p in msg.content if isinstance(p, LanguageModelTextPart)
            ]
            text_content = " ".join(p.text for p in text_parts)
            tool_calls = [
                {
                    "id": p.toolCallId,
                    "name": p.toolName,
                    "args": p.args,
                }
                for p in msg.content
                if isinstance(p, LanguageModelToolCallPart)
            ]
            result.append(AIMessage(content=text_content, tool_calls=tool_calls))
        elif msg.role == "tool":
            for tool_result in msg.content:
                result.append(
                    ToolMessage(
                        content=str(tool_result.result),
                        tool_call_id=tool_result.toolCallId,
                    )
                )
    return result


class FrontendToolCall(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: dict[str, Any]


class ChatRequest(BaseModel):
    system: Optional[str] = ""
    tools: Optional[List[FrontendToolCall]] = []
    messages: List[LanguageModelV1Message]


def add_langgraph_route(app: FastAPI, graph, path: str):
    async def chat_completions(request: ChatRequest):
        inputs = convert_to_langchain_messages(request.messages)

        async def generate_sse():
            try:
                final_response = ""

                async for event in graph.astream(
                    {"messages": inputs},                    {
                        "configurable": {
                            "system": request.system,
                            "frontend_tools": request.tools,
                        }
                    },
                    stream_mode="updates",
                ):
                    for node_name, node_state in event.items():
                        # Get the final LLM response from messages
                        if "messages" in node_state and node_state["messages"]:
                            last_message = node_state["messages"][-1]
                            if hasattr(last_message, 'content') and last_message.content:
                                # Only use messages that don't have tool calls (final responses)
                                if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
                                    final_response = last_message.content

                if final_response:
                    words = final_response.split()
                    for i, word in enumerate(words):
                        data = {
                            "type": "text-delta",
                            "textDelta": word + (" " if i < len(words) - 1 else ""),
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        # small delay for streaming effect
                        await asyncio.sleep(0.05)
                else:
                    error_data = {
                        "type": "text-delta",
                        "textDelta": "No response was generated. Please try again.",
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

                yield f"data: [DONE]\n\n"

            except Exception as e:
                error_data = {"type": "text-delta", "textDelta": f"Error: {str(e)}"}
                yield f"data: {json.dumps(error_data)}\n\n"
                yield f"data: [DONE]\n\n"

        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    async def chat_options():
        return {"message": "OK"}

    app.add_api_route(path, chat_completions, methods=["POST"])
    app.add_api_route(path, chat_options, methods=["OPTIONS"])