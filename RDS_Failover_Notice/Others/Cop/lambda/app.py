import os
import boto3
import json

sns = boto3.client('sns')
topic_arn = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    detail = event.get('detail', {})
    instance_id = detail.get('SourceIdentifier', 'Unknown')
    message = detail.get('Message', 'No message provided')

    notification = {
        "RDS Instance": instance_id,
        "Event Message": message,
        "Event Time": event.get('time')
    }

    sns.publish(
        TopicArn=topic_arn,
        Subject="🚨 RDS Failover Detected",
        Message=json.dumps(notification, indent=2)
    )

    return {
        "statusCode": 200,
        "body": json.dumps("Notification sent.")
    }
