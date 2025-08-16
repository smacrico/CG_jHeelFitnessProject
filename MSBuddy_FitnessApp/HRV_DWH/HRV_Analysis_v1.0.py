import sqlite3
import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
DB_PATH = "c:/smakrykoDBs/Mercury_DWH_HRV.db"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HRVAnalytics:
    """Enhanced HRV Analytics and Recovery Score System"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._validate_database()

    def _validate_database(self):
        """Validate database connection and tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='hrv_sessions'"
                )
                if not cursor.fetchone():
                    logger.warning("hrv_sessions table not found. Creating tables...")
                    self._create_tables_if_missing()
        except sqlite3.Error as e:
            logger.error(f"Database validation failed: {e}")
            raise

    def _create_tables_if_missing(self):
        """Create tables if they don't exist (placeholder)"""
        pass

    # ================= TREND ANALYSIS ===================

    def analyze_hrv_trends(self, days: int = 30, include_stats: bool = True) -> Dict:
        """Enhanced HRV trend analysis with statistical significance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT
                    date(timestamp) AS date,
                    AVG(armssd) AS avg_rmssd,
                    AVG(asdnn) AS avg_sdnn,
                    AVG(nn50) AS avg_pnn50,
                    AVG(mean_hr) AS avg_hr,
                    AVG(recovery) AS avg_recovery,
                    COUNT(*) AS session_count,
                    MIN(armssd) AS min_rmssd,
                    MAX(armssd) AS max_rmssd
                FROM hrv_sessions
                WHERE timestamp >= date('now', ?) 
                AND name = 'F3b Monitor+HRV'
                GROUP BY date(timestamp)
                ORDER BY date(timestamp) ASC
                """
                df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
                df['std_rmssd'] = df['avg_rmssd'].rolling(window=7).std()
        except sqlite3.Error as e:
            logger.error(f"Database error in analyze_hrv_trends: {e}")
            return self._generate_sample_trend_data(days)

        if df.empty:
            return {"status": "no_data", "message": "No HRV data found for analysis"}

        df['date'] = pd.to_datetime(df['date'])

        results = {
            "status": "success",
            "data_points": len(df),
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d'),
                "end": df['date'].max().strftime('%Y-%m-%d')
            },
            "dataframe": df
        }

        if len(df) > 1:
            x = np.arange(len(df))
            rmssd_trend = np.polyfit(x, df['avg_rmssd'].fillna(0), 1)
            sdnn_trend = np.polyfit(x, df['avg_sdnn'].fillna(0), 1)
            rmssd_r_value = np.corrcoef(x, df['avg_rmssd'].fillna(0))[0, 1]
            sdnn_r_value = np.corrcoef(x, df['avg_sdnn'].fillna(0))[0, 1]

            results["trends"] = {
                "rmssd": {
                    "slope": rmssd_trend[0],
                    "intercept": rmssd_trend[1],
                    "correlation": rmssd_r_value,
                    "trend_strength": self._interpret_trend_strength(abs(rmssd_r_value)),
                    "direction": "improving" if rmssd_trend[0] > 0 else "declining" if rmssd_trend[0] < 0 else "stable"
                },
                "sdnn": {
                    "slope": sdnn_trend[0],
                    "intercept": sdnn_trend[1],
                    "correlation": sdnn_r_value,
                    "trend_strength": self._interpret_trend_strength(abs(sdnn_r_value)),
                    "direction": "improving" if sdnn_trend[0] > 0 else "declining" if sdnn_trend[0] < 0 else "stable"
                }
            }

        if include_stats:
            results["statistics"] = self._calculate_trend_statistics(df)

        self._print_trend_summary(results)
        return results

    def _interpret_trend_strength(self, correlation: float) -> str:
        if correlation >= 0.7:
            return "strong"
        elif correlation >= 0.4:
            return "moderate"
        elif correlation >= 0.2:
            return "weak"
        return "negligible"

    def _calculate_trend_statistics(self, df: pd.DataFrame) -> Dict:
        return {
            "rmssd": {
                "mean": df['avg_rmssd'].mean(),
                "std": df['avg_rmssd'].std(),
                "min": df['avg_rmssd'].min(),
                "max": df['avg_rmssd'].max(),
                "cv": (df['avg_rmssd'].std() / df['avg_rmssd'].mean()) * 100,
                "recent_7day_avg": df['avg_rmssd'].tail(7).mean(),
                "recent_vs_overall": ((df['avg_rmssd'].tail(7).mean() / df['avg_rmssd'].mean()) - 1) * 100
            },
            "sdnn": {
                "mean": df['avg_sdnn'].mean(),
                "std": df['avg_sdnn'].std(),
                "min": df['avg_sdnn'].min(),
                "max": df['avg_sdnn'].max(),
                "cv": (df['avg_sdnn'].std() / df['avg_sdnn'].mean()) * 100,
                "recent_7day_avg": df['avg_sdnn'].tail(7).mean(),
                "recent_vs_overall": ((df['avg_sdnn'].tail(7).mean() / df['avg_sdnn'].mean()) - 1) * 100
            }
        }

    def _print_trend_summary(self, results: Dict):
        if results["status"] != "success":
            logger.warning(results.get('message', 'Unknown error'))
            return
        print("\n=== HRV TREND ANALYSIS REPORT ===")
        print(f"Period: {results['date_range']['start']} to {results['date_range']['end']} ({results['data_points']} days)")
        if "trends" in results:
            for metric, trend in results["trends"].items():
                print(f"{metric.upper()}: {trend['direction']} ({trend['trend_strength']}), slope={trend['slope']:.3f}, correlation={trend['correlation']:.3f}")
        if "statistics" in results:
            for metric, stats in results["statistics"].items():
                print(f"{metric.upper()} recent change: {stats['recent_vs_overall']:+.1f}%")

    # ================= RECOVERY SCORES ===================

    def calculate_recovery_score(self, activity_id: str, method: str = "comprehensive") -> Optional[Dict]:
        """Calculate HRV recovery score using chosen method"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT armssd, asdnn, nn50, mean_hr, recovery,
                           lf, hf, vlf, stress_hrpa, name, source
                    FROM hrv_sessions
                    WHERE activity_id = ?
                """, (activity_id,))
                result = cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Database error in calculate_recovery_score: {e}")
            return None

        if not result:
            logger.warning(f"No session data for activity_id: {activity_id}")
            return None

        rmssd, sdnn, pnn50, mean_hr, existing_recovery, lf, hf, vlf, stress, name, source = result
        rmssd = rmssd or 0
        sdnn = sdnn or 0
        pnn50 = pnn50 or 0
        mean_hr = mean_hr or 65
        lf = lf or 0
        hf = hf or 0
        stress = stress or 50

        if method == "simple":
            return self._calculate_simple_recovery_score(rmssd, sdnn, pnn50, activity_id, name)
        elif method == "comprehensive":
            return self._calculate_comprehensive_recovery_score(rmssd, sdnn, pnn50, mean_hr, lf, hf, stress, activity_id, name)
        elif method == "personalized":
            return self._calculate_personalized_recovery_score(rmssd, sdnn, pnn50, mean_hr, lf, hf, stress, activity_id, name, source)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _calculate_simple_recovery_score(self, rmssd: float, sdnn: float, pnn50: float, activity_id: str, name: str) -> Dict:
        rmssd_score = min(100, max(0, rmssd / 0.8))
        sdnn_score = min(100, max(0, sdnn / 1.0))
        pnn50_score = min(100, max(0, pnn50 * 2))
        recovery_score = (rmssd_score + sdnn_score + pnn50_score) / 3
        return {"activity_id": activity_id, "name": name, "method": "simple", "recovery_score": recovery_score}

    def _calculate_comprehensive_recovery_score(self, rmssd: float, sdnn: float, pnn50: float, mean_hr: float, lf: float, hf: float, stress: float, activity_id: str, name: str) -> Dict:
        time_domain_score = min(100, max(0, rmssd / 0.8)) * 0.6 + min(100, max(0, sdnn / 1.0)) * 0.4
        if hf > 0:
            lf_hf_ratio = lf / hf
            freq_domain_score = min(100, max(0, np.log10(max(1, hf)) * 25)) * 0.7 + min(100, max(0, 100 - lf_hf_ratio * 20)) * 0.3
        else:
            freq_domain_score = 50
        hr_score = min(100, max(0, 100 - abs(mean_hr - 60) * 2))
        stress_score = min(100, max(0, 100 - stress))
        recovery_score = time_domain_score * 0.4 + freq_domain_score * 0.3 + hr_score * 0.2 + stress_score * 0.1
        return {"activity_id": activity_id, "name": name, "method": "comprehensive", "recovery_score": recovery_score}

    def _calculate_personalized_recovery_score(self, rmssd: float, sdnn: float, pnn50: float, mean_hr: float, lf: float, hf: float, stress: float, activity_id: str, name: str, source: str) -> Dict:
        baselines = self._get_personal_baselines(source)
        rmssd_relative = (rmssd / baselines['rmssd']) * 100 if baselines['rmssd'] > 0 else 50
        sdnn_relative = (sdnn / baselines['sdnn']) * 100 if baselines['sdnn'] > 0 else 50
        recovery_score = min(100, max(0, (rmssd_relative + sdnn_relative) / 2))
        return {"activity_id": activity_id, "name": name, "method": "personalized", "recovery_score": recovery_score, "baselines_used": baselines}

    def _get_personal_baselines(self, source: str) -> Dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG(armssd), AVG(asdnn)
                    FROM hrv_sessions
                    WHERE source = ? AND armssd IS NOT NULL AND asdnn IS NOT NULL
                    AND timestamp >= date('now', '-90 days')
                """, (source,))
                result = cursor.fetchone()
                if result and result[0] and result[1]:
                    return {"rmssd": result[0], "sdnn": result[1]}
        except sqlite3.Error as e:
            logger.error(f"Error getting personal baselines: {e}")
        return {"rmssd": 45.0, "sdnn": 50.0}

    # ================= VISUALIZATION ===================
    def _generate_sample_trend_data(self, days: int) -> Dict:
        dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
        np.random.seed(42)
        df = pd.DataFrame({
            'date': dates,
            'avg_rmssd': np.random.normal(50, 8, days),
            'avg_sdnn': np.random.normal(60, 10, days),
            'avg_pnn50': np.random.normal(25, 5, days),
            'avg_hr': np.random.normal(65, 5, days),
            'avg_recovery': np.random.normal(75, 10, days),
            'session_count': np.random.randint(1, 4, days)
        })
        return {"status": "sample_data", "dataframe": df, "data_points": len(df)}

# Simple plotting functions
def plot_hrv_trend(df, rmssd_col='daily_rmssd'):
    if rmssd_col not in df.columns:
        logger.error(f"Column {rmssd_col} missing in DataFrame")
        return
    plt.figure()
    plt.plot(df['date'], df[rmssd_col])
    plt.title('HRV Trend')
    plt.show()

def plot_hrv_histogram(df, column='daily_rmssd'):
    if column not in df.columns:
        logger.error(f"Column {column} missing in DataFrame")
        return
    plt.figure()
    plt.hist(df[column])
    plt.title('HRV Histogram')
    plt.show()

def get_daily_hrv_dataframe(days=30):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            query = """
            SELECT date(timestamp) as date, AVG(armssd) as daily_rmssd
            FROM hrv_sessions
            WHERE timestamp >= date('now', ?) AND name = 'F3b Monitor+HRV'
            GROUP BY date(timestamp)
            ORDER BY date(timestamp) ASC
            """
            return pd.read_sql_query(query, conn, params=(f'-{days} days',))
    except sqlite3.Error as e:
        logger.error(f"Database error in get_daily_hrv_dataframe: {e}")
        return pd.DataFrame()

# Example usage
def main():
    hrv_analytics = HRVAnalytics()
    trend_results = hrv_analytics.analyze_hrv_trends(days=30, include_stats=True)
    df_plot = get_daily_hrv_dataframe()
    plot_hrv_trend(df_plot)
    plot_hrv_histogram(df_plot)
    simple_score = hrv_analytics.calculate_recovery_score("17080654324", "simple")
    comp_score = hrv_analytics.calculate_recovery_score("example_session_001", "comprehensive")
    pers_score = hrv_analytics.calculate_recovery_score("example_session_001", "personalized")
    print(simple_score, comp_score, pers_score)

if __name__ == "__main__":
    main()
