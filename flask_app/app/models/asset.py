from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import Base

class Asset(Base):
    __tablename__ = "asset"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # 'image'
    url: Mapped[str] = mapped_column(String, nullable=False)
    alt: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Relationships
    cards = relationship("Card", back_populates="image")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, kind='{self.kind}', url='{self.url}')>"