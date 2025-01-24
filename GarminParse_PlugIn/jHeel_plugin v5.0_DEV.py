
# this file is used to parse the fit file and store the dev_data in the database
""" stelios (c) steliosmacrico "jHeel 2024 creating plugin"""

######################################
"jHEEL Run version" ##################
'Purse fields only for Running' ######
######################################

import sqlite3
import os
import logging
import datetime


# Set up logging

# Get the current date and time
now = datetime.datetime.now()

# Format it as a string
timestamp = now.strftime('%Y%m%d_%H%M%S')

# Include the timestamp in the log file name
logging.basicConfig(filename=f'e:/jHeel_Dev/gProjects/Artemis/Logs_Dev/jheel_parse_DevFielsV5{timestamp}.log', level=logging.INFO)

# Include the timestamp in the log file name
logging.info('Starting script...')
print('Starting script...')

# Set up the database connection
# database_path = os.path.abspath('c:/users/stma/healthdata/dbs/garmin_activities.db')
# database_path = os.path.abspath('e:/jheel_dev/DataBasesDev/artemis.db')
 
def create_table_if_not_exists():
    conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/artemis.db')
    cursor = conn.cursor()

    #drop table if exists
    cursor.execute('DROP TABLE IF EXISTS Artemistbl_Prod')
    logging.info('Table dropped successfully.')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Artemistbl_Prod (
            activity_id INT PRIMARY KEY,
            timestamp TEXT,
            sport TEXT,
            avg_heart_rate INT,
            total_elapsed_time INT,
            distance REAL,
            hrv INT,
            fat INT,
            total_fat INT,  
            carbs INT,
            total_carbs INT,
            VO2maxSmooth INT,
            VO2maxSession INT,
            CardiacDrift INT,    
            CooperTest INT,
            steps INT,     
            field110 TXT,
            Running_Economy TXT
        )
    ''')
    
    logging.info('Table Artemistbl_Prod created successfully.')

    conn.commit()
    conn.close()


# Parse all .fit files in the specified folder (folder_path)
from fitparse import FitFile

def parse_all_fit_files_in_folder(folder_path):
    all_session_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.fit'):
            try:
                fit_file_path = os.path.join(folder_path, filename)
                activity_id = os.path.splitext(filename)[0]  # Get filename without extension
                activity_id = activity_id.split('_')[0]  # Get everything before '_' character
                session_data = parse_fit_file(fit_file_path, activity_id)
                all_session_data.extend(session_data)
            except Exception as e:
                logging.error(f'Error parsing file {filename}: {e}')
                print(f'Error parsing file {filename}: {e}')
                continue
            
            logging.info('All files parsed successfully.')  
            print('All files parsed successfully.')
            
    return all_session_data


# Parse a single .fit file and return the session data

def parse_fit_file(file_path, activity_id):
    fit_file = FitFile(file_path)

    messages = fit_file.messages
    session_data = []

    for msg in messages:

            if msg.name == 'session':
                fields = msg.fields
                field_dict = {field.name: field.value for field in fields}
                
                activity_id = activity_id
                timestamp = field_dict.get('timestamp')
                sport = field_dict.get('sport')
                avg_heart_rate = field_dict.get('avg_heart_rate')
                total_elapsed_time = field_dict.get('total_elapsed_time')
                distance = field_dict.get('total_distance')
                fat = field_dict.get('Fat')  
                total_fat = field_dict.get('Total Fat')
                carbs = field_dict.get('Carbs')
                total_carbs = field_dict.get('Total Carbs')
                VO2maxSmooth = field_dict.get('VO2maxSmooth')
                VO2maxSession = field_dict.get('VO2maxSession')
                CardiaDrift = field_dict.get('CardiacDrift')
                CooperTest = field_dict.get('CooperTest')
                steps = field_dict.get('Steps')
                field110 = field_dict.get('field 110')
                Running_Economy = field_dict.get('Running Economy')

                if steps is None:
                    steps = field_dict.get('steps')
                
                session_data.append({
                    'activity_id': activity_id,
                    'timestamp': timestamp, # '2021-09-01 12:00:00
                    'sport': sport,
                    'avg_heart_rate': avg_heart_rate,
                    'total_elapsed_time': total_elapsed_time,
                    'distance': distance,
                    'fat': fat,
                    'Total Fat': total_fat, # 'extra field for total fat
                    'Carbs' : carbs, 
                    'Total Carbs' : total_carbs, # 'extra field for total carbs
                    'VO2maxSmooth' : VO2maxSmooth,
                    'VO2maxSession' : VO2maxSession,
                    'CardiacDrift' : CardiaDrift,
                    'CooperTest' : CooperTest,
                    'Steps' : steps,
                    'field 110' : field110,
                    'Running Economy' : Running_Economy

                })
                
                logging.info(f'Parsed session data for activity ID {activity_id}.')

    return session_data


# Insert the session data into the database

def insert_data_into_db(data):
    conn = sqlite3.connect('e:/jheel_dev/DataBasesDev/artemis.db')
    cursor = conn.cursor()
    
    # Specify the fields you care about
    specific_fields = ['fat','Total Fat','Carbs','Total Carbs',
                    'VO2maxSmooth','sport',
                    'avg_heart_rate', 'total_elapsed_time',
                    'VO2maxSession', 'timestamp',
                    'CardiacDrift',
                    'CooperTest',
                    'Steps',
                    'field 110',
                    'Running Economy']  # Replace with your specific fields

    for session in data:
        # Check if all specific fields in the session dictionary are None
        if all(session[field] is None for field in specific_fields):
            # If they are, skip this iteration
            continue

        # The activity_id does not exist in the table, so insert the new record
        cursor.execute('''
            INSERT OR REPLACE INTO Artemistbl_Prod (activity_id, timestamp, sport, avg_heart_rate, total_elapsed_time, distance, fat, total_fat,carbs, total_carbs,  VO2maxSmooth, VO2maxSession, CardiacDrift, CooperTest, steps, field110, Running_Economy)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (session['activity_id'], session['timestamp'], session['sport'], session['avg_heart_rate'], session['total_elapsed_time'], session['distance'], session['fat'], session['Total Fat'], session['Carbs'], session['Total Carbs'], session['VO2maxSmooth'], session['VO2maxSession'], session['CardiacDrift'], session['CooperTest'], session['Steps'], session['field 110'], session['Running Economy']))

    conn.commit()
    conn.close()

#create view to join activities and garmin tables
def create_view_if_not_exists():
    # conn = sqlite3.connect('c:/users/stma/healthdata/dbs/garmin_activities.db')
    # conn = sqlite3.connect('c:/users/stma/healthdata/dbs/garmin_activities.db')
    conn = sqlite3.connect('e:/jheel_dev/DataBasesDev/artemis.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS RunProd_view AS
        SELECT activities.*
        FROM activities
        INNER JOIN Artemistbl_DevFields ON activities.activity_id = Artemistbl_DevFields.activity_id
        where Artemistbl_DevFields.sport == "running" ORDER BY Artemistbl_DevFields.timestamp DESC
    ''')
    
    logging.info('View created successfully.')

    conn.commit()
    conn.close()

# run the script as wanted - main function - jHeel artemis data
if __name__ == "__main__":  
    # create view and table
    create_table_if_not_exists()
    # create_view()
    create_view_if_not_exists()
    # all_session_data = parse_all_fit_files_in_folder('c:/steliosdev/jheel_dev/devinout/testfit')
    all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activities')
    # all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activities')
    insert_data_into_db(all_session_data)
    logging.info('All data inserted successfully.')
    print('All data inserted successfully.')

logging.info('Script completed successfully.')
print('Script completed successfully.')
