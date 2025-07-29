import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="Atwork Attendance Analyzer", layout="wide")
st.title("🏢 Atwork Employee Attendance Analyzer")

# Upload files
seating_file = st.file_uploader("Upload Atwork Seating CSV", type="csv")
punch_file = st.file_uploader("Upload Punch In/Out CSV", type="csv")

if seating_file and punch_file:
    try:
        # Manual decoding for seating file
        seating_text = seating_file.read().decode("latin1")
        seating_df = pd.read_csv(StringIO(seating_text))
        seating_df.columns = seating_df.columns.str.strip()

        # Manual decoding for punch file
        punch_text = punch_file.read().decode("latin1")
        punch_df = pd.read_csv(StringIO(punch_text))
        punch_df.columns = punch_df.columns.str.strip()

        # Standardize names and timestamps
        seating_df["Employee ID"] = seating_df["Employee ID"].astype(str).str.strip()
        seating_df["Employee Name"] = seating_df["Employee Name"].astype(str).str.strip()
        punch_df["Cardholder"] = punch_df["Cardholder"].astype(str).str.strip()
        punch_df["Event timestamp"] = pd.to_datetime(punch_df["Event timestamp"], errors="coerce")
        punch_df = punch_df.dropna(subset=["Event timestamp"])
        punch_df["Date"] = punch_df["Event timestamp"].dt.date

        # Get in-time and out-time by day
        first_last = punch_df.groupby(["Cardholder", "Date"]).agg(
            In_Time=("Event timestamp", "min"),
            Out_Time=("Event timestamp", "max")
        ).reset_index()
        first_last["Visit"] = 1

        # Count Days Visited
        visit_count = first_last.groupby("Cardholder")["Visit"].sum().reset_index(name="Days_Visited")

        # Date mapping
        date_map = first_last.groupby("Cardholder")["Date"].apply(lambda x: ", ".join(sorted(x.astype(str)))).reset_index(name="Date_List")

        # Merge visit_count and date_map
        summary_df = seating_df.copy()
        summary_df = summary_df.merge(visit_count, how="left", left_on="Employee Name", right_on="Cardholder")
        summary_df = summary_df.merge(date_map, how="left", left_on="Employee Name", right_on="Cardholder")
        summary_df.drop(columns=["Cardholder_x", "Cardholder_y"], errors="ignore", inplace=True)
        summary_df["Days_Visited"] = summary_df["Days_Visited"].fillna(0).astype(int)
        summary_df["Date"] = summary_df["Date_List"].fillna("")
        summary_df.drop(columns=["Date_List"], inplace=True)

        st.subheader("📘 Seating with Days Visited and Dates")
        st.dataframe(summary_df)
        st.download_button("⬇️ Download Seating_Daily_Visits", data=summary_df.to_csv(index=False), file_name="Seating_Daily_Visits.csv")

        # Visitor-Only (not in seating)
        known_names = set(seating_df["Employee Name"])
        visitor_only = first_last[~first_last["Cardholder"].isin(known_names)].copy()
        visitor_only.rename(columns={"Cardholder": "Visitor Name"}, inplace=True)

        st.subheader("🛂 Visitor Only List (Not in Seating File)")
        st.dataframe(visitor_only)
        st.download_button("⬇️ Download Visitor_Only_List", data=visitor_only.to_csv(index=False), file_name="Visitor_Only_List.csv")

        # Daily Attendance Bifurcation
        all_punch = first_last.copy()
        all_punch["Type"] = all_punch["Cardholder"].apply(lambda x: "Atwork Employee" if x in known_names else "Visitor")
        attendance_summary = all_punch.groupby(["Date", "Type"]).size().unstack(fill_value=0).reset_index()
        if "Atwork Employee" not in attendance_summary.columns:
            attendance_summary["Atwork Employee"] = 0
        if "Visitor" not in attendance_summary.columns:
            attendance_summary["Visitor"] = 0

        st.subheader("📊 Daily Attendance Bifurcation (Atwork vs Visitor)")
        st.dataframe(attendance_summary)
        st.download_button("⬇️ Download Daily_Attendance_Bifurcation", data=attendance_summary.to_csv(index=False), file_name="Daily_Attendance_Bifurcation.csv")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")