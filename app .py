import pandas as pd
import streamlit as st

st.set_page_config(page_title="Attendance Analysis", layout="wide")
st.title("🏢 AtWork Attendance Analyzer")
st.write("Upload **Seating File** and **Security Punch File** to generate attendance analytics.")

seating_file = st.file_uploader("📌 Upload AtWork Seating CSV", type="csv")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv")

if seating_file and security_file:
    try:
        # Read with encoding fallback
        try:
            seating_df = pd.read_csv(seating_file, encoding='utf-8')
        except:
            seating_df = pd.read_csv(seating_file, encoding='ISO-8859-1')

        try:
            security_df = pd.read_csv(security_file, encoding='utf-8')
        except:
            security_df = pd.read_csv(security_file, encoding='ISO-8859-1')

        # Clean
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()
        seating_df['Employee ID'] = seating_df['Employee ID'].astype(str).str.strip()

        # Output 1: Seating + Days_Visited (No Date)
        visits = security_df[['Cardholder', 'Date']].drop_duplicates()
        visits.columns = ['Employee ID', 'Date']
        days_visited = visits.groupby('Employee ID').size().reset_index(name='Days_Visited')
        seating_with_days = pd.merge(seating_df, days_visited, on='Employee ID', how='left')
        seating_with_days['Days_Visited'] = seating_with_days['Days_Visited'].fillna(0).astype(int)

        st.subheader("✅ 1. Seating with Days Visited")
        st.dataframe(seating_with_days)
        st.download_button("📥 Download Seating_Daily_Visits", 
                           seating_with_days.to_csv(index=False).encode('utf-8'), 
                           "Seating_Daily_Visits.csv", 
                           "text/csv")

        # Output 2: Visitors not in Seating + Days_Visited (No Date)
        seating_ids = set(seating_df['Employee ID'])
        visitor_ids = set(security_df['Cardholder'])
        only_visitors = visitor_ids - seating_ids

        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)][
            ['Cardholder', 'First name', 'Last name', 'Date']
        ].drop_duplicates()

        visitor_days = visitor_df.groupby('Cardholder')['Date'].nunique().reset_index()
        visitor_days.columns = ['Cardholder', 'Days_Visited']

        visitor_final = pd.merge(
            visitor_df[['Cardholder', 'First name', 'Last name']].drop_duplicates(),
            visitor_days,
            on='Cardholder',
            how='left'
        )

        st.subheader("🕵️‍♂️ 2. Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_final)
        st.download_button("📥 Download Visitor_Only_List", 
                           visitor_final.to_csv(index=False).encode('utf-8'), 
                           "Visitor_Only_List.csv", 
                           "text/csv")

        # Output 3: Daily Attendance Bifurcation (Only present users)
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
        st.download_button("📥 Download Daily_Attendance_Bifurcation", 
                           daily_summary.to_csv(index=False).encode('utf-8'), 
                           "Daily_Attendance_Bifurcation.csv", 
                           "text/csv")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")