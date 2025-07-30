import json
import boto3
import os

sns = boto3.client('sns')

def lambda_handler(event, context):
    # Extract relevant information from the CloudTrail event
    print(json.dumps(event))
    detail = event.get('detail', {})
    event_name = detail.get('eventName', '')
    rule_name = detail.get('requestParameters', {}).get('name', 'UNKNOWN')
    user_identity = detail.get('userIdentity', {}).get('arn', 'UNKNOWN')
    event_time = detail.get('eventTime', 'UNKNOWN')
    
    # Prepare the notification message
    subject = f"AWS EventBridge Rule {event_name} Alert"
    message = f"""
    EventBridge Rule Modification Detected!
    
    Event: {event_name}
    Rule Name: {rule_name}
    Performed By: {user_identity}
    Time: {event_time}
    
    This is an automated notification for changes to EventBridge rules.

    Here is the complete CloudTrail event:
    {json.dumps(event)}
    """
    
    # Publish to SNS
    try:
        response = sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=message,
            Subject=subject
        )
        print(f"Notification sent: {response}")
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        raise
    
    return {
        'statusCode': 200,
        'body': json.dumps('Notification processed successfully!')
    }