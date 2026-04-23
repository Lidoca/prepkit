import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Question,
    QuestionCreate,
    QuestionTagLink,
    QuestionUpdate,
    ReviewSchedule,
    ReviewSubmit,
    Tag,
    TagCreate,
    TagUpdate,
    User,
    UserCreate,
    UserUpdate,
    utcnow,
)

# ─── User ─────────────────────────────────────────────────────────────────────


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        extra_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


# Argon2 hash used only to ensure constant-time comparison when the user is not found
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_hash:
        db_user.hashed_password = updated_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


# ─── Tag ──────────────────────────────────────────────────────────────────────


def create_tag(*, session: Session, tag_in: TagCreate, user_id: uuid.UUID) -> Tag:
    db_tag = Tag.model_validate(tag_in, update={"user_id": user_id})
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag


def update_tag(*, session: Session, db_tag: Tag, tag_in: TagUpdate) -> Tag:
    tag_data = tag_in.model_dump(exclude_unset=True)
    db_tag.sqlmodel_update(tag_data)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag


def get_tags(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Tag], int]:
    tags = list(
        session.exec(
            select(Tag).where(Tag.user_id == user_id).offset(skip).limit(limit)
        ).all()
    )
    count = session.exec(select(Tag).where(Tag.user_id == user_id)).all().__len__()
    return tags, count


# ─── Question ─────────────────────────────────────────────────────────────────


def _set_question_tags(
    session: Session, question: Question, tag_ids: list[uuid.UUID], user_id: uuid.UUID
) -> None:
    existing = session.exec(
        select(QuestionTagLink).where(QuestionTagLink.question_id == question.id)
    ).all()
    for link in existing:
        session.delete(link)
    # Add new links (only tags owned by this user)
    if tag_ids:
        valid_tags = session.exec(
            select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)  # type: ignore[attr-defined]
        ).all()
        for tag in valid_tags:
            session.add(QuestionTagLink(question_id=question.id, tag_id=tag.id))


def create_question(
    *, session: Session, question_in: QuestionCreate, user_id: uuid.UUID
) -> Question:
    db_question = Question.model_validate(
        question_in,
        update={"user_id": user_id},
    )
    session.add(db_question)
    session.flush()

    _set_question_tags(session, db_question, question_in.tag_ids, user_id)

    review = ReviewSchedule(
        question_id=db_question.id,
        user_id=user_id,
        next_review_at=utcnow(),
    )
    session.add(review)
    session.commit()
    session.refresh(db_question)
    return db_question


def update_question(
    *, session: Session, db_question: Question, question_in: QuestionUpdate
) -> Question:
    update_data = question_in.model_dump(exclude_unset=True)
    tag_ids: list[uuid.UUID] | None = update_data.pop("tag_ids", None)

    update_data["updated_at"] = utcnow()
    db_question.sqlmodel_update(update_data)
    session.add(db_question)

    if tag_ids is not None:
        _set_question_tags(session, db_question, tag_ids, db_question.user_id)

    session.commit()
    session.refresh(db_question)
    return db_question


def get_questions(
    *,
    session: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    tag_id: uuid.UUID | None = None,
    difficulty: int | None = None,
) -> tuple[list[Question], int]:
    query = select(Question).where(Question.user_id == user_id)
    if tag_id is not None:
        query = query.join(QuestionTagLink).where(QuestionTagLink.tag_id == tag_id)
    if difficulty is not None:
        query = query.where(Question.difficulty == difficulty)
    questions = list(session.exec(query.offset(skip).limit(limit)).all())
    count = len(session.exec(query).all())
    return questions, count


# ─── Review (SM-2 Spaced Repetition) ──────────────────────────────────────────


def _sm2_update(
    repetitions: int, ease_factor: float, interval_days: int, quality: int
) -> tuple[int, float, int]:
    """SM-2 algorithm: quality 0-5 (0=blackout, 5=perfect recall)."""
    if quality < 3:
        return 0, ease_factor, 1

    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = round(interval_days * ease_factor)

    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return repetitions + 1, max(1.3, new_ef), new_interval


def get_due_reviews(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 50
) -> tuple[list[ReviewSchedule], int]:
    now = datetime.now(timezone.utc)
    query = select(ReviewSchedule).where(
        ReviewSchedule.user_id == user_id,
        ReviewSchedule.next_review_at <= now,
    )
    reviews = list(session.exec(query.offset(skip).limit(limit)).all())
    count = len(session.exec(query).all())
    return reviews, count


def submit_review(
    *, session: Session, db_review: ReviewSchedule, review_in: ReviewSubmit
) -> ReviewSchedule:
    new_reps, new_ef, new_interval = _sm2_update(
        db_review.repetitions,
        db_review.ease_factor,
        db_review.interval_days,
        review_in.quality,
    )
    now = datetime.now(timezone.utc)
    db_review.repetitions = new_reps
    db_review.ease_factor = new_ef
    db_review.interval_days = new_interval
    db_review.last_reviewed_at = now
    db_review.next_review_at = now + timedelta(days=new_interval)
    session.add(db_review)
    session.commit()
    session.refresh(db_review)
    return db_review
