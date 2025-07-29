import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Analysis", layout="wide")
st.title("🏢 AtWork Attendance Analyzer")

st.write("Upload **Seating File** and **Security Punch File** to generate attendance analytics.")

# Upload files
seating_file = st.file_uploader("📌 Upload AtWork Seating CSV", type="csv")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv")

# Function to read and handle file safely
def read_csv_safe(uploaded_file):
    try:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding='ISO-8859-1')

if seating_file and security_file:
    try:
        # ✅ Read files with fallback encoding
        seating_df = read_csv_safe(seating_file)
        security_df = read_csv_safe(security_file)

        # ✅ Standardize
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()
        seating_df['Employee ID'] = seating_df['Employee ID'].astype(str).str.strip()

        # ✅ Output 1: Seating with Days Visited
        visits = security_df[['Cardholder', 'Date']].drop_duplicates()
        visits.columns = ['Employee ID', 'Date']

        # Days visited count
        days_visited = visits.groupby('Employee ID').size().reset_index(name='Days_Visited')

        # Join visits with original seating
        seating_with_days = pd.merge(seating_df, days_visited, on='Employee ID', how='left')
        seating_with_days['Days_Visited'] = seating_with_days['Days_Visited'].fillna(0).astype(int)

        st.subheader("✅ 1. Seating with Days Visited")
        st.dataframe(seating_with_days)

        seating_csv = seating_with_days.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Seating_Daily_Visits.csv", seating_csv, file_name="Seating_Daily_Visits.csv")

        # ✅ Output 2: Visitor-Only List
        seating_ids = set(seating_df['Employee ID'].astype(str))
        visitor_ids = set(security_df['Cardholder'].astype(str))
        only_visitors = visitor_ids - seating_ids

        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)].copy()
        visitor_df = visitor_df[['Cardholder', 'First name', 'Last name', 'Date']].drop_duplicates()

        visitor_days = visitor_df.groupby('Cardholder')['Date'].nunique().reset_index()
        visitor_days.columns = ['Cardholder', 'Days_Visited']
        visitor_df = pd.merge(visitor_df.drop('Date', axis=1), visitor_days, on='Cardholder', how='left').drop_duplicates()

        st.subheader("🕵️‍♂️ 2. Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_df)

        visitor_csv = visitor_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Visitor_Only_List.csv", visitor_csv, file_name="Visitor_Only_List.csv")

        # ✅ Output 3: Daily Attendance Summary
        security_df['Employee Type'] = security_df['Cardholder'].apply(
            lambda x: "AtWork" if x in seating_ids else "Visitor"
        )

        daily_summary = (
            security_df[['Cardholder', 'Date', 'Employee Type']]
            .drop_duplicates()
            .groupby(['Date', 'Employee Type'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )

        daily_summary['Total_Employees_Present'] = daily_summary.get('AtWork', 0) + daily_summary.get('Visitor', 0)

        st.subheader("📆 3. Daily Attendance Summary (Bifurcation)")
        st.dataframe(daily_summary)

        summary_csv = daily_summary.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Daily_Attendance_Bifurcation.csv", summary_csv, file_name="Daily_Attendance_Bifurcation.csv")

        # ✅ Excel Export
        output_path = "/tmp/full_attendance_report.xlsx"
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            seating_with_days.to_excel(writer, index=False, sheet_name="Seating Daily Visits")
            visitor_df.to_excel(writer, index=False, sheet_name="Visitor Only")
            daily_summary.to_excel(writer, index=False, sheet_name="Daily Summary")

        with open(output_path, "rb") as f:
            st.download_button("📦 Download Full Excel Report", f, file_name="Full_Attendance_Report.xlsx")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")