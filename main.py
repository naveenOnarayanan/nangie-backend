from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from contextlib import contextmanager
import os
import uvicorn
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = FastAPI()

HEADERS = [
    "accessCode",
    "maxGuests",
    "partyName",
    "confirmedGuests",
    "phoneNumber",
    "emailAddress",
    "rsvpAsk",
    "dietaryRestrictions",
    "hotelAccommodations",
    "questions",
    "rawNames",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class UserUpdate(BaseModel):
    """Model for user update data"""

    model_config = ConfigDict(extra="allow")  # Allow extra fields
    data: Dict[str, str]


# Create a service singleton
_sheets_service = None


@contextmanager
def get_sheets_service():
    """Context manager for Google Sheets API service"""
    global _sheets_service
    try:
        if _sheets_service is None:
            credentials = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS", "{}"))
            creds = service_account.Credentials.from_service_account_info(
                credentials, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            _sheets_service = build("sheets", "v4", credentials=creds)
        yield _sheets_service
    except Exception as e:
        print(f"Error with sheets service: {str(e)}")
        if _sheets_service:
            _sheets_service.close()
            _sheets_service = None
        raise HTTPException(
            status_code=500, detail="Could not initialize Google Sheets service"
        )


def find_user_row(service, spreadsheet_id: str, user_id: str) -> Optional[int]:
    """Find user row in spreadsheet by ID"""
    range_name = f"{os.getenv('SHEET_NAME', 'Sheet1')}!A:A"
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )

    values = result.get("values", [])
    for idx, row in enumerate(values):
        if row and row[0] == user_id:
            return idx + 1
    return None


@app.get("/user/{user_id}")
async def get_user(user_id: str) -> Dict[str, str]:
    """Get user information from Google Sheets"""
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise HTTPException(status_code=500, detail="Spreadsheet ID not configured")

    with get_sheets_service() as service:
        row_num = find_user_row(service, spreadsheet_id, user_id)
        if not row_num:
            raise HTTPException(status_code=404, detail="User not found")

        range_name = f"{os.getenv('SHEET_NAME', 'Sheet1')}!{row_num}:{row_num}"
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )

        values = result.get("values", [[]])[0]
        headers = HEADERS

        return dict(zip(headers, values))


@app.post("/update/{user_id}")
async def update_user(user_id: str, update_data: UserUpdate) -> Dict[str, str]:
    """Update user information in Google Sheets"""
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise HTTPException(status_code=500, detail="Spreadsheet ID not configured")

    with get_sheets_service() as service:
        row_num = find_user_row(service, spreadsheet_id, user_id)
        if not row_num:
            raise HTTPException(status_code=404, detail="User not found")

        # Get current row data
        range_name = f"{os.getenv('SHEET_NAME', 'Sheet1')}!{row_num}:{row_num}"
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )

        current_values = result.get("values", [[]])[0]
        headers = HEADERS
        # Remove rawNames from HEADERS
        headers.remove("rawNames")
        current_data = dict(zip(headers, current_values))

        # Update with new data
        updated_data = {**current_data, **update_data.data}
        new_values = [[updated_data[header] for header in headers]]

        body = {"values": new_values}

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()

        return {"message": "User updated successfully"}


# Add cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    global _sheets_service
    if _sheets_service:
        _sheets_service.close()
        _sheets_service = None


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
