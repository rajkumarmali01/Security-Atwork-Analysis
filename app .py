import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Report", layout="wide")
st.title("🏢 Attendance Report - Seating & Visitors")

st.write("Upload **Seating** and **Security Punch** CSV files to get:")
st.markdown("- ✅ Employees with Days Visited")
st.markdown("- 👥 Visitors not in seating")

# Upload files
seating_file = st.file_uploader("📌 Upload AtWork Seating CSV", type="csv", key="seating")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv", key="security")

if seating_file and security_file:
    seating_df = pd.read_csv(seating_file)
    security_df = pd.read_csv(security_file)

    try:
        # Clean and prepare
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()
        seating_df['Employee ID'] = seating_df['Employee ID'].astype(str).str.strip()

        # 🧮 Count Days Visited by Cardholder ID
        days_count = security_df.groupby('Cardholder')['Date'].nunique().reset_index()
        days_count.columns = ['Employee ID', 'Days_Visited']

        # ✅ Merge with Seating
        seating_with_days = pd.merge(seating_df, days_count, on='Employee ID', how='left')
        seating_with_days['Days_Visited'] = seating_with_days['Days_Visited'].fillna(0).astype(int)

        st.subheader("✅ Seating with Days Visited")
        st.dataframe(seating_with_days)

        seating_csv = seating_with_days.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Seating + Days CSV", seating_csv, "Seating_with_Days.csv", "text/csv")

        # 👤 Visitor-Only List
        seating_ids = set(seating_df['Employee ID'].astype(str))
        visitor_ids = set(security_df['Cardholder'].astype(str))
        only_visitors = visitor_ids - seating_ids

        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)].copy()
        visitor_df = visitor_df[['Cardholder', 'First name', 'Last name', 'Date']].drop_duplicates()

        # Add Days Visited for each visitor
        visitor_days = visitor_df.groupby('Cardholder')['Date'].nunique().reset_index()
        visitor_days.columns = ['Cardholder', 'Days_Visited']
        visitor_df = pd.merge(visitor_df, visitor_days, on='Cardholder', how='left')

        st.subheader("🕵️‍♂️ Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_df)

        visitor_csv = visitor_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Visitor-Only CSV", visitor_csv, "Visitor_Only_List.csv", "text/csv")

        # 💾 Combined Excel Download (optional)
        output_path = "/tmp/attendance_report.xlsx"
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            seating_with_days.to_excel(writer, index=False, sheet_name="Seating + Days")
            visitor_df.to_excel(writer, index=False, sheet_name="Visitor Only")

        with open(output_path, "rb") as f:
            st.download_button("📥 Download Combined Excel Report", f, file_name="Attendance_Report.xlsx")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")