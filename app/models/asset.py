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
    
    @property
    def normalized_url(self) -> str:
        """Return a safe, normalized URL usable in templates.
        Handles values like 'media/uuid.jpg', '/media/uuid.jpg',
        '/static/media/uuid.jpg', absolute http(s), or data URLs.
        """
        if not self.url:
            return ""
        url = self.url.strip()
        # Absolute or data URLs pass through
        if url.startswith("http://") or url.startswith("https://") or url.startswith("data:"):
            return url
        # Already a full static path
        if url.startswith("/static/"):
            return url
        # '/media/...' -> '/static/media/...'
        if url.startswith("/media/"):
            return "/static" + url
        # 'media/...' -> '/static/media/...'
        if url.startswith("media/"):
            return "/static/" + url
        # plain filename or other relative -> assume static/media
        return "/static/media/" + url.lstrip("/")

    def __repr__(self):
        return f"<Asset(id={self.id}, kind='{self.kind}', url='{self.url}')>"