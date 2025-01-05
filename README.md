# Nangie Backend

A FastAPI application deployed on AWS Lambda that integrates with Google Sheets.

## Prerequisites

Before deploying, ensure you have:

1. AWS CLI installed and configured with your credentials
2. AWS SAM CLI installed:
   ```bash
   # For macOS
   brew install aws-sam-cli
   
   # For other systems, follow the official guide:
   # https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
   ```
3. Python 3.9 installed
4. Google Sheets API credentials stored in AWS Secrets Manager

## Setting up AWS Secrets Manager

Before deploying, you need to store your Google Sheets API credentials in AWS Secrets Manager:

1. Go to AWS Console > Secrets Manager
2. Click "Store a new secret"
3. Choose "Other type of secret"
4. Add your Google Sheets service account credentials as a JSON:
   ```json
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "your-private-key-id",
     "private_key": "your-private-key",
     "client_email": "your-service-account-email",
     "client_id": "your-client-id",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "your-cert-url"
   }
   ```
5. Click "Next"
6. Give your secret a name (e.g., "nangie-google-sheets-creds")
7. Complete the secret creation

This secret name will be used as the `GOOGLE_SHEETS_SECRET_NAME` environment variable during deployment.

## Environment Variables

Before deploying, make sure you have the following environment variables set:

- `GOOGLE_SHEETS_SECRET_NAME`: Name of the secret in AWS Secrets Manager containing Google Sheets credentials
- `SPREADSHEET_ID`: The ID of your Google Sheets spreadsheet
- `SHEET_NAME`: The name of the sheet to use (defaults to 'Sheet1')

## Deployment

1. Install AWS SAM CLI if you haven't already:
   ```bash
   brew install aws-sam-cli  # For macOS
   ```

2. Set required environment variables:
   ```bash
   export GOOGLE_SHEETS_SECRET_NAME="your-secret-name"
   export SPREADSHEET_ID="your-spreadsheet-id"
   export SHEET_NAME="your-sheet-name"
   ```

3. Run the deployment script:
   ```bash
   ./scripts/deploy.sh
   ```

The script will:
- Create a Lambda layer with all Python dependencies
- Build the SAM application
- Deploy the stack to AWS

## API Endpoints

The API will be deployed with the following endpoints:

- `GET /user/{user_id}`: Get user information from Google Sheets
- `POST /update/{user_id}`: Update user information in Google Sheets

## Architecture

The application uses:
- AWS Lambda for serverless compute
- API Gateway for REST API endpoints
- AWS Secrets Manager for Google Sheets credentials
- Lambda Layers for Python dependencies
- FastAPI for API implementation
- Mangum for AWS Lambda integration

## Security

- CORS is configured to only allow requests from `https://nangie.framer.website`
- AWS Secrets Manager is used to securely store Google Sheets credentials
- IAM roles are configured with least privilege access
