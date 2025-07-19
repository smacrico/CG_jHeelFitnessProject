"""
Comprehensive HRV Analysis & Visualization System
Integrates HRV calculation, trend analysis, and interactive visualizations
Designed for health monitoring and MS management
"""

import sqlite3
import os
import logging
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import welch
from scipy.interpolate import interp1d
import scipy.integrate
from fitparse import FitFile

# Optional for interactive plots
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Plotly not available. Interactive plots will be disabled.")

# Configuration
DB_PATH = "hrv_comprehensive.db"
LOG_DIR = "logs"
SAMPLE_DATA_DIR = "sample_fit_files"

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
logging.basicConfig(
    filename=f'{LOG_DIR}/hrv_comprehensive_{timestamp}.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('HRV_Comprehensive')

# Set visualization style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class HRVComprehensiveSystem:
    """Complete HRV analysis and visualization system"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize comprehensive database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sessions table with all HRV metrics
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hrv_sessions (
                activity_id TEXT PRIMARY KEY,
                source TEXT,
                timestamp DATETIME,
                sport TEXT,
                duration_seconds INTEGER,
                
                -- Time Domain Metrics
                hrv_rmssd REAL,
                hrv_sdnn REAL,
                hrv_pnn50 REAL,
                hrv_nn50 INTEGER,
                mean_hr REAL,
                min_hr INTEGER,
                max_hr INTEGER,
                mean_ibi REAL,
                
                -- Frequency Domain Metrics
                vlf_power REAL,
                lf_power REAL,
                hf_power REAL,
                total_power REAL,
                lf_hf_ratio REAL,
                lf_nu REAL,
                hf_nu REAL,
                
                -- Calculated Scores
                hrv_score REAL,
                recovery_score REAL,
                stress_score REAL,
                
                -- Additional Metrics
                artifacts_filtered INTEGER,
                data_quality_score REAL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Records table for beat-by-beat data
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hrv_records (
                activity_id TEXT,
                record_number INTEGER,
                timestamp DATETIME,
                ibi_ms REAL,
                hr_bpm REAL,
                rr_interval REAL,
                valid_beat BOOLEAN DEFAULT 1,
                PRIMARY KEY (activity_id, record_number),
                FOREIGN KEY (activity_id) REFERENCES hrv_sessions(activity_id)
            )''')
            
            # Analysis results table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hrv_analysis_results (
                analysis_id TEXT PRIMARY KEY,
                activity_id TEXT,
                analysis_type TEXT,
                analysis_date DATETIME,
                parameters TEXT,
                results TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (activity_id) REFERENCES hrv_sessions(activity_id)
            )''')
            
            logger.info("Database schema initialized")

    # === HRV CALCULATION FUNCTIONS ===
    
    def calculate_ibi(self, timestamps_ms):
        """Calculate inter-beat intervals from timestamps"""
        return np.diff(timestamps_ms)

    def filter_ibi_artifacts(self, ibi, lower_threshold=300, upper_threshold=2000, method='statistical'):
        """Enhanced artifact filtering with multiple methods"""
        if method == 'range':
            valid_mask = (ibi >= lower_threshold) & (ibi <= upper_threshold)
        elif method == 'statistical':
            q1, q3 = np.percentile(ibi, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            valid_mask = (ibi >= max(lower_bound, lower_threshold)) & (ibi <= min(upper_bound, upper_threshold))
        
        return ibi[valid_mask], valid_mask

    def calculate_time_domain_hrv(self, ibi):
        """Calculate comprehensive time-domain HRV metrics"""
        if len(ibi) < 2:
            return {
                "hrv_rmssd": np.nan, "hrv_sdnn": np.nan, "hrv_pnn50": np.nan,
                "hrv_nn50": np.nan, "mean_ibi": np.nan, "min_hr": np.nan,
                "max_hr": np.nan, "mean_hr": np.nan
            }
        
        diff_ibi = np.diff(ibi)
        
        # Convert IBI to HR
        hr_values = 60000 / ibi  # Convert ms to BPM
        
        metrics = {
            "hrv_rmssd": np.sqrt(np.mean(diff_ibi**2)),
            "hrv_sdnn": np.std(ibi, ddof=1),
            "hrv_nn50": np.sum(np.abs(diff_ibi) > 50),
            "hrv_pnn50": (np.sum(np.abs(diff_ibi) > 50) / len(diff_ibi)) * 100 if len(diff_ibi) > 0 else np.nan,
            "mean_ibi": np.mean(ibi),
            "min_hr": np.min(hr_values),
            "max_hr": np.max(hr_values),
            "mean_hr": np.mean(hr_values)
        }
        
        return metrics

    def interpolate_ibi_for_frequency_analysis(self, ibi, target_fs=4.0):
        """Interpolate IBI data for frequency analysis"""
        if len(ibi) < 4:
            return None, None
        
        cumulative_time = np.cumsum(np.concatenate([[0], ibi])) / 1000.0
        
        f_interpolate = interp1d(cumulative_time[1:], ibi, kind='cubic', 
                               bounds_error=False, fill_value='extrapolate')
        
        total_duration = cumulative_time[-1]
        time_vector = np.arange(0, total_duration, 1.0/target_fs)
        
        if len(time_vector) > 0 and time_vector[-1] > cumulative_time[-1]:
            time_vector = time_vector[:-1]
        
        interpolated_ibi = f_interpolate(time_vector)
        return interpolated_ibi, time_vector

    def calculate_frequency_domain_hrv(self, ibi, target_fs=4.0):
        """Calculate comprehensive frequency-domain HRV metrics"""
        if len(ibi) < 10:
            return {
                "vlf_power": np.nan, "lf_power": np.nan, "hf_power": np.nan,
                "total_power": np.nan, "lf_hf_ratio": np.nan, "lf_nu": np.nan, "hf_nu": np.nan
            }
        
        interpolated_ibi, time_vector = self.interpolate_ibi_for_frequency_analysis(ibi, target_fs)
        
        if interpolated_ibi is None or len(interpolated_ibi) < 64:
            return {
                "vlf_power": np.nan, "lf_power": np.nan, "hf_power": np.nan,
                "total_power": np.nan, "lf_hf_ratio": np.nan, "lf_nu": np.nan, "hf_nu": np.nan
            }
        
        interpolated_ibi = interpolated_ibi - np.mean(interpolated_ibi)
        
        nperseg = min(256, len(interpolated_ibi) // 4)
        frequencies, psd = welch(interpolated_ibi, fs=target_fs, nperseg=nperseg, 
                               noverlap=nperseg//2, window='hann')
        
        vlf_band = (frequencies >= 0.0033) & (frequencies < 0.04)
        lf_band = (frequencies >= 0.04) & (frequencies < 0.15)
        hf_band = (frequencies >= 0.15) & (frequencies <= 0.4)
        
        vlf_power = scipy.integrate.trapezoid(psd[vlf_band], frequencies[vlf_band]) if np.any(vlf_band) else 0
        lf_power = scipy.integrate.trapezoid(psd[lf_band], frequencies[lf_band]) if np.any(lf_band) else 0
        hf_power = scipy.integrate.trapezoid(psd[hf_band], frequencies[hf_band]) if np.any(hf_band) else 0
        
        total_power = vlf_power + lf_power + hf_power
        
        lf_nu = (lf_power / (lf_power + hf_power)) * 100 if (lf_power + hf_power) > 0 else np.nan
        hf_nu = (hf_power / (lf_power + hf_power)) * 100 if (lf_power + hf_power) > 0 else np.nan
        lf_hf_ratio = lf_power / hf_power if hf_power > 0 else np.nan
        
        return {
            "vlf_power": vlf_power, "lf_power": lf_power, "hf_power": hf_power,
            "total_power": total_power, "lf_hf_ratio": lf_hf_ratio,
            "lf_nu": lf_nu, "hf_nu": hf_nu
        }

    def calculate_comprehensive_scores(self, time_metrics, freq_metrics, baseline_rmssd=45, baseline_sdnn=50):
        """Calculate comprehensive HRV scores"""
        if not time_metrics or not freq_metrics:
            return {"hrv_score": np.nan, "recovery_score": np.nan, "stress_score": np.nan}
        
        # HRV Score
        hrv_score = 0
        total_weight = 0
        weights = {'rmssd': 0.35, 'sdnn': 0.25, 'hf': 0.20, 'lf_hf_ratio': 0.20}
        
        rmssd = time_metrics.get("hrv_rmssd", np.nan)
        if not np.isnan(rmssd):
            rmssd_score = min(100, max(0, (rmssd / baseline_rmssd) * 100))
            hrv_score += rmssd_score * weights['rmssd']
            total_weight += weights['rmssd']
        
        sdnn = time_metrics.get("hrv_sdnn", np.nan)
        if not np.isnan(sdnn):
            sdnn_score = min(100, max(0, (sdnn / baseline_sdnn) * 100))
            hrv_score += sdnn_score * weights['sdnn']
            total_weight += weights['sdnn']
        
        hf = freq_metrics.get("hf_power", np.nan)
        if not np.isnan(hf) and hf > 0:
            hf_score = min(100, max(0, np.log10(hf) * 20))
            hrv_score += hf_score * weights['hf']
            total_weight += weights['hf']
        
        lf_hf = freq_metrics.get("lf_hf_ratio", np.nan)
        if not np.isnan(lf_hf):
            lf_hf_score = max(0, min(100, 100 - (lf_hf * 25)))
            hrv_score += lf_hf_score * weights['lf_hf_ratio']
            total_weight += weights['lf_hf_ratio']
        
        final_hrv_score = hrv_score / total_weight if total_weight > 0 else np.nan
        
        # Recovery Score (simplified)
        recovery_score = final_hrv_score * 0.8 if not np.isnan(final_hrv_score) else np.nan
        
        # Stress Score (inverse of recovery)
        stress_score = 100 - recovery_score if not np.isnan(recovery_score) else np.nan
        
        return {
            "hrv_score": final_hrv_score,
            "recovery_score": recovery_score,
            "stress_score": stress_score
        }

    # === DATA INGESTION FUNCTIONS ===
    
    def analyze_ibi_data(self, ibi_data, activity_id, source="MANUAL"):
        """Complete analysis of IBI data"""
        # Filter artifacts
        ibi_filtered, artifact_mask = self.filter_ibi_artifacts(ibi_data, method='statistical')
        artifacts_filtered = len(ibi_data) - len(ibi_filtered)
        
        # Calculate data quality
        data_quality_score = (len(ibi_filtered) / len(ibi_data)) * 100 if len(ibi_data) > 0 else 0
        
        # Calculate metrics
        time_metrics = self.calculate_time_domain_hrv(ibi_filtered)
        freq_metrics = self.calculate_frequency_domain_hrv(ibi_filtered)
        scores = self.calculate_comprehensive_scores(time_metrics, freq_metrics)
        
        # Combine all metrics
        session_data = {
            **time_metrics,
            **freq_metrics,
            **scores,
            'artifacts_filtered': artifacts_filtered,
            'data_quality_score': data_quality_score
        }
        
        # Store in database
        self._store_session_data(activity_id, session_data, source)
        self._store_record_data(activity_id, ibi_data, artifact_mask)
        
        return session_data

    def _store_session_data(self, activity_id, session_data, source):
        """Store session data in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO hrv_sessions (
                activity_id, source, timestamp, hrv_rmssd, hrv_sdnn, hrv_pnn50, hrv_nn50,
                mean_hr, min_hr, max_hr, mean_ibi, vlf_power, lf_power, hf_power,
                total_power, lf_hf_ratio, lf_nu, hf_nu, hrv_score, recovery_score,
                stress_score, artifacts_filtered, data_quality_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity_id, source, datetime.datetime.now(),
                session_data.get('hrv_rmssd'), session_data.get('hrv_sdnn'),
                session_data.get('hrv_pnn50'), session_data.get('hrv_nn50'),
                session_data.get('mean_hr'), session_data.get('min_hr'),
                session_data.get('max_hr'), session_data.get('mean_ibi'),
                session_data.get('vlf_power'), session_data.get('lf_power'),
                session_data.get('hf_power'), session_data.get('total_power'),
                session_data.get('lf_hf_ratio'), session_data.get('lf_nu'),
                session_data.get('hf_nu'), session_data.get('hrv_score'),
                session_data.get('recovery_score'), session_data.get('stress_score'),
                session_data.get('artifacts_filtered'), session_data.get('data_quality_score')
            ))

    def _store_record_data(self, activity_id, ibi_data, artifact_mask):
        """Store beat-by-beat data in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for i, ibi in enumerate(ibi_data):
                valid_beat = i < len(artifact_mask) and artifact_mask[i]
                hr_bpm = 60000 / ibi if ibi > 0 else np.nan
                
                cursor.execute('''
                INSERT OR REPLACE INTO hrv_records (
                    activity_id, record_number, timestamp, ibi_ms, hr_bpm, valid_beat
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (activity_id, i, datetime.datetime.now(), ibi, hr_bpm, valid_beat))

    # === VISUALIZATION FUNCTIONS ===
    
    def get_session_data(self, days=30, source=None):
        """Retrieve session data for visualization"""
        with sqlite3.connect(self.db_path) as conn:
            where_clause = "WHERE timestamp >= date('now', ?)"
            params = [f'-{days} days']
            
            if source:
                where_clause += " AND source = ?"
                params.append(source)
                
            query = f"""
            SELECT date(timestamp) as date, 
                   AVG(hrv_rmssd) as avg_rmssd, 
                   AVG(hrv_sdnn) as avg_sdnn,
                   AVG(hrv_pnn50) as avg_pnn50,
                   AVG(mean_hr) as avg_hr,
                   AVG(recovery_score) as avg_recovery,
                   AVG(stress_score) as avg_stress,
                   COUNT(*) as session_count,
                   source
            FROM hrv_sessions
            {where_clause}
            GROUP BY date(timestamp), source
            ORDER BY date(timestamp) ASC
            """
            
            try:
                df = pd.read_sql_query(query, conn, params=params)
                df['date'] = pd.to_datetime(df['date'])
                return df
            except Exception as e:
                logger.error(f"Database error: {e}")
                return self._generate_sample_data(days)

    def _generate_sample_data(self, days=30):
        """Generate sample data for demonstration"""
        dates = pd.date_range(end=pd.Timestamp.today(), periods=days)
        np.random.seed(42)
        
        return pd.DataFrame({
            'date': dates,
            'avg_rmssd': np.random.normal(50, 8, days) + np.sin(np.arange(days)/7) * 5,
            'avg_sdnn': np.random.normal(60, 10, days) + np.sin(np.arange(days)/7) * 7,
            'avg_pnn50': np.random.normal(25, 5, days),
            'avg_hr': np.random.normal(65, 5, days),
            'avg_recovery': np.random.normal(75, 10, days),
            'avg_stress': np.random.normal(25, 8, days),
            'session_count': np.random.randint(1, 4, days),
            'source': ['SAMPLE'] * days
        })

    def create_comprehensive_dashboard(self, days=30):
        """Create comprehensive HRV dashboard"""
        df = self.get_session_data(days)
        
        if df.empty:
            print("No data available for visualization")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Comprehensive HRV Health Dashboard', fontsize=16, fontweight='bold')
        
        # 1. HRV Trends Over Time
        axes[0,0].plot(df['date'], df['avg_rmssd'], 'o-', label='RMSSD', linewidth=2)
        axes[0,0].plot(df['date'], df['avg_sdnn'], 's-', label='SDNN', linewidth=2)
        axes[0,0].set_title('HRV Trend Analysis', fontweight='bold')
        axes[0,0].set_ylabel('HRV Value (ms)')
        axes[0,0].legend()
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # 2. Recovery vs Stress
        axes[0,1].plot(df['date'], df['avg_recovery'], 'o-', color='green', label='Recovery')
        axes[0,1].plot(df['date'], df['avg_stress'], 'o-', color='red', label='Stress')
        axes[0,1].set_title('Recovery vs Stress Trends', fontweight='bold')
        axes[0,1].set_ylabel('Score')
        axes[0,1].legend()
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # 3. HR vs HRV Correlation
        scatter = axes[0,2].scatter(df['avg_hr'], df['avg_rmssd'], c=df['avg_recovery'], 
                                  cmap='RdYlGn', s=60, alpha=0.7)
        axes[0,2].set_title('HR vs HRV Correlation', fontweight='bold')
        axes[0,2].set_xlabel('Average Heart Rate (bpm)')
        axes[0,2].set_ylabel('RMSSD (ms)')
        plt.colorbar(scatter, ax=axes[0,2], label='Recovery Score')
        
        # 4. Weekly Pattern Analysis
        df['day_of_week'] = df['date'].dt.day_name()
        weekly_pattern = df.groupby('day_of_week')['avg_rmssd'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        axes[1,0].bar(weekly_pattern.index, weekly_pattern.values, color='skyblue', alpha=0.7)
        axes[1,0].set_title('Weekly HRV Pattern', fontweight='bold')
        axes[1,0].set_ylabel('Average RMSSD (ms)')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # 5. Distribution Analysis
        axes[1,1].hist(df['avg_rmssd'], bins=12, alpha=0.7, color='blue', label='RMSSD')
        axes[1,1].hist(df['avg_sdnn'], bins=12, alpha=0.7, color='red', label='SDNN')
        axes[1,1].set_title('HRV Distribution', fontweight='bold')
        axes[1,1].set_xlabel('HRV Value (ms)')
        axes[1,1].set_ylabel('Frequency')
        axes[1,1].legend()
        
        # 6. Summary Statistics
        stats_text = f"""
        Mean RMSSD: {df['avg_rmssd'].mean():.1f} ± {df['avg_rmssd'].std():.1f}
        Mean SDNN: {df['avg_sdnn'].mean():.1f} ± {df['avg_sdnn'].std():.1f}
        Mean Recovery: {df['avg_recovery'].mean():.1f}%
        Mean Stress: {df['avg_stress'].mean():.1f}%
        Sessions: {df['session_count'].sum()}
        """
        axes[1,2].text(0.1, 0.5, stats_text, transform=axes[1,2].transAxes, 
                      fontsize=12, verticalalignment='center',
                      bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        axes[1,2].set_title('Summary Statistics', fontweight='bold')
        axes[1,2].axis('off')
        
        plt.tight_layout()
        plt.show()
        return fig

    def create_interactive_dashboard(self, days=30):
        """Create interactive Plotly dashboard"""
        if not PLOTLY_AVAILABLE:
            print("Plotly not available. Please install plotly for interactive visualizations.")
            return
        
        df = self.get_session_data(days)
        
        if df.empty:
            print("No data available for interactive visualization")
            return
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['HRV Trends', 'Recovery vs Stress', 'Weekly Patterns', 'Correlation Matrix'],
            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                   [{"type": "bar"}, {"type": "heatmap"}]]
        )
        
        # HRV Trends
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['avg_rmssd'], name='RMSSD', 
                      line=dict(color='blue', width=3), mode='lines+markers'),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['avg_sdnn'], name='SDNN', 
                      line=dict(color='red', width=3), mode='lines+markers'),
            row=1, col=1, secondary_y=True
        )
        
        # Recovery vs Stress
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['avg_recovery'], name='Recovery', 
                      line=dict(color='green', width=3), mode='lines+markers'),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=df['date'], y=df['avg_stress'], name='Stress', 
                      line=dict(color='red', width=3), mode='lines+markers'),
            row=1, col=2, secondary_y=True
        )
        
        # Weekly patterns
        df['day_of_week'] = df['date'].dt.day_name()
        weekly_pattern = df.groupby('day_of_week')['avg_rmssd'].mean().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        
        fig.add_trace(
            go.Bar(x=weekly_pattern.index, y=weekly_pattern.values, 
                   name='Weekly RMSSD', marker_color='lightblue'),
            row=2, col=1
        )
        
        fig.update_layout(
            title_text="Interactive HRV Health Dashboard",
            title_x=0.5,
            height=800,
            showlegend=True
        )
        
        fig.show()
        return fig

# === USAGE EXAMPLES AND INSTRUCTIONS ===

def example_usage():
    """Comprehensive usage examples"""
    
    print("=== HRV Comprehensive System Examples ===\n")
    
    # Initialize system
    hrv_system = HRVComprehensiveSystem()
    
    # Example 1: Analyze simulated IBI data
    print("1. Analyzing simulated IBI data...")
    np.random.seed(42)
    base_ibi = 900  # ~67 BPM
    n_beats = 500
    
    # Create realistic IBI data with trends and noise
    trend = np.sin(np.linspace(0, 4*np.pi, n_beats)) * 50
    noise = np.random.normal(0, 20, n_beats)
    ibi_data = base_ibi + trend + noise
    
    # Analyze the data
    results = hrv_system.analyze_ibi_data(ibi_data, "example_session_001", "SIMULATED")
    
    print("Analysis Results:")
    print(f"  RMSSD: {results.get('hrv_rmssd', 0):.2f} ms")
    print(f"  SDNN: {results.get('hrv_sdnn', 0):.2f} ms")
    print(f"  HRV Score: {results.get('hrv_score', 0):.1f}/100")
    print(f"  Recovery Score: {results.get('recovery_score', 0):.1f}/100")
    print(f"  Artifacts Filtered: {results.get('artifacts_filtered', 0)}")
    print(f"  Data Quality: {results.get('data_quality_score', 0):.1f}%\n")
    
    # Example 2: Create multiple sessions for trend analysis
    print("2. Creating multiple sessions for trend analysis...")
    for i in range(10):
        # Simulate different days with varying HRV
        variation = np.random.normal(0, 30, n_beats)
        daily_ibi = base_ibi + trend + noise + variation
        activity_id = f"daily_session_{i+1:03d}"
        hrv_system.analyze_ibi_data(daily_ibi, activity_id, "DAILY")
    
    print("Created 10 daily sessions for analysis\n")
    
    # Example 3: Generate visualizations
    print("3. Generating comprehensive dashboard...")
    hrv_system.create_comprehensive_dashboard(days=30)
    
    print("4. Creating interactive dashboard...")
    hrv_system.create_interactive_dashboard(days=30)
    
    print("\n=== Examples Complete ===")

def create_sample_fit_file_processor():
    """Example of processing FIT files"""
    
    def process_fit_file(file_path, hrv_system):
        """Process a single FIT file"""
        try:
            fit_file = FitFile(file_path)
            activity_id = os.path.splitext(os.path.basename(file_path))[0]
            
            ibi_data = []
            for msg in fit_file.messages:
                if msg.name == 'record':
                    fields = {field.name: field.value for field in msg.fields}
                    if 'RRint' in fields and fields['RRint']:
                        ibi_data.append(fields['RRint'])
            
            if len(ibi_data) > 10:
                results = hrv_system.analyze_ibi_data(ibi_data, activity_id, "FIT_FILE")
                return results
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
        
        return None
    
    return process_fit_file

# === MAIN EXECUTION ===

if __name__ == "__main__":
    
    print("Starting HRV Comprehensive System...")
    
    # Run examples
    example_usage()
    
    print("\nSystem ready for use!")
    print("\nAvailable methods:")
    print("- hrv_system.analyze_ibi_data(ibi_data, activity_id, source)")
    print("- hrv_system.create_comprehensive_dashboard(days)")
    print("- hrv_system.create_interactive_dashboard(days)")
    print("- hrv_system.get_session_data(days, source)")
