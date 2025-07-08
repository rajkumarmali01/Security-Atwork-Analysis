import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Report", layout="wide")
st.title("🏢 Attendance Report - Daily Summary & Visitors")

st.write("Upload the latest **Seating** and **Security Punch** CSV files to get:")
st.markdown("- 📆 **Daily Attendance Summary** (Total employees present each day)")
st.markdown("- 🕵️ **Visitor-Only List** (People not in Seating)")

# Upload files
seating_file = st.file_uploader("📌 Upload AtWork Seating CSV", type="csv", key="seating")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv", key="security")

if seating_file and security_file:
    seating_df = pd.read_csv(seating_file)
    security_df = pd.read_csv(security_file)

    try:
        # Clean and prepare data
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()
        seating_df['Employee ID'] = seating_df['Employee ID'].astype(str).str.strip()

        # ✅ Output 1: Daily Attendance Summary
        daily_attendance = security_df[['Cardholder', 'Date']].drop_duplicates()
        attendance_by_date = daily_attendance.groupby('Date').size().reset_index(name='Total_Employees_Present')
        attendance_by_date = attendance_by_date.sort_values(by='Date')

        st.subheader("📆 Daily Attendance Summary")
        st.dataframe(attendance_by_date)

        daily_csv = attendance_by_date.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Daily Attendance CSV", daily_csv, "Daily_Attendance_Summary.csv", "text/csv")

        # ✅ Output 2: Visitor-Only List
        seating_ids = set(seating_df['Employee ID'].astype(str))
        visitor_ids = set(security_df['Cardholder'].astype(str))
        only_visitors = visitor_ids - seating_ids

        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)].copy()
        visitor_df = visitor_df[['Cardholder', 'First name', 'Last name', 'Date']].drop_duplicates()

        # Add Days Visited for visitors
        visitor_days = visitor_df.groupby('Cardholder')['Date'].nunique().reset_index()
        visitor_days.columns = ['Cardholder', 'Days_Visited']
        visitor_df = pd.merge(visitor_df, visitor_days, on='Cardholder', how='left')

        st.subheader("🕵️ Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_df)

        visitor_csv = visitor_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Visitor-Only CSV", visitor_csv, "Visitor_Only_List.csv", "text/csv")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")