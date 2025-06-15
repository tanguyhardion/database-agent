from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from agent import graph
from add_langgraph_route import add_langgraph_route

app = FastAPI()

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add route to serve cost.txt
@app.get("/api/cost")
async def get_cost():
    try:
        cost_file_path = os.path.join(os.path.dirname(__file__), "cost.txt")
        if os.path.exists(cost_file_path):
            with open(cost_file_path, 'r') as f:
                cost = float(f.read().strip())
                return {"cost": cost}
        else:
            return {"cost": 0.0}
    except Exception:
        return {"cost": 0.0}

add_langgraph_route(app, graph, "/api/chat")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app)