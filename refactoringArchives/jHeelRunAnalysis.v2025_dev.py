import sqlite3
from fitparse import FitFile

def create_database():
    """Create the Runanalysis SQLite database and tables."""
    connection = sqlite3.connect('e:/jheel_dev/DataBasesDev/RunAnalysis_v2025.db')
    cursor = connection.cursor()

    # Create run_session table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS run_session (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            total_duration REAL,
            total_distance REAL,
            total_calories INTEGER
        )
    ''')

    # Create run_records table
    cursor.execute('''
       CREATE TABLE IF NOT EXISTS run_recordsDEV (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        timestamp INTEGER,
        distance FLOAT,
        speed FLOAT,
        heart_rate INTEGER,
        cadence INTEGER,
        altitude FLOAT,
        temperature FLOAT,
        running_economy FLOAT,
        FOREIGN KEY (session_id) REFERENCES run_sessions(id)
        )
    ''')

    connection.commit()
    connection.close()

def parse_fit_file(file_path):
    """Parse the FIT file and extract session and record data."""
    fitfile = FitFile(file_path)

    session_data = None
    record_data = []

    # Extract session data
    for record in fitfile.get_messages('session'):
        fields = {field.name: field.value for field in record}
        session_data = {
            "start_time": fields.get("start_time"),
            "total_duration": fields.get("total_elapsed_time"),
            "total_distance": fields.get("total_distance"),
            "total_calories": fields.get("total_calories")
        }

    # Extract record data
    for record in fitfile.get_messages('record'):
        fields = {field.name: field.value for field in record}
        record_data.append({
            "timestamp": fields.get("timestamp"),
            "distance": fields.get("distance"),
            "speed": fields.get("speed"),
            "heart_rate": fields.get("heart_rate"),
            "cadence": fields.get("cadence"),
            "altitude": fields.get("altitude"),
            "temperature": fields.get("temperature"),
            "running_economy": fields.get("Running Economy")
        })

    return session_data, record_data

def insert_data(session_data, record_data):
    """Insert session and record data into the SQLite database."""
    connection = sqlite3.connect('e:/jheel_dev/DataBasesDev/RunAnalysis_v2025.db')
    cursor = connection.cursor()

    # Insert session data
    cursor.execute('''
        INSERT INTO run_session (start_time, total_duration, total_distance, total_calories)
        VALUES (?, ?, ?, ?)
    ''', (session_data["start_time"], session_data["total_duration"], session_data["total_distance"], session_data["total_calories"]))

    session_id = cursor.lastrowid

    # Insert record data
    for record in record_data:
        cursor.execute('''
            INSERT INTO run_recordsDev (session_id, timestamp, distance, speed, heart_rate, cadence, altitude, temperature, running_economy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, record["timestamp"], record["distance"], record["speed"], record["heart_rate"], record["cadence"], record["altitude"], record["temperature"], record["running_economy"]))

    connection.commit()
    connection.close()

if __name__ == "__main__":
    file_path = ('c:/users/stma/healthdata/fitfiles/activitiesTEST_Run/128408-118657300.fit')

    # Create database and tables
    create_database()

    # Parse the FIT file
    session_data, record_data = parse_fit_file(file_path)

    # Insert data into the database
    insert_data(session_data, record_data)

    print("Data successfully stored in Runanalysis.db.")
