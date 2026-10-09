import os
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# ==============================================================================
# Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="Composite Master Index: Global Country Rankings 2025",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# Data Loading from DuckDB
# ==============================================================================
@st.cache_data(ttl=60)
def load_data():
    db_path = os.path.join(os.path.dirname(__file__), "master_index.duckdb")
    if not os.path.exists(db_path):
        st.error(f"Database file not found at: {db_path}")
        return pd.DataFrame()
    
    con = duckdb.connect(db_path, read_only=True)
    try:
        query = "SELECT * FROM Global_Rankings;"
        df = con.execute(query).df()
    finally:
        con.close()
    return df


df = load_data()

# ==============================================================================
# Header & KPI Metrics
# ==============================================================================
st.markdown('<div class="main-header">🌍 Composite Master Index: Global Country Rankings 2025</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Aggregating 20 disparate socioeconomic, governance, peace, and development indices into a unified, polarity-corrected benchmark.</div>',
    unsafe_allow_html=True
)

if df.empty:
    st.warning("No data found in DuckDB database. Please run the ETL pipeline first.")
    st.stop()

# Key KPI summary
col1, col2, col3, col4 = st.columns(4)

top_country = df.iloc[0]["Country"]
top_score = df.iloc[0]["Total_Score"]
bottom_country = df.iloc[-1]["Country"]
bottom_score = df.iloc[-1]["Total_Score"]
avg_score = df["Total_Score"].mean()
total_nations = len(df)

with col1:
    st.metric("Total Nations Evaluated", f"{total_nations}")
with col2:
    st.metric("Top Ranked Country", f"{top_country}", f"{top_score:.2f} pts")
with col3:
    st.metric("Global Average Score", f"{avg_score:.2f} pts")
with col4:
    st.metric("Lowest Ranked Country", f"{bottom_country}", f"{bottom_score:.2f} pts")

st.divider()

# ==============================================================================
# Interactive Choropleth World Map
# ==============================================================================
st.subheader("🗺️ Global Total_Score Choropleth Heatmap")
st.caption("Interactive world map displaying the 0 - 100 Composite Total_Score by ISO-3 country code.")

fig = px.choropleth(
    df,
    locations="ISO_Code",
    color="Total_Score",
    hover_name="Country",
    hover_data={
        "Rank": True,
        "ISO_Code": True,
        "Total_Score": ":.2f",
    },
    color_continuous_scale="Viridis",
    range_color=(0, 100),
    labels={"Total_Score": "Total Score"},
    projection="natural earth"
)

fig.update_layout(
    margin=dict(l=0, r=0, t=20, b=0),
    geo=dict(
        showframe=False,
        showcoastlines=True,
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)"
    ),
    height=540,
    coloraxis_colorbar=dict(
        title="Score (0-100)",
        ticks="outside",
        thickness=15,
        len=0.75
    )
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==============================================================================
# Full Leaderboard Dataframe Table
# ==============================================================================
st.subheader("🏆 Global Rankings Leaderboard")
st.caption("Complete table of sovereign states sorted by Total_Score descending. Search, sort, or inspect sub-index dimensions.")

# Optional search and column selection
search_term = st.text_input("🔍 Search Country or ISO-3 Code", "")

filtered_df = df.copy()
if search_term.strip():
    term = search_term.strip().lower()
    filtered_df = filtered_df[
        filtered_df["Country"].str.lower().str.contains(term) |
        filtered_df["ISO_Code"].str.lower().str.contains(term)
    ]

# Display columns
display_cols = ["Rank", "ISO_Code", "Country", "Total_Score"]
additional_cols = [c for c in filtered_df.columns if c not in display_cols]

show_all_dimensions = st.checkbox("Show all 20 normalized sub-index scores", value=False)
if show_all_dimensions:
    active_cols = display_cols + additional_cols
else:
    active_cols = display_cols

st.dataframe(
    filtered_df[active_cols],
    use_container_width=True,
    height=480,
    column_config={
        "Rank": st.column_config.NumberColumn("Rank", format="%d"),
        "ISO_Code": st.column_config.TextColumn("ISO-3"),
        "Country": st.column_config.TextColumn("Country"),
        "Total_Score": st.column_config.ProgressColumn(
            "Total Score",
            format="%.2f",
            min_value=0,
            max_value=100
        )
    },
    hide_index=True
)

# Download CSV option
csv_data = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Leaderboard as CSV",
    data=csv_data,
    file_name="global_rankings_2025.csv",
    mime="text/csv",
)
