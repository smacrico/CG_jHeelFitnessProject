"""
HRV Data Processor and Analyzer v.1 (Development Version)
Processes heart rate variance data from FIT files using fbbbrown's Heart Monitor + HRV app format.
"""

import logging
import os
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, Column, Integer, DateTime, String, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fitparse import FitFile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create SQLAlchemy base
Base = declarative_base()

class HRVRecords(Base):
    """Table for storing detailed HRV records"""
    __tablename__ = 'hrv_records'
    
    activity_id = Column(String, primary_key=True)
    record = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    hrv_s = Column(Integer)      # ms
    hrv_btb = Column(Integer)    # ms
    hrv_hr = Column(Integer)     # bpm

class HRVSessions(Base):
    """Table for storing HRV session summaries"""
    __tablename__ = 'hrv_sessions'
    
    activity_id = Column(String, primary_key=True)
    timestamp = Column(DateTime)
    min_hr = Column(Integer)     # bpm
    hrv_rmssd = Column(Integer)  # bpm
    hrv_sdrr_f = Column(Integer) # bpm
    hrv_sdrr_l = Column(Integer) # bpm
    hrv_pnn50 = Column(Integer)  # percentage
    hrv_pnn20 = Column(Integer)  # percentage

class HRVProcessor:
    """Main class for processing and analyzing HRV data"""
    
    _application_id = bytearray(b'\x0b\xdc\x0eu\x9b\xaaAz\x8c\x9f\xe9vf*].')

    def __init__(self, db_path='sqlite:///astremis_hrv.db'):
        self.engine = create_engine(db_path)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self._create_views()

    def _create_views(self):
        """Create database views for analysis"""
        views = {
            'daily_hrv_summary': """
                CREATE VIEW IF NOT EXISTS daily_hrv_summary AS
                SELECT 
                    DATE(timestamp) as date,
                    AVG(hrv_rmssd) as avg_rmssd,
                    AVG(hrv_sdrr_f) as avg_sdrr_f,
                    AVG(hrv_sdrr_l) as avg_sdrr_l,
                    AVG(hrv_pnn50) as avg_pnn50,
                    AVG(hrv_pnn20) as avg_pnn20,
                    MIN(min_hr) as lowest_hr
                FROM hrv_sessions
                GROUP BY DATE(timestamp)
            """,
            'detailed_hrv_analysis': """
                CREATE VIEW IF NOT EXISTS detailed_hrv_analysis AS
                SELECT 
                    r.activity_id,
                    r.timestamp,
                    r.hrv_btb,
                    r.hrv_hr,
                    s.hrv_rmssd,
                    s.hrv_sdrr_f,
                    s.hrv_sdrr_l
                FROM hrv_records r
                JOIN hrv_sessions s ON r.activity_id = s.activity_id
            """
        }
        
        with self.engine.connect() as conn:
            for view_name, view_sql in views.items():
                conn.execute(text(view_sql))
                conn.commit()

    def write_record_entry(self, db_session, fit_file, activity_id, message_fields, record_num):
        """Write a record message into the records table"""
        try:
            record = {
                'activity_id': activity_id,
                'record': record_num,
                'timestamp': fit_file.utc_datetime_to_local(message_fields.timestamp),
                'hrv_s': message_fields.get('dev_hrv_s'),
                'hrv_btb': message_fields.get('dev_hrv_btb'),
                'hrv_hr': message_fields.get('dev_hrv_hr'),
            }
            
            existing = db_session.query(HRVRecords).filter_by(
                activity_id=activity_id, 
                record=record_num
            ).first()
            
            if not existing:
                logger.debug(f"Writing HRV record {record} for {fit_file.filename}")
                db_session.add(HRVRecords(**record))
                
            return record
            
        except Exception as e:
            logger.error(f"Error writing record entry: {e}")
            return None

    def write_session_entry(self, db_session, fit_file, activity_id, message_fields):
        """Write a session message into the sessions table"""
        try:
            session = {
                'activity_id': activity_id,
                'timestamp': fit_file.utc_datetime_to_local(message_fields.timestamp),
                'min_hr': message_fields.get('dev_min_hr'),
                'hrv_rmssd': message_fields.get('dev_hrv_rmssd'),
                'hrv_sdrr_f': message_fields.get('dev_hrv_sdrr_f'),
                'hrv_sdrr_l': message_fields.get('dev_hrv_sdrr_l'),
                'hrv_pnn50': message_fields.get('dev_hrv_pnn50'),
                'hrv_pnn20': message_fields.get('dev_hrv_pnn20'),
            }
            
            existing = db_session.query(HRVSessions).filter_by(
                activity_id=activity_id
            ).first()
            
            if not existing:
                logger.debug(f"Writing HRV session {session} for {fit_file.filename}")
                db_session.add(HRVSessions(**session))
                
            return session
            
        except Exception as e:
            logger.error(f"Error writing session entry: {e}")
            return None

    def process_fit_file(self, fit_file_path):
        """Process a single FIT file"""
        try:
            fit_file = FitFile(fit_file_path)
            
            # Check if this is an HRV activity
            messages = fit_file.messages
            app_id = None
            for message in messages:
                if message.name == 'file_id':
                    app_id = message.fields.get('application_id')
                    break
                    
            if app_id != self._application_id:
                logger.info(f"Skipping {fit_file_path} - not an HRV activity")
                return False

            session = self.Session()
            try:
                record_num = 0
                activity_id = os.path.basename(fit_file_path)
                
                for message in messages:
                    if message.name == 'record':
                        self.write_record_entry(session, fit_file, activity_id, message.fields, record_num)
                        record_num += 1
                    elif message.name == 'session':
                        self.write_session_entry(session, fit_file, activity_id, message.fields)
                
                session.commit()
                logger.info(f"Successfully processed {fit_file_path}")
                return True
                
            except Exception as e:
                logger.error(f"Error processing file {fit_file_path}: {e}")
                session.rollback()
                return False
                
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error opening file {fit_file_path}: {e}")
            return False

    def get_daily_summary(self, start_date=None, end_date=None):
        """Get daily HRV summary within date range"""
        query = """
        SELECT * FROM daily_hrv_summary 
        WHERE date BETWEEN :start_date AND :end_date
        ORDER BY date
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"start_date": start_date, "end_date": end_date}
            )
            return pd.DataFrame(result.fetchall())

    def analyze_hrv_trends(self, days=30):
        """Analyze HRV trends over specified number of days"""
        query = """
        SELECT 
            date,
            avg_rmssd,
            avg_sdrr_f,
            avg_sdrr_l,
            avg_pnn50
        FROM daily_hrv_summary
        ORDER BY date DESC
        LIMIT :days
        """
        
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={"days": days})
            
            stats = {
                'rmssd_mean': df['avg_rmssd'].mean(),
                'rmssd_std': df['avg_rmssd'].std(),
                'sdrr_f_mean': df['avg_sdrr_f'].mean(),
                'sdrr_l_mean': df['avg_sdrr_l'].mean(),
                'pnn50_mean': df['avg_pnn50'].mean()
            }
            
            # Calculate trends
            stats['rmssd_trend'] = np.polyfit(range(len(df)), df['avg_rmssd'], 1)[0]
            
            return stats

    def calculate_recovery_score(self, activity_id):
        """Calculate recovery score based on HRV metrics"""
        query = """
        SELECT 
            hrv_rmssd,
            hrv_sdrr_l,
            hrv_pnn50,
            min_hr
        FROM hrv_sessions
        WHERE activity_id = :activity_id
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"activity_id": activity_id}).fetchone()
            
            if result:
                rmssd_score = min(100, result.hrv_rmssd / 2)
                sdrr_score = min(100, result.hrv_sdrr_l / 2)
                pnn50_score = result.hrv_pnn50
                
                recovery_score = (rmssd_score + sdrr_score + pnn50_score) / 3
                return round(recovery_score, 2)
            return None

def process_activities_folder(folder_path):
    """Process all FIT files in the specified folder"""
    processor = HRVProcessor()
    
    if not os.path.exists(folder_path):
        logger.error(f"Folder {folder_path} does not exist")
        return
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.fit'):
            file_path = os.path.join(folder_path, filename)
            logger.info(f"Processing {file_path}")
            processor.process_fit_file(file_path)
    
    return processor

def main():
    # Process activities from the test folder
    activities_folder = "activitiesTest"
    processor = process_activities_folder(activities_folder)
    
    if processor:
        # Example analysis
        print("\nAnalyzing HRV trends for the last 30 days:")
        trends = processor.analyze_hrv_trends()
        for metric, value in trends.items():
            print(f"{metric}: {value:.2f}")

if __name__ == "__main__":
    main()