# this file is used to parse the fit file and store the dev_data in the database
""" stelios (c) steliosmacrico "jHeel 2024 creating plugin"""
""" runningAalysis using average values"""

import sqlite3
import os
import logging
import datetime
from fitparse import FitFile

# Set up logging
now = datetime.datetime.now()
timestamp = now.strftime('%Y%m%d_%H%M%S')
logging.basicConfig(filename=f'e:/jHeel_Dev/gProjects/Artemis/Plugins/Logs/jheel_parse_RunningAnalysis{timestamp}.log', 
                   level=logging.INFO)

# Set up logging with debug level
logging.basicConfig(
    filename=f'e:/jHeel_Dev/gProjects/Artemis/Plugins/Logs/jheel_parse_RunningAnalysis{timestamp}.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def print_all_fields(fit_file_path):
    """Helper function to print all available fields in a FIT file"""
    fit_file = FitFile(fit_file_path)
    print("Available fields in FIT file:")
    for msg in fit_file.messages:
        if msg.name in ['session', 'record']:
            print(f"\nMessage type: {msg.name}")
            for field in msg.fields:
                print(f"Field name: {field.name}, Value: {field.value}")

logging.info('Starting RunninAnalysis Script...')
print('Starting RunninAnalysis script...')

def create_table_if_not_exists():
    conn = sqlite3.connect(r'e:/jheel_dev/dev_learn/dbs/running_analysis.db')
    cursor = conn.cursor()

    # Drop and create RunningAnalysis table
    # date, running_economy, vo2max, distance, time, heart_rate
    cursor.execute('DROP TABLE IF EXISTS RunAnal')
    logging.info('RunAnal table dropped successfully.')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RunAnal (
            activity_id INT PRIMARY KEY,
            timestamp TEXT,
            distance REAL,
            VO2maxSmooth INT,
            VO2maxSession INT,
            RunningEconomy INT,
            HeartRateAvg INT
        )
    ''')
    
    logging.info('Runanalysis table created successfully.')
    conn.commit()
    conn.close()

def parse_fit_file(file_path, activity_id):
    fit_file = FitFile(file_path)
    messages = fit_file.messages
    session_data = []

    for msg in messages:
        if msg.name == 'session':
            fields = msg.fields
            field_dict = {field.name: field.value for field in fields}
            
            # Create session data with proper field name handling and default None values
            session = {
                'activity_id': activity_id,
                'timestamp': field_dict.get('timestamp', None),
                'distance': field_dict.get('total_distance', None),
                'VO2maxSmooth': field_dict.get('VO2maxSmooth', None),
                'VO2maxSession': field_dict.get('VO2maxSession', None),
                'RunningEconomy': field_dict.get('Running Economy', None),
                'HeartRateAvg': field_dict.get('avg_heart_rate', None)
            }

            # Log available fields for debugging
            logging.debug(f"Available fields in session message: {list(field_dict.keys())}")
            
            session_data.append(session)

    # Add debug logging for the first session
    if session_data:
        logging.debug(f"First session data: {session_data[0]}")

    logging.info(f'Parsed session data for activity ID {activity_id}.')
    
    
    return session_data



def insert_data_into_db(data):
    conn = sqlite3.connect('e:/jheel_dev/dev_learn/dbs/running_analysis.db')
    cursor = conn.cursor()

    try:
        # Specify the fields you care about for jHeel component/ RunningAnalysis with average values
        specific_fields = ['VO2maxSmooth',
                        'VO2maxSession',
                        'Runningeconomy',
                        'HeartRateAvg']

        # Insert jHeel session data
        for session in data:
            # Check if all specific fields in the session dictionary are None
            if all(session.get(field) is None for field in specific_fields):
                # If they are, skip this iteration
                continue

            cursor.execute('''
                INSERT OR REPLACE INTO RunAnal (
                    activity_id, timestamp, distance, VO2maxSmooth, VO2maxSession, RunningEconomy, HeartRateAvg
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['activity_id'],
                session['timestamp'],
                session['distance'], 
                session['VO2maxSmooth'], 
                session['VO2maxSession'],
                session['RunningEconomy'], 
                session['HeartRateAvg']
            ))

        conn.commit()
        logging.info('RunAnal Data insertion completed successfully.')

    except Exception as e:
        logging.error(f"Error during data insertion: {str(e)}")
        conn.rollback()
        raise

    finally:
        conn.close()
    
def parse_all_fit_files_in_folder(folder_path):
    all_session_data = []
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.fit'):
            try:
                fit_file_path = os.path.join(folder_path, filename)
                activity_id = os.path.splitext(filename)[0].split('_')[0]
                
                session_data = parse_fit_file(
                    fit_file_path, activity_id)
                
                all_session_data.extend(session_data)
                    
            except Exception as e:
                logging.error(f'Error parsing file {filename}: {e}')
                print(f'Error parsing file {filename}: {e}')
                continue
    
    logging.info('All files parsed successfully.')
    print('All files parsed successfully.')
    
    return all_session_data

if __name__ == "__main__":
    try:
        create_table_if_not_exists()

        folder_path = 'c:/users/stma/healthdata/fitfiles/activitiesTEST'
        logging.info(f"Processing files from folder: {folder_path}")
        
        all_session_data = parse_all_fit_files_in_folder(folder_path)
        
        logging.info(f"Parsed data summary:")
        logging.info(f"Sessions: {len(all_session_data)}")
        
        insert_data_into_db(all_session_data)
        
        # Verify the database contents after insertion
        verify_database_contents()
        
        logging.info('RunningAnalysis Script completed successfully.')
        print('RunningAnalysis Script completed successfully.')
        
    except Exception as e:
        logging.error(f"Script failed with error: {str(e)}")
        print(f"Script failed with error: {str(e)}")