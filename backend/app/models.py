import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import DateTime, Text
from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── User ─────────────────────────────────────────────────────────────────────


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    questions: list["Question"] = Relationship(
        back_populates="author", cascade_delete=True
    )
    tags: list["Tag"] = Relationship(back_populates="author", cascade_delete=True)
    reviews: list["ReviewSchedule"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# ─── Tag ──────────────────────────────────────────────────────────────────────


class TagBase(SQLModel):
    name: str = Field(max_length=50)


class TagCreate(TagBase):
    pass


class TagUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=50)


class QuestionTagLink(SQLModel, table=True):
    __tablename__ = "question_tag_link"
    question_id: uuid.UUID = Field(
        foreign_key="questions.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: uuid.UUID = Field(
        foreign_key="tags.id", primary_key=True, ondelete="CASCADE"
    )


class Tag(TagBase, table=True):
    __tablename__ = "tags"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    author: User | None = Relationship(back_populates="tags")
    questions: list["Question"] = Relationship(
        back_populates="tags", link_model=QuestionTagLink
    )


class TagPublic(TagBase):
    id: uuid.UUID
    user_id: uuid.UUID


class TagsPublic(SQLModel):
    data: list[TagPublic]
    count: int


# ─── Question ─────────────────────────────────────────────────────────────────


class QuestionBase(SQLModel):
    title: str = Field(min_length=1, max_length=500)
    difficulty: int = Field(default=3, ge=1, le=5)


class QuestionCreate(QuestionBase):
    content: str
    answer: str | None = None
    tag_ids: list[uuid.UUID] = []


class QuestionUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = None
    answer: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    tag_ids: list[uuid.UUID] | None = None


class Question(QuestionBase, table=True):
    __tablename__ = "questions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    content: str = Field(sa_type=Text())  # type: ignore
    answer: str | None = Field(default=None, sa_type=Text())  # type: ignore
    created_at: datetime | None = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    author: User | None = Relationship(back_populates="questions")
    tags: list[Tag] = Relationship(
        back_populates="questions", link_model=QuestionTagLink
    )
    review: Optional["ReviewSchedule"] = Relationship(
        back_populates="question", cascade_delete=True
    )


class QuestionPublic(QuestionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    content: str
    answer: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    tags: list[TagPublic] = []


class QuestionsPublic(SQLModel):
    data: list[QuestionPublic]
    count: int


# ─── Review Schedule (SM-2 Spaced Repetition) ─────────────────────────────────


class ReviewScheduleBase(SQLModel):
    interval_days: int = 1
    ease_factor: float = Field(default=2.5)
    repetitions: int = 0


class ReviewSchedule(ReviewScheduleBase, table=True):
    __tablename__ = "review_schedules"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    question_id: uuid.UUID = Field(
        foreign_key="questions.id", unique=True, ondelete="CASCADE"
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    next_review_at: datetime = Field(
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    last_reviewed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    question: Question | None = Relationship(back_populates="review")
    user: User | None = Relationship(back_populates="reviews")


class ReviewSchedulePublic(ReviewScheduleBase):
    id: uuid.UUID
    question_id: uuid.UUID
    user_id: uuid.UUID
    next_review_at: datetime
    last_reviewed_at: datetime | None = None


class ReviewSubmit(SQLModel):
    quality: int = Field(ge=0, le=5)


class DueReview(SQLModel):
    question: QuestionPublic
    review: ReviewSchedulePublic


# ─── Auth / Generic ───────────────────────────────────────────────────────────


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
