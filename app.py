import os
import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI-Powered Fitness Tracker", page_icon="💪", layout="centered")
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0">', unsafe_allow_html=True)
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

st.title("🌟 AI-Powered Fitness Tracker")
st.subheader("Track your daily activity, predict your calorie burn, and compare your performance with others.")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE")
    )

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS calories (id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(255) NOT NULL, date DATE NOT NULL, calories FLOAT NOT NULL, UNIQUE(username, date), FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE)")
    conn.commit()
    conn.close()

initialize_db()

def get_daily_report(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, calories FROM calories WHERE username = %s ORDER BY date ASC", (username,))
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows, columns=["Date", "Calories"]) if rows else None

DATASET_FILE = "activity_data_heartrate.csv"

def load_dataset():
    df = pd.read_csv(DATASET_FILE)
    df.rename(columns={"HeartRate": "Heart_rate"}, inplace=True)
    return df

def train_model():
    df = load_dataset()
    X = df[["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate"]]
    y = df["Calories"]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

model = train_model()

def register_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
        conn.commit()
        return "Registration successful!"
    except mysql.connector.IntegrityError:
        return "Username already exists!"
    finally:
        conn.close()

def user_exists(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0

def update_calories(username, pre_calories, update_option="Replace"):
    pre_calories = float(pre_calories)
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT calories FROM calories WHERE username = %s AND date = %s", (username, today))
    result = cursor.fetchone()
    if result:
        current_calories = result[0]
        if update_option == "Replace":
            new_calories = pre_calories
        else:
            new_calories = current_calories + pre_calories
        cursor.execute("UPDATE calories SET calories = %s WHERE username = %s AND date = %s", (new_calories, username, today))
    else:
        new_calories = pre_calories
        cursor.execute("INSERT INTO calories (username, date, calories) VALUES (%s, %s, %s)", (username, today, new_calories))
    conn.commit()
    conn.close()
    return new_calories

def check_calories_exist(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT calories FROM calories WHERE username = %s AND date = %s", (username, today))
    result = cursor.fetchone()
    conn.close()
    return result is not None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "show_update_options" not in st.session_state:
    st.session_state.show_update_options = False
if "calories_updated" not in st.session_state:
    st.session_state.calories_updated = False
if "new_calories" not in st.session_state:
    st.session_state.new_calories = None
if "update_message" not in st.session_state:
    st.session_state.update_message = ""

if not st.session_state.logged_in:
    if st.session_state.page == "Login":
        st.subheader("🔐 Login")
        with st.form(key="login_form"):
            username = st.text_input("Username")
            login_button = st.form_submit_button("Login")
            switch_to_register = st.form_submit_button("Don't have an account? Register")
        if login_button:
            if user_exists(username):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ User not found! Please register.")
        if switch_to_register:
            st.session_state.page = "Register"
            st.rerun()
    elif st.session_state.page == "Register":
        st.subheader("📝 Register")
        new_user = st.text_input("Choose a Username")
        if st.button("✅ Register"):
            msg = register_user(new_user)
            st.success(msg)
        if st.button("🔙 Already have an account? Login here"):
            st.session_state.page = "Login"
            st.rerun()
else:
    menu = st.sidebar.selectbox("Menu", ["🏠 Dashboard", "📊 Daily Report", "🏆 Top Users", "🚪 Logout"])
    if menu == "🚪 Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.success("Logged out successfully!")
        st.rerun()
    elif menu == "🏠 Dashboard":
        st.subheader(f"Welcome, {st.session_state.username}!")
        st.sidebar.header("User Input Parameters")
        steps = st.sidebar.number_input("Total Steps", min_value=0, value=0)
        distance = st.sidebar.number_input("Total Distance (km)", min_value=0.0, value=0.0)
        active_minutes = st.sidebar.number_input("Total Active Minutes", min_value=0, value=0)
        heart_rate = st.sidebar.number_input("Heart Rate", min_value=40, max_value=200, value=40)
        st.session_state.total_steps = steps
        st.session_state.total_distance = distance
        st.session_state.total_active_minutes = active_minutes
        st.session_state.heart_rate = heart_rate
        if st.button("Predict Calories"):
            input_data = pd.DataFrame([[steps, distance, active_minutes, heart_rate]], columns=["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate"])
            predicted = float(model.predict(input_data)[0])
            st.success(f"You have burned {predicted:.2f} predicted calories!")
            if check_calories_exist(st.session_state.username):
                st.session_state.new_calories = predicted
                st.session_state.show_update_options = True
                st.session_state.calories_updated = False
                st.info("Calories for today already logged. Please choose an option to update your record.")
            else:
                new_cal = update_calories(st.session_state.username, predicted, update_option="Replace")
                st.success(f"Recorded calories: {new_cal:.2f} for today!")
            df_activity = load_dataset()
            if len(df_activity) > 0:
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
                st.info("Fitness activity data is not available at the moment.")
        if st.session_state.get("show_update_options", False) and not st.session_state.get("calories_updated", False):
            with st.form(key="update_form"):
                st.write("Update Options:")
                update_option = st.radio("How would you like to update your calories for today?", ["Replace", "Add"], key="update_option")
                submitted = st.form_submit_button("Confirm Update")
                if submitted:
                    new_total = update_calories(st.session_state.username, st.session_state.new_calories, update_option=update_option)
                    st.session_state.update_message = f"Calories updated successfully using option: {update_option}. New total: {new_total:.2f}"
                    st.session_state.show_update_options = False
                    st.session_state.calories_updated = True
            if st.session_state.get("update_message"):
                st.success(st.session_state.update_message)
    elif menu == "📊 Daily Report":
        st.subheader("Your Daily Report")
        report = get_daily_report(st.session_state.username)
        if report is not None:
            st.dataframe(report)
        else:
            st.info("No data available yet.")
    elif menu == "🏆 Top Users":
        st.subheader("Top Users")
        conn = get_db_connection()
        cursor = conn.cursor()
        today = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT u.username, COALESCE(c.calories, 0) AS calories FROM users u LEFT JOIN calories c ON u.username = c.username AND c.date = %s ORDER BY calories DESC LIMIT 50", (today,))
        top_users = cursor.fetchall()
        conn.close()
        if top_users:
            st.info(f"Top 50 users on {today}")
            st.dataframe(pd.DataFrame(top_users, columns=["Username", "Calories"]))
        else:
            st.info("No data available for today.")
