from fastapi import FastAPI, status

app = FastAPI(
    title="AI News Agreegator",
    description="This is a news aggregator app which fetch news from different resources, agreegate them and then show to the user",
    version="0.1",
)


@app.get("/")
def root():
    return {"message": "Welcome"}


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"message": "OK"}
