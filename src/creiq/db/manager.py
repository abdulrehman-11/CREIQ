"""
Database manager for the CREIQ application.

This module provides a database manager class to handle database operations.
"""

import os
import logging
import datetime
from typing import List, Dict, Any, Optional, Union
from dateutil import parser as date_parser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, joinedload

from creiq.db.config import DATABASE_URL, DATABASE_LOG_LEVEL
from creiq.db.models import Base, Property, Appeal, AppealDetail, Representative, Hearing

# Set up logging
logging.basicConfig(level=getattr(logging, DATABASE_LOG_LEVEL))
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager class for handling database operations."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database manager with a connection string.
        
        Args:
            connection_string: Optional database connection string.
                If not provided, uses the DATABASE_URL from environment variables.
        """
        self.connection_string = connection_string or DATABASE_URL
        logger.info(f"Initializing database with connection string: {self.connection_string}")
        
        # Create engine and session factory
        self.engine = create_engine(self.connection_string)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        logger.info("Creating database tables")
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session.
        
        Returns:
            A new SQLAlchemy session.
        """
        return self.Session()
    
    def parse_date(self, date_str: str) -> Optional[datetime.datetime]:
        """Parse date string into a datetime object.
        
        Args:
            date_str: Date string in various formats.
        
        Returns:
            Datetime object or None if parsing fails.
        """
        if not date_str or date_str == "":
            return None
        
        try:
            return date_parser.parse(date_str)
        except Exception as e:
            logger.warning(f"Failed to parse date: {date_str}. Error: {str(e)}")
            return None
    
    def store_data(self, parsed_data: Dict[str, Any]) -> None:
        """Store parsed data in the database.
        
        Args:
            parsed_data: Parsed data dictionary with URLs as keys.
        """
        logger.info("Storing parsed data in database")
        
        with self.get_session() as session:
            for url, data in parsed_data.items():
                property_info = data.get('property_info', {})
                appeals = data.get('appeals', [])
                
                if not property_info or not property_info.get('roll_number'):
                    logger.warning(f"Skipping URL {url} - no valid property info")
                    continue
                
                # Create or update property
                property_obj = self._store_property(session, property_info)
                
                # Process appeals
                for appeal_data in appeals:
                    self._store_appeal(session, appeal_data, property_obj.roll_number)
                
            # Commit all changes
            session.commit()
    
    def _store_property(self, session: Session, property_info: Dict[str, Any]) -> Property:
        """Store property information in the database.
        
        Args:
            session: Database session.
            property_info: Property information dictionary.
        
        Returns:
            Property object.
        """
        roll_number = property_info.get('roll_number')
        
        # Check if property already exists
        property_obj = session.query(Property).filter_by(roll_number=roll_number).first()
        
        if not property_obj:
            # Create new property
            property_obj = Property(
                roll_number=roll_number,
                property_description=property_info.get('property_description', '')
            )
            session.add(property_obj)
            logger.info(f"Created new property: {roll_number}")
        
        # Update property attributes if details available
        if property_info.get('details') and property_info.get('details').get('property_information'):
            prop_details = property_info.get('details').get('property_information')
            property_obj.municipality = prop_details.get('municipality')
            property_obj.property_classification = prop_details.get('property_classification')
            property_obj.neighborhood = prop_details.get('nbhd')
        
        return property_obj
    
    def _store_appeal(self, session: Session, appeal_data: Dict[str, Any], roll_number: str) -> Optional[Appeal]:
        """Store appeal information in the database.
        
        Args:
            session: Database session.
            appeal_data: Appeal data dictionary.
            roll_number: Property roll number.
        
        Returns:
            Appeal object or None if invalid appeal.
        """
        appeal_info = appeal_data.get('AppealNo', {})
        if not appeal_info or not appeal_info.get('text'):
            logger.warning(f"Skipping appeal - no valid appeal number")
            return None
        
        appeal_number = appeal_info.get('text')
        
        # Check if appeal already exists
        appeal_obj = session.query(Appeal).filter_by(appeal_number=appeal_number).first()
        
        if not appeal_obj:
            # Create new appeal
            appeal_obj = Appeal(
                appeal_number=appeal_number,
                roll_number=roll_number,
                appellant=appeal_data.get('Appellant', ''),
                section=appeal_data.get('Section', ''),
                tax_date=self.parse_date(appeal_data.get('Tax Date')),
                status=appeal_data.get('Status', ''),
                board_order_no=appeal_data.get('Board Order No', '')
            )
            session.add(appeal_obj)
            logger.info(f"Created new appeal: {appeal_number}")
        else:
            # Update appeal attributes
            appeal_obj.appellant = appeal_data.get('Appellant', appeal_obj.appellant)
            appeal_obj.section = appeal_data.get('Section', appeal_obj.section)
            appeal_obj.status = appeal_data.get('Status', appeal_obj.status)
            appeal_obj.board_order_no = appeal_data.get('Board Order No', appeal_obj.board_order_no)
            
            if appeal_data.get('Tax Date'):
                appeal_obj.tax_date = self.parse_date(appeal_data.get('Tax Date'))
        
        # Process representative
        if appeal_data.get('Representative'):
            self._store_representative(session, appeal_obj, appeal_data.get('Representative'))
        
        # Process hearing
        if appeal_data.get('Hearing Date') or (appeal_data.get('Hearing No') and appeal_data.get('Hearing No').get('text')):
            self._store_hearing(session, appeal_obj, appeal_data)
        
        # Process appeal details
        if appeal_info.get('details'):
            self._store_appeal_details(session, appeal_obj, appeal_info.get('details'))
        
        return appeal_obj
    
    def _store_representative(self, session: Session, appeal: Appeal, representative_name: str) -> Representative:
        """Store representative information in the database.
        
        Args:
            session: Database session.
            appeal: Appeal object.
            representative_name: Representative name.
        
        Returns:
            Representative object.
        """
        # Check if representative already exists
        rep_obj = session.query(Representative).filter_by(name=representative_name).first()
        
        if not rep_obj:
            # Create new representative
            rep_obj = Representative(
                name=representative_name,
                type='Unknown'  # Default type
            )
            session.add(rep_obj)
            logger.info(f"Created new representative: {representative_name}")
        
        # Add association if it doesn't exist
        if rep_obj not in appeal.representatives:
            appeal.representatives.append(rep_obj)
        
        return rep_obj
    
    def _store_hearing(self, session: Session, appeal: Appeal, appeal_data: Dict[str, Any]) -> Optional[Hearing]:
        """Store hearing information in the database.
        
        Args:
            session: Database session.
            appeal: Appeal object.
            appeal_data: Appeal data dictionary.
        
        Returns:
            Hearing object or None if no hearing data.
        """
        hearing_date = self.parse_date(appeal_data.get('Hearing Date', ''))
        hearing_number = appeal_data.get('Hearing No', {}).get('text', '')
        
        if not hearing_date and not hearing_number:
            return None
        
        # Check if hearing already exists
        hearing_obj = None
        if hearing_number:
            hearing_obj = session.query(Hearing).filter_by(
                appeal_number=appeal.appeal_number,
                hearing_number=hearing_number
            ).first()
        
        if not hearing_obj:
            # Create new hearing
            hearing_obj = Hearing(
                appeal_number=appeal.appeal_number,
                hearing_number=hearing_number,
                hearing_date=hearing_date
            )
            session.add(hearing_obj)
            logger.info(f"Created new hearing for appeal: {appeal.appeal_number}")
        else:
            # Update hearing
            if hearing_date:
                hearing_obj.hearing_date = hearing_date
        
        return hearing_obj
    
    def _store_appeal_details(self, session: Session, appeal: Appeal, details: Dict[str, Any]) -> Optional[AppealDetail]:
        """Store appeal detail information in the database.
        
        Args:
            session: Database session.
            appeal: Appeal object.
            details: Appeal details dictionary.
        
        Returns:
            AppealDetail object or None if no detail data.
        """
        if not details:
            return None
        
        appellant_info = details.get('appellant_information', {})
        property_info = details.get('property_information', {})
        
        # Check if appeal details already exist
        detail_obj = session.query(AppealDetail).filter_by(appeal_number=appeal.appeal_number).first()
        
        if not detail_obj:
            # Create new appeal details
            detail_obj = AppealDetail(
                appeal_number=appeal.appeal_number,
                filing_date=self.parse_date(appellant_info.get('filing_date', '')),
                reason_for_appeal=appellant_info.get('reason_for_appeal', ''),
                decision_mailing_date=self.parse_date(property_info.get('decision_mailing_date', '')),
                decision_text=property_info.get('decision_s', ''),
                decision_details=property_info.get('decisiondetails', '')
            )
            session.add(detail_obj)
            logger.info(f"Created new appeal details for appeal: {appeal.appeal_number}")
        else:
            # Update appeal details
            if appellant_info.get('filing_date'):
                detail_obj.filing_date = self.parse_date(appellant_info.get('filing_date', ''))
            
            if appellant_info.get('reason_for_appeal'):
                detail_obj.reason_for_appeal = appellant_info.get('reason_for_appeal', '')
            
            if property_info.get('decision_mailing_date'):
                detail_obj.decision_mailing_date = self.parse_date(property_info.get('decision_mailing_date', ''))
            
            if property_info.get('decision_s'):
                detail_obj.decision_text = property_info.get('decision_s', '')
            
            if property_info.get('decisiondetails'):
                detail_obj.decision_details = property_info.get('decisiondetails', '')
        
        return detail_obj
    
    def get_property_by_roll_number(self, roll_number: str) -> Optional[Property]:
        """Get property by roll number.
        
        Args:
            roll_number: Property roll number.
        
        Returns:
            Property object or None if not found.
        """
        with self.get_session() as session:
            return session.query(Property).filter_by(roll_number=roll_number).first()
    
    def get_appeal_by_number(self, appeal_number: str) -> Optional[Appeal]:
        """Get appeal by appeal number.
        
        Args:
            appeal_number: Appeal number.
        
        Returns:
            Appeal object or None if not found.
        """
        with self.get_session() as session:
            # Use eager loading to load all related data
            return session.query(Appeal).options(
                joinedload(Appeal.details),
                joinedload(Appeal.representatives),
                joinedload(Appeal.hearings)
            ).filter_by(appeal_number=appeal_number).first()
    
    def get_appeals_by_property(self, roll_number: str) -> List[Appeal]:
        """Get all appeals for a property.
        
        Args:
            roll_number: Property roll number.
        
        Returns:
            List of Appeal objects.
        """
        with self.get_session() as session:
            # Use eager loading to load all related data
            return session.query(Appeal).options(
                joinedload(Appeal.details),
                joinedload(Appeal.representatives),
                joinedload(Appeal.hearings)
            ).filter_by(roll_number=roll_number).all()
    
    def get_appeals_by_status(self, status: str) -> List[Appeal]:
        """Get appeals by status.
        
        Args:
            status: Appeal status.
        
        Returns:
            List of Appeal objects with matching status.
        """
        with self.get_session() as session:
            # Use eager loading to load all related data
            return session.query(Appeal).options(
                joinedload(Appeal.details),
                joinedload(Appeal.representatives),
                joinedload(Appeal.hearings)
            ).filter_by(status=status).all()
    
    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()