# hotel_review_app_topN_slider.py
import streamlit as st
import pandas as pd
import os
import glob
import json
import plotly.express as px
from io import BytesIO
from zipfile import ZipFile

# --- Helper Functions ---
def load_json_files(folder_path="scrap_out"):
    return glob.glob(os.path.join(folder_path, "*.json"))

def load_reviews_from_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    hotel_info = {
        "hotel_id": data.get("id"),
        "hotel_name": data.get("name"),
        "hotel_town": data.get("town")
    }
    reviews = data.get("scrap", {}).get("reviews", [])
    for r in reviews:
        r.update(hotel_info)
    df = pd.DataFrame(reviews)
    return df

def filter_reviews(df, guest_types, room_names):
    if guest_types:
        df = df[df["guest_type"].isin(guest_types)]
    if room_names and "room_name" in df.columns:
        df = df[df["room_name"].isin(room_names)]
    return df

def get_topic_counts_stacked(df, as_percentage=False, top_n=10):
    df_filtered = df.copy()
    total_reviews = len(df_filtered) if as_percentage else 1
    
    # Handle empty dataframe or missing columns
    if df_filtered.empty or "positive_topics" not in df_filtered.columns:
        pos = pd.Series(dtype=str)
    else:
        pos = df_filtered["positive_topics"].explode().dropna()
        
    if df_filtered.empty or "negative_topics" not in df_filtered.columns:
        neg = pd.Series(dtype=str)
    else:
        neg = df_filtered["negative_topics"].explode().dropna()
    
    pos_df = pd.DataFrame({
        "topic": pos,
        "count": 1 / total_reviews if as_percentage else 1,
        "sentiment": "Positive"
    })
    neg_df = pd.DataFrame({
        "topic": neg,
        "count": -1 / total_reviews if as_percentage else -1,
        "sentiment": "Negative"
    })
    
    stacked_df = pd.concat([pos_df, neg_df], ignore_index=True)
    if stacked_df.empty:
        return pd.DataFrame(columns=["topic", "sentiment", "count"])
    
    summary = stacked_df.groupby(["topic", "sentiment"])["count"].sum().reset_index()
    
    # Keep only top N topics by absolute count
    total_counts = summary.groupby("topic")["count"].apply(lambda x: x.abs().sum())
    top_topics = total_counts.nlargest(top_n).index
    summary = summary[summary["topic"].isin(top_topics)]
    
    if as_percentage:
        summary["count"] = summary["count"] * 100  # convert to %
    
    return summary

def generate_stacked_bar_chart(topic_summary):
    if topic_summary.empty:
        return None
    fig = px.bar(
        topic_summary,
        x="topic",
        y="count",
        color="sentiment",
        color_discrete_map={"Positive": "green", "Negative": "red"},
        title="Stacked Topic Counts by Sentiment"
    )
    fig.update_layout(barmode="relative")
    return fig

def bulk_export_topic_csvs(filtered_topic_dfs, filenames):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zip_file:
        for df, name in zip(filtered_topic_dfs, filenames):
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            zip_file.writestr(f"{name}_topic_counts.csv", csv_bytes)
    buffer.seek(0)
    return buffer

# --- Streamlit App ---
st.set_page_config(page_title="Hotel Review Analyzer - Top N Topics", layout="wide")
st.title("🏨 Hotel Review Analyzer (Guest + Room Name Filter, Top N Topics)")

# --- File Selection ---
json_files = load_json_files("scrap_out")
selected_file = st.sidebar.selectbox("Select JSON file (or 'All')", ["All"] + json_files)

# --- Load selected JSON for dynamic filters ---
if selected_file != "All":
    df_selected = load_reviews_from_json(selected_file)
else:
    df_selected = pd.DataFrame()

# --- Dynamic Filters ---
if not df_selected.empty:
    guest_types = st.sidebar.multiselect(
        "Guest Type",
        options=df_selected["guest_type"].dropna().unique(),
    )
    room_names = st.sidebar.multiselect(
        "Room Name",
        options=df_selected["room_name"].dropna().unique() if "room_name" in df_selected.columns else [],
    )
else:
    guest_types = st.sidebar.multiselect("Guest Type", options=[])
    room_names = st.sidebar.multiselect("Room Name", options=[])

# Option to display/export as ratio
as_ratio = st.sidebar.checkbox("Export/Display bar chart as % ratio", value=False)

# --- Slider for top N topics ---
top_n = st.sidebar.slider("Top N Topics", min_value=1, max_value=50, value=25, step=1)

# --- Processing ---
if selected_file == "All":
    filtered_topic_dfs = []
    file_names = []
    for file_path in json_files:
        df = load_reviews_from_json(file_path)
        df_filtered = filter_reviews(df, guest_types, room_names)
        topic_summary = get_topic_counts_stacked(df_filtered, as_percentage=as_ratio, top_n=top_n)
        filtered_topic_dfs.append(topic_summary)
        file_names.append(os.path.splitext(os.path.basename(file_path))[0])
    
    st.subheader("Bulk Export")
    st.write("Apply filters to all JSON files and download a ZIP of topic counts CSVs")
    if st.button("📥 Download ZIP of Topic Counts CSVs"):
        zip_buffer = bulk_export_topic_csvs(filtered_topic_dfs, file_names)
        st.download_button("Download ZIP", zip_buffer, "topic_counts.zip", mime="application/zip")
else:
    filtered_df = filter_reviews(df_selected, guest_types, room_names)
    st.subheader(f"Filtered Reviews for Hotel: {df_selected['hotel_name'].iloc[0] if not df_selected.empty else 'N/A'}")
    st.write(f"Total reviews after filtering: {len(filtered_df)}")
    
    # --- Display filtered reviews table ---
    with st.expander("Show Filtered Reviews Table"):
        st.dataframe(filtered_df)
    
    # --- Stacked bar chart ---
    topic_summary = get_topic_counts_stacked(filtered_df, as_percentage=as_ratio, top_n=top_n)
    fig = generate_stacked_bar_chart(topic_summary)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No topics found for the selected filters.")
    
    # --- CSV export of topic counts ---
    csv_data = topic_summary.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Topic Counts as CSV",
        csv_data,
        "topic_counts.csv",
        mime="text/csv"
    )
