############### create RunningAnalysis database in Production environment
# dev 4.0 - fixed statments for training score and training log
# 
# 
# 
import sqlite3
import sys


def create_table_if_not_exists():
    conn = sqlite3.connect(r'g:/My Drive/Genesis_dev/DataBasesDev/Apex.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS running_sessions (
            running_economy INT, 
            date TXT, 
            distance INT, 
            sport TXT, 
            vo2max INT,  
            cardiacdrift INT,
            heart_rate INT,
            time INT 
        )
    ''')
    
    conn.commit()
    conn.close()
    
create_table_if_not_exists()
    
try:
    # Establish connections to both databases
    conn_artemis = sqlite3.connect('g:/My Drive/Genesis_dev/DataBasesDev/artemis.db')
    conn_running_analysis = sqlite3.connect('g:/My Drive/Genesis_dev/DataBasesDev/Apex.db')

    # Create cursors
    cursor_artemis = conn_artemis.cursor()
    cursor_running_analysis = conn_running_analysis.cursor()
    
    
    

    # Select the specific columns from Artemis database
    # FROM Artemistbl_Prod prod
    # FROM Artemistbl_mariner
    cursor_artemis.execute('''
        SELECT running_economy, timestamp, distance, sport, vo2maxsession,  cardiacdrift, avg_heart_rate, total_elapsed_time
        FROM Artemistbl_fields

        WHERE sport like 'running'
    ''')

    # Fetch all the rows
    rows = cursor_artemis.fetchall()

    # Insert the data into running_session table in RunningAnalysis database
    cursor_running_analysis.executemany('''
        INSERT INTO running_sessions (running_economy, date, distance, sport, vo2max,  cardiacdrift, heart_rate, time)
        VALUES (?, ?,?,?,?,?,?,?)
    ''', rows)

    # Commit the changes
    conn_running_analysis.commit()

except sqlite3.Error as e:
    print(f"An error occurred: {e}")
    # Rollback any changes if an error occurs
    conn_running_analysis.rollback()

finally:
    # Always close the connections
    if conn_artemis:
        conn_artemis.close()
    if conn_running_analysis:
        conn_running_analysis.close()

print("Data transfer completed successfully!")