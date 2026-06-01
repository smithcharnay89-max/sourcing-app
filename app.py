import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# The raw configuration block
GCP_CONFIG = {
    "type": "service_account",
    "project_id": "numeric-nova-352015",
    "private_key_id": "86363936730e00097bfbcac9fb2fb4eda406a99a",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC+RzPJAqxaizSWnRJYyxVhroxDLICggXRQIX/avC2r8g7iJcc0z1JbgAC8wuMB/3paTp3raMVqfF9yqNF5QX56AJJ5lnLfRuRYMNCqIGO0Bzb7syXkdKH4PizzJ1EsP4y5PxAK+XuU1mn5XhGzFA2bed6pirLpYtKXLmHQPAvQ8xzg+0nD0/IwJtKWZzh3RsDf5t5E+9fI7nP0UXejwW7C2LJSXVSQsnrez83m2An2fvm45JqaqNE4Fmvh0SW5XQLUu6WjnDUJJf\nnW9K8TEL073uUswh9iyoIs1501JFkRNvTsUjZf8isoKDBeUhumAw7jYh0+AmYSuMA\nnzEmoe5I7AgMBAAECggEAcNHDdBUWgm1FNg\n-----END PRIVATE KEY-----\n",
    "client_email": "sourcing-app@numeric-nova-352015.iam.gserviceaccount.com",
    "client_id": "109876543210987654321",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sourcing-app%40numeric-nova-352015.iam.gserviceaccount.com"
}

# Connect using the dictionary above instead of the secrets box
creds = Credentials.from_service_account_info(GCP_CONFIG, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(creds)
FOLDER_ID = "1TxurbcHWwa3VVGFqjb-_13mXKoSs6L_X"

st.title("🏛️ Design Source Pro")

# Simple check to see if we are connected
try:
    files = client.list_spreadsheet_files(folder_id=FOLDER_ID)
    st.success("Successfully connected to Google Drive!")
    project_names = [f['name'] for f in files]
    selected_proj = st.selectbox("Select Project", project_names)
except Exception as e:
    st.error(f"Connection error: {e}")
