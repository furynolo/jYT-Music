import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from utils.config import config

# Scope required to view user's YouTube account safely
SCOPES = ['https://www.googleapis.com/auth/youtube']

class AuthManager:
    def __init__(self):
        self.credentials = None
        self.load_credentials()

    def is_authenticated(self):
        if self.credentials and self.credentials.valid:
            return True
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                self.save_credentials()
                return True
            except Exception:
                return False
        return False

    def login(self):
        if self.is_authenticated():
            return True

        if not os.path.exists(config.CLIENT_SECRETS_FILE):
            raise FileNotFoundError(f"Missing {config.CLIENT_SECRETS_FILE}. Please create OAuth credentials in Google Cloud Console.")

        flow = InstalledAppFlow.from_client_secrets_file(config.CLIENT_SECRETS_FILE, SCOPES)
        self.credentials = flow.run_local_server(port=0)
        self.save_credentials()
        return True

    def load_credentials(self):
        if os.path.exists(config.TOKEN_FILE):
            try:
                self.credentials = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)
            except Exception as e:
                print(f"Could not load token: {e}")
                self.credentials = None

    def save_credentials(self):
        if self.credentials:
            with open(config.TOKEN_FILE, 'w') as token:
                token.write(self.credentials.to_json())

    def logout(self):
        if os.path.exists(config.TOKEN_FILE):
            os.remove(config.TOKEN_FILE)
        self.credentials = None

