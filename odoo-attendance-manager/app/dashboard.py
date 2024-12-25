import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import glob
import os
import json
from datetime import datetime, timedelta
import time
import base64
import io

# Set page config
st.set_page_config(
    page_title="Monitoring Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stDownloadButton button {
        width: 100%;
    }
    .log-entry {
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 5px solid;
    }
    .filter-section {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

def get_csv_download_link(df, filename="data.csv"):
    """Generate a download link for dataframe"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    return href

def get_excel_download_link(df, filename="data.xlsx"):
    """Generate a download link for Excel file"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel</a>'
    return href

def parse_logs():
    """Parse log files and return a DataFrame with enhanced error detection"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
        with open('logs/app_sample.log', 'w') as f:
            f.write(f"{datetime.now()} - INFO - Application started\n")
    
    log_files = glob.glob('logs/app_*.log')
    logs = []
    
    for log_file in log_files:
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    timestamp = line[:23]
                    remaining = line[25:].split(' - ')
                    
                    if len(remaining) >= 2:
                        level = remaining[0].strip()
                        message = ' - '.join(remaining[1:]).strip()
                        
                        # Extract additional information from message
                        operation = 'Unknown'
                        duration = None
                        if 'completed in' in message:
                            operation = message.split(' completed in')[0]
                            duration = float(message.split('in ')[-1].replace('s', ''))
                        
                        logs.append({
                            'timestamp': pd.to_datetime(timestamp),
                            'level': level,
                            'message': message,
                            'operation': operation,
                            'duration': duration
                        })
                except Exception as e:
                    continue
    
    if not logs:
        logs = [{
            'timestamp': pd.to_datetime('now'),
            'level': 'INFO',
            'message': 'No logs found. Starting monitoring...',
            'operation': 'System',
            'duration': 0
        }]
    
    return pd.DataFrame(logs)

def create_time_series(df, column, title):
    """Create an interactive time series plot"""
    fig = px.line(df, x='timestamp', y=column, title=title)
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title=column,
        hovermode='x unified'
    )
    return fig

def main():
    st.title("📊 Advanced Application Monitoring Dashboard")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh")
    if auto_refresh:
        refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 30)
    
    # Initialize session state for last refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # Load and filter logs
    try:
        logs_df = parse_logs()
        
        # Time range filter
        time_ranges = {
            'Last hour': timedelta(hours=1),
            'Last 24 hours': timedelta(days=1),
            'Last 7 days': timedelta(days=7),
            'All time': timedelta(days=365*10)
        }
        selected_range = st.sidebar.selectbox("Time Range", list(time_ranges.keys()))
        time_filter = datetime.now() - time_ranges[selected_range]
        logs_df = logs_df[logs_df['timestamp'] > time_filter]
        
        # Level filter
        available_levels = ['All'] + sorted(logs_df['level'].unique().tolist())
        selected_level = st.sidebar.selectbox("Log Level", available_levels)
        if selected_level != 'All':
            logs_df = logs_df[logs_df['level'] == selected_level]
        
        # Search filter
        search_term = st.sidebar.text_input("Search in messages")
        if search_term:
            logs_df = logs_df[logs_df['message'].str.contains(search_term, case=False, na=False)]
        
        # Export options
        st.sidebar.header("Export Options")
        export_format = st.sidebar.selectbox("Export Format", ["CSV", "Excel"])
        if st.sidebar.button("Export Data"):
            if export_format == "CSV":
                st.sidebar.markdown(get_csv_download_link(logs_df), unsafe_allow_html=True)
            else:
                st.sidebar.markdown(get_excel_download_link(logs_df), unsafe_allow_html=True)
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Logs", len(logs_df))
        with col2:
            error_count = len(logs_df[logs_df['level'] == 'ERROR'])
            st.metric("Errors", error_count)
        with col3:
            success_rate = ((len(logs_df) - error_count) / len(logs_df) * 100) if len(logs_df) > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col4:
            avg_duration = logs_df['duration'].mean()
            if pd.notnull(avg_duration):
                st.metric("Avg Duration", f"{avg_duration:.2f}s")
        
        # Visualizations
        tab1, tab2, tab3 = st.tabs(["📈 Trends", "📊 Analysis", "📑 Logs"])
        
        with tab1:
            # Error trend
            error_trend = logs_df[logs_df['level'] == 'ERROR'].groupby(
                logs_df['timestamp'].dt.floor('H')).size().reset_index()
            error_trend.columns = ['timestamp', 'count']
            st.plotly_chart(create_time_series(error_trend, 'count', 'Error Trend'), use_container_width=True)
            
            # Operation duration trend
            duration_df = logs_df[pd.notnull(logs_df['duration'])]
            if not duration_df.empty:
                st.plotly_chart(create_time_series(duration_df, 'duration', 'Operation Durations'), use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Log levels distribution
                level_dist = logs_df['level'].value_counts()
                fig = px.pie(values=level_dist.values, names=level_dist.index, title='Log Levels Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Operations distribution
                op_dist = logs_df['operation'].value_counts().head(10)
                fig = px.bar(x=op_dist.index, y=op_dist.values, title='Top Operations')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Recent logs with enhanced display
            st.subheader("Recent Logs")
            for _, log in logs_df.head(20).iterrows():
                severity_color = {
                    'ERROR': 'red',
                    'WARNING': 'orange',
                    'INFO': 'blue',
                    'DEBUG': 'gray'
                }.get(log['level'].upper(), 'black')
                
                st.markdown(f"""
                    <div class="log-entry" style="border-left-color: {severity_color}">
                        <small>{log['timestamp']}</small><br>
                        <strong style="color:{severity_color};">{log['level']}</strong>: {log['message']}
                    </div>
                """, unsafe_allow_html=True)
        
        # Auto-refresh
        if auto_refresh:
            if (datetime.now() - st.session_state.last_refresh).total_seconds() > refresh_interval:
                st.session_state.last_refresh = datetime.now()
                st.experimental_rerun()
            
            # Show countdown
            time_to_refresh = refresh_interval - (datetime.now() - st.session_state.last_refresh).total_seconds()
            st.sidebar.markdown(f"Refreshing in: {int(time_to_refresh)}s")
        
    except Exception as e:
        st.error(f"Error processing logs: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main() 