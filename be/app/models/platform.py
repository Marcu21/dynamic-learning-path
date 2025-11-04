from sqlalchemy import Column, String, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base


class Platform(Base):
    __tablename__ = 'platforms'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    website_url = Column(String(500), nullable=True)
    
    modules = relationship("Module", back_populates="platform")
    
    def __init__(self, name, website_url=None):
        self.name = name
        self.website_url = website_url
    
    def __repr__(self):
        return f'<Platform:\n \
                id: {self.id}\n \
                name: {self.name}\n \
                website_url: {self.website_url}>'
