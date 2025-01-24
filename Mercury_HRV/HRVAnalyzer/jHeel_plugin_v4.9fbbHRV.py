# this file is used to parse the fit file and store the dev_data in the database
""" stelios (c) steliosmacrico "jHeel 2024 creating plugin - integrate fbb_HRV
""" 
""" purpose of this is to make a more simple plugin to manage hrvData"""
import sqlite3
import os
import logging
import datetime
from fbb_hrv_plugin import fbb_hrv

# Set up logging
# Get the current date and time
now = datetime.datetime.now()

# Format it as a string
timestamp = now.strftime('%Y%m%d_%H%M%S')

# Include the timestamp in the log file name
logging.basicConfig(filename=f'e:/jHeel_Dev/gProjects/Artemis/Logs_Dev/Prod_jheel_parse_fbbHRV_HRVv50{timestamp}.log', level=logging.INFO)

# Include the timestamp in the log file name
logging.info('Starting script...')
print('Starting script...')
 
def execute_fbb_hrv_plugin(fit_file_path, activity_id):
    try:
        fit_file = FitFile(fit_file_path)
        
        # Connect to database
        conn = sqlite3.connect('e:/jheel_dev/DataBasesDev/artemis_hrv.db')
        cursor = conn.cursor()
        
        # Process records
        record_num = 0
        for msg in fit_file.messages:
            if msg.name == 'record':
                fields = {field.name: field.value for field in msg.fields}
                
                cursor.execute('''
                    INSERT INTO hrv_records (activity_id, record, timestamp, hrv_s, hrv_btb, hrv_hr, rrhr, rawHR, RRint, hrv, rmssd, sdnn, SaO2_C, trndG_hrv, rR, bb, stress, stress_hra, hrvrmssd30s)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?,?,?)
                ''', (
                    activity_id,
                    record_num,
                    fields.get('timestamp'),
                    fields.get('hrv_s'),
                    fields.get('hrv_btb'),
                    fields.get('hrv_hr'),
                    fields.get('rrhr'),
                    fields.get('rawHR'),
                    fields.get('RRint'),
                    fields.get('hrv'),
                    fields.get('rmssd'),
                    fields.get('sdnn'),
                    fields.get('SaO2_C'),
                    fields.get('trndG_hrv'),
                    fields.get('rR'),
                    fields.get('bb'),
                    fields.get('stress'),
                    fields.get('stress_hra'),
                    fields.get('hrvrmssd30s')
                ))
                record_num += 1
            
            # Process session data
            elif msg.name == 'session':
                fields = {field.name: field.value for field in msg.fields}
                
                cursor.execute('''
                    INSERT INTO hrv_sessions (
                        activity_id, timestamp, sport, name, min_hr, hrv_rmssd, hrv_sdrr_f, 
                        hrv_sdrr_l, hrv_pnn50, hrv_pnn20, session_hrv, stress_hrpa, dBeats, sBeats, NN50, NN20, armssd, asdnn, SaO2, trnd_hrv, recovery, sdnn, sdsd, sd1, sd2, mean_rr, mean_hr, RMSSD, pNN50, PNN20, vlf, lf, hf,  lf_nu, hf_nu
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    activity_id,
                    fields.get('timestamp'),
                    fields.get('sport'),
                    fields.get('name'),
                    fields.get('min_hr'),
                    fields.get('hrv_rmssd'),
                    fields.get('hrv_sdrr_f'),
                    fields.get('hrv_sdrr_l'),
                    fields.get('hrv_pnn50'),
                    fields.get('hrv_pnn20'),
                    fields.get('session_hrv'),
                    fields.get('stress_hrpa'),
                    fields.get('dBeats'),
                    fields.get('sBeats'),
                    fields.get('NN50'),
                    fields.get('NN20'),
                    fields.get('armssd'),
                    fields.get('asdnn'),
                    fields.get('SaO2'),
                    fields.get('trnd_hrv'),
                    fields.get('recovery'),
                    fields.get('SDNN'),
                    fields.get('SDSD'),
                    fields.get('SD1'),
                    fields.get('SD2'),
                    fields.get('Mean RR'),
                    fields.get('Mean HR'),
                    fields.get('RMSSD'),
                    fields.get('pNN50'),
                    fields.get('PNN20'),
                    fields.get('VLF'),
                    fields.get('LF'),
                    fields.get('HF'),
                    fields.get('LFnu'),
                    fields.get('HFnu')
                ))
        
        conn.commit()
        conn.close()
        
        logging.info(f'fbb_hrv plugin executed successfully for activity {activity_id}')
    except Exception as e:
        logging.error(f'Error executing fbb_hrv plugin: {e}')

def create_table_if_not_exists():
    conn = sqlite3.connect(r'e:/jheel_dev/DataBasesDev/artemis_hrv.db')
    cursor = conn.cursor()

    #drop table if exists
    #cursor.execute('DROP TABLE IF EXISTS ArtemistblHRVdev')
    #logging.info('ArtemisTable41dev dropped successfully.')
    cursor.execute('DROP TABLE IF EXISTS hrv_records')
    logging.info('hrv_recordsDEV Table dropped successfully.')
    cursor.execute('DROP TABLE IF EXISTS hrv_sessions')
    logging.info('hrv_sessionsDEV Table dropped successfully.')
   
       # Create hrv_records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hrv_records (
            activity_id TEXT,
            record INTEGER,
            timestamp TEXT,
            hrv_s INTEGER,
            hrv_btb INTEGER,
            hrv_hr INTEGER,
            rrhr INTEGER,
            rawHR INTEGER,
            RRint INTEGER,
            hrv INTEGER,
            rmssd TEXT,
            sdnn INTEGER,
            SaO2_C INTEGER,
            trndG_hrv INTEGER,
            rR INTEGER,
            bb INTEGER,
            stress INTEGER,
            PRIMARY KEY (activity_id, record)
        )
    ''')

    # Create hrv_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hrv_sessions (
            activity_id TEXT PRIMARY KEY,
            timestamp TEXT,
            sport TEXT,
            name TEXT,
            min_hr INTEGER,
            hrv_rmssd INTEGER,
            hrv_sdrr_f INTEGER,
            hrv_sdrr_l INTEGER,
            hrv_pnn50 INTEGER,
            hrv_pnn20 INTEGER,
            stress_hrpa INTEGER,
            dBeats INTEGER,
            sBeats INTEGER,
            session_hrv INTEGER,
            NN50 INTEGER,
            NN20 INTEGER,
            armssd INTEGER,
            asdnn INTEGER,
            SaO2 INTEGER,
            trnd_hrv INTEGER,
            recovery INTEGER,
            sdnn INT,
            sdsd INT,
            sd1 INT,
            sd2 INT,
            mean_rr INT,
            mean_hr INT,
            RMSSD INT,
            pNN50 INT,
            PNN20 INT,
            vlf INT,
            lf INT,
            hf INT,
            lf_nu INT,
            hf_nu INT,
            stress_hra INTEGER,
            hrvrmssd30s INTEGER,
            FOREIGN KEY (activity_id) REFERENCES hrv_records (activity_id)
        )
    ''')

    # Create main ArtemistblV41dev the Production - main table
   

    
    logging.info('Table(s) created successfully.')

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
    
    # First execute the HRV plugin
    execute_fbb_hrv_plugin(file_path, activity_id)
    
    # Then continue with existing processing
    fit_file = FitFile(file_path)
    messages = fit_file.messages
    
    session_data = []

    for msg in messages:

            if msg.name == 'session':
                fields = msg.fields
                field_dict = {field.name: field.value for field in fields}
                
                timestamp = field_dict.get('timestamp')
                activity_id = activity_id
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

                
                session_data.append({
                    'activity_id': activity_id,
                    'timestamp': timestamp, # '2021-09-01 12:00:00
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
                    'MeanRR' : MeanRR

                })
                
                logging.info(f'Parsed session data for activity ID {activity_id}.')

    return session_data


# Insert the session data into the database

def insert_data_into_db(data):
    conn = sqlite3.connect('e:/jheel_dev/DataBasesDev/artemis_hrv.db')
    cursor = conn.cursor()

    # Specify the fields you care about
    specific_fields = ['timestamp',
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
                    'VLF','pNN50','LFnu','HFnu','MeanHR', 'MeanRR']  # Replace with your specific fields

    for session in data:
        # Check if all specific fields in the session dictionary are None
        if all(session[field] is None for field in specific_fields):
            # If they are, skip this iteration
            continue

        # The activity_id does not exist in the table, so insert the new record
        cursor.execute('''
            INSERT OR REPLACE INTO ArtemistblHRVdev(activity_id, timestamp, hrv, stress_hrpa, HR_RS_Deviation_Index ,hrv_sdrr_f, hrv_pnn50, hrv_pnn20, rmssd, lnrmssd, sdnn, sdsd, nn50, nn20, pnn20, Long, Short, Ectopic_S, hrv_rmssd, SD2, SD1, HF, LF, VLF, pNN50, LFnu, HFnu, MeanHR, MeanRR)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (session['activity_id'], session['timestamp'],session['stress_hrpa'], session['HR-RS_Deviation Index'], session['hrv_sdrr_f'], session['hrv_pnn50'], session['hrv_pnn20'], session['RMSSD'], session['lnRMSSD'], session['SDNN'], session['SDSD'], session['NN50'], session['NN20'], session['pnn20'], session['Long'], session['Short'], session['Ectopic_S'], session['hrv_rmssd'], session['SD2'], session['SD1'], session['HF'], session['LF'], session['VLF'], session['pNN50'], session['LFnu'], session['HFnu'], session['MeanHR'], session['MeanRR']))

    conn.commit()
    conn.close()


# run the script as wanted - main function - jHeel artemis data
if __name__ == "__main__":  
    create_table_if_not_exists()
try:
    all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activities2025')
    # all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activities')
    # insert_data_into_db(all_session_data)
    logging.info('All data inserted successfully.')
    print('All data inserted successfully (c)smacrico ')
except Exception as e:
    logging.error(f'Error processing data: {e}')
    print(f'Error processing data: {e}')

logging.info('Script completed successfully.')
print('Script completed successfully.')