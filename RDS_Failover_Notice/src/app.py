import json
import boto3
import os

def lambda_handler(event, context):
    print(json.dumps(event))
    sns = boto3.client('sns')
    
    # Extract relevant information from the event
    detail = event.get('detail', {})
    event_id = detail.get('EventID', 'N/A')
    event_message = detail.get('Message', 'N/A')
    source_id = detail.get('SourceIdentifier', 'N/A')
    source_arn = detail.get('SourceArn', 'N/A')
    event_time = detail.get('EventTime', 'N/A')
    
    # Determine if this is a reader or writer failover
    failover_type = "unknown"
    if "reader" in event_message.lower():
        failover_type = "READER"
    elif "writer" in event_message.lower():
        failover_type = "WRITER"
    
    # Prepare the notification message
    subject = f"AWS RDS {failover_type} Failover Notification"
    message = f"""
    RDS Failover Event Detected!
    
    Event Type: {failover_type} Failover
    Event ID: {event_id}
    Event Time: {event_time}
    Source Identifier: {source_id}
    Source ARN: {source_arn}
    
    Message Details:
    {event_message}
    
    Please investigate the RDS instance to ensure proper operation.
    """
    
    # Publish to SNS topic
    try:
        response = sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Subject=subject,
            Message=message
        )
        print(f"Notification sent: {response['MessageId']}")
        print(message)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent successfully!')
        }
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error sending notification')
        }
    