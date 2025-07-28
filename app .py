import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Attendance Analysis", layout="wide")
st.title("🏢 AtWork Attendance Analyzer")

st.write("Upload **Seating File** and **Security Punch File** to generate attendance analytics.")

# Upload files
seating_file = st.file_uploader("📌 Upload AtWork Seating CSV", type="csv")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv")

if seating_file and security_file:
    try:
        # 🧹 Read files using decoding workaround
        seating_content = seating_file.read().decode("utf-8", errors="ignore")
        seating_df = pd.read_csv(io.StringIO(seating_content))

        security_content = security_file.read().decode("utf-8", errors="ignore")
        security_df = pd.read_csv(io.StringIO(security_content))

        # ✅ Clean and format
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()
        seating_df['Employee ID'] = seating_df['Employee ID'].astype(str).str.strip()

        # ✅ Output 1: Seating with Daily Visit Records + Days_Visited + Date
        visits = security_df[['Cardholder', 'Date']].drop_duplicates()
        visits.columns = ['Employee ID', 'Date']

        days_visited = visits.groupby('Employee ID').size().reset_index(name='Days_Visited')
        merged_df = pd.merge(seating_df, days_visited, on='Employee ID', how='left')
        merged_df['Days_Visited'] = merged_df['Days_Visited'].fillna(0).astype(int)

        visits_full = pd.merge(visits, seating_df, on='Employee ID', how='inner')
        merged_df = pd.merge(merged_df, visits, on='Employee ID', how='left')
        merged_df['Date'] = merged_df['Date'].where(merged_df['Days_Visited'] > 0, '')

        merged_df = merged_df.drop_duplicates(subset=['Employee ID', 'Date'])
        merged_df = merged_df.sort_values(by=['Date', 'Employee ID'])

        st.subheader("✅ 1. Seating with Daily Visit Records")
        st.dataframe(merged_df)

        seating_csv = merged_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Seating Daily Visits CSV", seating_csv, "Seating_Daily_Visits.csv", "text/csv")

        # ✅ Output 2: Visitor-Only List (Not in Seating)
        seating_ids = set(seating_df['Employee ID'].astype(str))
        visitor_ids = set(security_df['Cardholder'].astype(str))
        only_visitors = visitor_ids - seating_ids

        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)].copy()
        visitor_df = visitor_df[['Cardholder', 'First name', 'Last name', 'Date']].drop_duplicates()

        visitor_days = visitor_df.groupby('Cardholder')['Date'].nunique().reset_index()
        visitor_days.columns = ['Cardholder', 'Days_Visited']
        visitor_df = pd.merge(visitor_df, visitor_days, on='Cardholder', how='left')

        st.subheader("🕵️‍♂️ 2. Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_df)

        visitor_csv = visitor_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Visitor-Only CSV", visitor_csv, "Visitor_Only_List.csv", "text/csv")

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
        st.download_button("📥 Download Daily Summary CSV", summary_csv, "Daily_Attendance_Bifurcation.csv", "text/csv")

        # ✅ Excel Report Export
        output_path = "/tmp/full_attendance_report.xlsx"
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            merged_df.to_excel(writer, index=False, sheet_name="Seating Daily Visits")
            visitor_df.to_excel(writer, index=False, sheet_name="Visitor Only")
            daily_summary.to_excel(writer, index=False, sheet_name="Daily Summary")

        with open(output_path, "rb") as f:
            st.download_button("📦 Download Full Excel Report", f, "Full_Attendance_Report.xlsx")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")