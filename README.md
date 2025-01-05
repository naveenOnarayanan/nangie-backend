# Nangie Backend

A FastAPI application that integrates with Google Sheets. Can be deployed either on AWS Lambda or using buildpacks on platforms like Heroku, Google Cloud Run, or similar services.

## Deployment Options

This application supports three deployment methods:
1. AWS Lambda deployment (original method)
2. Buildpack deployment
3. Docker deployment

Choose the deployment method that best suits your needs.

## Docker Deployment

### Prerequisites for Docker Deployment

Before deploying with Docker, ensure you have:
1. Docker installed on your system
2. Google Sheets API credentials
3. Access to a container registry (optional, for production deployment)

### Building and Running with Docker

1. Build the Docker image:
```bash
docker build -t nangie-backend .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e GOOGLE_SHEETS_CREDENTIALS='{"type": "service_account", ...}' \
  -e SPREADSHEET_ID='your_spreadsheet_id' \
  -e SHEET_NAME='Sheet1' \
  nangie-backend
```

### Docker Compose (Optional)

Create a `docker-compose.yml` file for easier development:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_SHEETS_CREDENTIALS={"type": "service_account", ...}
      - SPREADSHEET_ID=your_spreadsheet_id
      - SHEET_NAME=Sheet1
```

Then run:
```bash
docker-compose up
```

## Buildpack Deployment

### Prerequisites for Buildpack Deployment

Before deploying with buildpacks, ensure you have:
1. A platform that supports buildpacks (Heroku, Google Cloud Run, etc.)
2. Google Sheets API credentials
3. Python 3.11 (specified in runtime.txt)

### Environment Variables for Buildpack

Set the following environment variables on your deployment platform:
```bash
GOOGLE_SHEETS_CREDENTIALS={"type": "service_account", ...}  # Your service account JSON
SPREADSHEET_ID=your_spreadsheet_id
SHEET_NAME=Sheet1  # Optional, defaults to Sheet1
PORT=8000  # Optional, usually set by the platform
```

### Files for Buildpack Deployment

The following files are used for buildpack deployment:
- `Procfile`: Defines the web process
- `runtime.txt`: Specifies Python version
- `requirements.txt`: Lists Python dependencies

## AWS Lambda Deployment

### Prerequisites for AWS Lambda

Before deploying to AWS Lambda, ensure you have:

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
