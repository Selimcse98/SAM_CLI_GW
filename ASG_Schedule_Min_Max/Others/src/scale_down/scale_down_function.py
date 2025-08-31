import os
import boto3
import json
from botocore.exceptions import ClientError

# Initialize AWS clients
autoscaling = boto3.client('autoscaling')
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    This function scales down an Auto Scaling Group by setting its desired and minimum capacities to 1.
    """
    asg_name = os.environ.get('ASG_NAME')
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')

    if not asg_name or not sns_topic_arn:
        print("Error: ASG_NAME and SNS_TOPIC_ARN environment variables must be set.")
        return {'statusCode': 500, 'body': json.dumps('Configuration error.')}

    try:
        # Get current ASG state
        response = autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
        if not response['AutoScalingGroups']:
            message = f"Auto Scaling Group '{asg_name}' not found."
            print(f"Error: {message}")
            send_sns_notification(sns_topic_arn, f"Scale-Down Failed for {asg_name}", message)
            return {'statusCode': 404, 'body': json.dumps(message)}

        asg = response['AutoScalingGroups'][0]
        current_desired = asg['DesiredCapacity']
        current_min = asg['MinSize']
        current_max = asg['MaxSize']

        # Scale down the ASG
        autoscaling.update_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            MinSize=1,
            DesiredCapacity=1
        )

        message = (
            f"Successfully scaled down the Auto Scaling Group '{asg_name}'.\n\n"
            f"Previous State:\n"
            f"- Desired Capacity: {current_desired}\n"
            f"- Min Size: {current_min}\n"
            f"- Max Size: {current_max}\n\n"
            f"New State:\n"
            f"- Desired Capacity: 1\n"
            f"- Min Size: 1"
        )
        print(message)
        send_sns_notification(sns_topic_arn, f"Scale-Down Successful for {asg_name}", message)

        return {'statusCode': 200, 'body': json.dumps(message)}

    except ClientError as e:
        error_message = f"An AWS client error occurred: {e.response['Error']['Message']}"
        print(error_message)
        send_sns_notification(sns_topic_arn, f"Scale-Down Failed for {asg_name}", error_message)
        return {'statusCode': 500, 'body': json.dumps(error_message)}
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        print(error_message)
        send_sns_notification(sns_topic_arn, f"Scale-Down Failed for {asg_name}", error_message)
        return {'statusCode': 500, 'body': json.dumps(error_message)}

def send_sns_notification(topic_arn, subject, message):
    """
    Sends a notification to the specified SNS topic.
    """
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print(f"Error sending SNS notification: {e.response['Error']['Message']}")
