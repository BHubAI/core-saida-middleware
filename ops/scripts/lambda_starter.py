import json
import logging

import urllib3


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Create a handler that sends logs to CloudWatch
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

http = urllib3.PoolManager()


def lambda_handler(event, context):
    try:
        logger.info(f"Received event from EventBridge: {json.dumps(event)}")

        # Parse input parameters
        url = event.get("url")
        process_key = event.get("process_key")

        logger.info(f"Params received from Bridge - URL: {url}, Process Key: {process_key}")
        if not url or not process_key:
            logger.error("Missing required parameters: url or process_key")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Both url and process_key parameters are required"}),
            }

        # Prepare the request payload
        payload = {"process_key": process_key}

        headers = {"Content-Type": "application/json", "ngrok-skip-browser-warning": "1"}

        logger.info(f"Making request to {url} with payload: {json.dumps(payload)}")

        # Make the HTTP POST request
        response = http.request("POST", url, body=json.dumps(payload), headers=headers)

        logger.info(f"Response from Core - Status: {response.status}, Body: {response.data.decode('utf-8')}")

        return {"statusCode": response.status, "headers": {"Content-Type": "application/json"}}

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
