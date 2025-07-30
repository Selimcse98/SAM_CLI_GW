import os
import json
import boto3
from datetime import datetime

# Initialize the SNS client
sns_client = boto3.client('sns')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    This function is triggered by an EventBridge rule.
    It formats and sends a notification to an SNS topic when an
    EventBridge rule is created, modified, or deleted.
    """
    print(f"Received event: {json.dumps(event)}")

    if not SNS_TOPIC_ARN:
        print("Error: SNS_TOPIC_ARN environment variable is not set.")
        return {'statusCode': 500}

    try:
        # Extract relevant details from the CloudTrail event
        detail = event.get('detail', {})
        event_name = detail.get('eventName')
        aws_region = detail.get('awsRegion')
        principal_id = detail.get('userIdentity', {}).get('principalId')
        rule_name = detail.get('requestParameters', {}).get('name')

        # Determine the action for the notification subject
        action = "modified/created" if event_name == "PutRule" else "deleted"

        # Create the notification message
        subject = f"Alert: EventBridge Rule {action.upper()} in {aws_region}"
        message = (
            f"An EventBridge rule has been {action}.\n\n"
            f"Rule Name: {rule_name}\n"
            f"Region: {aws_region}\n"
            f"Event Time: {event.get('time')}\n"
            f"Principal ID: {principal_id}\n\n"
            f"This is an automated notification. Please review this change in the AWS Console if it was unexpected.\n\n"
            f"Event Detail:\n{json.dumps(detail, indent=2)}"
        )

        # Publish the message to the SNS topic
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        
        print(f"Successfully sent notification. Message ID: {response['MessageId']}")
        return {'statusCode': 200}

    except Exception as e:
        print(f"Error processing event and sending notification: {str(e)}")
        # Optionally, you could send the raw event to a dead-letter queue
        # or another SNS topic for error handling.
        raise e