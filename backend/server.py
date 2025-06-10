from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
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

add_langgraph_route(app, graph, "/api/chat")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)