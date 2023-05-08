import string
import random

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import Session, relationship

from .db import Base


class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    shortcode = Column(String, unique=True)
    created_at = Column(DateTime, default=func.now())

    visits = relationship('Visit', back_populates='url')

    @classmethod
    def create_url(cls, db: Session, original_url: str, shortcode: str):
        url = cls(url=original_url, shortcode=shortcode)
        db.add(url)
        db.commit()
        db.refresh(url)
        return url

    @classmethod
    def get_url_by_original_url(cls, db: Session, url: str):
        return db.query(cls).filter(cls.url == url).first()

    @classmethod
    def get_url_by_shortcode(cls, db: Session, shortcode: str):
        return db.query(cls).filter(cls.shortcode == shortcode).first()

    @staticmethod
    def _generate_shortcode(length=6):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    @classmethod
    def create_unique_url(cls, db: Session, original_url: str):
        unique_shortcode = False
        while not unique_shortcode:
            shortcode = cls._generate_shortcode()
            existing_url = cls.get_url_by_shortcode(db, shortcode)
            if existing_url is None:
                unique_shortcode = True
        return cls.create_url(db, original_url, shortcode)


class Visit(Base):
    __tablename__ = 'visits'

    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('urls.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())

    url = relationship('Url', back_populates='visits')

    @classmethod
    async def create_visit(cls, db: Session, url: Url):
        visit = cls(url=url)
        db.add(visit)
        db.commit()
