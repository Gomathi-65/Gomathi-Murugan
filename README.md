SecureCheck - Police Stop Log Dashboard

SecureCheck is a Streamlit-based dashboard for managing, analyzing, and predicting traffic stop data. It connects to a MySQL database to track police stops, generate insights, and predict likely outcomes.

Features
- Real-time dashboard displaying arrests, searches, and stop data.
- Quick search by vehicle number.
- Advanced SQL-based insights and analytics.
- Predict stop outcome and violation type using past records.

Tech Stack
- Frontend: Streamlit
- Backend: Python (Pandas, SQLAlchemy)
- Database: MySQL

Setup
1. Clone the repository:
  git clone https://github.com/Gomathi-65/Gomathi-Murugan.git
   cd securecheck

2. Install dependencies:
   pip install -r requirements.txt

3. Run the app:
   streamlit run app.py

Database
Create a table named traffic_stops in MySQL with columns:
stop_date, stop_time, country_name, driver_gender, driver_age, violation, search_conducted, is_arrested, drugs_related_stop, vehicle_number.

Prediction Mode
The app predicts:
- Stop outcome
- Likely violation type
based on previously recorded stops.
