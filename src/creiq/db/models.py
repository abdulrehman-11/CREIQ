"""
Database models for the CREIQ application.

This module defines the SQLAlchemy ORM models for storing property and appeal data.
"""

import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# Many-to-many relationship table between appeals and representatives
appeal_representatives = Table(
    'appeal_representatives', 
    Base.metadata,
    Column('appeal_number', String, ForeignKey('appeals.appeal_number')),
    Column('representative_id', Integer, ForeignKey('representatives.id'))
)


class Property(Base):
    """Property model representing a real estate property."""
    
    __tablename__ = 'properties'
    
    roll_number = Column(String, primary_key=True)
    property_description = Column(String)
    municipality = Column(String, nullable=True)
    property_classification = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    
    # Relationships
    appeals = relationship("Appeal", back_populates="property", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Property(roll_number='{self.roll_number}', description='{self.property_description}')>"


class Appeal(Base):
    """Appeal model representing an assessment appeal for a property."""
    
    __tablename__ = 'appeals'
    
    appeal_number = Column(String, primary_key=True)
    roll_number = Column(String, ForeignKey('properties.roll_number'))
    appellant = Column(String)
    section = Column(String)
    tax_date = Column(DateTime, nullable=True)
    status = Column(String)
    board_order_no = Column(String, nullable=True)
    
    # Relationships
    property = relationship("Property", back_populates="appeals")
    details = relationship("AppealDetail", back_populates="appeal", cascade="all, delete-orphan", uselist=False)
    representatives = relationship("Representative", secondary=appeal_representatives, back_populates="appeals")
    hearings = relationship("Hearing", back_populates="appeal", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Appeal(appeal_number='{self.appeal_number}', appellant='{self.appellant}', status='{self.status}')>"


class AppealDetail(Base):
    """AppealDetail model representing detailed information about an appeal."""
    
    __tablename__ = 'appeal_details'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    appeal_number = Column(String, ForeignKey('appeals.appeal_number'), unique=True)
    filing_date = Column(DateTime, nullable=True)
    reason_for_appeal = Column(String, nullable=True)
    decision_mailing_date = Column(DateTime, nullable=True)
    decision_text = Column(Text, nullable=True)
    decision_details = Column(Text, nullable=True)
    
    # Relationships
    appeal = relationship("Appeal", back_populates="details")
    
    def __repr__(self) -> str:
        return f"<AppealDetail(appeal_number='{self.appeal_number}', reason='{self.reason_for_appeal}')>"


class Representative(Base):
    """Representative model representing a party involved in an appeal."""
    
    __tablename__ = 'representatives'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    type = Column(String, nullable=True)  # appellant, respondent, etc.
    
    # Relationships
    appeals = relationship("Appeal", secondary=appeal_representatives, back_populates="representatives")
    
    def __repr__(self) -> str:
        return f"<Representative(id={self.id}, name='{self.name}', type='{self.type}')>"


class Hearing(Base):
    """Hearing model representing a scheduled hearing for an appeal."""
    
    __tablename__ = 'hearings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    appeal_number = Column(String, ForeignKey('appeals.appeal_number'))
    hearing_number = Column(String, nullable=True)
    hearing_date = Column(DateTime, nullable=True)
    
    # Relationships
    appeal = relationship("Appeal", back_populates="hearings")
    
    def __repr__(self) -> str:
        return f"<Hearing(id={self.id}, appeal_number='{self.appeal_number}', date='{self.hearing_date}')>"