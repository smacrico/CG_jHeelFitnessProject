import sqlite3
import pandas as pd

DB_PATH = "c:/smakryko/myHealthData/DataBasesDev/Mercury_DWH-HRV.db"

def main():
    # Load only the relevant records
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM hrv_sessions WHERE name IN ('HRV', 'Fb3 Monoitor+HRV', 'Meditation')",
            conn
        )

    # Identify columns
    columns = df.columns.tolist()
    exclude_cols = {'date', 'DayBlock'}
    numeric_cols = df.select_dtypes(include='number').columns.difference(exclude_cols).tolist()

    # Prepare aggregation dictionary
    agg_dict = {col: 'mean' for col in numeric_cols}
    for col in columns:
        if col not in numeric_cols and col not in ['date', 'DayBlock']:
            agg_dict[col] = 'first'

    # Group and aggregate
    grouped = df.groupby(['date', 'DayBlock'], as_index=False).agg(agg_dict)
    grouped['session_count'] = df.groupby(['date', 'DayBlock']).size().values

    # Write to new table
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS hrv_session_block")
        # Build CREATE TABLE statement dynamically
        create_cols = ", ".join([
            f"{col} REAL" if col in numeric_cols or col == 'session_count' else f"{col} TEXT"
            for col in grouped.columns if col not in ['date', 'DayBlock']
        ])
        create_stmt = f"""
            CREATE TABLE hrv_session_block (
                date TEXT,
                DayBlock TEXT,
                {create_cols}
            )
        """
        conn.execute(create_stmt)
        grouped.to_sql('hrv_session_block', conn, if_exists='append', index=False)

    print("Filtered and aggregated HRV data has been written to 'hrv_session_block'.")

if __name__ == "__main__":
    main()
