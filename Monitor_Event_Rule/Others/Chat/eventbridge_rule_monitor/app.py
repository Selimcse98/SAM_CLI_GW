import os
import json
import boto3

sns = boto3.client('sns')

def lambda_handler(event, context):
    topic_arn = os.environ['SNS_TOPIC_ARN']
    
    message = {
        'EventName': event['detail']['eventName'],
        'UserIdentity': event['detail'].get('userIdentity', {}),
        'EventTime': event['detail'].get('eventTime'),
        'RequestParameters': event['detail'].get('requestParameters')
    }

    sns.publish(
        TopicArn=topic_arn,
        Subject='Alert: EventBridge Rule Modified or Deleted',
        Message=json.dumps(message, indent=2)
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent!')
    }
