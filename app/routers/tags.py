from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import EditorDep
from app.models import Tag
from app.schemas import InputModel, TagResponse
from app.services.services import commit_or_duplicate

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(InputModel):
    name: str = Field(min_length=2, max_length=50)
    slug: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9-]+$")


@router.get("", response_model=list[TagResponse])
async def list_tags(db: AsyncSession = Depends(get_db)):
    return list((await db.scalars(select(Tag).order_by(Tag.id))).all())


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(data: TagCreate, user: EditorDep, db: AsyncSession = Depends(get_db)):
    item = Tag(**data.model_dump())
    db.add(item)
    await commit_or_duplicate(db, "El tag ya existe")
    await db.refresh(item)
    return item
