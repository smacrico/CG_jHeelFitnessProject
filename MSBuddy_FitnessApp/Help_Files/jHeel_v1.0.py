import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta
import os # For environment variables (secure password handling)
# from dotenv import load_dotenv # Uncomment if you use a .env file for secrets

# --- 0. Configuration & Personal Baselines ---
# load_dotenv() # Uncomment if you use a .env file

# Database Paths (UPDATE THESE TO YOUR ACTUAL PATHS)
HRV_DB_PATH = "path/to/your/hrv_database.db"
GARMIN_DB_PATH = "path/to/your/garmin_database.db" # This DB will hold both sleep/stress and activities

# Personal Baselines (Crucial for Recovery Score, adjust based on your data)
YOUR_BASELINE_HRV_HIGH = 80  # Example: Your healthy high HRV (RMSSD or general HRV)
YOUR_BASELINE_RHR_LOW = 50   # Example: Your healthy low Resting Heart Rate

# Recovery Score Weights (Adjust these to reflect importance for you)
WEIGHT_HRV = 0.3
WEIGHT_SLEEP = 0.4
WEIGHT_RHR = 0.15
WEIGHT_BB = 0.15

# Training Load / TSS Configuration
YOUR_FTP_WATTS = 250         # Example: Functional Threshold Power in Watts (for cycling)
YOUR_LTHR_BPM = 170          # Example: Lactate Threshold Heart Rate in beats per minute (for HRTSS)
YOUR_THRESHOLD_PACE_MIN_PER_KM = 4.5 # Example: Your Threshold Pace for running (e.g., 4:30 min/km)

# Heart Rate Zone Weights for HRTSS (adjust if your zones or stress contribution differ)
# These are common approximations for intensity factor contribution.
HR_ZONE_WEIGHTS = {
    "Z1": 0.0, # Below 81% LTHR, very light
    "Z2": 0.6, # 81-89% LTHR
    "Z3": 0.8, # 89-95% LTHR
    "Z4": 1.0, # 95-105% LTHR (around threshold)
    "Z5": 1.2, # Above 105% LTHR
}

# Fat Burn Calculation Configuration
YOUR_AGE = 40 # Your age for MHR calculation
YOUR_WEIGHT_KG = 70 # Your body weight in kilograms (Crucial for calorie calculations)

YOUR_MAX_HR = 220 - YOUR_AGE # Estimated Max Heart Rate

FAT_BURN_HR_ZONE_LOWER_PERCENT = 0.50 # 50% of MHR
FAT_BURN_HR_ZONE_UPPER_PERCENT = 0.70 # 70% of MHR

FAT_BURN_HR_LOWER_BPM = FAT_BURN_HR_ZONE_LOWER_PERCENT * YOUR_MAX_HR
FAT_BURN_HR_UPPER_BPM = FAT_BURN_HR_ZONE_UPPER_PERCENT * YOUR_MAX_HR

# Estimated percentage of calories from fat at different intensities
# These are general approximations, adjust if you have more specific data.
FAT_PERCENTAGE_IN_VERY_LIGHT_ZONE = 0.80 # e.g., below fat burn zone
FAT_PERCENTAGE_IN_FAT_BURN_ZONE = 0.65   # In the 50-70% MHR zone
FAT_PERCENTAGE_IN_MODERATE_ZONE = 0.50   # Above fat burn, but not max effort
FAT_PERCENTAGE_IN_HIGH_ZONE = 0.30       # High intensity (more carbs)


# MET Values by Pace (min/km). Lower pace_max_min_per_km means faster speed.
# These are general estimates from compendium of physical activities.
MET_VALUES_BY_PACE = {
    "Walk": [
        {"pace_max_min_per_km": 10.0, "mets": 2.0}, # Very slow walk (>16 min/mile)
        {"pace_max_min_per_km": 8.5, "mets": 2.8}, # Slow walk (~13.5-16 min/mile)
        {"pace_max_min_per_km": 7.0, "mets": 3.5}, # Moderate walk (~11-13.5 min/mile, 3-3.5 mph)
        {"pace_max_min_per_km": 6.0, "mets": 4.5}, # Brisk walk (~9.5-11 min/mile, 3.5-4 mph)
        {"pace_max_min_per_km": 5.0, "mets": 5.8}, # Very brisk walk (~8-9.5 min/mile, 4-4.5 mph)
    ],
    "Run": [
        {"pace_max_min_per_km": 6.0, "mets": 7.0},  # Jogging / Very Slow Run (10 min/mile)
        {"pace_max_min_per_km": 5.5, "mets": 8.0},  # Slow Run (approx 8.5-9 min/mile)
        {"pace_max_min_per_km": 5.0, "mets": 9.0},  # Moderate Run (approx 8 min/mile)
        {"pace_max_min_per_km": 4.5, "mets": 10.0}, # Brisk Run (approx 7 min/mile)
        {"pace_max_min_per_km": 4.0, "mets": 11.5}, # Fast Run (approx 6.5 min/mile)
        {"pace_max_min_per_km": 3.5, "mets": 13.0}, # Very Fast Run (approx 5.5 min/mile)
    ]
}


# Email Settings
SENDER_EMAIL = "your_email@example.com"
# Use environment variables for password for security!
# Set this in your OS: export EMAIL_PASSWORD="your_secure_password"
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = "your_recipient_email@example.com"
SMTP_SERVER = "smtp.your_email_provider.com" # e.g., 'smtp.gmail.com'
SMTP_PORT = 465 # Typically 465 for SSL or 587 for TLS


# --- 1. Data Extraction Functions ---

def fetch_hrv_data(db_path, target_date):
    """Fetches HRV data for a specific date."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT hrv, rmssd, sdnn FROM hrv_table WHERE date=?", (target_date.strftime("%Y-%m-%d"),))
        hrv_data = cursor.fetchone()
        if hrv_data:
            return {"hrv": hrv_data[0], "rmssd": hrv_data[1], "sdnn": hrv_data[2]}
        return None
    except sqlite3.Error as e:
        print(f"Database error fetching HRV data: {e}")
        return None
    finally:
        if conn:
            conn.close()

def fetch_garmin_sleep_stress_data(db_path, target_date):
    """Fetches Garmin sleep and stress data for a specific date (typically overnight data)."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Assuming overnight data is stored with the date it started (i.e., yesterday's date)
        cursor.execute("""
            SELECT sleep_score, deep_sleep_duration, rem_sleep_duration, stress_level_avg,
                   spo2_min, resting_hr, body_battery_start, body_battery_end
            FROM garmin_sleep_stress_table
            WHERE date=?
        """, (target_date.strftime("%Y-%m-%d"),))
        garmin_data = cursor.fetchone()
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
    except sqlite3.Error as e:
        print(f"Database error fetching Garmin sleep/stress data: {e}")
        return None
    finally:
        if conn:
            conn.close()

def fetch_garmin_activity_data(db_path, target_date):
    """Fetches Garmin activity data for a specific date."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT activity_type, duration_seconds, avg_hr, normalized_power,
                   time_in_hr_zone1_seconds, time_in_hr_zone2_seconds,
                   time_in_hr_zone3_seconds, time_in_hr_zone4_seconds,
                   time_in_hr_zone5_seconds, avg_pace_min_per_km, training_load_garmin
            FROM garmin_activities_table
            WHERE date=?
        """, (target_date.strftime("%Y-%m-%d"),))
        activities_data = cursor.fetchall()

        parsed_activities = []
        for activity in activities_data:
            parsed_activities.append({
                "activity_id": None, # Assuming no ID needed for calculation
                "activity_type": activity[0],
                "duration_seconds": activity[1],
                "avg_hr": activity[2],
                "normalized_power": activity[3],
                "time_in_hr_zone1_seconds": activity[4],
                "time_in_hr_zone2_seconds": activity[5],
                "time_in_hr_zone3_seconds": activity[6],
                "time_in_hr_zone4_seconds": activity[7],
                "time_in_hr_zone5_seconds": activity[8],
                "avg_pace_min_per_km": activity[9],
                "training_load_garmin": activity[10]
            })
        return parsed_activities
    except sqlite3.Error as e:
        print(f"Database error fetching Garmin activity data: {e}")
        return []
    finally:
        if conn:
            conn.close()

# --- 2. Metric Calculation Functions ---

def calculate_recovery_score(hrv_data, garmin_data, baseline_hrv_high, baseline_rhr_low,
                             weight_hrv, weight_sleep, weight_rhr, weight_bb):
    """Calculates a composite recovery score (0-100)."""
    if not hrv_data or not garmin_data:
        return 0

    hrv_contribution = (hrv_data["hrv"] / baseline_hrv_high) * weight_hrv if baseline_hrv_high else 0
    sleep_quality_contribution = (garmin_data["sleep_score"] / 100) * weight_sleep
    rhr_contribution = (baseline_rhr_low / garmin_data["rhr"]) * weight_rhr if garmin_data["rhr"] else 0
    body_battery_recharge = (garmin_data["bb_end"] - garmin_data["bb_start"]) / 100 * weight_bb

    total_weight = weight_hrv + weight_sleep + weight_rhr + weight_bb
    if total_weight == 0: return 0

    recovery_score = (hrv_contribution + sleep_quality_contribution +
                      rhr_contribution + body_battery_recharge) / total_weight * 100

    return max(0, min(100, recovery_score))

def calculate_fatigue_level(recovery_score, garmin_data, total_daily_tss):
    """Estimates fatigue level (0-100) based on recovery, sleep, stress, and training load."""
    fatigue = 0

    if recovery_score < 40:
        fatigue += 40
    elif recovery_score < 60:
        fatigue += 20

    if garmin_data and garmin_data.get("sleep_score", 0) < 60:
        fatigue += 30
    elif garmin_data and garmin_data.get("sleep_score", 0) < 75:
        fatigue += 15

    if garmin_data and garmin_data.get("stress_avg", 0) > 50:
        fatigue += 20
    elif garmin_data and garmin_data.get("stress_avg", 0) > 30:
        fatigue += 10

    if garmin_data and garmin_data.get("bb_start", 0) < 30:
        fatigue += 30
    elif garmin_data and garmin_data.get("bb_start", 0) < 50:
        fatigue += 15

    # Add TSS contribution to fatigue
    if total_daily_tss > 200:
        fatigue += 30
    elif total_daily_tss > 100:
        fatigue += 15

    return min(100, fatigue)

def calculate_sleep_charge(garmin_data):
    """Calculates how restorative sleep was (0-100)."""
    if not garmin_data:
        return 0

    # Assuming deep/rem sleep durations are in seconds, convert to hours for target comparison
    # Target of 1 hour (3600s) deep/rem is a rough baseline. Adjust these weights/targets.
    sleep_charge = (garmin_data["sleep_score"] / 100 * 0.4 +
                    (garmin_data["deep_sleep"] / 3600) * 0.3 +
                    (garmin_data["rem_sleep"] / 3600) * 0.2 +
                    (garmin_data["bb_end"] - garmin_data["bb_start"]) / 100 * 0.1) * 100
    return max(0, min(100, sleep_charge))

def calculate_recovery_ratio(hrv_data, garmin_data):
    """Calculates HRV (RMSSD) to RHR ratio. Higher often better."""
    if not hrv_data or not garmin_data or garmin_data.get("rhr", 0) == 0:
        return 0
    return hrv_data["rmssd"] / garmin_data["rhr"]

def calculate_power_tss(duration_seconds, normalized_power, ftp):
    """Calculates Training Stress Score (TSS) for power-based activities."""
    if ftp == 0 or normalized_power is None or normalized_power == 0 or duration_seconds == 0:
        return 0
    
    # Intensity Factor (IF) = Normalized Power / FTP
    intensity_factor = normalized_power / ftp
    
    # TSS = (duration_seconds * IF^2) / 3600 * 100
    tss = (duration_seconds * (intensity_factor ** 2)) / 3600 * 100
    return tss

def calculate_hr_tss(duration_seconds, lthr, avg_hr, activity_type, hr_zone_weights):
    """
    Calculates Heart Rate-based Training Stress Score (HRTSS).
    Uses a simplified model based on average HR and LTHR.
    """
    if lthr == 0 or duration_seconds == 0 or avg_hr is None:
        return 0

    # Common exponents for IF_HR (adjust if needed for specific sport science models)
    if activity_type == "Run":
        if_hr_exponent = 1.28
    elif activity_type == "Cycle":
        if_hr_exponent = 1.98 # For HR-based cycling, power is preferred
    else:
        if_hr_exponent = 1.5 # Default for other activities

    # IF_HR = (Average HR / LTHR) ^ exponent
    if_hr = (avg_hr / lthr) ** if_hr_exponent

    # HRTSS = (duration_seconds * IF_HR^2) / 3600 * 100
    hr_tss_score = (duration_seconds * (if_hr ** 2)) / 3600 * 100
    return hr_tss_score

def calculate_pace_tss(duration_seconds, avg_pace_min_per_km, threshold_pace_min_per_km):
    """Calculates Training Stress Score (TSS) for pace-based activities (e.g., running)."""
    if threshold_pace_min_per_km == 0 or avg_pace_min_per_km is None or avg_pace_min_per_km == 0 or duration_seconds == 0:
        return 0

    # Intensity Factor for pace: IF = Threshold Pace / Average Pace (lower number = faster pace)
    intensity_factor = threshold_pace_min_per_km / avg_pace_min_per_km

    # TSS = (duration_seconds * IF^2) / 3600 * 100
    tss = (duration_seconds * (intensity_factor ** 2)) / 3600 * 100
    return tss

def get_mets_from_pace(activity_type, pace_min_per_km, met_values_by_pace):
    """
    Looks up an estimated MET value based on activity type and pace.
    Pace is expected in min/km. Lower pace_min_per_km means faster speed.
    """
    if activity_type not in met_values_by_pace:
        print(f"Warning: No MET pace data for activity type: {activity_type}")
        return None

    # Sort the MET ranges by pace_max_min_per_km in ascending order (slowest pace first)
    # This ensures we pick the highest applicable MET for a given pace range.
    sorted_paces = sorted(met_values_by_pace[activity_type], key=lambda x: x["pace_max_min_per_km"], reverse=True)

    # Iterate from slowest to fastest pace to find the appropriate MET
    for entry in sorted_paces:
        if pace_min_per_km >= entry["pace_max_min_per_km"]: # Pace is slower or equal to this max pace
            return entry["mets"]

    # If pace is faster than the fastest defined pace, return the highest MET value
    # for that activity type or a default.
    return sorted_paces[-1]["mets"] if sorted_paces else None


def calculate_total_calories_burned_mets(activity_type, duration_minutes, weight_kg, avg_pace_min_per_km, met_values_by_pace):
    """
    Calculates total calories burned using METs based on activity type and pace.
    """
    if weight_kg == 0 or duration_minutes == 0:
        return 0

    met = get_mets_from_pace(activity_type, avg_pace_min_per_km, met_values_by_pace)

    if met is None:
        return 0 # Could not determine MET for this activity

    # Formula: Calories = (METs * 3.5 * weight_kg * duration_minutes) / 200
    calories = (met * 3.5 * weight_kg * duration_minutes) / 200
    return calories

def calculate_fat_calories_burned(total_calories, avg_hr, max_hr):
    """
    Estimates fat calories burned based on total calories and HR intensity.
    """
    if total_calories == 0 or max_hr == 0:
        return 0

    fat_percentage = 0.0
    hr_percentage_of_max = (avg_hr / max_hr) if max_hr > 0 else 0

    if hr_percentage_of_max < FAT_BURN_HR_ZONE_LOWER_PERCENT: # Very light
        fat_percentage = FAT_PERCENTAGE_IN_VERY_LIGHT_ZONE
    elif hr_percentage_of_max >= FAT_BURN_HR_ZONE_LOWER_PERCENT and \
         hr_percentage_of_max <= FAT_BURN_HR_ZONE_UPPER_PERCENT: # Fat burn zone
        fat_percentage = FAT_PERCENTAGE_IN_FAT_BURN_ZONE
    elif hr_percentage_of_max > FAT_BURN_HR_ZONE_UPPER_PERCENT: # Moderate to High
        fat_percentage = FAT_PERCENTAGE_IN_HIGH_ZONE # Could differentiate more here

    fat_calories = total_calories * fat_percentage
    return fat_calories

def calculate_grams_fat_burned(fat_calories):
    """Converts fat calories to grams of fat (1 gram fat ~ 9 calories)."""
    return fat_calories / 9.0

# --- 3. Recommendation Generation Function ---

def generate_recommendation(recovery_score, fatigue_level):
    """Generates a personalized activity recommendation."""
    if recovery_score >= 70 and fatigue_level <= 30:
        return "Your body shows good recovery. You can likely proceed with your planned activities."
    elif 50 <= recovery_score < 70 and 30 < fatigue_level <= 60:
        return "Your recovery is moderate. Consider a balanced day with moderate activity and listen to your body."
    elif recovery_score < 50 or fatigue_level > 60:
        return "Your body may need more rest. Consider limiting strenuous activities and prioritize recovery."
    else:
        return "Unable to determine recommendation based on current data. Please review your metrics."

# --- 4. Email Reporting Function ---

def send_email_report(recipient_email, subject, body, sender_email, sender_password, smtp_server, smtp_port):
    """Sends the daily report via email."""
    if not sender_password:
        print("Error: Email password not set. Cannot send email.")
        return

    message = MIMEText(body)
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email report sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- Main Script Execution ---

def generate_daily_health_report():
    today = date.today()
    yesterday = today - timedelta(days=1) # For overnight data (e.g., Garmin sleep/BB)

    print(f"Generating daily health report for {today.strftime('%Y-%m-%d')}...")

    # --- Fetch Data ---
    hrv_data = fetch_hrv_data(HRV_DB_PATH, today)
    garmin_sleep_stress_data = fetch_garmin_sleep_stress_data(GARMIN_DB_PATH, yesterday) # Sleep is from yesterday night
    garmin_activities_today = fetch_garmin_activity_data(GARMIN_DB_PATH, today)

    if not hrv_data:
        print("Warning: Could not retrieve HRV data for today. Calculations may be incomplete.")
        hrv_data = {"hrv": 0, "rmssd": 0, "sdnn": 0} # Default to zero to avoid errors
    if not garmin_sleep_stress_data:
        print("Warning: Could not retrieve Garmin sleep/stress data for yesterday. Calculations may be incomplete.")
        # Default to neutral values to avoid errors and allow other calculations
        garmin_sleep_stress_data = {
            "sleep_score": 75, "deep_sleep": 0, "rem_sleep": 0,
            "stress_avg": 30, "spo2_min": 95, "rhr": 60,
            "bb_start": 50, "bb_end": 50,
        }

    # --- Calculate Core Metrics ---
    recovery_score = calculate_recovery_score(
        hrv_data, garmin_sleep_stress_data, YOUR_BASELINE_HRV_HIGH, YOUR_BASELINE_RHR_LOW,
        WEIGHT_HRV, WEIGHT_SLEEP, WEIGHT_RHR, WEIGHT_BB
    )
    sleep_charge = calculate_sleep_charge(garmin_sleep_stress_data)
    recovery_ratio = calculate_recovery_ratio(hrv_data, garmin_sleep_stress_data)

    # --- Calculate Training Load and Fat Burn Metrics ---
    total_daily_tss = 0
    total_daily_garmin_load = 0
    total_calories_burned_today = 0
    total_fat_calories_burned_today = 0
    total_grams_fat_burned_today = 0

    for activity in garmin_activities_today:
        activity_tss = 0
        activity_type = activity.get("activity_type")
        duration_seconds = activity.get("duration_seconds", 0)
        avg_hr = activity.get("avg_hr")
        normalized_power = activity.get("normalized_power")
        avg_pace_min_per_km = activity.get("avg_pace_min_per_km")
        garmin_load = activity.get("training_load_garmin", 0)

        # Calculate TSS based on activity type and available data
        if activity_type == "Cycle" and normalized_power is not None:
            activity_tss = calculate_power_tss(duration_seconds, normalized_power, YOUR_FTP_WATTS)
        elif activity_type == "Run" and avg_pace_min_per_km is not None:
            activity_tss = calculate_pace_tss(duration_seconds, avg_pace_min_per_km, YOUR_THRESHOLD_PACE_MIN_PER_KM)
        elif avg_hr is not None: # Fallback for other activities or if specific data is missing
            activity_tss = calculate_hr_tss(duration_seconds, YOUR_LTHR_BPM, avg_hr, activity_type, HR_ZONE_WEIGHTS)

        total_daily_tss += activity_tss
        total_daily_garmin_load += garmin_load

        # Calculate Calories and Fat Burn for Run/Walk activities
        if activity_type in ["Run", "Walk"]:
            duration_minutes = duration_seconds / 60.0
            current_activity_calories = calculate_total_calories_burned_mets(
                activity_type, duration_minutes, YOUR_WEIGHT_KG, avg_pace_min_per_km, MET_VALUES_BY_PACE
            )
            total_calories_burned_today += current_activity_calories

            current_activity_fat_calories = calculate_fat_calories_burned(
                current_activity_calories, avg_hr, YOUR_MAX_HR
            )
            total_fat_calories_burned_today += current_activity_fat_calories
            total_grams_fat_burned_today += calculate_grams_fat_burned(current_activity_fat_calories)


    # Calculate Fatigue Level (after TSS is known)
    fatigue_level = calculate_fatigue_level(recovery_score, garmin_sleep_stress_data, total_daily_tss)

    # --- Generate Recommendation ---
    recommendation = generate_recommendation(recovery_score, fatigue_level)

    # --- Construct Email Body ---
    report_body = f"""
Daily Health & Recovery Report - {today.strftime("%Y-%m-%d")}

---
**Recovery & Readiness**
Recovery Score: **{recovery_score:.2f}** / 100
Fatigue Level: **{fatigue_level:.2f}** / 100
Sleep Charge: {sleep_charge:.2f} / 100
Recovery Ratio (RMSSD/RHR): {recovery_ratio:.2f}

---
**Training Metrics**
Total Daily Training Stress Score (TSS): {total_daily_tss:.2f}
Total Daily Garmin Training Load: {total_daily_garmin_load:.2f} (from Garmin's proprietary calculation)
Total Calories Burned (Run/Walk): {total_calories_burned_today:.2f} kcal
Total Fat Calories Burned (Run/Walk): {total_fat_calories_burned_today:.2f} kcal
Total Fat Burned (Grams): {total_grams_fat_burned_today:.2f} grams

---
**Raw Data Summary (from {yesterday.strftime("%Y-%m-%d")} for sleep/stress, {today.strftime("%Y-%m-%d")} for HRV/Activities)**
Morning HRV (RMSSD): {hrv_data.get('rmssd', 'N/A')} (HRV: {hrv_data.get('hrv', 'N/A')}, SDNN: {hrv_data.get('sdnn', 'N/A')})
Sleep Score: {garmin_sleep_stress_data.get('sleep_score', 'N/A')}
Deep Sleep: {garmin_sleep_stress_data.get('deep_sleep', 'N/A')} seconds
REM Sleep: {garmin_sleep_stress_data.get('rem_sleep', 'N/A')} seconds
Average Stress: {garmin_sleep_stress_data.get('stress_avg', 'N/A')}
Min SpO2: {garmin_sleep_stress_data.get('spo2_min', 'N/A')}
Resting HR: {garmin_sleep_stress_data.get('rhr', 'N/A')}
Body Battery (Start/End): {garmin_sleep_stress_data.get('bb_start', 'N/A')} / {garmin_sleep_stress_data.get('bb_end', 'N/A')}
Activities Today:
"""

    if garmin_activities_today:
        for i, activity in enumerate(garmin_activities_today):
            report_body += f"- Activity {i+1}: {activity.get('activity_type', 'N/A')}, Duration: {activity.get('duration_seconds', 'N/A')}s, Avg HR: {activity.get('avg_hr', 'N/A')}bpm, Pace: {activity.get('avg_pace_min_per_km', 'N/A')} min/km\n"
    else:
        report_body += "- No activities recorded today.\n"

    report_body += f"""
---
**Daily Recommendation:** {recommendation}

Please remember this report is for informational purposes and should not replace professional medical advice.
"""

    # --- Send Email ---
    send_email_report(RECIPIENT_EMAIL, "Daily Health & Recovery Report", report_body,
                      SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT)

# --- Call Example (How you would run the system) ---
if __name__ == "__main__":
    # IMPORTANT: Before running, make sure to:
    # 1. Replace placeholder paths for HRV_DB_PATH and GARMIN_DB_PATH.
    # 2. Set your personal baselines (YOUR_BASELINE_HRV_HIGH, YOUR_BASELINE_RHR_LOW, etc.).
    # 3. Set your email SENDER_EMAIL, RECIPIENT_EMAIL, SMTP_SERVER, SMTP_PORT.
    # 4. Set your email password as an environment variable named EMAIL_PASSWORD.
    #    (e.g., on Linux/macOS: export EMAIL_PASSWORD="your_password")
    #    (e.g., on Windows (in cmd): set EMAIL_PASSWORD="your_password")
    #    For production, consider a more robust secret management solution.

    # This function will execute the entire process
    generate_daily_health_report()