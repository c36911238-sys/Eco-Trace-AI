import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base


class CategoryEnum(str, enum.Enum):
    transportation = "transportation"
    food = "food"
    electricity = "electricity"
    shopping = "shopping"
    waste = "waste"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    eco_level: Mapped[int] = mapped_column(Integer, default=1)
    total_carbon_saved: Mapped[float] = mapped_column(Float, default=0.0)  # kg CO2
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    logs: Mapped[list["CarbonLog"]] = relationship("CarbonLog", back_populates="user")
    predictions: Mapped[list["CarbonPrediction"]] = relationship(
        "CarbonPrediction", back_populates="user"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="user"
    )


class CarbonLog(Base):
    __tablename__ = "carbon_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # index=True on FK columns eliminates full table scans on user lookups
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    category: Mapped[CategoryEnum] = mapped_column(
        Enum(CategoryEnum), nullable=False
    )
    emission_amount: Mapped[float] = mapped_column(Float, nullable=False)  # kg CO2
    source: Mapped[str] = mapped_column(String, default="manual")  # 'manual' | 'ocr'
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    logged_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="logs")


class CarbonPrediction(Base):
    __tablename__ = "carbon_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    target_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    predicted_emission: Mapped[float] = mapped_column(Float, nullable=False)
    feature_importance: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # SHAP explanation as JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="predictions")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    action_title: Mapped[str] = mapped_column(String, nullable=False)
    action_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    potential_impact: Mapped[float] = mapped_column(Float, nullable=False)  # kg CO2
    status: Mapped[str] = mapped_column(
        String, default="pending"
    )  # pending | accepted | completed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="recommendations")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    badge_name: Mapped[str] = mapped_column(String, nullable=False)
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
