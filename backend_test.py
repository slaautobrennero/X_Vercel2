#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class SLAAPITester:
    def __init__(self, base_url="https://portale-rimborsi.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.admin_token = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            self.failed_tests.append({"test": name, "details": details})

    def test_login(self, email, password):
        """Test login and store token"""
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                # Check if cookies are set
                if 'access_token' in self.session.cookies:
                    self.log_test("Login SuperAdmin", True)
                    return True
                else:
                    self.log_test("Login SuperAdmin", False, "No access_token cookie set")
                    return False
            else:
                self.log_test("Login SuperAdmin", False, f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Login SuperAdmin", False, str(e))
            return False

    def test_auth_me(self):
        """Test getting current user info"""
        try:
            response = self.session.get(f"{self.base_url}/auth/me")
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('ruolo') == 'superadmin':
                    self.log_test("Get Current User", True)
                    return user_data
                else:
                    self.log_test("Get Current User", False, f"Wrong role: {user_data.get('ruolo')}")
                    return None
            else:
                self.log_test("Get Current User", False, f"Status {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Get Current User", False, str(e))
            return None

    def test_get_sedi(self):
        """Test getting sedi (headquarters)"""
        try:
            response = self.session.get(f"{self.base_url}/sedi")
            if response.status_code == 200:
                sedi = response.json()
                if len(sedi) >= 3:  # Should have A22, CAV, ASPI
                    self.log_test("Get Sedi", True)
                    return sedi
                else:
                    self.log_test("Get Sedi", False, f"Expected at least 3 sedi, got {len(sedi)}")
                    return sedi
            else:
                self.log_test("Get Sedi", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Sedi", False, str(e))
            return []

    def test_get_annunci(self):
        """Test getting announcements"""
        try:
            response = self.session.get(f"{self.base_url}/annunci")
            if response.status_code == 200:
                annunci = response.json()
                self.log_test("Get Annunci", True)
                return annunci
            else:
                self.log_test("Get Annunci", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Annunci", False, str(e))
            return []

    def test_create_annuncio(self):
        """Test creating an announcement"""
        try:
            test_annuncio = {
                "titolo": "Test Annuncio API",
                "contenuto": "Questo è un annuncio di test creato dall'API testing",
                "link_documento": None
            }
            response = self.session.post(f"{self.base_url}/annunci", json=test_annuncio)
            if response.status_code == 200:
                annuncio = response.json()
                self.log_test("Create Annuncio", True)
                return annuncio.get('id')
            else:
                self.log_test("Create Annuncio", False, f"Status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Create Annuncio", False, str(e))
            return None

    def test_get_documenti(self):
        """Test getting documents"""
        try:
            response = self.session.get(f"{self.base_url}/documenti")
            if response.status_code == 200:
                documenti = response.json()
                self.log_test("Get Documenti", True)
                return documenti
            else:
                self.log_test("Get Documenti", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Documenti", False, str(e))
            return []

    def test_get_motivi_rimborso(self):
        """Test getting reimbursement reasons"""
        try:
            response = self.session.get(f"{self.base_url}/motivi-rimborso")
            if response.status_code == 200:
                motivi = response.json()
                if len(motivi) >= 6:  # Should have default motivi
                    self.log_test("Get Motivi Rimborso", True)
                    return motivi
                else:
                    self.log_test("Get Motivi Rimborso", False, f"Expected at least 6 motivi, got {len(motivi)}")
                    return motivi
            else:
                self.log_test("Get Motivi Rimborso", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Motivi Rimborso", False, str(e))
            return []

    def test_get_rimborsi(self):
        """Test getting reimbursements"""
        try:
            response = self.session.get(f"{self.base_url}/rimborsi")
            if response.status_code == 200:
                rimborsi = response.json()
                self.log_test("Get Rimborsi", True)
                return rimborsi
            else:
                self.log_test("Get Rimborsi", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Rimborsi", False, str(e))
            return []

    def test_get_users(self):
        """Test getting users (admin only)"""
        try:
            response = self.session.get(f"{self.base_url}/users")
            if response.status_code == 200:
                users = response.json()
                self.log_test("Get Users", True)
                return users
            else:
                self.log_test("Get Users", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Users", False, str(e))
            return []

    def test_get_notifiche(self):
        """Test getting notifications"""
        try:
            response = self.session.get(f"{self.base_url}/notifiche")
            if response.status_code == 200:
                notifiche = response.json()
                self.log_test("Get Notifiche", True)
                return notifiche
            else:
                self.log_test("Get Notifiche", False, f"Status {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Get Notifiche", False, str(e))
            return []

    def test_logout(self):
        """Test logout"""
        try:
            response = self.session.post(f"{self.base_url}/auth/logout")
            if response.status_code == 200:
                self.log_test("Logout", True)
                return True
            else:
                self.log_test("Logout", False, f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Logout", False, str(e))
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting SLA API Tests...")
        print(f"Testing against: {self.base_url}")
        print("-" * 50)

        # Test login
        if not self.test_login("superadmin@sla.it", "SlaAdmin2024!"):
            print("❌ Login failed - stopping tests")
            return False

        # Test authenticated endpoints
        user_data = self.test_auth_me()
        if not user_data:
            print("❌ Auth verification failed - stopping tests")
            return False

        # Test all main endpoints
        self.test_get_sedi()
        self.test_get_annunci()
        annuncio_id = self.test_create_annuncio()
        self.test_get_documenti()
        self.test_get_motivi_rimborso()
        self.test_get_rimborsi()
        self.test_get_users()
        self.test_get_notifiche()
        
        # Test logout
        self.test_logout()

        # Print summary
        print("-" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print("\n❌ Failed tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = SLAAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())