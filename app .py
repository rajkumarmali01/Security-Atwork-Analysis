import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Analysis", layout="wide")
st.title("🏢 Atwork Employee Attendance Analyzer")

st.write("Upload Seating and Security (Punch In/Out) files to analyze attendance patterns.")

seating_file = st.file_uploader("📌 Upload Seating CSV", type="csv", key="seating")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv", key="security")

if seating_file and security_file:
    seating_df = pd.read_csv(seating_file)
    security_df = pd.read_csv(security_file)

    try:
        # 🛠️ Preprocessing
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()
        seating_df['EMPLOYEE ID(Security)'] = seating_df['EMPLOYEE ID(Security)'].astype(str).str.strip()

        # 1️⃣ Days Visited per Employee
        days_count = security_df.groupby('Cardholder')['Date'].nunique().reset_index()
        days_count.columns = ['EMPLOYEE ID(Security)', 'Days_Visited']

        # Add to seating
        seating_with_days = pd.merge(seating_df, days_count, on='EMPLOYEE ID(Security)', how='left')
        seating_with_days['Days_Visited'] = seating_with_days['Days_Visited'].fillna(0).astype(int)

        # 2️⃣ Visitors not in Seating
        seating_ids = set(seating_df['EMPLOYEE ID(Security)'].astype(str))
        visitor_ids = set(security_df['Cardholder'].astype(str))

        only_visitors = visitor_ids - seating_ids
        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)].copy()
        visitor_df = visitor_df[['Cardholder', 'First name', 'Last name', 'Date']]
        visitor_df = visitor_df.drop_duplicates()

        # 3️⃣ Overall Summary
        total_employees = len(seating_df)
        total_visitor_only = len(only_visitors)
        total_unique_attendees = security_df['Cardholder'].nunique()
        most_frequent = security_df['Cardholder'].value_counts().head(5)

        st.subheader("📊 Overall Summary")
        st.markdown(f"👩‍💼 Total Employees in Seating File: `{total_employees}`")
        st.markdown(f"🚶‍♂️ Visitors Only (Not in Seating): `{total_visitor_only}`")
        st.markdown(f"📅 Unique Cardholders from Security: `{total_unique_attendees}`")
        st.markdown("🔥 **Top 5 Most Frequent Visitors:**")
        st.dataframe(most_frequent.rename_axis("Cardholder").reset_index(name="Punch Count"))

        st.subheader("✅ Seating with Days Visited")
        st.dataframe(seating_with_days)

        st.subheader("🕵️‍♂️ Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_df)

        # 💾 Downloadable Outputs
        output = pd.ExcelWriter("/tmp/attendance_analysis.xlsx", engine='xlsxwriter')
        seating_with_days.to_excel(output, index=False, sheet_name="Seating + Days")
        visitor_df.to_excel(output, index=False, sheet_name="Visitor Only")
        summary_df = pd.DataFrame({
            "Metric": ["Total Seating Employees", "Visitor Only", "Unique Cardholders"],
            "Value": [total_employees, total_visitor_only, total_unique_attendees]
        })
        summary_df.to_excel(output, index=False, sheet_name="Summary")
        output.save()

        with open("/tmp/attendance_analysis.xlsx", "rb") as f:
            st.download_button("📥 Download Full Excel Report", f, file_name="Attendance_Analysis.xlsx")

    except Exception as e:
        st.error(f"Error processing files: {e}")