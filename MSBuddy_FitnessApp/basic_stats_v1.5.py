# this file is used to analyze basic data from Garmin Forunner 245
""" stelios (c) steliosmacrico "jHeel 2025 creating plugin"""

######################################
"jHEEL data analysis"#################
######################################

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta


# Καθορίστε την περίοδο των τελευταίων 45 ημερών
end_date = datetime.now()
start_date = end_date - timedelta(days=90)
start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S') # Ή '%Y-%m-%d' ανάλογα με τη στήλη



# Συνδεθείτε στη βάση δεδομένων SQLite
# conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin_activities.db')


#connect from EY latpop
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_activities.db')



# db_path = 'path/to/your/garmin_data.db'  # Αντικαταστήστε με την πραγματική διαδρομή


# db_path = 'path/to/your/garmin_data.db'  # Αντικαταστήστε με την πραγματική διαδρομή
# conn = sqlite3.connect(db_path)

# Δημιουργήστε ένα cursor
cursor = conn.cursor()

# --- Παράδειγμα 1: Μέσοι καρδιακοί παλμοί ανά τύπο δραστηριότητας (τελευταίες 45 ημέρες) ---


query_avg_hr_last_45 = f"""
SELECT a.sport, AVG(r.hr) AS avg_heart_rate
FROM activities a
JOIN activity_records r ON a.activity_id = r.activity_id
WHERE a.start_time >= '{start_date_str}'
GROUP BY a.sport;
"""
df_avg_hr_last_45 = pd.read_sql_query(query_avg_hr_last_45, conn)
print("\nΜέσοι Καρδιακοί Παλμοί ανά Τύπο Δραστηριότητας (τελευταίες 45 ημέρες):")
print(df_avg_hr_last_45)

# Οπτικοποίηση
plt.figure(figsize=(10, 6))
sns.barplot(x='sport', y='avg_heart_rate', data=df_avg_hr_last_45)
plt.title('Μέσοι Καρδιακοί Παλμοί ανά Τύπο Δραστηριότητας (τελευταίες 45 ημέρες)')
plt.xlabel('Τύπος Δραστηριότητας')
plt.ylabel('Μέσοι Καρδιακοί Παλμοί')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# --- Παράδειγμα 2: Μέση διάρκεια ύπνου ανά ημέρα (τελευταίες 45 ημέρες) ---

#### conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin.db')
#connect from EY latpop
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin.db')

query_avg_sleep_last_45 = f"""
SELECT DATE(day) AS sleep_date, AVG(total_sleep / 3600.0) AS avg_sleep_hours
FROM sleep
WHERE start >= '{start_date_str}'
GROUP BY sleep_date;
"""
df_avg_sleep_last_45 = pd.read_sql_query(query_avg_sleep_last_45, conn)
print("\nΜέση Διάρκεια Ύπνου ανά Ημέρα (τελευταίες 45 ημέρες):")
print(df_avg_sleep_last_45.head())

# Οπτικοποίηση
plt.figure(figsize=(12, 6))
plt.plot(df_avg_sleep_last_45['sleep_date'], df_avg_sleep_last_45['avg_sleep_hours'], marker='o')
plt.title('Μέση Διάρκεια Ύπνου ανά Ημέρα (τελευταίες 45 ημέρες)')
plt.xlabel('Ημερομηνία')
plt.ylabel('Μέση Διάρκεια Ύπνου (ώρες)')
plt.grid(True)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# --- Παράδειγμα 3: Ημερήσια βήματα (τελευταίες 45 ημέρες) ---


### conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin_summary.db')

#connect from EY latpop
# conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_summary.db')
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_summary.db')



query_daily_steps_last_45 = f"""
SELECT day, steps
FROM days_summary
WHERE day >= DATE('{start_date.strftime('%Y-%m-%d')}')
"""
df_daily_steps_last_45 = pd.read_sql_query(query_daily_steps_last_45, conn)
df_daily_steps_last_45['date'] = pd.to_datetime(df_daily_steps_last_45['day'])
print("\nΗμερήσια Βήματα (τελευταίες 45 ημέρες):")
print(df_daily_steps_last_45.head())

# Οπτικοποίηση
plt.figure(figsize=(12, 6))
plt.plot(df_daily_steps_last_45['day'], df_daily_steps_last_45['steps'], marker='.')
plt.title('Ημερήσια Βήματα (τελευταίες 45 ημέρες)')
plt.xlabel('Ημερομηνία')
plt.ylabel('Βήματα')
plt.grid(True)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()


# Κλείστε τη σύνδεση με τη βάση δεδομένων
conn.close()