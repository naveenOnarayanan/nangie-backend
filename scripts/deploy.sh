#!/bin/bash
set -e

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "AWS SAM CLI is not installed. Please install it first:"
    echo "For macOS: brew install aws-sam-cli"
    echo "For other systems, follow: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
    exit 1
fi

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd $REPO_ROOT

# Create package directory for Lambda layer
echo "Creating Lambda layer package..."
rm -rf package/
mkdir -p package/python
pip install -r requirements.txt --target package/python

# Build SAM application
echo "Building SAM application..."
sam build

# Deploy using SAM
echo "Deploying with SAM..."
sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name nangie-backend \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    GoogleSheetsSecretName=${GOOGLE_SHEETS_SECRET_NAME} \
    SpreadsheetId=${SPREADSHEET_ID} \
    SheetName=${SHEET_NAME} \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

echo "Deployment complete!"
