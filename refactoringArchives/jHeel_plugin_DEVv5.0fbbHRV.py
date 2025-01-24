# this file is used to parse the fit file and store the dev_data in the database
""" stelios (c) steliosmacrico "jHeel 2024 creating plugin - integrate fbb_HRV
"""" revision (c) November 2019 - save data to PostgresSQL"
""" purpose of this is to make a more simple plugin to manage hrvData"""
import psycopg2
import os
import logging
import datetime
import fitparse
from fitparse import FitFile

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="garminDB_v2",
        user="postgres",
        password="Penivalia2627"
    )

def create_tables_in_postgres():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS hrv_recordsDEV')
    cursor.execute('DROP TABLE IF EXISTS hrv_sessionsDEV')
    cursor.execute('DROP TABLE IF EXISTS ArtemistblV41dev')

    # Create hrv_records table
    cursor.execute('''
        CREATE TABLE hrv_recordsDEV (
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
            PRIMARY KEY (activity_id, record)
        )
    ''')

    # Create hrv_sessions table
    cursor.execute('''
        CREATE TABLE hrv_sessionsDEV (
            activity_id TEXT PRIMARY KEY,
            timestamp TEXT,
            min_hr INTEGER,
            hrv_rmssd INTEGER,
            hrv_sdrr_f INTEGER,
            hrv_sdrr_l INTEGER,
            hrv_pnn50 INTEGER,
            hrv_pnn20 INTEGER,
            session_hrv INTEGER,
            NN50 INTEGER,
            NN20 INTEGER,
            armssd INTEGER,
            asdnn INTEGER,
            SaO2 INTEGER,
            trnd_hrv INTEGER,
            recovery INTEGER
        )
    ''')

    # Create main ArtemistblV41dev table
    cursor.execute('''
        CREATE TABLE ArtemistblV41dev (
            activity_id TEXT PRIMARY KEY,
            timestamp TEXT,
            distance REAL,
            hrv INTEGER,
            fat INTEGER,
            total_fat INTEGER,  
            carbs INTEGER,
            total_carbs INTEGER,
            VO2maxSmooth INTEGER,
            VO2maxSession INTEGER,
            CardiacDrift INTEGER,    
            CooperTest INTEGER,
            steps INTEGER,     
            field110 TEXT,
            stress_hrpa INTEGER,
            HR_RS_Deviation_Index INTEGER,
            hrv_sdrr_f INTEGER,
            hrv_pnn50 INTEGER,                          
            hrv_pnn20 INTEGER,
            rmssd INTEGER,
            lnrmssd INTEGER,
            sdnn INTEGER,
            sdsd INTEGER,
            nn50 INTEGER,
            nn20 INTEGER,
            pnn20 INTEGER,
            Long INTEGER,
            Short INTEGER,
            Ectopic_S INTEGER,
            hrv_rmssd INTEGER,
            SD2 INTEGER,
            SD1 INTEGER,
            LF INTEGER,
            HF INTEGER,
            VLF INTEGER,
            pNN50 INTEGER, 
            LFnu INTEGER, 
            HFnu INTEGER,
            MeanHR INTEGER, 
            MeanRR INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info('PostgreSQL tables created successfully.')
    
    
    
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
                field110 = field_dict.get('field110')
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

                if steps is None:
                    steps = field_dict.get('steps')
                
                session_data.append({
                    'activity_id': activity_id,
                    'timestamp': timestamp, # '2021-09-01 12:00:00
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
                    'field110' : field110,
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

def insert_session_data_into_postgres(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    specific_fields = ['fat','Total Fat','Carbs','Total Carbs',
                    'VO2maxSmooth', 'VO2maxSession', 'CardiacDrift',
                    'CooperTest', 'Steps', 'field110', 'stress_hrpa',
                    'HR-RS_Deviation Index', 'hrv_sdrr_f', 'hrv_pnn50',
                    'hrv_pnn20', 'RMSSD', 'lnRMSSD', 'SDNN', 'SDSD',
                    'NN50', 'NN20', 'pnn20', 'Long', 'Short', 
                    'Ectopic_S', 'hrv_rmssd', 'SD2', 'SD1', 'LF',
                    'HF', 'VLF', 'pNN50', 'LFnu', 'HFnu', 
                    'MeanHR', 'MeanRR']

    for session in data:
        # Skip sessions with all specific fields as None
        if all(session[field] is None for field in specific_fields):
            continue

        # Insert or replace record
        cursor.execute('''
            INSERT INTO ArtemistblV41dev (
                activity_id, distance, hrv, fat, total_fat, carbs, total_carbs,  
                VO2maxSmooth, steps, field110, stress_hrpa, HR_RS_Deviation_Index,
                hrv_sdrr_f, hrv_pnn50, hrv_pnn20, rmssd, lnrmssd, sdnn, sdsd, 
                nn50, nn20, pnn20, Long, Short, Ectopic_S, hrv_rmssd, 
                VO2maxSession, CardiacDrift, CooperTest, SD2, SD1, HF, LF, VLF, 
                pNN50, LFnu, HFnu, MeanRR, MeanHR
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        ''', (
            session['activity_id'], session['distance'], session['hrv'], 
            session['fat'], session['Total Fat'], session['Carbs'], 
            session['Total Carbs'], session['VO2maxSmooth'], session['Steps'], 
            session['field110'], session['stress_hrpa'], 
            session['HR-RS_Deviation Index'], session['hrv_sdrr_f'], 
            session['hrv_pnn50'], session['hrv_pnn20'], session['RMSSD'], 
            session['lnRMSSD'], session['SDNN'], session['SDSD'], 
            session['NN50'], session['NN20'], session['pnn20'], 
            session['Long'], session['Short'], session['Ectopic_S'], 
            session['hrv_rmssd'], session['VO2maxSession'], 
            session['CardiacDrift'], session['CooperTest'], session['SD2'], 
            session['SD1'], session['HF'], session['LF'], session['VLF'], 
            session['pNN50'], session['LFnu'], session['HFnu'], 
            session['MeanRR'], session['MeanHR']
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Set up logging
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    logging.basicConfig(filename=f'postgres_import_{timestamp}.log', level=logging.INFO)

    try:
        # Create tables in PostgreSQL
        create_tables_in_postgres()

        # Parse and insert data
        all_session_data = parse_all_fit_files_in_folder('c:/users/stma/healthdata/fitfiles/activitiesTEST')
        insert_session_data_into_postgres(all_session_data)
        
        logging.info('All data inserted successfully.')
        print('All data inserted successfully (c)smacrico')
    except Exception as e:
        logging.error(f'Error processing data: {e}')
        print(f'Error processing data: {e}')