import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
sns = boto3.client('sns')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to monitor EventBridge rule changes from CloudTrail
    and send notifications via SNS
    """
    
    try:
        # Get SNS topic ARN from environment variables
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if not sns_topic_arn:
            raise ValueError("SNS_TOPIC_ARN environment variable not set")
        
        # Extract CloudTrail event details
        detail = event.get('detail', {})
        event_name = detail.get('eventName', 'Unknown')
        event_time = detail.get('eventTime', 'Unknown')
        user_identity = detail.get('userIdentity', {})
        source_ip = detail.get('sourceIPAddress', 'Unknown')
        user_agent = detail.get('userAgent', 'Unknown')
        
        # Extract user information
        user_type = user_identity.get('type', 'Unknown')
        user_name = user_identity.get('userName', user_identity.get('principalId', 'Unknown'))
        
        # Extract rule information from request parameters
        request_params = detail.get('requestParameters', {})
        rule_name = request_params.get('name', 'Unknown')
        rule_state = request_params.get('state', 'Unknown')
        
        # Create notification message based on event type
        message = create_notification_message(
            event_name, event_time, user_type, user_name, 
            source_ip, user_agent, rule_name, rule_state, detail
        )
        
        # Send SNS notification
        response = sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f'EventBridge Rule Alert: {event_name} - {rule_name}',
            Message=message
        )
        
        print(f"Successfully sent notification. MessageId: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification sent successfully',
                'messageId': response['MessageId'],
                'eventName': event_name,
                'ruleName': rule_name
            })
        }
        
    except Exception as e:
        error_msg = f"Error processing event: {str(e)}"
        print(error_msg)
        
        # Send error notification
        try:
            if sns_topic_arn:
                sns.publish(
                    TopicArn=sns_topic_arn,
                    Subject='EventBridge Monitor - Error',
                    Message=f"Error occurred while processing CloudTrail event:\n\n{error_msg}\n\nOriginal event:\n{json.dumps(event, indent=2)}"
                )
        except:
            pass  # Don't fail if error notification fails
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }

def create_notification_message(event_name: str, event_time: str, user_type: str, 
                              user_name: str, source_ip: str, user_agent: str,
                              rule_name: str, rule_state: str, detail: Dict) -> str:
    """
    Create a formatted notification message for the SNS topic
    """
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        formatted_time = event_time
    
    # Get AWS region and account
    aws_region = detail.get('awsRegion', 'Unknown')
    account_id = detail.get('recipientAccountId', 'Unknown')
    
    # Create action description
    action_descriptions = {
        'DeleteRule': 'DELETED',
        'PutRule': 'CREATED/MODIFIED',
        'DisableRule': 'DISABLED',
        'EnableRule': 'ENABLED',
        'PutTargets': 'TARGETS ADDED/MODIFIED',
        'RemoveTargets': 'TARGETS REMOVED'
    }
    
    action = action_descriptions.get(event_name, event_name)
    
    message = f"""
🚨 EVENTBRIDGE RULE ALERT 🚨

ACTION: {action}
RULE NAME: {rule_name}
RULE STATE: {rule_state}

EVENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Event Name: {event_name}
• Timestamp: {formatted_time}
• AWS Region: {aws_region}
• Account ID: {account_id}

USER INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• User Type: {user_type}
• User Name: {user_name}
• Source IP: {source_ip}
• User Agent: {user_agent}

SECURITY CONSIDERATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please verify this change was authorized. EventBridge rules control
event routing and automation, and unauthorized changes could impact
your infrastructure monitoring and automation workflows.

Raw CloudTrail Event ID: {detail.get('eventID', 'Unknown')}
"""

    return message.strip()

def format_json(data: Dict) -> str:
    """
    Format JSON data for readable display in notifications
    """
    return json.dumps(data, indent=2, default=str)