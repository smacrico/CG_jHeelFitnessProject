# this file is used to analyze myRun data from Garmin Forunner 245
""" stelios (c) steliosmacrico "jHeel (c)April 2025"""

######################################
"jHEEL data analysis"#################
######################################

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Συνδεθείτε στη βάση δεδομένων SQLite
#conn = sqlite3.connect(r'c:/users/jheel/jheelHealthData/DBs/garmin_activities.db')
#connect from EY latpop
conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_activities.db')

# Δημιουργήστε ένα cursor
cursor = conn.cursor()

# Example 1: Average Pace per Run

query_avg_pace = """
SELECT
    CAST(strftime('%Y-%m-%d', a.start_time) AS TEXT) AS run_date,
    AVG(1000.0 / avg_speed) / 60.0 AS avg_pace_min_km
FROM activities a
JOIN activity_records r ON a.activity_id = r.activity_id
WHERE a.sport = 'running' AND r.speed > 0
GROUP BY run_date
ORDER BY run_date;
"""

cursor.execute(query_avg_pace)
results = cursor.fetchall()
df_pace = pd.DataFrame(results, columns=['run_date', 'avg_pace_min_km'])
df_pace['run_date'] = pd.to_datetime(df_pace['run_date'])

if not df_pace.empty:
    plt.figure(figsize=(12, 6))
    plt.plot(df_pace['run_date'], df_pace['avg_pace_min_km'], marker='o', linestyle='-')
    plt.title('Average Running Pace Over Time')
    plt.xlabel('Date')
    plt.ylabel('Average Pace (min/km)')
    plt.grid(True)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
else:
    print('No running data found for pace analysis.')

# conn.close()


# Example 2: Heart Rate Zones

conn = sqlite3.connect(r'c:/smakryko/myHealthData/DBs/garmin_activities.db')

query_hr_records = """
SELECT
    CAST(strftime('%Y-%m-%d', a.start_time) AS TEXT) AS run_date,
    r.hr,
    a.activity_id
FROM activities a
JOIN activity_records r ON a.activity_id = r.activity_id
WHERE a.sport = 'running' AND r.hr > 0
ORDER BY a.start_time;
"""

cursor.execute(query_hr_records)
results = cursor.fetchall()
df_hr_records = pd.DataFrame(results, columns=['run_date', 'avg_hr', 'activity_id'])

def calculate_hr_zones(heart_rates, max_hr):
    zones = {'Zone 1': 0, 'Zone 2': 0, 'Zone 3': 0, 'Zone 4': 0, 'Zone 5': 0}
    total_time = len(heart_rates)
    if total_time > 0:
        for hr in heart_rates:
            if hr < 0.6 * max_hr:
                zones['Zone 1'] += 1
            elif hr < 0.7 * max_hr:
                zones['Zone 2'] += 1
            elif hr < 0.8 * max_hr:
                zones['Zone 3'] += 1
            elif hr < 0.9 * max_hr:
                zones['Zone 4'] += 1
            else:
                zones['Zone 5'] += 1
        return {zone: count / total_time for zone, count in zones.items()}
    else:
        return zones

MAX_HEART_RATE = 190  # Replace with your max heart rate

if not df_hr_records.empty:
    hr_zone_analysis = df_hr_records.groupby('run_date')['avg_hr'].apply(list).apply(lambda x: calculate_hr_zones(x, MAX_HEART_RATE)).apply(pd.Series)
    hr_zone_analysis.index = hr_zone_analysis.index.map(pd.to_datetime)
    hr_zone_analysis = hr_zone_analysis.sort_index()

    hr_zone_analysis.plot(kind='bar', stacked=True, figsize=(14, 7))
    plt.title('Heart Rate Zone Distribution per Run')
    plt.xlabel('Date')
    plt.ylabel('Percentage of Time')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Heart Rate Zone')
    plt.tight_layout()
    plt.show()
else:
    print('No heart rate data found for analysis.')

conn.close()