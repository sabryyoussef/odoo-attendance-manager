import streamlit as st
from . import dashboard
from .utils.odoo_api import OdooAPI, get_config
from .utils.data_processor import process_excel_file, visualize_attendance
from dotenv import load_dotenv
import os
import pandas as pd
from collections import defaultdict

def create_missing_employees(odoo, missing_employees):
    """Create missing employees in Odoo with user input"""
    success_count = 0
    error_count = 0
    error_details = defaultdict(list)

    st.subheader("Create Missing Employees")
    st.write("Please provide names for the following employees:")

    # Create a form for employee names
    with st.form("employee_creation_form"):
        employee_names = {}
        for badge_id in missing_employees:
            default_name = f"Employee {badge_id}"
            employee_names[badge_id] = st.text_input(
                f"Name for Employee with Badge ID {badge_id}",
                value=default_name,
                key=f"emp_{badge_id}"
            )
        
        submit = st.form_submit_button("Create Employees")
        
        if submit:
            progress_bar = st.progress(0)
            for i, (badge_id, name) in enumerate(employee_names.items()):
                try:
                    odoo.create_employee(badge_id, name)
                    success_count += 1
                    st.success(f"✓ Created employee: {name} (Badge ID: {badge_id})")
                except Exception as e:
                    error_count += 1
                    error_details[str(e)].append(badge_id)
                    st.error(f"✗ Error creating employee with Badge ID {badge_id}: {str(e)}")
                progress_bar.progress((i + 1) / len(employee_names))

            # Print summary
            st.write("---")
            st.write("### Employee Creation Summary:")
            st.write(f"Successfully created: {success_count} employees")
            st.write(f"Failed to create: {error_count} employees")
            
            if error_details:
                st.write("### Error Details:")
                for error, employees in error_details.items():
                    st.error(f"Error: {error}")
                    st.write("Affected Badge IDs:", ", ".join(map(str, employees)))

def run_app():
    # Load environment variables if running locally
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(env_path)

    st.title("My Odoo Attendance Manager")
    
    with st.sidebar:
        st.title("Settings")
        
        st.subheader("Odoo Connection")
        with st.expander("Connection Details", expanded=True):
            st.info("These settings are pre-filled from your configuration. Edit only if needed.")
            url = st.text_input(
                "Odoo URL", 
                value=get_config("ODOO_URL"),
                help="The URL of your Odoo instance"
            )
            db = st.text_input(
                "Database", 
                value=get_config("ODOO_DB"),
                help="Your Odoo database name"
            )
            username = st.text_input(
                "Username", 
                value=get_config("ODOO_USERNAME"),
                help="Your Odoo login email"
            )
            password = st.text_input(
                "Password", 
                value=get_config("ODOO_PASSWORD"),
                type="password",
                help="Your Odoo password"
            )
            api_key = st.text_input(
                "API Key", 
                value=get_config("api_key"),
                type="password",
                help="Your Odoo API key for authentication"
            )
        
        if st.button("Connect to Odoo", help="Test connection to Odoo with provided credentials"):
            try:
                odoo = OdooAPI()
                st.session_state['odoo'] = odoo
                st.success("✅ Connected successfully!")
                
                # Add connection summary
                with st.expander("Connection Summary", expanded=True):
                    st.write("### Connection Details")
                    st.info(f"""
                    - **URL**: {url}
                    - **Database**: {db}
                    - **Username**: {username}
                    - **Connection Status**: Active
                    """)
                    
                    # Get some basic stats from Odoo
                    try:
                        # Count total employees
                        employees = odoo.get_all_employees()
                        total_employees = len(employees) if employees else 0
                        
                        # Get recent attendance records
                        recent_attendance = odoo.get_recent_attendance()
                        total_attendance = len(recent_attendance) if recent_attendance else 0
                        
                        st.write("### System Statistics")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Employees", total_employees)
                        with col2:
                            st.metric("Recent Attendance Records", total_attendance)
                            
                    except Exception as e:
                        st.warning("Could not fetch all statistics. Some features might be limited.")
                        st.error(f"Error: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["Data Import", "Dashboard", "Reports"])
    
    with tab1:
        st.header("Import Attendance Data")
        
        # File upload section
        st.subheader("Upload Attendance File")
        with st.expander("File Requirements", expanded=True):
            st.info("""
            The Excel file should contain the following columns:
            - AC-No.: Employee badge/ID number
            - Time: Date and time of check-in/out
            - State: 'C/In' for check-in, 'C/Out' for check-out
            """)
            
            upload_method = st.radio(
                "Choose upload method:",
                ["Upload File", "Use Default Path"],
                help="Select how you want to provide the attendance data"
            )
            
            if upload_method == "Upload File":
                uploaded_file = st.file_uploader(
                    "Choose an Excel file", 
                    type=['xls', 'xlsx'],
                    help="Upload your attendance Excel file"
                )
                if uploaded_file:
                    if st.button("Process Uploaded File"):
                        with st.spinner("Processing data..."):
                            df = process_excel_file(uploaded_file)
                            if df is not None:
                                st.session_state.attendance_df = df
                                st.success("✅ File processed successfully!")
                                st.write("Preview of the data:")
                                st.dataframe(df.head())
            else:
                default_path = "/home/sabry/yarab/data/acnLog12.xls"
                st.text_input("Default file path", value=default_path, disabled=True)
                if st.button("Process Default File"):
                    if os.path.exists(default_path):
                        with st.spinner("Processing data..."):
                            df = process_excel_file(default_path)
                            if df is not None:
                                st.session_state.attendance_df = df
                                st.success("✅ File processed successfully!")
                                st.write("Preview of the data:")
                                st.dataframe(df.head())
                    else:
                        st.error(f"❌ File not found at: {default_path}")
            
            if 'attendance_df' in st.session_state and 'odoo' in st.session_state:
                st.subheader("Upload to Odoo")
                if st.button("Upload Processed Data to Odoo"):
                    try:
                        with st.spinner("Checking employees..."):
                            unique_employees = st.session_state.attendance_df['employee_id'].unique()
                            missing, existing = st.session_state.odoo.check_missing_employees(unique_employees)
                            
                            if missing:
                                st.warning("⚠️ The following employees need to be created in Odoo first:")
                                st.write("Missing Employee IDs:", missing)
                                
                                create_missing_employees(st.session_state.odoo, missing)
                                
                                # Recheck for missing employees
                                missing, existing = st.session_state.odoo.check_missing_employees(unique_employees)
                                if missing:
                                    st.error("Some employees could not be created. Please check the errors above.")
                                    return
                            
                            # If no missing employees (or all were created), proceed with upload
                            with st.spinner("Uploading attendance records..."):
                                success_count = 0
                                error_count = 0
                                error_details = defaultdict(list)
                                
                                progress_bar = st.progress(0)
                                for index, row in st.session_state.attendance_df.iterrows():
                                    try:
                                        employee_id = st.session_state.odoo.get_employee_id(row['employee_id'])
                                        st.session_state.odoo.create_attendance(
                                            employee_id=employee_id,
                                            check_in=row['check_in'],
                                            check_out=row['check_out']
                                        )
                                        success_count += 1
                                    except Exception as e:
                                        error_count += 1
                                        error_details[str(e)].append(row['employee_id'])
                                    progress_bar.progress((index + 1) / len(st.session_state.attendance_df))

                                st.write("### Upload Summary:")
                                st.write(f"Successfully uploaded: {success_count} records")
                                st.write(f"Failed to upload: {error_count} records")
                                
                                if error_details:
                                    st.write("### Error Details:")
                                    for error, employees in error_details.items():
                                        st.error(f"Error: {error}")
                                        st.write("Affected employees:", ", ".join(map(str, employees)))
                                
                                if success_count > 0:
                                    st.success("✅ Data upload completed!")
                                
                    except Exception as e:
                        st.error(f"❌ Error during upload: {str(e)}")
    
    with tab2:
        st.header("Attendance Dashboard")
        if 'attendance_df' in st.session_state:
            visualize_attendance(st.session_state.attendance_df)
        else:
            st.info("👆 Please import attendance data first")
    
    with tab3:
        st.header("Attendance Reports")
        if 'attendance_df' in st.session_state:
            st.write("Attendance Summary")
            st.dataframe(st.session_state.attendance_df)
        else:
            st.info("👆 Please import attendance data first")
