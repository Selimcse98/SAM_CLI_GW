import boto3
import os
import json
from datetime import datetime

def lambda_handler(event, context):
    asg_name = os.environ['ASG_NAME']
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']
    
    autoscaling = boto3.client('autoscaling')
    sns = boto3.client('sns')
    
    try:
        # Get current ASG configuration
        response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        
        if not response['AutoScalingGroups']:
            raise Exception(f"Auto Scaling Group {asg_name} not found")
        
        asg = response['AutoScalingGroups'][0]
        current_min = asg['MinSize']
        current_desired = asg['DesiredCapacity']
        max_capacity = asg['MaxSize']
        
        # Update ASG to decrease capacity
        autoscaling.update_auto_scaling_group(
            AutoScalingGroupName=asg_name,
            MinSize=1,
            DesiredCapacity=1
        )
        
        # Prepare notification message
        message = f"""
        Auto Scaling Group Capacity Decreased Successfully!
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Auto Scaling Group: {asg_name}
        
        Previous Configuration:
        - Min Size: {current_min}
        - Desired Capacity: {current_desired}
        - Max Size: {max_capacity}
        
        New Configuration:
        - Min Size: 1
        - Desired Capacity: 1
        - Max Size: {max_capacity}
        
        This change was made as part of the daily schedule to reduce capacity during off-hours.
        """
        
        # Send SNS notification
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"ASG Capacity Decreased: {asg_name}",
            Message=message
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'ASG capacity decreased successfully',
                'previous_min': current_min,
                'previous_desired': current_desired,
                'new_min': 1,
                'new_desired': 1
            })
        }
        
    except Exception as e:
        error_message = f"Error decreasing ASG capacity: {str(e)}"
        
        # Send error notification
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f"ERROR: ASG Capacity Decrease Failed - {asg_name}",
            Message=f"Error occurred while decreasing ASG capacity:\n\n{error_message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        raise e
