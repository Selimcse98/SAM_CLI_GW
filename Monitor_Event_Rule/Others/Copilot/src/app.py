import boto3
import os

def lambda_handler(event, context):
    sns = boto3.client('sns')
    message = f"⚠️ EventBridge rule change detected:\n{event['detail']['eventName']}\n"
    message += f"Initiated by: {event['detail'].get('userIdentity', {}).get('arn', 'Unknown')}"
    
    sns.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Message=message,
        Subject="Alert: EventBridge Rule Change"
    )
