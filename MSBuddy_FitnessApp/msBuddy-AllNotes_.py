# 1. Data Extraction from SQLite Databases:

import sqlite3
from datetime import date, timedelta

today = date.today()
yesterday = today - timedelta(days=1) # For overnight data

def fetch_hrv_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT hrv, rmssd, sdnn FROM hrv_table WHERE date=?", (today,))
    hrv_data = cursor.fetchone()
    conn.close()
    if hrv_data:
        return {"hrv": hrv_data[0], "rmssd": hrv_data[1], "sdnn": hrv_data[2]}
    return None

def fetch_garmin_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sleep_score, deep_sleep_duration, rem_sleep_duration, stress_level_avg,
               spo2_min, resting_hr, body_battery_start, body_battery_end
        FROM garmin_sleep_stress_table
        WHERE date=?
    """, (yesterday,)) # Assuming overnight data is stored with the date it started
    garmin_data = cursor.fetchone()
    conn.close()
    if garmin_data:
        return {
            "sleep_score": garmin_data[0],
            "deep_sleep": garmin_data[1],
            "rem_sleep": garmin_data[2],
            "stress_avg": garmin_data[3],
            "spo2_min": garmin_data[4],
            "rhr": garmin_data[5],
            "bb_start": garmin_data[6],
            "bb_end": garmin_data[7],
        }
    return None

hrv_data = fetch_hrv_data("path/to/your/hrv_database.db")
garmin_data = fetch_garmin_data("path/to/your/garmin_database.db")

if not hrv_data or not garmin_data:
    print("Error: Could not retrieve necessary data.")
    exit()
    

# 2. Calculating Key Metrics:

def calculate_recovery_score(hrv_data, garmin_data):
    hrv_contribution = (hrv_data["hrv"] / your_baseline_hrv_high) * weight_hrv
    sleep_quality_contribution = (garmin_data["sleep_score"] / 100) * weight_sleep
    rhr_contribution = (your_baseline_rhr_low / garmin_data["rhr"]) * weight_rhr # Lower RHR generally better
    body_battery_recharge = (garmin_data["bb_end"] - garmin_data["bb_start"]) / 100 * weight_bb
    # Consider adding weights for deep and REM sleep duration

    recovery_score = (hrv_contribution + sleep_quality_contribution +
                      rhr_contribution + body_battery_recharge) / \
                     (weight_hrv + weight_sleep + weight_rhr + weight_bb) * 100

    return max(0, min(100, recovery_score)) # Ensure score is between 0 and 100

# Define your personal baselines and weights
your_baseline_hrv_high = 80  # Example
your_baseline_rhr_low = 50   # Example
weight_hrv = 0.3
weight_sleep = 0.4
weight_rhr = 0.15
weight_bb = 0.15

recovery_score = calculate_recovery_score(hrv_data, garmin_data)


def calculate_fatigue_level(recovery_score, garmin_data):
    fatigue = 0
    if recovery_score < 40:
        fatigue += 40
    elif recovery_score < 60:
        fatigue += 20

    if garmin_data["sleep_score"] < 60:
        fatigue += 30
    elif garmin_data["sleep_score"] < 75:
        fatigue += 15

    if garmin_data["stress_avg"] > 50:
        fatigue += 20
    elif garmin_data["stress_avg"] > 30:
        fatigue += 10

    if garmin_data["bb_start"] < 30:
        fatigue += 30
    elif garmin_data["bb_start"] < 50:
        fatigue += 15

    return min(100, fatigue) # Scale to 0-100


def calculate_sleep_charge(garmin_data):
    sleep_charge = (garmin_data["sleep_score"] / 100 * 0.4 +
                    (garmin_data["deep_sleep"] / 3600) * 0.3 + # Assuming target of 1 hour deep sleep
                    (garmin_data["rem_sleep"] / 3600) * 0.2 +   # Assuming target of 1 hour REM sleep
                    (garmin_data["bb_end"] - garmin_data["bb_start"]) / 100 * 0.1) * 100
    return max(0, min(100, sleep_charge))



def calculate_recovery_ratio(hrv_data, garmin_data):
    if garmin_data["rhr"] > 0:
        recovery_ratio = hrv_data["rmssd"] / garmin_data["rhr"]
        return recovery_ratio
    return 0


# 3  Generating Daily Recommendations:

def generate_recommendation(recovery_score, fatigue_level):
    if recovery_score >= 70 and fatigue_level <= 30:
        return "Your body shows good recovery. You can likely proceed with your planned activities."
    elif 50 <= recovery_score < 70 and 30 < fatigue_level <= 60:
        return "Your recovery is moderate. Consider a balanced day with moderate activity and listen to your body."
    elif recovery_score < 50 or fatigue_level > 60:
        return "Your body may need more rest. Consider limiting strenuous activities and prioritize recovery."
    else:
        return "Unable to determine recommendation based on current data."
    
    
    # 4. Generating Daily Report &  Formatting the Email Report : 
    
    import smtplib
from email.mime.text import MIMEText

def send_email_report(recipient_email, subject, body):
    sender_email = "your_email@example.com"
    sender_password = "your_email_password"  # Consider secure methods for storing passwords

    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.your_email_provider.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email report sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Construct the email body
report_body = f"""
Daily Recovery Report - {today.strftime("%Y-%m-%d")}

Recovery Score: {recovery_score:.2f}
Fatigue Level: {fatigue_level:.2f}
Sleep Charge: {sleep_charge:.2f}
Recovery Ratio (RMSSD/RHR): {recovery_ratio:.2f}

Daily Recommendation: {generate_recommendation(recovery_score, fatigue_level)}
"""

send_email_report("your_recipient_email@example.com", "Daily Health & Recovery Report", report_body)
    
# 5. Scheduling the Script:       
# You can use your operating system's scheduling tools (like cron on Linux/macOS or Task Scheduler on Windows) to run this Python script automatically each morning.

# Important Considerations and Next Steps:

# Personalization is Key: The formulas and weights used in the calculations are examples. You'll need to experiment and adjust them based on how these metrics correlate with your personal experience of fatigue, recovery, and MS symptoms. Tracking your subjective feelings alongside these metrics will be crucial for fine-tuning the calculations.
# Baselines: Establishing your personal baselines for HRV, RHR, and other metrics during periods of stable health is important for interpreting daily fluctuations.
# MS-Specific Factors: Consider how specific MS symptoms or flares might influence these metrics and how you want to incorporate that understanding into your analysis.
# Data Quality: Ensure the accuracy and consistency of your data collection.
# Ethical Considerations: Be mindful of data privacy and security.
# Visualization: As you collect more data, consider using libraries like matplotlib or seaborn to visualize trends and patterns. This can provide further insights into your body's responses.
# Consultation with Professionals: This automated report is a tool to help you understand your body better. It's essential to continue working closely with your neurologist and other healthcare providers for personalized medical advice and management of your multiple sclerosis.