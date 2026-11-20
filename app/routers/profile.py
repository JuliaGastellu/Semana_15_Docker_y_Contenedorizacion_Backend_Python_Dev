from fastapi import APIRouter
from pydantic import EmailStr

from app.dependencies import CurrentUserDep, PostServiceDep, UserServiceDep
from app.schemas import InputModel, PostResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users/me", tags=["profile"])


class ProfileUpdate(InputModel):
    email: EmailStr


@router.get("", response_model=UserResponse)
async def me(user: CurrentUserDep):
    return user


@router.put("", response_model=UserResponse)
async def update_me(data: ProfileUpdate, user: CurrentUserDep, service: UserServiceDep):
    return await service.update(user.id, UserUpdate(email=data.email))


@router.get("/posts", response_model=list[PostResponse])
async def my_posts(user: CurrentUserDep, service: PostServiceDep):
    items, _ = await service.page(
        skip=0, limit=100, status=None, category_id=None, tag=None, author_id=user.id
    )
    return items
