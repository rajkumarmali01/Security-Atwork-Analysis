import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="AtWork Attendance Analyzer", layout="wide")
st.title("🏢 AtWork Attendance Analyzer")

# Upload Files
seating_file = st.file_uploader("📋 Upload AtWork Seating CSV", type="csv")
security_file = st.file_uploader("🔐 Upload Security Punch CSV", type="csv")

if seating_file and security_file:
    try:
        # Read and decode content safely (for special chars)
        seating_content = seating_file.read().decode("utf-8", errors="ignore")
        seating_df = pd.read_csv(io.StringIO(seating_content))

        security_content = security_file.read().decode("utf-8", errors="ignore")
        security_df = pd.read_csv(io.StringIO(security_content))

        # Clean security file
        security_df['Event timestamp'] = pd.to_datetime(security_df['Event timestamp'], errors='coerce')
        security_df['Date'] = security_df['Event timestamp'].dt.date
        security_df['Cardholder'] = security_df['Cardholder'].astype(str).str.strip()

        # Clean seating file
        seating_df['Employee ID'] = seating_df['Employee ID'].astype(str).str.strip()

        # Output 1: Seating + Days_Visited + Last Visit Date
        # Count unique days visited by each cardholder
        visits_df = security_df[['Cardholder', 'Date']].drop_duplicates()
        days_visited = visits_df.groupby('Cardholder').size().reset_index(name='Days_Visited')
        last_dates = visits_df.groupby('Cardholder')['Date'].max().reset_index(name='Last_Visit_Date')

        visit_summary = pd.merge(days_visited, last_dates, on='Cardholder', how='outer')

        # Merge visit summary into seating_df
        result_df = seating_df.copy()
        result_df = result_df.merge(visit_summary, how='left', left_on='Employee ID', right_on='Cardholder')

        result_df['Days_Visited'] = result_df['Days_Visited'].fillna(0).astype(int)
        result_df['Date'] = result_df['Last_Visit_Date'].fillna("").astype(str)

        # Drop the join helper column
        result_df.drop(columns=['Cardholder', 'Last_Visit_Date'], inplace=True)

        st.subheader("✅ 1. Seating with Visit Info (Preserved All Rows)")
        st.dataframe(result_df)
        st.download_button("📥 Download Seating Visit Info CSV", result_df.to_csv(index=False).encode('utf-8'), "Seating_Visit_Info.csv")

        # Output 2: Visitors Only (Not in Seating)
        seating_ids = set(seating_df['Employee ID'].astype(str))
        visitor_ids = set(security_df['Cardholder'].astype(str))
        only_visitors = visitor_ids - seating_ids

        visitor_df = security_df[security_df['Cardholder'].isin(only_visitors)].copy()
        visitor_df = visitor_df[['Cardholder', 'First name', 'Last name', 'Date']].drop_duplicates()

        visitor_days = visitor_df.groupby('Cardholder')['Date'].nunique().reset_index(name='Days_Visited')
        visitor_df = pd.merge(visitor_df, visitor_days, on='Cardholder', how='left')

        st.subheader("🕵️‍♂️ 2. Visitor-Only List (Not in Seating)")
        st.dataframe(visitor_df)
        st.download_button("📥 Download Visitor CSV", visitor_df.to_csv(index=False).encode('utf-8'), "Visitor_Only_List.csv")

        # Output 3: Daily Summary
        security_df['Employee Type'] = security_df['Cardholder'].apply(lambda x: "AtWork" if x in seating_ids else "Visitor")
        daily_summary = (
            security_df[['Cardholder', 'Date', 'Employee Type']]
            .drop_duplicates()
            .groupby(['Date', 'Employee Type'])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        daily_summary['Total_Employees_Present'] = daily_summary.get('AtWork', 0) + daily_summary.get('Visitor', 0)

        st.subheader("📆 3. Daily Attendance Summary")
        st.dataframe(daily_summary)
        st.download_button("📥 Download Daily Summary CSV", daily_summary.to_csv(index=False).encode('utf-8'), "Daily_Attendance_Summary.csv")

    except Exception as e:
        st.error(f"❌ Error: {e}")