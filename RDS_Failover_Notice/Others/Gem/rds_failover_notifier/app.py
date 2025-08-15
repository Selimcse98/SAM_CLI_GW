import json
import os
import boto3
from datetime import datetime

# Initialize the SNS client
sns_client = boto3.client('sns')

# Get the SNS Topic ARN from environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    """
    Handles an RDS failover event from EventBridge, formats a message,
    and publishes it to an SNS topic.
    """
    print("Received event: " + json.dumps(event, indent=2))

    if not SNS_TOPIC_ARN:
        print("Error: SNS_TOPIC_ARN environment variable not set.")
        raise ValueError("SNS Topic ARN is not configured.")

    try:
        # Extract relevant details from the event
        # The structure of the event payload is consistent for these event IDs
        event_time_str = event.get('time')
        region = event.get('region')
        detail = event.get('detail', {})
        source_id = detail.get('SourceIdentifier', 'N/A')
        event_id = detail.get('EventID', 'N/A')
        message_text = detail.get('Message', 'No message available.')

        # Format the timestamp for readability
        event_time = datetime.strptime(event_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_time = event_time.strftime('%Y-%m-%d %H:%M:%S UTC')

        # Create a clear subject and message for the notification
        subject = f"ALERT: AWS RDS Failover Detected for {source_id} in {region}"
        
        message_body = (
            f"--- RDS Failover Notification ---\n\n"
            f"An RDS failover event has been detected. Please review the details below.\n\n"
            f"Database Identifier: {source_id}\n"
            f"AWS Region: {region}\n"
            f"Event Time: {formatted_time}\n"
            f"Event ID: {event_id}\n\n"
            f"Message from AWS:\n\"{message_text}\"\n\n"
            f"This is an automated notification. Please check the AWS RDS console for the current status of your database."
        )

        print(f"Publishing message to SNS Topic: {SNS_TOPIC_ARN}")
        
        # Publish the message to the SNS topic
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message_body,
            Subject=subject
        )

        print("Successfully published message to SNS. Message ID: " + response['MessageId'])

        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent successfully!')
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        # Re-raise the exception to ensure the Lambda invocation is marked as failed
        raise e

