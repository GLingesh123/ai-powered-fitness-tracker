import streamlit as st
import pandas as pd
import sqlite3
import os
import re
import hashlib
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor

DB_FILE = "fitness_data.db"
DATASET_FILE = "activity_data_heartrate.csv"

def is_valid_username(username):
    if not username:
        return False
    username = username.strip()
    return bool(re.search(r"[A-Za-z0-9]", username))

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS daily_data (username TEXT, date TEXT, calories REAL, PRIMARY KEY (username, date), FOREIGN KEY (username) REFERENCES users(username))""")
    conn.commit()
    return conn

conn = init_db()

def load_dataset():
    try:
        df = pd.read_csv(DATASET_FILE)
        df.rename(columns={"HeartRate": "Heart_rate"}, inplace=True)
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        df = pd.DataFrame(columns=["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate", "Calories"])
    return df

def train_model():
    df = load_dataset()
    if df.empty:
        st.error("Activity dataset is empty. Cannot train model.")
        return None
    try:
        X = df[["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate"]]
        y = df["Calories"]
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
    except Exception as e:
        st.error(f"Error training model: {e}")
        model = None
    return model

model = train_model()

def load_fitness():
    return load_dataset()

def register_user_db(username, password):
    if not is_valid_username(username):
        return "Enter a valid username!"
    try:
        cursor = conn.cursor()
        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username.strip(), hashed_pw))
        conn.commit()
        return "Registration successful!"
    except sqlite3.IntegrityError:
        return "Username already exists!"
    except Exception as e:
        return f"Registration failed: {e}"

def authenticate_user(username, password):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username.strip(),))
        row = cursor.fetchone()
        if row:
            stored_hashed = row[0]
            if stored_hashed == hash_password(password):
                return True
        return False
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False

def update_calories_db(username, calories, update_option="Replace"):
    today = datetime.today().strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute("SELECT calories FROM daily_data WHERE username = ? AND date = ?", (username, today))
    row = cursor.fetchone()
    if row:
        current_value = row[0] if row[0] is not None else 0.0
        try:
            updated_value = calories if update_option == "Replace" or current_value == 0 else current_value + calories
        except:
            updated_value = calories
        cursor.execute("UPDATE daily_data SET calories = ? WHERE username = ? AND date = ?", (updated_value, username, today))
    else:
        updated_value = calories
        cursor.execute("INSERT INTO daily_data (username, date, calories) VALUES (?, ?, ?)", (username, today, calories))
    conn.commit()
    return updated_value

def get_top_users_db():
    today = datetime.today().strftime('%Y-%m-%d')
    query = "SELECT username, calories FROM daily_data WHERE date = ? ORDER BY calories DESC LIMIT 50"
    top_users = pd.read_sql_query(query, conn, params=(today,))
    return top_users

def get_daily_report_db(username):
    query = "SELECT date, calories FROM daily_data WHERE username = ? ORDER BY date"
    report = pd.read_sql_query(query, conn, params=(username,))
    return report

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "new_calories" not in st.session_state:
    st.session_state.new_calories = 0.0
if "calories_updated" not in st.session_state:
    st.session_state.calories_updated = False
if "show_update_options" not in st.session_state:
    st.session_state.show_update_options = False
if "update_message" not in st.session_state:
    st.session_state.update_message = ""
if "total_steps" not in st.session_state:
    st.session_state.total_steps = 0
if "total_distance" not in st.session_state:
    st.session_state.total_distance = 0.0
if "total_active_minutes" not in st.session_state:
    st.session_state.total_active_minutes = 0
if "heart_rate" not in st.session_state:
    st.session_state.heart_rate = 40

st.set_page_config(page_title="AI-Powered Fitness Tracker", page_icon="💪", layout="centered")
st.title("🌟 AI-Powered Fitness Tracker")
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0">', unsafe_allow_html=True)
st.subheader("Track your daily activity, predict your calorie burn, and compare your performance with others.")

st.markdown(
    """
    <style>
    @media (prefers-color-scheme: dark) {
        .stApp { background-color: #1e1e1e; color: #ffffff; }
        .block-container { color: #ffffff; }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .stMarkdown p, .stMarkdown li { color: #ffffff; }
        .css-1d391kg { background-color: #333333; color: #ffffff; }
    }
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; max-width: 100% !important; }
        .stButton>button { padding: 0.8rem 1.2rem; font-size: 1.1rem; }
        .stTextInput>div>input { font-size: 1.1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.logged_in:
    if st.session_state.page == "Login":
        st.subheader("🔐 Login")
        with st.form(key="login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            switch_to_register = st.form_submit_button("Don't have an account? Register")
        if login_button:
            if not is_valid_username(username):
                st.error("Enter a valid username!!")
            else:
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
        if switch_to_register:
            st.session_state.page = "Register"
            st.rerun()
    elif st.session_state.page == "Register":
        st.subheader("📝 Register")
        with st.form(key="register_form"):
            new_user = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("✅ Register")
        if register_button:
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            else:
                msg = register_user_db(new_user, new_password)
                if "successful" in msg:
                    st.success(msg)
                else:
                    st.error(msg)
        if st.button("🔙 Already have an account? Login here"):
            st.session_state.page = "Login"
            st.rerun()
else:
    menu = st.sidebar.selectbox("Menu", ["🏠 Dashboard", "📊 Daily Report", "🏆 Top Users", "📝 Activity History", "🔑 Change Password", "🚪 Logout"])
    if menu == "🚪 Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.new_calories = 0.0
        st.session_state.calories_updated = False
        st.session_state.show_update_options = False
        st.session_state.update_message = ""
        st.success("Logged out successfully!")
        st.rerun()
    elif menu == "🏠 Dashboard":
        st.subheader(f"Welcome, {st.session_state.username}!")
        st.sidebar.header("User Input Parameters")
        steps = st.sidebar.slider("Total Steps", min_value=0, max_value=100000, value=0, step=100)
        distance = st.sidebar.slider("Total Distance (km)", min_value=0.0, max_value=50.0, value=0.0, step=0.1)
        active_minutes = st.sidebar.slider("Total Active Minutes", min_value=0, max_value=300, value=0, step=1)
        heart_rate = st.sidebar.slider("Heart Rate", min_value=40, max_value=200, value=40, step=1)
        st.session_state.total_steps = steps
        st.session_state.total_distance = distance
        st.session_state.total_active_minutes = active_minutes
        st.session_state.heart_rate = heart_rate
        if st.button("Predict Calories"):
            input_data = pd.DataFrame([[steps, distance, active_minutes, heart_rate]], columns=["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate"])
            if model:
                predicted = float(model.predict(input_data)[0])
                st.success(f"You have burned {predicted:.2f} predicted calories!")
                cursor = conn.cursor()
                today = datetime.today().strftime('%Y-%m-%d')
                cursor.execute("SELECT calories FROM daily_data WHERE username = ? AND date = ?", (st.session_state.username, today))
                row = cursor.fetchone()
                if row:
                    st.session_state.new_calories = predicted
                    st.session_state.show_update_options = True
                    st.session_state.calories_updated = False
                    st.info("Calories for today already logged. Please choose an option to update your record.")
                else:
                    new_cal = update_calories_db(st.session_state.username, predicted, update_option="Replace")
                    st.success(f"Recorded calories: {new_cal:.2f} for today!")
                df_activity = load_fitness()
                if not df_activity.empty:
                    st.subheader("Your Fitness Stats Compared to Others")
                    heart_rate_percent = round((sum(df_activity["Heart_rate"] < st.session_state.heart_rate) / len(df_activity)) * 100, 2)
                    st.write(f"Your heart rate is higher than {heart_rate_percent}% of other people.")
                    steps_percent = round((sum(df_activity["TotalSteps"] < st.session_state.total_steps) / len(df_activity)) * 100, 2)
                    st.write(f"Your steps count is higher than {steps_percent}% of other people.")
                    distance_percent = round((sum(df_activity["TotalDistance"] < st.session_state.total_distance) / len(df_activity)) * 100, 2)
                    st.write(f"Your total distance is higher than {distance_percent}% of other people.")
                    active_minutes_percent = round((sum(df_activity["TotalActiveMinutes"] < st.session_state.total_active_minutes) / len(df_activity)) * 100, 2)
                    st.write(f"Your total active minutes are higher than {active_minutes_percent}% of other people.")
            else:
                st.error("Model is not available.")
        if st.session_state.get("show_update_options", False) and not st.session_state.get("calories_updated", False):
            with st.form(key="update_form"):
                st.write("Update Options:")
                update_option = st.radio("How would you like to update your calories for today?", options=["Replace", "Add"], key="update_option")
                col1, col2 = st.columns(2)
                submit_button = col1.form_submit_button("Confirm Update")
                cancel_button = col2.form_submit_button("Cancel")
                if submit_button:
                    new_total = update_calories_db(st.session_state.username, st.session_state.new_calories, update_option=update_option)
                    st.session_state.update_message = f"Calories updated successfully using option: {update_option}. New total: {new_total:.2f}"
                    st.session_state.show_update_options = False
                    st.session_state.calories_updated = True
                elif cancel_button:
                    st.session_state.show_update_options = False
        if st.session_state.get("update_message", ""):
            st.success(st.session_state.update_message)
    elif menu == "📊 Daily Report":
        st.subheader("Your Daily Report")
        report = get_daily_report_db(st.session_state.username)
        if not report.empty:
            st.dataframe(report)
            chart_data = report.copy()
            chart_data['date'] = pd.to_datetime(chart_data['date'])
            chart_data = chart_data.sort_values('date').set_index('date')
            st.line_chart(chart_data['calories'])
        else:
            st.info("No data available yet.")
    elif menu == "🏆 Top Users":
        st.subheader("Top Users")
        top_users = get_top_users_db()
        if not top_users.empty:
            st.dataframe(top_users)
        else:
            st.info("No data available for today.")
    elif menu == "📝 Activity History":
        st.subheader("Your Activity History")
        report = get_daily_report_db(st.session_state.username)
        if not report.empty:
            st.dataframe(report)
        else:
            st.info("No activity history available.")
    elif menu == "🔑 Change Password":
        st.subheader("Change Your Password")
        with st.form(key="change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input("Confirm New Password", type="password")
            cp_submit = st.form_submit_button("Change Password")
        if cp_submit:
            if not authenticate_user(st.session_state.username, current_password):
                st.error("Current password is incorrect.")
            elif new_password != confirm_new_password:
                st.error("New passwords do not match.")
            else:
                try:
                    cursor = conn.cursor()
                    hashed_new = hash_password(new_password)
                    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_new, st.session_state.username))
                    conn.commit()
                    st.success("Password changed successfully.")
                except Exception as e:
                    st.error(f"Failed to change password: {e}")
