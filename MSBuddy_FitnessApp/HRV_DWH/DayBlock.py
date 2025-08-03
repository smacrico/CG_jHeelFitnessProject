import sqlite3
from datetime import datetime, time

DB_PATH = "c:/smakryko/myHealthData/DataBasesDev/Mercury_DWH-HRV.db"

def get_dayblock(dt):
    t = dt.time()
    if time(0,0,0) <= t <= time(7,0,0):
        return "sleep"
    elif time(7,0,1) <= t <= time(11,30,0):
        return "morning"
    elif time(11,30,1) <= t <= time(17,0,0):
        return "midday"
    else:
        return "night"

def add_column_if_missing(conn, column_name, column_type):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(hrv_sessions)")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE hrv_sessions ADD COLUMN {column_name} {column_type}")
        conn.commit()

def update_dayblock_and_date():
    with sqlite3.connect(DB_PATH) as conn:
        add_column_if_missing(conn, "DayBlock", "TEXT")
        add_column_if_missing(conn, "date", "TEXT")
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, timestamp FROM hrv_sessions")
        rows = cursor.fetchall()
        for rowid, ts in rows:
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            dayblock = get_dayblock(dt)
            date_only = dt.date().isoformat()
            cursor.execute(
                "UPDATE hrv_sessions SET DayBlock = ?, date = ? WHERE rowid = ?",
                (dayblock, date_only, rowid)
            )
        conn.commit()
        print("DayBlock and date columns updated for all records.")

if __name__ == "__main__":
    update_dayblock_and_date()
