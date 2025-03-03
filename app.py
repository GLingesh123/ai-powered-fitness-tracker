import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor

DATA_FILE = "fitness_data.csv"
DATASET_FILE = "activity_data_heartrate.csv"

# Username validation: must contain at least one alphanumeric character.
def is_valid_username(username):
    if not username:
        return False
    username = username.strip()
    return bool(re.search(r"[A-Za-z0-9]", username))

# Session state initialization.
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

# Functions for ML model using the activity dataset for calorie prediction.
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
    X = df[["TotalSteps", "TotalDistance", "TotalActiveMinutes", "Heart_rate"]]
    y = df["Calories"]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    try:
        model.fit(X, y)
    except Exception as e:
        st.error(f"Error training model: {e}")
    return model

model = train_model()

# For comparing fitness stats, we load the activity dataset.
def load_fitness():
    return load_dataset()

# Functions for CSV-based user & daily data handling.
def load_data():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        return pd.DataFrame(columns=["Username"])
    df = pd.read_csv(DATA_FILE, dtype={"Username": str})
    df["Username"] = df["Username"].fillna("").astype(str)
    if df["Username"].str.strip().eq("").all():
        return pd.DataFrame(columns=["Username"])
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def register_user(username):
    if not is_valid_username(username):
        return "Enter a valid username!"
    df = load_data()
    if username.strip() in df["Username"].values:
        return "Username already exists!"
    new_user = pd.DataFrame([[username.strip()]], columns=["Username"])
    df = pd.concat([df, new_user], ignore_index=True)
    save_data(df)
    return "Registration successful!"

def update_calories(username, calories, update_option="Replace"):
    df = load_data()
    today = datetime.today().strftime('%Y-%m-%d')
    if today not in df.columns:
        df[today] = 0
    if username in df["Username"].values:
        current_value = df.loc[df["Username"] == username, today].iloc[0]
        try:
            current_value = float(current_value)
        except:
            current_value = 0.0
        updated_value = calories if update_option == "Replace" or pd.isnull(current_value) or current_value == 0 else current_value + calories
        df.loc[df["Username"] == username, today] = updated_value
    else:
        new_row = pd.DataFrame({"Username": [username], today: [calories]})
        df = pd.concat([df, new_row], ignore_index=True)
        updated_value = calories
    save_data(df)
    return updated_value

def get_top_users():
    df = load_data()
    today = datetime.today().strftime('%Y-%m-%d')
    if today in df.columns:
        top_users = df[["Username", today]].sort_values(by=today, ascending=False).head(50)
        top_users = top_users.reset_index(drop=True)
        return top_users
    return None

st.set_page_config(
    page_title="AI-Powered Fitness Tracker",
    page_icon="💪",
    layout="centered",
    
)
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

# UI: Login/Registration and Navigation.
if not st.session_state.logged_in:
    if st.session_state.page == "Login":
        st.subheader("🔐 Login")
        with st.form(key="login_form"):
            username = st.text_input("Username")
            login_button = st.form_submit_button("Login")
            switch_to_register = st.form_submit_button("Don't have an account? Register")
        if login_button:
            if not is_valid_username(username):
                st.error("Enter a valid username!")
            else:
                data = load_data()
                if username.strip() in data["Username"].values:
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip()
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
            data = load_data()
            today = datetime.today().strftime('%Y-%m-%d')
            if today in data.columns and st.session_state.username in data["Username"].values:
                st.session_state.new_calories = predicted
                st.session_state.show_update_options = True
                st.session_state.calories_updated = False
                st.info("Calories for today already logged. Please choose an option to update your record.")
            else:
                new_cal = update_calories(st.session_state.username, predicted, update_option="Replace")
                st.success(f"Recorded calories: {new_cal:.2f} for today!")
            
            # Display fitness statistics compared to the activity dataset.
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
        
        if st.session_state.get("show_update_options", False) and not st.session_state.get("calories_updated", False):
            with st.form(key="update_form"):
                st.write("Update Options:")
                update_option = st.radio(
                    "How would you like to update your calories for today?",
                    options=["Replace", "Add"],
                    key="update_option"
                )
                col1, col2 = st.columns(2)
                submit_button = col1.form_submit_button("Confirm Update")
                cancel_button = col2.form_submit_button("Cancel")
                if submit_button:
                    new_total = update_calories(
                        st.session_state.username,
                        st.session_state.new_calories,
                        update_option=update_option
                    )
                    st.session_state.update_message = (
                        f"Calories updated successfully using option: {update_option}. New total: {new_total:.2f}"
                    )
                    st.session_state.show_update_options = False
                    st.session_state.calories_updated = True
                elif cancel_button:
                    st.session_state.show_update_options = False
        if st.session_state.get("update_message", ""):
            st.success(st.session_state.update_message)
    elif menu == "📊 Daily Report":
        st.subheader("Your Daily Report")
        data = load_data()
        user_data = data[data["Username"] == st.session_state.username]
        if not user_data.empty:
            user_long = user_data.drop(columns=["Username"]).melt(var_name="Date", value_name="Calories")
            user_long = user_long[user_long["Date"] != "registered"].sort_values("Date")
            st.dataframe(user_long)
        else:
            st.info("No data available yet.")
    elif menu == "🏆 Top Users":
        st.subheader("Top Users")
        top_users = get_top_users()
        if top_users is not None:
            st.dataframe(top_users)
        else:
            st.info("No data available for today.")
