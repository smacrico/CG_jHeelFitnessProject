 # this file is used to analyze basic data from Garmin Forunner 245
""" stelios (c) steliosmacrico "jHeel 2025 creating plugin"""

######################################
"jHEEL data analysis"#################
######################################

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Συνδεθείτε στη βάση δεδομένων SQLite
##### conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin_activities.db')


#connect from EY latpop
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_activities.db')



# db_path = 'path/to/your/garmin_data.db'  # Αντικαταστήστε με την πραγματική διαδρομή


# db_path = 'path/to/your/garmin_data.db'  # Αντικαταστήστε με την πραγματική διαδρομή
# conn = sqlite3.connect(db_path)

# Δημιουργήστε ένα cursor
cursor = conn.cursor()

# --- Παράδειγμα 1: Μέσοι καρδιακοί παλμοί ανά τύπο δραστηριότητας ---
query_avg_hr = """
SELECT a.sport, AVG(r.hr) AS avg_heart_rate
FROM activities a
JOIN activity_records r ON a.activity_id = r.activity_id
GROUP BY a.sport;
"""
df_avg_hr = pd.read_sql_query(query_avg_hr, conn)
print("\nΜέσοι Καρδιακοί Παλμοί ανά Τύπο Δραστηριότητας:")
print(df_avg_hr)

# Οπτικοποίηση
plt.figure(figsize=(10, 6))
sns.barplot(x='sport', y='avg_heart_rate', data=df_avg_hr)
plt.title('Μέσοι Καρδιακοί Παλμοί ανά Τύπο Δραστηριότητας')
plt.xlabel('Τύπος Δραστηριότητας')
plt.ylabel('Μέσοι Καρδιακοί Παλμοί')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# --- Παράδειγμα 2: Μέση διάρκεια ύπνου ανά ημέρα ---

#### conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin.db')
#connect from EY latpop
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin.db')


query_avg_sleep = """
SELECT DATE(day) AS sleep_date, AVG(total_sleep / 3600.0) AS avg_sleep_hours
FROM sleep
GROUP BY sleep_date;
"""
df_avg_sleep = pd.read_sql_query(query_avg_sleep, conn)
print("\nΜέση Διάρκεια Ύπνου ανά Ημέρα:")
print(df_avg_sleep.head())

# Οπτικοποίηση
plt.figure(figsize=(12, 6))
plt.plot(df_avg_sleep['sleep_date'], df_avg_sleep['avg_sleep_hours'], marker='o')
plt.title('Μέση Διάρκεια Ύπνου ανά Ημέρα')
plt.xlabel('Ημερομηνία')
plt.ylabel('Μέση Διάρκεια Ύπνου (ώρες)')
plt.grid(True)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# --- Παράδειγμα 3: Ημερήσια βήματα ---
### conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin_summary.db')

#connect from EY latpop
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_summary.db')

query_daily_steps = """
SELECT day, steps
FROM days_summary;
"""
df_daily_steps = pd.read_sql_query(query_daily_steps, conn)
df_daily_steps['date'] = pd.to_datetime(df_daily_steps['day'])
print("\nΗμερήσια Βήματα:")
print(df_daily_steps.head())

# Οπτικοποίηση
plt.figure(figsize=(12, 6))
plt.plot(df_daily_steps['day'], df_daily_steps['steps'], marker='.')
plt.title('Ημερήσια Βήματα')
plt.xlabel('Ημερομηνία')
plt.ylabel('Βήματα')
plt.grid(True)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Κλείστε τη σύνδεση με τη βάση δεδομένων
conn.close()