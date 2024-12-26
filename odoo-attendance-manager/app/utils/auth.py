import streamlit as st

def show_login_page():
    """Shows a beautifully styled login form"""
    
    # Custom CSS for login page
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            background: white;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .login-header img {
            width: 80px;
            margin-bottom: 1rem;
        }
        
        .stTextInput > div > div > input {
            border-radius: 5px;
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        .login-footer {
            text-align: center;
            margin-top: 2rem;
            color: #666;
            font-size: 0.8rem;
        }
        
        .main {
            background-color: #f5f5f5;
            padding: 2rem;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div class="login-container">
                <div class="login-header">
                    <img src="https://cdn-icons-png.flaticon.com/512/2910/2910756.png" alt="Logo">
                    <h1>Welcome Back!</h1>
                    <p style="color: #666;">Please enter your credentials to continue</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Create a form
        with st.form("login_form"):
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Default password is 'admin'",
            )
            
            # Center the login button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if password == st.secrets.get("ADMIN_PASSWORD", "admin"):
                st.session_state["password_correct"] = True
                
                # Show success message with animation
                success_msg = st.success("🎉 Login successful! Redirecting...")
                
                # Add a spinner for visual feedback
                with st.spinner("Please wait..."):
                    import time
                    time.sleep(1)  # Short delay for better UX
                
                return True
            else:
                # Show error with animation
                st.error("❌ Incorrect password")
                st.warning("Please try again or contact your administrator")
        
        # Add footer
        st.markdown("""
            <div class="login-footer">
                <p>Odoo Attendance Manager v1.0</p>
                <p>© 2024 Your Company. All rights reserved.</p>
            </div>
        """, unsafe_allow_html=True)
    
    return False

def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
        
    return st.session_state.get("password_correct", False) 