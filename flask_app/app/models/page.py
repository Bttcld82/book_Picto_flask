from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import Base

class Page(Base):
    __tablename__ = "page"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    grid_cols: Mapped[int] = mapped_column(Integer, default=3)
    grid_rows: Mapped[int] = mapped_column(Integer, default=3)
    order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    book = relationship("Book", back_populates="pages", foreign_keys=[book_id])
    cards = relationship("Card", back_populates="page", cascade="all, delete-orphan")
    target_cards = relationship("Card", foreign_keys="Card.target_page_id", back_populates="target_page")
    
    def __repr__(self):
        return f"<Page(id={self.id}, title='{self.title}', book_id={self.book_id})>"