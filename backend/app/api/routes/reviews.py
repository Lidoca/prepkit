import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import DueReview, ReviewSchedule, ReviewSchedulePublic, ReviewSubmit

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/due", response_model=list[DueReview])
def read_due_reviews(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    reviews, _ = crud.get_due_reviews(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    result = []
    for review in reviews:
        if review.question:
            result.append(DueReview(question=review.question, review=review))
    return result


@router.get("/{question_id}", response_model=ReviewSchedulePublic, responses={404: {"description": "Review schedule not found"}})
def read_review(
    session: SessionDep, current_user: CurrentUser, question_id: uuid.UUID
) -> Any:
    review = session.exec(
        select(ReviewSchedule).where(
            ReviewSchedule.question_id == question_id,
            ReviewSchedule.user_id == current_user.id,
        )
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review schedule not found")
    return review


@router.post("/{question_id}/submit", response_model=ReviewSchedulePublic, responses={404: {"description": "Review schedule not found"}})
def submit_review(
    session: SessionDep,
    current_user: CurrentUser,
    question_id: uuid.UUID,
    review_in: ReviewSubmit,
) -> Any:
    review = session.exec(
        select(ReviewSchedule).where(
            ReviewSchedule.question_id == question_id,
            ReviewSchedule.user_id == current_user.id,
        )
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review schedule not found")
    return crud.submit_review(session=session, db_review=review, review_in=review_in)
