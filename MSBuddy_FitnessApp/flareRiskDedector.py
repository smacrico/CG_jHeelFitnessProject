import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FlareRiskConfig:
    """Configuration for flare risk prediction"""
    # Lookback periods (days)
    hrv_trend_days: int = 7
    sleep_pattern_days: int = 14
    stress_trend_days: int = 5
    environmental_days: int = 3
    medication_adherence_days: int = 30
    
    # Risk thresholds
    hrv_decline_threshold: float = 0.15  # 15% decline
    sleep_disruption_threshold: float = 0.20  # 20% decline
    stress_elevation_threshold: float = 1.5  # 1.5 std deviations
    medication_adherence_threshold: float = 0.85  # 85% adherence
    
    # Risk weights (must sum to 1.0)
    weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                'hrv_decline': 0.25,
                'sleep_disruption': 0.30,
                'stress_elevation': 0.20,
                'environmental_triggers': 0.15,
                'medication_gaps': 0.10
            }

class MSFlarePredictor:
    """Advanced MS Flare Risk Prediction System"""
    
    def __init__(self, db_path: str, config: FlareRiskConfig = None):
        self.db_path = db_path
        self.config = config or FlareRiskConfig()
        self.initialize_database()
        
    def initialize_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        tables = {
            'daily_metrics': '''
                CREATE TABLE IF NOT EXISTS daily_metrics (
                    date TEXT PRIMARY KEY,
                    hrv_rmssd REAL,
                    sleep_score REAL,
                    deep_sleep_minutes REAL,
                    rem_sleep_minutes REAL,
                    stress_avg REAL,
                    resting_hr REAL,
                    body_battery_start REAL,
                    body_battery_end REAL,
                    temperature_celsius REAL,
                    humidity_percent REAL,
                    barometric_pressure REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'medication_log': '''
                CREATE TABLE IF NOT EXISTS medication_log (
                    date TEXT,
                    medication_name TEXT,
                    scheduled_dose_time TEXT,
                    actual_dose_time TEXT,
                    dose_taken BOOLEAN,
                    side_effects TEXT,
                    PRIMARY KEY (date, medication_name, scheduled_dose_time)
                )
            ''',
            'symptom_log': '''
                CREATE TABLE IF NOT EXISTS symptom_log (
                    date TEXT PRIMARY KEY,
                    fatigue_level INTEGER,
                    cognitive_fog INTEGER,
                    mobility_score INTEGER,
                    pain_level INTEGER,
                    mood_score INTEGER,
                    heat_sensitivity INTEGER,
                    overall_wellbeing INTEGER,
                    notes TEXT
                )
            ''',
            'flare_history': '''
                CREATE TABLE IF NOT EXISTS flare_history (
                    date TEXT PRIMARY KEY,
                    flare_severity INTEGER,
                    symptoms_affected TEXT,
                    duration_days INTEGER,
                    recovery_days INTEGER,
                    triggers_identified TEXT
                )
            ''',
            'risk_predictions': '''
                CREATE TABLE IF NOT EXISTS risk_predictions (
                    date TEXT PRIMARY KEY,
                    overall_risk_score REAL,
                    hrv_risk REAL,
                    sleep_risk REAL,
                    stress_risk REAL,
                    environmental_risk REAL,
                    medication_risk REAL,
                    risk_level TEXT,
                    recommendations TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        }
        
        for table_name, table_sql in tables.items():
            cursor.execute(table_sql)
            
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def get_recent_data(self, days_back: int) -> pd.DataFrame:
        """Retrieve recent data from database"""
        conn = sqlite3.connect(self.db_path)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        query = '''
            SELECT dm.*, sl.fatigue_level, sl.cognitive_fog, sl.mobility_score,
                   sl.pain_level, sl.mood_score, sl.heat_sensitivity, sl.overall_wellbeing
            FROM daily_metrics dm
            LEFT JOIN symptom_log sl ON dm.date = sl.date
            WHERE dm.date >= ? AND dm.date <= ?
            ORDER BY dm.date DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'), 
                                                   end_date.strftime('%Y-%m-%d')))
        conn.close()
        return df

    def calculate_hrv_trend_decline(self, recent_ pd.DataFrame) -> float:
        """Calculate HRV decline risk factor"""
        if len(recent_data) < self.config.hrv_trend_days:
            logger.warning("Insufficient HRV data for trend analysis")
            return 0.0
            
        hrv_data = recent_data['hrv_rmssd'].dropna()
        if len(hrv_data) < 3:
            return 0.0
            
        # Calculate 7-day moving average
        recent_avg = hrv_data.head(self.config.hrv_trend_days).mean()
        baseline_avg = hrv_data.tail(min(30, len(hrv_data))).mean()
        
        if baseline_avg == 0:
            return 0.0
            
        decline_ratio = (baseline_avg - recent_avg) / baseline_avg
        
        # Calculate trend slope
        days = np.arange(len(hrv_data.head(self.config.hrv_trend_days)))
        if len(days) > 1:
            slope = np.polyfit(days, hrv_data.head(self.config.hrv_trend_days), 1)[0]
            trend_factor = max(0, -slope / baseline_avg)  # Negative slope indicates decline
        else:
            trend_factor = 0
            
        # Combine decline ratio and trend
        risk_score = min(1.0, max(0.0, (decline_ratio * 0.7 + trend_factor * 0.3)))
        
        logger.info(f"HRV decline risk: {risk_score:.3f} (decline: {decline_ratio:.3f}, trend: {trend_factor:.3f})")
        return risk_score

    def detect_sleep_pattern_changes(self, recent_ pd.DataFrame) -> float:
        """Detect sleep pattern disruption"""
        if len(recent_data) < self.config.sleep_pattern_days:
            logger.warning("Insufficient sleep data for pattern analysis")
            return 0.0
            
        sleep_scores = recent_data['sleep_score'].dropna()
        deep_sleep = recent_data['deep_sleep_minutes'].dropna()
        rem_sleep = recent_data['rem_sleep_minutes'].dropna()
        
        if len(sleep_scores) < 3:
            return 0.0
            
        # Recent vs baseline comparison
        recent_sleep_avg = sleep_scores.head(7).mean()
        baseline_sleep_avg = sleep_scores.tail(min(30, len(sleep_scores))).mean()
        
        # Sleep architecture analysis
        recent_deep_avg = deep_sleep.head(7).mean() if len(deep_sleep) > 0 else 0
        baseline_deep_avg = deep_sleep.tail(min(30, len(deep_sleep))).mean() if len(deep_sleep) > 0 else 0
        
        recent_rem_avg = rem_sleep.head(7).mean() if len(rem_sleep) > 0 else 0
        baseline_rem_avg = rem_sleep.tail(min(30, len(rem_sleep))).mean() if len(rem_sleep) > 0 else 0
        
        # Calculate disruption scores
        sleep_score_disruption = max(0, (baseline_sleep_avg - recent_sleep_avg) / baseline_sleep_avg) if baseline_sleep_avg > 0 else 0
        deep_sleep_disruption = max(0, (baseline_deep_avg - recent_deep_avg) / baseline_deep_avg) if baseline_deep_avg > 0 else 0
        rem_sleep_disruption = max(0, (baseline_rem_avg - recent_rem_avg) / baseline_rem_avg) if baseline_rem_avg > 0 else 0
        
        # Sleep variability (consistency measure)
        sleep_variability = sleep_scores.head(7).std() / sleep_scores.head(7).mean() if sleep_scores.head(7).mean() > 0 else 0
        
        # Composite sleep risk
        risk_score = min(1.0, (sleep_score_disruption * 0.4 + 
                              deep_sleep_disruption * 0.3 + 
                              rem_sleep_disruption * 0.2 + 
                              min(0.5, sleep_variability) * 0.1))
        
        logger.info(f"Sleep disruption risk: {risk_score:.3f}")
        return risk_score

    def analyze_stress_trends(self, recent_ pd.DataFrame) -> float:
        """Analyze stress level trends"""
        if len(recent_data) < self.config.stress_trend_days:
            logger.warning("Insufficient stress data for trend analysis")
            return 0.0
            
        stress_data = recent_data['stress_avg'].dropna()
        if len(stress_data) < 3:
            return 0.0
            
        # Calculate recent stress elevation
        recent_stress = stress_data.head(self.config.stress_trend_days).mean()
        baseline_stress = stress_data.tail(min(30, len(stress_data))).mean()
        stress_std = stress_data.tail(min(30, len(stress_data))).std()
        
        if stress_std == 0:
            return 0.0
            
        # Z-score based elevation
        stress_elevation = (recent_stress - baseline_stress) / stress_std
        
        # Convert to risk score (0-1)
        risk_score = min(1.0, max(0.0, stress_elevation / self.config.stress_elevation_threshold))
        
        logger.info(f"Stress elevation risk: {risk_score:.3f} (elevation: {stress_elevation:.3f})")
        return risk_score

    def check_environmental_correlations(self, recent_ pd.DataFrame) -> float:
        """Check environmental trigger correlations"""
        if len(recent_data) < self.config.environmental_days:
            return 0.0
            
        # Temperature sensitivity (key for MS)
        temp_data = recent_data['temperature_celsius'].dropna()
        humidity_data = recent_data['humidity_percent'].dropna()
        pressure_data = recent_data['barometric_pressure'].dropna()
        
        risk_factors = []
        
        # High temperature risk (MS heat sensitivity)
        if len(temp_data) > 0:
            recent_temp = temp_data.head(3).mean()
            if recent_temp > 25:  # Above 25°C
                temp_risk = min(1.0, (recent_temp - 25) / 10)  # Scale 25-35°C to 0-1
                risk_factors.append(temp_risk)
                
        # High humidity risk
        if len(humidity_data) > 0:
            recent_humidity = humidity_data.head(3).mean()
            if recent_humidity > 70:
                humidity_risk = min(1.0, (recent_humidity - 70) / 30)  # Scale 70-100% to 0-1
                risk_factors.append(humidity_risk)
                
        # Barometric pressure changes
        if len(pressure_data) > 1:
            pressure_change = abs(pressure_data.iloc[0] - pressure_data.iloc[1])
            if pressure_change > 5:  # Significant pressure change
                pressure_risk = min(1.0, pressure_change / 20)
                risk_factors.append(pressure_risk)
        
        # Combine environmental risks
        if risk_factors:
            risk_score = np.mean(risk_factors)
        else:
            risk_score = 0.0
            
        logger.info(f"Environmental risk: {risk_score:.3f}")
        return risk_score

    def detect_medication_adherence_issues(self, recent_ pd.DataFrame) -> float:
        """Detect medication adherence issues"""
        conn = sqlite3.connect(self.db_path)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.config.medication_adherence_days)
        
        query = '''
            SELECT date, medication_name, dose_taken
            FROM medication_log
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
        '''
        
        med_data = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'), 
                                                         end_date.strftime('%Y-%m-%d')))
        conn.close()
        
        if len(med_data) == 0:
            logger.warning("No medication data available")
            return 0.0
            
        # Calculate adherence rate
        total_doses = len(med_data)
        taken_doses = len(med_data[med_data['dose_taken'] == True])
        adherence_rate = taken_doses / total_doses if total_doses > 0 else 1.0
        
        # Risk increases as adherence decreases below threshold
        if adherence_rate >= self.config.medication_adherence_threshold:
            risk_score = 0.0
        else:
            risk_score = (self.config.medication_adherence_threshold - adherence_rate) / self.config.medication_adherence_threshold
            
        logger.info(f"Medication adherence risk: {risk_score:.3f} (adherence: {adherence_rate:.3f})")
        return risk_score

    def calculate_composite_flare_risk(self, risk_factors: Dict[str, float]) -> Dict[str, float]:
        """Calculate composite flare risk score"""
        # Weighted sum of risk factors
        total_risk = sum(risk_factors[factor] * self.config.weights[factor] 
                        for factor in risk_factors.keys())
        
        # Determine risk level
        if total_risk <= 0.3:
            risk_level = "LOW"
        elif total_risk <= 0.6:
            risk_level = "MODERATE"
        elif total_risk <= 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"
            
        return {
            'overall_risk_score': total_risk,
            'risk_level': risk_level,
            'individual_risks': risk_factors
        }

    def generate_recommendations(self, risk_result: Dict) -> List[str]:
        """Generate personalized recommendations based on risk assessment"""
        recommendations = []
        risk_level = risk_result['risk_level']
        individual_risks = risk_result['individual_risks']
        
        # General recommendations by risk level
        if risk_level == "CRITICAL":
            recommendations.append("⚠️ CRITICAL: Contact your neurologist immediately")
            recommendations.append("🛌 Prioritize complete rest and avoid all strenuous activities")
            recommendations.append("💊 Verify all medications are taken as prescribed")
            
        elif risk_level == "HIGH":
            recommendations.append("🚨 HIGH RISK: Consider contacting your healthcare provider")
            recommendations.append("😴 Focus on sleep optimization and stress reduction")
            recommendations.append("🌡️ Avoid heat exposure and stay in cool environments")
            
        elif risk_level == "MODERATE":
            recommendations.append("⚡ MODERATE RISK: Implement preventive measures")
            recommendations.append("🧘 Practice stress management techniques")
            recommendations.append("💤 Maintain consistent sleep schedule")
            
        else:  # LOW
            recommendations.append("✅ LOW RISK: Continue current health practices")
            recommendations.append("🎯 Good time for planned activities")
            
        # Specific recommendations based on individual risk factors
        if individual_risks['hrv_decline'] > 0.5:
            recommendations.append("💓 HRV declining - consider gentle breathing exercises")
            
        if individual_risks['sleep_disruption'] > 0.5:
            recommendations.append("😴 Sleep issues detected - review sleep hygiene")
            
        if individual_risks['stress_elevation'] > 0.5:
            recommendations.append("😰 Elevated stress - practice relaxation techniques")
            
        if individual_risks['environmental_triggers'] > 0.5:
            recommendations.append("🌡️ Environmental triggers present - stay cool and hydrated")
            
        if individual_risks['medication_gaps'] > 0.3:
            recommendations.append("💊 Medication adherence issue - set up reminders")
            
        return recommendations

    def predict_flare_risk(self) -> Dict:
        """Main function to predict flare risk"""
        logger.info("Starting flare risk prediction...")
        
        # Get recent data
        max_days = max(self.config.hrv_trend_days, 
                      self.config.sleep_pattern_days,
                      self.config.stress_trend_days,
                      self.config.environmental_days)
        
        recent_data = self.get_recent_data(max_days)
        
        if len(recent_data) == 0:
            logger.error("No recent data available for prediction")
            return {
                'overall_risk_score': 0.0,
                'risk_level': 'UNKNOWN',
                'individual_risks': {},
                'recommendations': ['No data available for risk assessment']
            }
        
        # Calculate individual risk factors
        risk_factors = {
            'hrv_decline': self.calculate_hrv_trend_decline(recent_data),
            'sleep_disruption': self.detect_sleep_pattern_changes(recent_data),
            'stress_elevation': self.analyze_stress_trends(recent_data),
            'environmental_triggers': self.check_environmental_correlations(recent_data),
            'medication_gaps': self.detect_medication_adherence_issues(recent_data)
        }
        
        # Calculate composite risk
        risk_result = self.calculate_composite_flare_risk(risk_factors)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(risk_result)
        risk_result['recommendations'] = recommendations
        
        # Save prediction to database
        self.save_prediction(risk_result)
        
        logger.info(f"Flare risk prediction completed: {risk_result['risk_level']} ({risk_result['overall_risk_score']:.3f})")
        return risk_result

    def save_prediction(self, risk_result: Dict):
        """Save prediction results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().strftime('%Y-%m-%d')
        individual_risks = risk_result['individual_risks']
        
        cursor.execute('''
            INSERT OR REPLACE INTO risk_predictions 
            (date, overall_risk_score, hrv_risk, sleep_risk, stress_risk, 
             environmental_risk, medication_risk, risk_level, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            today,
            risk_result['overall_risk_score'],
            individual_risks.get('hrv_decline', 0),
            individual_risks.get('sleep_disruption', 0),
            individual_risks.get('stress_elevation', 0),
            individual_risks.get('environmental_triggers', 0),
            individual_risks.get('medication_gaps', 0),
            risk_result['risk_level'],
            '\n'.join(risk_result['recommendations'])
        ))
        
        conn.commit()
        conn.close()

    def get_risk_history(self, days: int = 30) -> pd.DataFrame:
        """Get historical risk predictions"""
        conn = sqlite3.connect(self.db_path)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        query = '''
            SELECT * FROM risk_predictions
            WHERE date >= ? AND date <= ?
            ORDER BY date DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'), 
                                                   end_date.strftime('%Y-%m-%d')))
        conn.close()
        return df

def main():
    """Main execution function for daily monitoring"""
    # Configuration
    db_path = "ms_flare_prediction.db"
    config = FlareRiskConfig()
    
    # Initialize predictor
    predictor = MSFlarePredictor(db_path, config)
    
    # Run daily prediction
    risk_result = predictor.predict_flare_risk()
    
    # Display results
    print("\n" + "="*60)
    print("🏥 MS FLARE RISK ASSESSMENT")
    print("="*60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"🎯 Overall Risk Score: {risk_result['overall_risk_score']:.3f}")
    print(f"⚠️  Risk Level: {risk_result['risk_level']}")
    
    print("\n📊 Individual Risk Factors:")
    for factor, score in risk_result['individual_risks'].items():
        print(f"   • {factor.replace('_', ' ').title()}: {score:.3f}")
    
    print("\n💡 Recommendations:")
    for i, rec in enumerate(risk_result['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*60)
    
    return risk_result

if __name__ == "__main__":
    main()
