from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import Base

class Book(Base):
    __tablename__ = "book"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    locale: Mapped[str] = mapped_column(String, default="it-IT")
    home_page_id: Mapped[int | None] = mapped_column(ForeignKey("page.id"), nullable=True)
    
    # Relationships
    pages = relationship("Page", back_populates="book", cascade="all, delete-orphan")
    home_page = relationship("Page", foreign_keys=[home_page_id], post_update=True)
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', locale='{self.locale}')>"