import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
from collections import defaultdict
import streamlit as st

def process_excel_file(file_path):
    """Process the Excel file and return attendance data"""
    df = pd.read_excel(file_path)
    
    # Convert Time column to datetime
    df['Time'] = pd.to_datetime(df['Time'])
    df['Date'] = df['Time'].dt.date
    
    # Process records by employee and date
    attendance_records = []
    
    for (employee_id, date), group in df.groupby(['AC-No.', 'Date']):
        check_ins = group[group['State'] == 'C/In']['Time']
        check_outs = group[group['State'] == 'C/Out']['Time']
        
        if not check_ins.empty and not check_outs.empty:
            first_check_in = check_ins.min()
            last_check_out = check_outs.max()
            
            if first_check_in < last_check_out:
                attendance_records.append({
                    'employee_id': str(employee_id),
                    'date': date,
                    'check_in': first_check_in,
                    'check_out': last_check_out,
                    'total_hours': (last_check_out - first_check_in).total_seconds() / 3600
                })
    
    return pd.DataFrame(attendance_records)

def visualize_attendance(attendance_df):
    """Create visualizations of the attendance data"""
    if attendance_df.empty:
        st.warning("No attendance records to visualize")
        return
    
    # Create a directory for the visualizations
    os.makedirs('attendance_analysis', exist_ok=True)
    
    # 1. Daily hours worked by employee
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    for employee in attendance_df['employee_id'].unique():
        employee_data = attendance_df[attendance_df['employee_id'] == employee]
        ax1.plot(employee_data['date'], employee_data['total_hours'], 
                marker='o', label=f'Employee {employee}')
    
    plt.title('Daily Hours Worked by Employee')
    plt.xlabel('Date')
    plt.ylabel('Hours Worked')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig1)
    
    # 2. Average hours worked by employee
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    avg_hours = attendance_df.groupby('employee_id')['total_hours'].mean()
    avg_hours.plot(kind='bar', ax=ax2)
    plt.title('Average Hours Worked by Employee')
    plt.xlabel('Employee ID')
    plt.ylabel('Average Hours')
    plt.tight_layout()
    st.pyplot(fig2)
    
    # Generate summary statistics
    summary = attendance_df.groupby('employee_id').agg({
        'total_hours': ['mean', 'min', 'max', 'count'],
        'check_in': lambda x: x.dt.strftime('%H:%M:%S').mode().iloc[0],
        'check_out': lambda x: x.dt.strftime('%H:%M:%S').mode().iloc[0]
    }).round(2)
    
    st.write("Summary Statistics:")
    st.dataframe(summary)