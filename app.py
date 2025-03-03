import os
import streamlit as st
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(
    page_title="AI-Powered Fitness Tracker",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)
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

USERS_FILE = "users.csv"
USERS_COLS = ["username"]
FITNESS_FILE = "fitness_data.csv"
FITNESS_COLS = ["username", "date", "calories"]

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            df = pd.read_csv(USERS_FILE)
            if not set(USERS_COLS).issubset(df.columns):
                df = pd.DataFrame(columns=USERS_COLS)
                df.to_csv(USERS_FILE, index=False)
        except Exception:
            df = pd.DataFrame(columns=USERS_COLS)
            df.to_csv(USERS_FILE, index=False)
    else:
        df = pd.DataFrame(columns=USERS_COLS)
        df.to_csv(USERS_FILE, index=False)
    return df

def save_users(df):
    df.to_csv(USERS_FILE, index=False)

def register_user(username):
    df = load_users()
    if username in df["username"].unique():
        return "Username already exists!"
    else:
        new_row = {"username": username}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_users(df)
        return "Registration successful!"

def user_exists(username):
    df = load_users()
    return username in df["username"].unique()

def load_fitness():
    if os.path.exists(FITNESS_FILE):
        try:
            df = pd.read_csv(FITNESS_FILE)
            if not set(FITNESS_COLS).issubset(df.columns):
                df = pd.DataFrame(columns=FITNESS_COLS)
                df.to_csv(FITNESS_FILE, index=False)
        except Exception:
            df = pd.DataFrame(columns=FITNESS_COLS)
            df.to_csv(FITNESS_FILE, index=False)
    else:
        df = pd.DataFrame(columns=FITNESS_COLS)
        df.to_csv(FITNESS_FILE, index=False)
    return df

def save_fitness(df):
    df.to_csv(FITNESS_FILE, index=False)

def update_calories(username, pre_calories, update_option="Replace"):
    pre_calories = float(pre_calories)
    today = datetime.today().strftime('%Y-%m-%d')
    df = load_fitness()
    mask = (df["username"] == username) & (df["date"] == today)
    if mask.any():
        current_calories = float(df.loc[mask, "calories"].values[0])
        new_calories = pre_calories if update_option == "Replace" else current_calories + pre_calories
        df.loc[mask, "calories"] = new_calories
    else:
        new_calories = pre_calories
        new_row = {"username": username, "date": today, "calories": new_calories}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_fitness(df)
    return new_calories

def check_calories_exist(username):
    today = datetime.today().strftime('%Y-%m-%d')
    df = load_fitness()
    return ((df["username"] == username) & (df["date"] == today)).any()

def get_daily_report(username):
    df = load_fitness()
    report = df[df["username"] == username]
    if not report.empty:
        return report
    else:
        return None

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
            input_data = pd.DataFrame([[steps, distance, active_minutes, heart_rate]],
                                      columns=["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate"])
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
            df_activity = load_fitness()
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
        df = load_fitness()
        today = datetime.today().strftime('%Y-%m-%d')
        top_users_df = df[df["date"] == today]
        top_users = top_users_df.groupby("username", as_index=False)["calories"].sum().sort_values("calories", ascending=False).head(50)
        if not top_users.empty:
            st.info(f"Top 50 users on {today}")
            st.dataframe(top_users)
        else:
            st.info("No data available for today.")
