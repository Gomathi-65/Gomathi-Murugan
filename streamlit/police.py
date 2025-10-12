import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

username = 'root'
password = '5555'
host = '127.0.0.1'
port = '3306'
database = 'traffic_logs'
engine = create_engine(f'mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}')

@st.cache_data
def fetch_one(query):
    df = pd.read_sql(query, engine)
    return df.iloc[0, 0] if not df.empty else None

@st.cache_data
def fetch_df(query):
    return pd.read_sql(query, engine)

st.set_page_config(page_title="SecureCheck Police Dashboard", layout="wide")
st.title("SecureCheck Police Stop Log Dashboard")

col1, col2, col3, col4 = st.columns(4)
with col1:
    total_stops = fetch_one("SELECT COUNT(*) FROM traffic_stops;")
    st.metric("Total Traffic Stops", total_stops)
with col2:
    arrests = fetch_one("SELECT COUNT(*) FROM traffic_stops WHERE is_arrested = 1;")
    st.metric("Total Arrests", arrests)
with col3:
    drugs = fetch_one("SELECT COUNT(*) FROM traffic_stops WHERE drugs_related_stop = 1;")
    st.metric("Drug-Related Stops", drugs)
with col4:
    searches = fetch_one("SELECT COUNT(*) FROM traffic_stops WHERE search_conducted = 1;")
    st.metric("Searches Conducted", searches)

st.divider()

# Do NOT cache the fetch for latest logs so it always shows the newest data
def fetch_recent():
    query = """
        SELECT stop_id, stop_date, stop_time, country_name, driver_gender,
               violation, search_conducted, is_arrested, drugs_related_stop, vehicle_number
        FROM traffic_stops ORDER BY created_at DESC LIMIT 10;
    """
    return pd.read_sql(query, engine)

st.subheader("Recent Traffic Stops (Latest 10)")
recent = fetch_recent()
st.dataframe(recent, hide_index=True, use_container_width=True)
st.divider()

# Quick Search
st.subheader("Quick Search")
with st.form("quicksearchform"):
    search_vnum = st.text_input("Vehicle Number")
    search_gender = st.selectbox("Driver Gender", ["Any", "M", "F"])
    quick_search_btn = st.form_submit_button("Search")
if quick_search_btn:
    q = "SELECT * FROM traffic_stops WHERE 1=1"
    if search_vnum:
        q += f" AND vehicle_number LIKE '%{search_vnum}%'"
    if search_gender != "Any":
        q += f" AND driver_gender = '{search_gender}'"
    res = fetch_df(q + " ORDER BY created_at DESC LIMIT 20")
    st.write(f"Results for vehicle: {search_vnum}, gender: {search_gender}")
    if not res.empty:
        st.dataframe(res, use_container_width=True)
    else:
        st.info("No matching records found.")

st.divider()

# Add new log
st.subheader("Add New Police Log")
with st.form("add_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.text_input("Stop Time (HH:MM:SS)", "12:00:00")
    country = st.text_input("Country Name")
    driver_gender = st.selectbox("Driver Gender", ["M", "F"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100)
    violation = st.text_input("Violation")
    search = st.selectbox("Search Conducted", [0, 1])
    arrest = st.selectbox("Arrested", [0, 1])
    drugs = st.selectbox("Drugs Related Stop", [0, 1])
    vnum = st.text_input("Vehicle Number")
    log_btn = st.form_submit_button("Add Log")
if log_btn:
    insert_q = text(
        "INSERT INTO traffic_stops (stop_date, stop_time, country_name, driver_gender, driver_age, violation, "
        "search_conducted, is_arrested, drugs_related_stop, vehicle_number) "
        "VALUES (:stop_date, :stop_time, :country, :driver_gender, :driver_age, :violation, "
        ":search, :arrest, :drugs, :vnum)"
    )
    try:
        with engine.begin() as conn:
            conn.execute(insert_q, {
                "stop_date": stop_date,
                "stop_time": stop_time,
                "country": country,
                "driver_gender": driver_gender,
                "driver_age": int(driver_age),
                "violation": violation,
                "search": int(search),
                "arrest": int(arrest),
                "drugs": int(drugs),
                "vnum": vnum
            })
        st.session_state['log_added_success'] = True
        st.rerun()  # This refreshes the entire app and shows most recent logs!
    except Exception as e:
        st.error(f"Failed to add log: {e}")

if st.session_state.get('log_added_success', False):
    st.success("Log added successfully!")


st.divider()

# Advanced Insights
st.subheader("Advanced Insights")
query_options = {
    "Top 10 Vehicles with Drug-Related Stops": """
        SELECT vehicle_number, COUNT(*) AS count FROM traffic_stops
        WHERE drugs_related_stop = 1 GROUP BY vehicle_number
        ORDER BY count DESC LIMIT 10;
    """,
    "Most Searched Vehicles": """
        SELECT vehicle_number, COUNT(*) AS count FROM traffic_stops
        WHERE search_conducted = 1 GROUP BY vehicle_number
        ORDER BY count DESC LIMIT 10;
    """,
    "Arrest Rate by Age Group": """
        SELECT
            CASE WHEN driver_age < 25 THEN 'Under 25'
                 WHEN driver_age BETWEEN 25 AND 35 THEN '25-35'
                 WHEN driver_age BETWEEN 36 AND 50 THEN '36-50'
                 ELSE 'Over 50' END AS age_group,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
            ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate
        FROM traffic_stops WHERE driver_age IS NOT NULL
        GROUP BY age_group
        ORDER BY arrest_rate DESC;
    """,
    "Gender/Race Breakdowns": """
        SELECT driver_gender, driver_race, COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests
        FROM traffic_stops
        GROUP BY driver_gender, driver_race
        ORDER BY total_stops DESC;
    """,
    "Time-Based Insights (Most Stops by Hour)": """
        SELECT HOUR(stop_time) AS hour, COUNT(*) AS total_stops
        FROM traffic_stops
        GROUP BY hour
        ORDER BY total_stops DESC
        LIMIT 5;
    """,
    "Country-wise/Violation Analytics": """
        SELECT country_name, violation, COUNT(*) AS stop_count,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests
        FROM traffic_stops
        GROUP BY country_name, violation
        ORDER BY stop_count DESC
        LIMIT 10;
    """
}
selected_query = st.selectbox("Select an insight to run", list(query_options.keys()))
if st.button("Run Query"):
    result_df = fetch_df(query_options[selected_query])
    if not result_df.empty:
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("No results found for this query.")

st.divider()

# Predict outcome
st.subheader("Predict Stop Outcome (Likelihood)")
with st.form("predict_form"):
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100)
    driver_gender = st.selectbox("Driver Gender", ["M", "F"])
    violation = st.text_input("Violation Type")
    country_name = st.text_input("Country")
    submit = st.form_submit_button("Predict Outcome Likelihood")
if submit:
    query = f"""
        SELECT COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
        SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS total_searches
        FROM traffic_stops
        WHERE driver_age = {driver_age} AND driver_gender = '{driver_gender}'
        AND violation = '{violation}' AND country_name = '{country_name}'
    """
    stats = fetch_df(query)
    if not stats.empty and stats.iloc[0]['total_stops'] > 0:
        stop_count = stats.iloc[0]['total_stops']
        arrest_rate = round((stats.iloc[0]['total_arrests'] / stop_count) * 100, 2) if stop_count else 0
        search_rate = round((stats.iloc[0]['total_searches'] / stop_count) * 100, 2) if stop_count else 0
        st.success(
            f"Out of {stop_count} similar stops: Arrest Rate = {arrest_rate}%, Search Rate = {search_rate}%"
        )
    else:
        st.info("No similar records found. Try adjusting your input.")