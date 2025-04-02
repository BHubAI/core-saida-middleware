#!/bin/bash

# Set variables
LAMBDA_FUNCTION_NAME="StartOrchestratorProcess"
ZIP_FILE="lambda_starter.zip"

# Create zip file
echo "Creating deployment package..."
zip $ZIP_FILE lambda_starter.py

# Update Lambda function code
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION_NAME \
    --zip-file fileb://$ZIP_FILE

# Clean up
rm $ZIP_FILE

echo "Deployment complete!"
