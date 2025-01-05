import json
import os
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
RANGE_NAME = 'RSVP!A:G'  # Adjust based on your sheet structure

def is_valid_code(code):
    """Validate the code format.
    """
    if not code or len(code) != 9 or not code.startswith('NANGIE'):
        return False
    
    return re.match(r'^[A-Z0-9]{9}$', code)

def get_google_sheets_service():
    """Initialize Google Sheets service with credentials."""
    try:
        # Load credentials from AWS Lambda environment
        creds_json = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        credentials = service_account.Credentials.from_service_account_info(
            creds_json, scopes=SCOPES)
        
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"Error initializing Google Sheets service: {str(e)}")
        raise

def find_user_by_code(sheets_service, code):
    """Find user data in Google Sheets by code."""
    try:
        # Get all data from the sheet
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        
        rows = result.get('values', [])
        if not rows:
            return None
            
        # Assuming first row contains headers
        headers = rows[0]
        code_index = headers.index('code')  # Adjust column name as needed
        
        # Search for the user with matching code
        for row in rows[1:]:  # Skip header row
            if len(row) > code_index and row[code_index] == code:
                return dict(zip(headers, row))
                
        return None
        
    except HttpError as e:
        print(f"Google Sheets API error: {str(e)}")
        raise
    except ValueError as e:
        print(f"Error processing data: {str(e)}")
        raise

def lambda_handler(event, context):
    """AWS Lambda handler for GET /user/{code} endpoint."""
    try:
        # Extract code from path parameters
        code = event['pathParameters']['code']
        
        # Validate code format
        if not is_valid_code(code):
            return {
                'statusCode': 403,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': 'https://nangie.framer.website'
                },
                'body': json.dumps({
                    'message': 'Forbidden - Invalid code format',
                    'details': 'Code must be 6 characters long and contain only letters and numbers'
                })
            }

        # Initialize Google Sheets service
        sheets_service = get_google_sheets_service()
        
        # Find user data
        user_data = find_user_by_code(sheets_service, code)
        
        if user_data:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': 'https://nangie.framer.website'
                },
                'body': json.dumps(user_data)
            }
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': 'https://nangie.framer.website'
                },
                'body': json.dumps({'message': 'User not found, please check the code'})
            }
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': 'https://nangie.framer.website'
            },
            'body': json.dumps({'message': 'Internal server error'})
        }
