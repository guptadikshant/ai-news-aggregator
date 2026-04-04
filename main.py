import uvicorn
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, status
from langchain_core.messages import HumanMessage

from src.agent_workflow.agent_pipeline import create_agent_pipeline
from src.utils.logger import init_logging

load_dotenv(find_dotenv(), override=True)

logger = init_logging(__name__)
VERSION = "v1"

app = FastAPI(
    title="AI News Aggregator",
    description="This is a news aggregator app which fetch news from different resources, aggregate them and then show to the user",
    version=VERSION,
)


@app.get("/")
def root():
    return {"message": "Welcome"}


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"message": "OK"}


# app.include_router(router=user_router, prefix=f"/api/{VERSION}/users", tags=["users"])


@app.post("/chat", status_code=status.HTTP_200_OK)
async def chat(user_input: str):
    logger.info(f"User Input: {user_input}")
    pipeline = create_agent_pipeline()
    result = await pipeline.ainvoke(
        {"messages": [HumanMessage(content=user_input)]}  # type:ignore
    )
    return {
        "final_response": result["final_response"],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
