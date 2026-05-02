from fastapi import APIRouter


user_router = APIRouter()

@user_router.get("/user_details")
async def user_details():
    return {"message": "dummy details"}


@user_router.get("/preference/{user_id}")
async def preference_details(user_id: int):
    pass