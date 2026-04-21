import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# ------------------- Supabase Connection -------------------
@st.cache_resource
def init_connection():
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# ------------------- App Configuration -------------------
st.set_page_config(page_title="Option Trade Log", layout="wide")
st.title("📊 Option Trade Log Dashboard")

# ------------------- Data Fetching & Processing -------------------
try:
    # Fetch data with filter (you can add more filters via UI later)
    response = (
        supabase.table("OptionTradeLog")
        .select("*")
        .neq("Strategy", "LEAPS Call")
        # .gt("profit", 100)   # Uncomment if needed
        .execute()
    )
    
    if not response.data:
        st.warning("No data found in the table.")
        st.stop()
    
    df = pd.DataFrame(response.data)
    
    # Ensure datetime column exists and convert it
    if "Option Expiry Date" in df.columns:
        df["Option Expiry Date"] = pd.to_datetime(df["Option Expiry Date"], errors="coerce")
    else:
        st.error("Column 'Option Expiry Date' not found in the data.")
        st.stop()
    
    # Create Month column for grouping (YYYY-MM format)
    df["Month"] = df["Option Expiry Date"].dt.to_period("M").astype(str)
    
    # ------------------- Monthly P&L Stats -------------------
    monthly_stats = (
        df.groupby("Month")[["Realized P&L", "Unrealized P&L"]]
        .sum()
        .reset_index()
    )
    #monthly_stats[["Realized P&L", "Unrealized P&L"]] = monthly_stats[["Realized P&L", "Unrealized P&L"]].abs()
    monthly_stats = monthly_stats.sort_values("Month")   # Sort chronologically
    
    # ------------------- Underlying P&L Stats -------------------
    underlying_stats = (
        df.groupby("Underlying")[["Realized P&L"]]
        .sum()
        .reset_index()
    )
    #underlying_stats["Realized P&L"] = underlying_stats["Realized P&L"].abs()
    underlying_stats = underlying_stats.sort_values("Realized P&L", ascending=False)
    
    # ------------------- Display Charts with Plotly -------------------
    st.subheader("📅 P&L by Month")
    fig_month = px.bar(
        monthly_stats,
        x="Month",
        y=["Realized P&L", "Unrealized P&L"],
        barmode="group",                    # Side-by-side bars (not stacked)
        color_discrete_sequence=["#2ecc71", "#3498db"],  # Green & Blue
        title="Monthly Realized vs Unrealized P&L",
        labels={"value": "P&L Amount", "variable": "Type"},
        text_auto=True                      # Show values on bars
    )
    fig_month.update_traces(textposition='outside')
    fig_month.update_layout(
        xaxis_title="Month",
        yaxis_title="P&L (Absolute Value)",
        legend_title="P&L Type",
        bargap=0.15,
        height=500
    )
    st.plotly_chart(fig_month, width='stretch')
    
    st.subheader("📌 P&L by Underlying")
    fig_underlying = px.bar(
        underlying_stats,
        x="Underlying",
        y="Realized P&L",
        color_discrete_sequence=["#2ecc71"],
        title="Total Realized P&L by Underlying",
        text_auto=True
    )
    fig_underlying.update_traces(textposition='outside')
    fig_underlying.update_layout(
        xaxis_title="Underlying",
        yaxis_title="Realized P&L (Absolute)",
        height=500,
        xaxis_tickangle=-45   # Better readability for long names
    )
    st.plotly_chart(fig_underlying, use_container_width=True)
    
    # Optional: Show raw data table (uncomment if needed)
    # with st.expander("View Raw Data"):
    #     st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error fetching or processing data: {e}")