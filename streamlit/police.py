import streamlit as st
import pandas as pd
import pymysql

# Database connection
def create_connection():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='123456',
            database='traffic_logs',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

# Fetch data from DB
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()

# Load all data for predictions
data = fetch_data("SELECT * FROM traffic_stops;")


st.set_page_config(page_title="SecureCheck Police Dashboard", layout="wide")
st.title("SecureCheck Police Stop Log Dashboard")


col1, col2, col3, col4 = st.columns(4)

# Total Traffic Stops
total_stops_query = "SELECT COUNT(*) AS total FROM traffic_stops;"
total_stops_df = fetch_data(total_stops_query)
total_stops = int(total_stops_df['total'][0]) if not total_stops_df.empty else 0
with col1:
    st.metric("Total Traffic Stops", total_stops)

# Total Arrests
arrests_query = "SELECT COUNT(*) AS total FROM traffic_stops WHERE is_arrested = 1;"
arrests_df = fetch_data(arrests_query)
arrests = int(arrests_df['total'][0]) if not arrests_df.empty else 0
with col2:
    st.metric("Total Arrests", arrests)

# Drug Related Stops
drugs_query = "SELECT COUNT(*) AS total FROM traffic_stops WHERE drugs_related_stop = 1;"
drugs_df = fetch_data(drugs_query)
drugs = int(drugs_df['total'][0]) if not drugs_df.empty else 0
with col3:
    st.metric("Drug-Related Stops", drugs)

# Searches Conducted
searches_query = "SELECT COUNT(*) AS total FROM traffic_stops WHERE search_conducted = 1;"
searches_df = fetch_data(searches_query)
searches = int(searches_df['total'][0]) if not searches_df.empty else 0
with col4:
    st.metric("Searches Conducted", searches)

st.divider()

# Fetch ALL traffic stops
st.subheader("Logs Overview")
recent_query = """SELECT * from traffic_stops"""
recent = fetch_data(recent_query)
st.dataframe(recent, hide_index=True, use_container_width=True)

st.divider()

# Quick Search
st.subheader("Quick Search")
with st.form("quicksearchform"):
    search_vnum = st.text_input("Vehicle Number")
    quick_search_btn = st.form_submit_button("Search")

if quick_search_btn:
    q = "SELECT * FROM traffic_stops WHERE 1=1"
    if search_vnum:
        q += f" AND vehicle_number LIKE '%{search_vnum}%'"
    q += " ORDER BY stop_date DESC, stop_time DESC LIMIT 20"
    res = fetch_data(q)
    st.write(f"Results for vehicle: {search_vnum}")
    if not res.empty:
        st.dataframe(res, use_container_width=True)
    else:
        st.info("No matching records found.")

st.divider()

# Advanced Insights
st.subheader("Advanced Insights")

query_options = {
    "Top 10 Vehicles with Drug-Related Stops": """
        SELECT vehicle_number, COUNT(*) AS count FROM traffic_stops
        WHERE drugs_related_stop = 1 GROUP BY vehicle_number
        ORDER BY count DESC LIMIT 10;
    """,
    "Most Frequently Searched Vehicles": """
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
    "Search Rate by Gender & Race": """
        SELECT driver_gender, driver_race,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS Searched
        FROM traffic_stops
        GROUP BY driver_gender, driver_race
        ORDER BY Searched DESC;
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
    """,
    "Are stops during the night more likely to lead to arrests?": """
        SELECT 
            CASE 
                WHEN EXTRACT(HOUR FROM stop_time) BETWEEN 6 AND 18 THEN 'Day'
                ELSE 'Night'
            END AS time_period,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
            ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY time_period;
    """,
    "Which violations are most associated with searches or arrests?": """
        SELECT violation,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrests DESC, searches DESC;
    """,
    "Violations most common among younger drivers (<25)": """
        SELECT violation, COUNT(*) AS stop_count
        FROM traffic_stops
        WHERE driver_age < 25
        GROUP BY violation
        ORDER BY stop_count DESC;
    """,
    "Violation that rarely results in search or arrest": """
        SELECT violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
            ROUND((SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) + 
                   SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END)) * 100.0 / COUNT(*), 2) AS total_action_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY total_action_rate ASC
        LIMIT 5;
    """,
    "Countries with the highest rate of drug-related stops": """
        SELECT country_name,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) AS drug_stops,
            ROUND(SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS drug_stop_rate
        FROM traffic_stops
        GROUP BY country_name
        ORDER BY drug_stop_rate DESC;
    """,
    "Arrest rate by country_name and violation": """
        SELECT country_name, violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
            ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY country_name, violation
        ORDER BY arrest_rate DESC;
    """,
    "Which country has the most stops with searches conducted?": """
        SELECT country_name, COUNT(*) AS total_searches
        FROM traffic_stops
        WHERE search_conducted = 1
        GROUP BY country_name
        ORDER BY total_searches DESC;
    """
}

selected_query_1 = st.selectbox(
    "Select an insight to run", 
    list(query_options.keys()), 
    key="query_select_1"
)

if st.button("Run Query", key="run_query_1"):
    result_df = fetch_data(query_options[selected_query_1])
    if not result_df.empty:
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("No results found for this query.")

st.divider()

# Complex Query Insights
st.subheader("Complex Query Insights")
complex_query_options = {
    "Yearly Breakdown of Stops and Arrests by Country": """
        SELECT 
            country_name,
            YEAR(stop_date) AS year,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
            ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate,
            RANK() OVER (PARTITION BY country_name ORDER BY YEAR(stop_date)) AS year_rank
        FROM traffic_stops
        GROUP BY country_name, YEAR(stop_date)
        ORDER BY country_name, year;
    """,
    "Driver Violation Trends Based on Age and Race": """
        SELECT 
            t.driver_race,
            t.violation,
            AVG(sub.avg_age) AS avg_driver_age,
            COUNT(*) AS total_stops
        FROM traffic_stops t
        JOIN (
            SELECT driver_race, violation, AVG(driver_age) AS avg_age
            FROM traffic_stops
            WHERE driver_age IS NOT NULL
            GROUP BY driver_race, violation
        ) sub ON t.driver_race = sub.driver_race AND t.violation = sub.violation
        GROUP BY t.driver_race, t.violation
        ORDER BY total_stops DESC;
    """,
    "Time Period Analysis of Stops": """
        SELECT 
            YEAR(stop_date) AS year,
            MONTH(stop_date) AS month,
            HOUR(stop_time) AS hour,
            COUNT(*) AS total_stops
        FROM traffic_stops
        GROUP BY YEAR(stop_date), MONTH(stop_date), HOUR(stop_time)
        ORDER BY year, month, hour;
    """,
    "Violations with High Search and Arrest Rates": """
        SELECT 
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) AS searches,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS arrests,
            ROUND(SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS search_rate,
            ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate,
            RANK() OVER (ORDER BY SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) DESC) AS rank_by_arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrest_rate DESC;
    """,
    "Driver Demographics by Country (Age, Gender, and Race)": """
        SELECT 
            country_name,
            driver_gender,
            driver_race,
            ROUND(AVG(driver_age), 2) AS avg_age,
            COUNT(*) AS total_stops
        FROM traffic_stops
        WHERE driver_age IS NOT NULL
        GROUP BY country_name, driver_gender, driver_race
        ORDER BY country_name, total_stops DESC;
    """,
    "Top 5 Violations with Highest Arrest Rates": """
        SELECT 
            violation,
            COUNT(*) AS total_stops,
            SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) AS total_arrests,
            ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS arrest_rate
        FROM traffic_stops
        GROUP BY violation
        ORDER BY arrest_rate DESC
        LIMIT 5;
    """
}

selected_query_2 = st.selectbox(
    "Select a complex insight to run", 
    list(complex_query_options.keys()), 
    key="query_select_2"
)

if st.button("Run Query", key="run_query_2"):
    result_df = fetch_data(complex_query_options[selected_query_2])
    if not result_df.empty:
        st.dataframe(result_df, use_container_width=True)
    else:
        st.warning("No results found for this query.")

st.divider()

# Prediction form
st.subheader("Predict Stop Outcome and Violation")

with st.form("predict_log_form"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    county_name = st.text_input("County Name")
    driver_gender = st.selectbox("Driver Gender", ["male", "female"])
    driver_age = st.number_input("Driver Age", min_value=16, max_value=100, value=27)
    search_conducted = st.selectbox("Was a Search Conducted?", ["0", "1"])
    search_type = st.text_input("Search Type")
    drugs_related_stop = st.selectbox("Was it Drug Related?", ["0", "1"])
    stop_duration = st.selectbox("Stop Duration", data['stop_duration'].dropna().unique())
    vehicle_number = st.text_input("Vehicle Number")

    submitted = st.form_submit_button("Predict Stop Outcome & Violation")

    if submitted:
        filtered = data[
            (data['driver_gender'].str.lower() == driver_gender.lower()) &
            (data['driver_age'] == driver_age) &
            (data['search_conducted'] == int(search_conducted)) &
            (data['drugs_related_stop'] == int(drugs_related_stop)) &
            (data['stop_duration'] == stop_duration)
        ]

        if not filtered.empty:
            predicted_outcome = filtered['stop_outcome'].mode()[0] if 'stop_outcome' in filtered.columns else "warning"
            predicted_violation = filtered['violation'].mode()[0] if 'violation' in filtered.columns else "speeding"
        else:
            predicted_outcome = "warning"
            predicted_violation = "speeding"

        search_text = "A search was conducted" if int(search_conducted) else "No search was conducted"
        drug_text = "was drug-related" if int(drugs_related_stop) else "was not drug-related"

        st.markdown(f"""
        **Prediction Summary**

        - **Predicted Violation:** {predicted_violation}
        - **Predicted Stop Outcome:** {predicted_outcome}

        A {driver_age}-year-old {driver_gender} driver in {county_name} was stopped at 
        {stop_time.strftime('%I:%M %p')} on {stop_date}.  
        {search_text}, and the stop {drug_text}.  
        Stop duration: **{stop_duration}**  
        Vehicle Number: **{vehicle_number}**  
        """)
