
# this file is used to parse the fit file and store the dev_data in the database
""" stelios (c) steliosmacrico "jHeel 2024 creating plugin"""

######################################
"Developement and testing verison"####
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
logging.basicConfig(filename=f'e:/jHeel_Dev/gProjects/Artemis/Logs_Dev/jheel_parse_DEVtest_{timestamp}.log', level=logging.INFO)

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
    cursor.execute('DROP TABLE IF EXISTS Artemistbl_mariner')
    logging.info('Table dropped successfully.')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Artemistbl_mariner (
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
            stress_hrpa INT,
            HR_RS_Deviation_Index INT,
            hrv_sdrr_f INT,
            hrv_pnn50 INT,                          
            hrv_pnn20 INT,
            rmssd INT,
            lnrmssd INT,
            sdnn INT,
            sdsd INT,
            nn50 INT,
            nn20 INT,
            pnn20 INT,
            Long  INT,
            Short INT,
            Ectopic_S INT,
            hrv_rmssd INT,
            SD2 INT,
            SD1 INT,
            LF INT,
            HF INT,
            VLF INT,
            pNN50 INT, 
            LFnu INT, HFnu INT,MeanHR INT, MeanRR INT, Running_Economy TXT
        )
    ''')
    
    logging.info('Table created successfully.')

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
                
                timestamp = field_dict.get('timestamp')
                sport = field_dict.get('sport')
                avg_heart_rate = field_dict.get('avg_heart_rate')
                total_elapsed_time = field_dict.get('total_elapsed_time')
                activity_id = activity_id
                distance = field_dict.get('total_distance')
                hrv = field_dict.get('HRV')
                fat = field_dict.get('Fat')  
                total_fat = field_dict.get('Total Fat')
                carbs = field_dict.get('Carbs')
                total_carbs = field_dict.get('Total Carbs')
                VO2maxSmooth = field_dict.get('VO2maxSmooth')
                VO2maxSession = field_dict.get('VO2maxSession')
                CardiaDrift = field_dict.get('CardiacDrift')
                CooperTest = field_dict.get('CooperTest')
                steps = field_dict.get('Steps')
                stress_hrpa = field_dict.get('stress_hrpa')
                HR_RS_Deviation_Index = field_dict.get('HR-RS Deviation Index')
                hrv_sdrr_f = field_dict.get('hrv_sdrr_f')
                hrv_pnn50 = field_dict.get('hrv_pnn50')
                hrv_pnn20 = field_dict.get('hrv_pnn20')
                rmssd = field_dict.get('RMSSD')
                lnrmssd = field_dict.get('lnRMSSD')
                sdnn = field_dict.get('SDNN')
                sdsd = field_dict.get('SDSD')
                nn50 = field_dict.get('NN50')
                nn20 = field_dict.get('NN20')
                pnn20 = field_dict.get('pNN20')
                Long = field_dict.get('Long')
                Short = field_dict.get('Short')
                Ectopic_S = field_dict.get('Ectopic-S')
                hrv_rmssd = field_dict.get('hrv_rmssd')
                SD2 = field_dict.get('SD2')
                SD1 = field_dict.get('SD1')
                LF = field_dict.get('LF')
                HF = field_dict.get('HF')
                VLF = field_dict.get('VLF')
                pNN50 = field_dict.get('pNN50')
                LFnu = field_dict.get('LFnu')
                HFnu = field_dict.get('HFnu')
                MeanHR = field_dict.get('Mean HR')
                MeanRR = field_dict.get('Mean RR')
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
                    'hrv': hrv,
                    'fat': fat,
                    'Total Fat': total_fat, # 'extra field for total fat
                    'Carbs' : carbs, 
                    'Total Carbs' : total_carbs, # 'extra field for total carbs
                    'VO2maxSmooth' : VO2maxSmooth,
                    'VO2maxSession' : VO2maxSession,
                    'CardiacDrift' : CardiaDrift,
                    'CooperTest' : CooperTest,
                    'Steps' : steps,
                    'stress_hrpa' : stress_hrpa,
                    'HR-RS_Deviation Index' : HR_RS_Deviation_Index,
                    'hrv_sdrr_f' : hrv_sdrr_f,
                    'hrv_pnn50' : hrv_pnn50,
                    'hrv_pnn20' : hrv_pnn20,
                    'RMSSD' : rmssd,
                    'lnRMSSD' : lnrmssd,
                    'SDNN' : sdnn,
                    'SDSD' : sdsd,
                    'NN50' : nn50,
                    'NN20' : nn20,
                    'pnn20' : pnn20,
                    'Long' : Long,
                    'Short' : Short,
                    'Ectopic_S' : Ectopic_S,
                    'hrv_rmssd' : hrv_rmssd,
                    'SD2' : SD2,
                    'SD1' : SD1,
                    'HF' : HF,
                    'LF' : LF,
                    'VLF' : VLF,
                    'pNN50' : pNN50,
                    'LFnu'  : LFnu,
                    'HFnu' : HFnu,
                    'MeanHR' : MeanHR,
                    'MeanRR' : MeanRR,
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
                    'stress_hrpa',
                    'HR-RS_Deviation Index',
                    'hrv_sdrr_f',
                    'hrv_pnn50',
                    'hrv_pnn20',
                    'RMSSD',
                    'lnRMSSD',
                    'SDNN',
                    'SDSD',
                    'NN50',
                    'NN20',
                    'pnn20',
                    'Long',
                    'Short', 
                    'Ectopic_S',
                    'hrv_rmssd',
                    'SD2',
                    'SD1',
                    'LF',
                    'HF',
                    'VLF','pNN50','LFnu','HFnu','MeanHR', 'MeanRR', 'Running Economy']  # Replace with your specific fields

    for session in data:
        # Check if all specific fields in the session dictionary are None
        if all(session[field] is None for field in specific_fields):
            # If they are, skip this iteration
            continue

        # The activity_id does not exist in the table, so insert the new record
        cursor.execute('''
            INSERT OR REPLACE INTO Artemistbl_mariner (activity_id, distance, hrv, fat, total_fat,carbs, total_carbs,  VO2maxSmooth, sport, avg_heart_rate, total_elapsed_time, steps, stress_hrpa, HR_RS_Deviation_Index ,hrv_sdrr_f, hrv_pnn50, hrv_pnn20, rmssd, lnrmssd, sdnn, sdsd, nn50, nn20, pnn20, Long, Short, Ectopic_S, hrv_rmssd, VO2maxSession, timestamp, CardiacDrift, CooperTest, SD2, SD1, HF, LF, VLF, pNN50, LFnu, HFnu, MeanHR, MeanRR, Running_Economy)
            VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (session['activity_id'], session['distance'], session['hrv'], session['fat'], session['Total Fat'],session['Carbs'], session['Total Carbs'],session['VO2maxSmooth'], session['sport'], 
              session['avg_heart_rate'], session['total_elapsed_time'],
              session['Steps'], session['stress_hrpa'], session['HR-RS_Deviation Index'],session['hrv_sdrr_f'], session['hrv_pnn50'], session['hrv_pnn20'], session['RMSSD'], session['lnRMSSD'], session['SDNN'], session['SDSD'], session['NN50'], session['NN20'], session['pnn20'], session['Long'], session['Short'], session['Ectopic_S'], session['hrv_rmssd'], session['VO2maxSession'], 
              session ['timestamp'],session['CardiacDrift'], session['CooperTest'], session['SD2'], session['SD1'], session['HF'] , session['LF'], session['LF'], session['pNN50'], session['LFnu'], session['HFnu'],
              session['MeanRR'], session['MeanHR'], session['Running Economy']))

    conn.commit()
    conn.close()

#create view to join activities and garmin tables
def create_view_if_not_exists():
    # conn = sqlite3.connect('c:/users/stma/healthdata/dbs/garmin_activities.db')
    # conn = sqlite3.connect('c:/users/stma/healthdata/dbs/garmin_activities.db')
    conn = sqlite3.connect('e:/jheel_dev/DataBasesDev/artemis.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE VIEW IF NOT EXISTS RunMariner_view AS
        SELECT activities.*
        FROM activities
        INNER JOIN Artemistbl_mariner ON activities.activity_id = Artemistbl_mariner.activity_id
        where Artemistbl_mariner.sport == "running" ORDER BY Artemistbl_mariner.timestamp DESC
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
    all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activitiesTEST')
    # all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activities')
    insert_data_into_db(all_session_data)
    logging.info('All data inserted successfully.')
    print('All data inserted successfully.')

logging.info('Script completed successfully.')
print('Script completed successfully.')
