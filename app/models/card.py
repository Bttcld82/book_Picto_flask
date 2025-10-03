from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db import Base

class Card(Base):
    __tablename__ = "card"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("page.id"), nullable=False)
    slot_row: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_col: Mapped[int] = mapped_column(Integer, nullable=False)
    row_span: Mapped[int] = mapped_column(Integer, default=1)
    col_span: Mapped[int] = mapped_column(Integer, default=1)
    label: Mapped[str] = mapped_column(String, nullable=False)
    background_color: Mapped[str] = mapped_column(String, default="#FFFFFF")
    border_color: Mapped[str] = mapped_column(String, default="#000000")
    action_type: Mapped[str] = mapped_column(String, default="none")
    image_id: Mapped[int | None] = mapped_column(ForeignKey("asset.id"), nullable=True)
    target_page_id: Mapped[int | None] = mapped_column(ForeignKey("page.id"), nullable=True)
    
    # Relationships
    page = relationship("Page", back_populates="cards", foreign_keys="Card.page_id")
    target_page = relationship("Page", back_populates="target_cards", foreign_keys="Card.target_page_id")
    image = relationship("Asset", back_populates="cards")
    
    # Compatibility properties for templates
    @property
    def image_asset(self):
        """Alias per image per compatibilità template"""
        return self.image
    
    @property
    def image_asset_id(self):
        """Alias per image_id per compatibilità template"""
        return self.image_id
    
    @property
    def x(self):
        return self.slot_col
    
    @x.setter
    def x(self, value):
        self.slot_col = value
    
    @property
    def y(self):
        return self.slot_row
    
    @y.setter  
    def y(self, value):
        self.slot_row = value
    
    def __repr__(self):
        return f"<Card(id={self.id}, label='{self.label}', page_id={self.page_id})>"