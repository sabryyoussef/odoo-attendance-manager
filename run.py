import os
import sys

# Get the absolute path to the odoo-attendance-manager directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "odoo-attendance-manager")

# Verify the path exists
if not os.path.exists(project_root):
    raise Exception(f"Project directory not found at: {project_root}")

# Add to Python path
sys.path.insert(0, project_root)

import streamlit as st
from app.main import run_app

if __name__ == "__main__":
    run_app()
