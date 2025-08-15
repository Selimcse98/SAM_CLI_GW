import os
import json
import boto3

sns = boto3.client('sns')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    detail = event.get("detail", {})
    instance_id = detail.get("SourceIdentifier", "Unknown instance")
    message = detail.get("Message", "No message provided")

    subject = f"RDS Failover Event: {instance_id}"
    body = f"""
    AWS RDS Failover Detected
    Instance: {instance_id}
    Message: {message}
    Event Time: {event.get("time")}
    Region: {event.get("region")}
    """

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=body.strip()
    )

    return {"status": "Notification sent"}
