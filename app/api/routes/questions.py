import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Question,
    QuestionCreate,
    QuestionPublic,
    QuestionsPublic,
    QuestionUpdate,
)

router = APIRouter(prefix="/questions", tags=["questions"])

_NOT_FOUND = "Question not found"
_FORBIDDEN = "Not enough permissions"
_ERROR_RESPONSES = {404: {"description": _NOT_FOUND}, 403: {"description": _FORBIDDEN}}


def _get_owned_question(
    session: Any, question_id: uuid.UUID, user_id: uuid.UUID
) -> Question:
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    if question.user_id != user_id:
        raise HTTPException(status_code=403, detail=_FORBIDDEN)
    return question


@router.get("/", response_model=QuestionsPublic)
def read_questions(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    tag_id: uuid.UUID | None = None,
    difficulty: int | None = None,
) -> Any:
    questions, count = crud.get_questions(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        tag_id=tag_id,
        difficulty=difficulty,
    )
    return QuestionsPublic(data=questions, count=count)


@router.post("/", response_model=QuestionPublic)
def create_question(
    session: SessionDep, current_user: CurrentUser, question_in: QuestionCreate
) -> Any:
    return crud.create_question(
        session=session, question_in=question_in, user_id=current_user.id
    )


@router.get("/{question_id}", response_model=QuestionPublic, responses=_ERROR_RESPONSES)
def read_question(
    session: SessionDep, current_user: CurrentUser, question_id: uuid.UUID
) -> Any:
    return _get_owned_question(session, question_id, current_user.id)


@router.put("/{question_id}", response_model=QuestionPublic, responses=_ERROR_RESPONSES)
def update_question(
    session: SessionDep,
    current_user: CurrentUser,
    question_id: uuid.UUID,
    question_in: QuestionUpdate,
) -> Any:
    question = _get_owned_question(session, question_id, current_user.id)
    return crud.update_question(
        session=session, db_question=question, question_in=question_in
    )


@router.delete("/{question_id}", response_model=Message, responses=_ERROR_RESPONSES)
def delete_question(
    session: SessionDep, current_user: CurrentUser, question_id: uuid.UUID
) -> Any:
    question = _get_owned_question(session, question_id, current_user.id)
    session.delete(question)
    session.commit()
    return Message(message="Question deleted successfully")
