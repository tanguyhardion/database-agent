from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from agent import graph
from add_langgraph_route import add_langgraph_route

app = FastAPI()

# Pydantic model for prompt switching
class PromptModeRequest(BaseModel):
    mode: str

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_langgraph_route(app, graph, "/api/chat")

@app.get("/api/prompt-mode")
async def get_prompt_mode():
    """Get the current prompt mode (business or technical)"""
    try:
        with open("system_prompts/active.txt", "r") as f:
            mode = f.read().strip()
        return {"mode": mode}
    except FileNotFoundError:
        # Default to technical if file doesn't exist
        return {"mode": "technical"}

@app.post("/api/prompt-mode")
async def set_prompt_mode(request: PromptModeRequest):
    """Set the prompt mode to business or technical"""
    if request.mode not in ["business", "technical"]:
        raise HTTPException(status_code=400, detail="Mode must be 'business' or 'technical'")
    
    try:
        with open("system_prompts/active.txt", "w") as f:
            f.write(request.mode)
        return {"success": True, "mode": request.mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update prompt mode: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app)