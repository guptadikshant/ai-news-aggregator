from fastapi import FastAPI, status
from src.api.users.routes import user_router

VERSION = "v1"

app = FastAPI(
    title="AI News Agreegator",
    description="This is a news aggregator app which fetch news from different resources, agreegate them and then show to the user",
    version=VERSION,
)



@app.get("/")
def root():
    return {"message": "Welcome"}


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"message": "OK"}

app.include_router(router=user_router, prefix=f"/api/{VERSION}/users", tags=["users"])
