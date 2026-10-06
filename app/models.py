from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class District(Base):
    """行政區"""

    __tablename__ = "districts"

    city_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    city_name: Mapped[str] = mapped_column(String(32))

    routes: Mapped[list["Route"]] = relationship(back_populates="district")


class Route(Base):
    """清運路線"""

    __tablename__ = "routes"

    line_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    city_id: Mapped[str] = mapped_column(ForeignKey("districts.city_id"), index=True)

    district: Mapped[District] = relationship(back_populates="routes")
    trucks: Mapped[list["Truck"]] = relationship(back_populates="route")


class Truck(Base):
    """垃圾車（以車牌為主鍵）"""

    __tablename__ = "trucks"

    car: Mapped[str] = mapped_column(String(16), primary_key=True)
    line_id: Mapped[str] = mapped_column(ForeignKey("routes.line_id"), index=True)

    route: Mapped[Route] = relationship(back_populates="trucks")
    locations: Mapped[list["Location"]] = relationship(back_populates="truck")


class Location(Base):
    """垃圾車位置紀錄"""

    __tablename__ = "locations"
    __table_args__ = (Index("ix_locations_car_time", "car", "recorded_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    car: Mapped[str] = mapped_column(ForeignKey("trucks.car"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    address: Mapped[str] = mapped_column(String(128))
    longitude: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float] = mapped_column(Float)

    truck: Mapped[Truck] = relationship(back_populates="locations")
