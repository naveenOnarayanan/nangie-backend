# Google Sheets API Lambda Service

A FastAPI service that integrates with Google Sheets API using AWS Secrets Manager for credential management, deployed as an AWS Lambda function.

## Features

- Read user information from Google Sheets using ID
- Update user information in Google Sheets
- Secure credential management using AWS Secrets Manager
- AWS Lambda deployment ready

## Prerequisites

1. AWS Account with:
   - Lambda access
   - Secrets Manager access
   - IAM permissions
2. Google Sheets API credentials
3. Python 3.9+

## Setup

1. **AWS Secrets Manager Setup**
   - Create a new secret in AWS Secrets Manager
   - Store your Google Sheets API credentials JSON in the secret
   - Note the secret name for configuration

2. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Update the values with your configuration:
     ```
     AWS_REGION=your_aws_region
     SPREADSHEET_ID=your_google_spreadsheet_id
     SHEET_NAME=your_sheet_name
     GOOGLE_SHEETS_SECRET_NAME=your_aws_secret_name
     ```

3. **Google Sheets Setup**
   - Ensure your spreadsheet has the following columns:
     - id (Column A)
     - name (Column B)
     - email (Column C)
     - phone (Column D)
   - Share the spreadsheet with the service account email from your Google API credentials

## Local Development

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the service locally:
   ```bash
   uvicorn app.main:app --reload
   ```

## AWS Lambda Deployment

1. **Create Deployment Package**
   ```bash
   pip install -r requirements.txt --target ./package
   cd package
   zip -r ../deployment.zip .
   cd ..
   zip -g deployment.zip app/main.py
   ```

2. **Create Lambda Function**
   - Create a new Lambda function in AWS Console
   - Runtime: Python 3.9
   - Handler: app.main.handler
   - Upload the deployment.zip file
   - Set environment variables in Lambda configuration
   - Configure memory and timeout settings (recommended: 256MB RAM, 30s timeout)

3. **Configure API Gateway**
   - Create a new HTTP API Gateway
   - Add routes:
     - GET /user/{user_id}
     - POST /update/{user_id}
   - Integrate with your Lambda function

4. **Set up IAM Permissions**
   - Create an IAM role for the Lambda function with:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "secretsmanager:GetSecretValue"
           ],
           "Resource": "arn:aws:secretsmanager:*:*:secret:your-secret-name*"
         }
       ]
     }
     ```

## API Endpoints

### Get User Information
```http
GET /user/{user_id}
```
Returns user information from the spreadsheet based on the ID.

### Update User Information
```http
POST /update/{user_id}
```
Updates user information in the spreadsheet.

Request body:
```json
{
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "1234567890"
  }
}
```

## Security Considerations

- Configure API Gateway with appropriate authorization
- Use AWS WAF for additional security
- Keep AWS credentials secure
- Regularly rotate API keys and credentials
- Monitor Lambda execution and implement appropriate alarms
- Set up CloudWatch logs for monitoring

## Error Handling

The service includes error handling for:
- Missing/invalid credentials
- Spreadsheet access issues
- User not found
- Invalid update data
- AWS Secrets Manager access issues
- Lambda execution timeouts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
