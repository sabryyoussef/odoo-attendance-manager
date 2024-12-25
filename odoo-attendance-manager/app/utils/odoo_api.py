import os
import requests
from dotenv import load_dotenv

class OdooAPI:
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.password = os.getenv('ODOO_PASSWORD')
        self.api_key = os.getenv('api_key')
        self.session = requests.Session()
        self.uid = None
        self.login()

    def login(self):
        """Login to Odoo and get user ID"""
        login_url = f"{self.url}/web/session/authenticate"
        login_data = {
            "jsonrpc": "2.0",
            "params": {
                "db": self.db,
                "login": self.username,
                "password": self.password,
                "api_key": self.api_key
            }
        }
        try:
            response = self.session.post(login_url, json=login_data)
            result = response.json()
            if 'error' in result:
                raise Exception(f"Login failed: {result['error']['data']['message']}")
            self.uid = result.get('result', {}).get('uid')
            if not self.uid:
                raise Exception("Login failed: Could not get user ID")
            return self.uid
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            raise Exception(f"Login error: {str(e)}")

    def get_employee_id(self, badge_id):
        """Get Odoo employee ID from badge ID"""
        endpoint = f"{self.url}/web/dataset/call_kw"
        params = {
            "model": "hr.employee",
            "method": "search_read",
            "args": [[["barcode", "=", str(badge_id)]]],
            "kwargs": {
                "fields": ["id", "name"],
                "limit": 1
            }
        }
        data = {
            "jsonrpc": "2.0",
            "params": params
        }
        try:
            response = self.session.post(endpoint, json=data)
            result = response.json()
            if 'error' in result:
                raise Exception(f"Error getting employee: {result['error']['data']['message']}")
            employees = result.get('result', [])
            return employees[0]['id'] if employees else None
        except Exception as e:
            raise Exception(f"Error getting employee: {str(e)}")

    def check_missing_employees(self, badge_ids):
        """Check which employees need to be created in Odoo"""
        missing_employees = []
        existing_employees = []
        
        for badge_id in badge_ids:
            if not self.get_employee_id(badge_id):
                missing_employees.append(badge_id)
            else:
                existing_employees.append(badge_id)
        
        return missing_employees, existing_employees

    def create_attendance(self, employee_id, check_in, check_out=None):
        """Create attendance record in Odoo"""
        endpoint = f"{self.url}/web/dataset/call_kw"
        
        def format_datetime(dt):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        attendance_data = {
            "employee_id": employee_id,
            "check_in": format_datetime(check_in),
        }
        if check_out:
            attendance_data["check_out"] = format_datetime(check_out)

        params = {
            "model": "hr.attendance",
            "method": "create",
            "args": [attendance_data],
            "kwargs": {}
        }
        data = {
            "jsonrpc": "2.0",
            "params": params
        }
        try:
            response = self.session.post(endpoint, json=data)
            result = response.json()
            if 'error' in result:
                raise Exception(f"Error creating attendance: {result['error']['data']['message']}")
            return result.get('result')
        except Exception as e:
            raise Exception(f"Error creating attendance: {str(e)}")

    def create_employee(self, badge_id, name):
        """Create a new employee in Odoo"""
        endpoint = f"{self.url}/web/dataset/call_kw"
        params = {
            "model": "hr.employee",
            "method": "create",
            "args": [{
                "name": name,
                "barcode": str(badge_id),
                "pin": str(badge_id),
            }],
            "kwargs": {}
        }
        data = {
            "jsonrpc": "2.0",
            "params": params
        }
        try:
            response = self.session.post(endpoint, json=data)
            result = response.json()
            if 'error' in result:
                raise Exception(f"Error creating employee: {result['error']['data']['message']}")
            return result.get('result')
        except Exception as e:
            raise Exception(f"Error creating employee: {str(e)}")

    def get_all_employees(self):
        """Get all employees from Odoo"""
        endpoint = f"{self.url}/web/dataset/call_kw"
        params = {
            "model": "hr.employee",
            "method": "search_read",
            "args": [[]],  # Empty domain to get all records
            "kwargs": {
                "fields": ["id", "name", "barcode"],
            }
        }
        data = {
            "jsonrpc": "2.0",
            "params": params
        }
        try:
            response = self.session.post(endpoint, json=data)
            result = response.json()
            if 'error' in result:
                raise Exception(f"Error getting employees: {result['error']['data']['message']}")
            return result.get('result', [])
        except Exception as e:
            raise Exception(f"Error getting employees: {str(e)}")

    def get_recent_attendance(self, limit=100):
        """Get recent attendance records from Odoo"""
        endpoint = f"{self.url}/web/dataset/call_kw"
        params = {
            "model": "hr.attendance",
            "method": "search_read",
            "args": [[]],
            "kwargs": {
                "fields": ["employee_id", "check_in", "check_out"],
                "limit": limit,
                "order": "create_date desc"
            }
        }
        data = {
            "jsonrpc": "2.0",
            "params": params
        }
        try:
            response = self.session.post(endpoint, json=data)
            result = response.json()
            if 'error' in result:
                raise Exception(f"Error getting attendance: {result['error']['data']['message']}")
            return result.get('result', [])
        except Exception as e:
            raise Exception(f"Error getting attendance: {str(e)}")

    # ... (rest of the OdooAPI class methods)