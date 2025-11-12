"""
Streamlit Web Dashboard for Fidelity Portfolio Tracker
Interactive visualization and analysis tool
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path to import fidelity_tracker
sys.path.insert(0, str(Path(__file__).parent.parent))

from fidelity_tracker.core.database import DatabaseManager
from fidelity_tracker.utils.config import Config

# Page configuration
st.set_page_config(
    page_title="Fidelity Portfolio Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive { color: #00B050; }
    .negative { color: #FF0000; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_database():
    """Load database connection"""
    config = Config()
    db_path = config.get('database.path', 'fidelity_portfolio.db')
    return DatabaseManager(db_path)


@st.cache_data(ttl=300)
def get_latest_snapshot(_db):
    """Get latest portfolio snapshot"""
    return _db.get_latest_snapshot()


@st.cache_data(ttl=300)
def get_holdings(_db, snapshot_id=None):
    """Get holdings data"""
    return _db.get_holdings(snapshot_id)


@st.cache_data(ttl=300)
def get_portfolio_history(_db, days=90):
    """Get portfolio history"""
    return _db.get_portfolio_history(days)


def format_currency(value):
    """Format value as currency"""
    return f"${value:,.2f}" if value is not None else "N/A"


def format_percentage(value):
    """Format value as percentage"""
    return f"{value:.2f}%" if value is not None else "N/A"


def main():
    """Main dashboard function"""

    # Header
    st.markdown('<div class="main-header">📈 Fidelity Portfolio Tracker</div>', unsafe_allow_html=True)

    # Load database
    try:
        db = load_database()
        latest = get_latest_snapshot(db)

        if latest is None:
            st.warning("No portfolio data available. Run `portfolio-tracker sync` first.")
            return

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # Sidebar
    with st.sidebar:
        st.header("Portfolio Overview")

        # Date range selector
        st.subheader("Date Range")
        days_back = st.selectbox(
            "History",
            options=[7, 30, 90, 180, 365],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )

        st.markdown("---")

        # Latest snapshot info
        st.subheader("Latest Update")
        st.write(f"**Date:** {latest['timestamp'][:10]}")
        st.write(f"**Time:** {latest['timestamp'][11:19]}")
        st.write(f"**Total Value:** {format_currency(latest['total_value'])}")

        st.markdown("---")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Main content
    holdings = get_holdings(db, latest['id'])

    if not holdings:
        st.info("No holdings found in the latest snapshot.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(holdings)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Portfolio Value",
            value=format_currency(latest['total_value']),
            delta=None
        )

    with col2:
        num_positions = len(df)
        st.metric(
            label="Number of Positions",
            value=num_positions
        )

    with col3:
        if 'gain_loss' in df.columns:
            total_gain_loss = df['gain_loss'].sum()
            st.metric(
                label="Total Gain/Loss",
                value=format_currency(total_gain_loss),
                delta=format_currency(total_gain_loss)
            )
        else:
            st.metric(label="Total Gain/Loss", value="N/A")

    with col4:
        if 'gain_loss' in df.columns and 'cost_basis' in df.columns:
            total_cost = df['cost_basis'].sum()
            if total_cost > 0:
                total_return_pct = (df['gain_loss'].sum() / total_cost) * 100
                st.metric(
                    label="Total Return %",
                    value=format_percentage(total_return_pct),
                    delta=format_percentage(total_return_pct)
                )
            else:
                st.metric(label="Total Return %", value="N/A")
        else:
            st.metric(label="Total Return %", value="N/A")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Holdings", "🥧 Allocation", "📈 History", "📋 Details"])

    with tab1:
        st.subheader("Top Holdings")

        # Sort by value - use available columns
        cols_to_display = ['ticker', 'company_name', 'value', 'portfolio_weight']
        top_holdings = df.nlargest(10, 'value')[cols_to_display]

        # Create bar chart
        fig = px.bar(
            top_holdings,
            x='ticker',
            y='value',
            title='Top 10 Holdings by Value',
            labels={'value': 'Value ($)', 'ticker': 'Ticker'},
            text='value',
            color='value',
            color_continuous_scale='Viridis'
        )
        fig.update_traces(texttemplate='$%{text:.2s}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Portfolio Allocation")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart by holdings
            st.markdown("**By Holdings**")
            top_10 = df.nlargest(10, 'value')
            others_value = df[~df['ticker'].isin(top_10['ticker'])]['value'].sum()

            pie_data = pd.concat([
                top_10[['ticker', 'value']],
                pd.DataFrame([{'ticker': 'Others', 'value': others_value}])
            ])

            fig_pie = px.pie(
                pie_data,
                values='value',
                names='ticker',
                title='Top 10 Holdings + Others',
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Sector allocation
            if 'sector' in df.columns:
                st.markdown("**By Sector**")
                sector_data = df.groupby('sector')['value'].sum().reset_index()
                sector_data = sector_data[sector_data['sector'] != 'Unknown']

                if not sector_data.empty:
                    fig_sector = px.pie(
                        sector_data,
                        values='value',
                        names='sector',
                        title='Sector Allocation',
                        hole=0.4
                    )
                    fig_sector.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_sector, use_container_width=True)
                else:
                    st.info("No sector data available. Run enrichment to add sector information.")
            else:
                st.info("No sector data available. Run enrichment to add sector information.")

    with tab3:
        st.subheader("Portfolio History")

        # Get historical data
        history = get_portfolio_history(db, days_back)

        if history and len(history) > 1:
            hist_df = pd.DataFrame(history)
            hist_df['timestamp'] = pd.to_datetime(hist_df['timestamp'])

            # Line chart
            fig_history = go.Figure()

            fig_history.add_trace(go.Scatter(
                x=hist_df['timestamp'],
                y=hist_df['total_value'],
                mode='lines+markers',
                name='Portfolio Value',
                line=dict(color='#00B050', width=2),
                marker=dict(size=6)
            ))

            fig_history.update_layout(
                title='Portfolio Value Over Time',
                xaxis_title='Date',
                yaxis_title='Total Value ($)',
                hovermode='x unified',
                height=500
            )

            st.plotly_chart(fig_history, use_container_width=True)

            # Statistics
            col1, col2, col3 = st.columns(3)

            with col1:
                if len(hist_df) > 1:
                    first_value = hist_df.iloc[-1]['total_value']
                    last_value = hist_df.iloc[0]['total_value']
                    change = last_value - first_value
                    change_pct = (change / first_value) * 100 if first_value > 0 else 0

                    st.metric(
                        label=f"Change (Last {days_back} days)",
                        value=format_currency(change),
                        delta=format_percentage(change_pct)
                    )

            with col2:
                max_value = hist_df['total_value'].max()
                st.metric(
                    label="Peak Value",
                    value=format_currency(max_value)
                )

            with col3:
                min_value = hist_df['total_value'].min()
                st.metric(
                    label="Lowest Value",
                    value=format_currency(min_value)
                )

        else:
            st.info("Not enough historical data. Sync data regularly to build history.")

    with tab4:
        st.subheader("Detailed Holdings")

        # Display settings
        show_all = st.checkbox("Show all columns", value=False)

        if show_all:
            display_df = df
        else:
            # Show most relevant columns - use actual column names from database
            cols = ['ticker', 'company_name', 'quantity', 'last_price', 'value', 'portfolio_weight']
            if 'sector' in df.columns:
                cols.append('sector')
            if 'industry' in df.columns:
                cols.append('industry')

            display_df = df[[col for col in cols if col in df.columns]]

        # Format display
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )

        # Export button
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"portfolio_holdings_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
