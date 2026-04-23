import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import Message, Tag, TagCreate, TagPublic, TagsPublic, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=TagsPublic)
def read_tags(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    tags, count = crud.get_tags(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    return TagsPublic(data=tags, count=count)


@router.post("", response_model=TagPublic)
def create_tag(
    session: SessionDep, current_user: CurrentUser, tag_in: TagCreate
) -> Any:
    return crud.create_tag(session=session, tag_in=tag_in, user_id=current_user.id)


@router.get("/{tag_id}", response_model=TagPublic)
def read_tag(
    session: SessionDep, current_user: CurrentUser, tag_id: uuid.UUID
) -> Any:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return tag


@router.put("/{tag_id}", response_model=TagPublic)
def update_tag(
    session: SessionDep,
    current_user: CurrentUser,
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
) -> Any:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.update_tag(session=session, db_tag=tag, tag_in=tag_in)


@router.delete("/{tag_id}", response_model=Message)
def delete_tag(
    session: SessionDep, current_user: CurrentUser, tag_id: uuid.UUID
) -> Any:
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(tag)
    session.commit()
    return Message(message="Tag deleted successfully")
