from fastapi import FastAPI, HTTPException
from typing import Dict, Optional
import boto3
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from pydantic import BaseModel, ConfigDict
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)  # AWS Lambda handler

class UserUpdate(BaseModel):
    """Model for user update data"""
    model_config = ConfigDict(extra='allow')  # Allow extra fields
    data: Dict[str, str]

def get_secrets() -> Dict[str, str]:
    """Retrieve Google Sheets API credentials from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    
    try:
        secret_value = client.get_secret_value(
            SecretId=os.getenv('GOOGLE_SHEETS_SECRET_NAME')
        )
        return json.loads(secret_value['SecretString'])
    except Exception as e:
        print(f"Error retrieving secret: {str(e)}")
        secret_value = os.environ.get('GOOGLE_SHEETS_API_KEY')
        if secret_value:
            return json.loads(secret_value)
    
    raise HTTPException(status_code=500, detail="Could not retrieve credentials")

def get_sheets_service():
    """Initialize Google Sheets API service"""
    credentials = get_secrets()
    creds = service_account.Credentials.from_service_account_info(
        credentials,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return build('sheets', 'v4', credentials=creds)

def find_user_row(sheet_service, spreadsheet_id: str, user_id: str) -> Optional[int]:
    """Find user row in spreadsheet by ID"""
    range_name = f"{os.getenv('SHEET_NAME', 'Sheet1')}!A:A"
    result = sheet_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    
    values = result.get('values', [])
    for idx, row in enumerate(values):
        if row and row[0] == user_id:
            return idx + 1
    return None

@app.get("/user/{user_id}")
async def get_user(user_id: str) -> Dict[str, str]:
    """Get user information from Google Sheets"""
    service = get_sheets_service()
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    
    row_num = find_user_row(service, spreadsheet_id, user_id)
    if not row_num:
        raise HTTPException(status_code=404, detail="User not found")
    
    range_name = f"{os.getenv('SHEET_NAME', 'Sheet1')}!{row_num}:{row_num}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    
    values = result.get('values', [[]])[0]
    headers = ['accessCode', 'maxGuests', 'partyName', 'dietaryRestrictions', 'hotelAccommodations', 'questions', 'RAW Names']
    
    return dict(zip(headers, values))

@app.post("/update/{user_id}")
async def update_user(user_id: str, update_data: UserUpdate) -> Dict[str, str]:
    """Update user information in Google Sheets"""
    service = get_sheets_service()
    spreadsheet_id = os.getenv('SPREADSHEET_ID')
    
    row_num = find_user_row(service, spreadsheet_id, user_id)
    if not row_num:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current row data
    range_name = f"{os.getenv('SHEET_NAME', 'Sheet1')}!{row_num}:{row_num}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    
    current_values = result.get('values', [[]])[0]
    headers = ['accessCode', 'maxGuests', 'partyName', 'dietaryRestrictions', 'hotelAccommodations', 'questions', 'RAW Names']
    current_data = dict(zip(headers, current_values))
    
    # Update with new data
    updated_data = {**current_data, **update_data.data}
    new_values = [[updated_data[header] for header in headers]]
    
    body = {
        'values': new_values
    }
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    
    return {"message": "User updated successfully"}
