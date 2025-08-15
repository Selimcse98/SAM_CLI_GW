import json
import boto3
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Initialize AWS clients
sns_client = boto3.client('sns')
rds_client = boto3.client('rds')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for processing RDS failover events from EventBridge
    and sending SNS notifications.
    """
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Validate SNS topic ARN
        if not SNS_TOPIC_ARN:
            raise ValueError("SNS_TOPIC_ARN environment variable is not set")
        
        # Extract event details
        detail = event.get('detail', {})
        source = event.get('source')
        detail_type = event.get('detail-type')
        
        if source != 'aws.rds':
            logger.warning(f"Unexpected event source: {source}")
            return create_response(400, "Invalid event source")
        
        # Process the failover event
        notification_data = extract_failover_info(detail)
        
        if not notification_data:
            logger.error("Failed to extract failover information from event")
            return create_response(400, "Invalid event data")
        
        # Get additional RDS information
        enhanced_data = enhance_with_rds_info(notification_data)
        
        # Send SNS notification
        send_notification(enhanced_data, detail_type)
        
        logger.info("Successfully processed RDS failover event and sent notifications")
        return create_response(200, "Notification sent successfully")
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return create_response(500, f"Error: {str(e)}")

def extract_failover_info(detail: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract relevant failover information from the event detail.
    """
    try:
        source_id = detail.get('SourceId', 'Unknown')
        source_type = detail.get('SourceType', 'Unknown')
        event_categories = detail.get('EventCategories', [])
        message = detail.get('Message', 'No message available')
        event_time = detail.get('Date', datetime.utcnow().isoformat())
        
        # Determine if it's a cluster or instance failover
        is_cluster = source_type == 'db-cluster'
        resource_type = 'DB Cluster' if is_cluster else 'DB Instance'
        
        return {
            'source_id': source_id,
            'source_type': source_type,
            'resource_type': resource_type,
            'event_categories': event_categories,
            'message': message,
            'event_time': event_time,
            'is_cluster': is_cluster
        }
    except Exception as e:
        logger.error(f"Error extracting failover info: {str(e)}")
        return None

def enhance_with_rds_info(notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance notification data with additional RDS information.
    """
    try:
        source_id = notification_data['source_id']
        is_cluster = notification_data['is_cluster']
        
        if is_cluster:
            # Get cluster information
            response = rds_client.describe_db_clusters(DBClusterIdentifier=source_id)
            cluster = response['DBClusters'][0]
            
            notification_data.update({
                'engine': cluster.get('Engine', 'Unknown'),
                'engine_version': cluster.get('EngineVersion', 'Unknown'),
                'status': cluster.get('Status', 'Unknown'),
                'availability_zones': cluster.get('AvailabilityZones', []),
                'cluster_members': [member['DBInstanceIdentifier'] 
                                  for member in cluster.get('DBClusterMembers', [])],
                'writer_endpoint': cluster.get('Endpoint'),
                'reader_endpoint': cluster.get('ReaderEndpoint')
            })
        else:
            # Get instance information
            response = rds_client.describe_db_instances(DBInstanceIdentifier=source_id)
            instance = response['DBInstances'][0]
            
            notification_data.update({
                'engine': instance.get('Engine', 'Unknown'),
                'engine_version': instance.get('EngineVersion', 'Unknown'),
                'status': instance.get('DBInstanceStatus', 'Unknown'),
                'availability_zone': instance.get('AvailabilityZone', 'Unknown'),
                'instance_class': instance.get('DBInstanceClass', 'Unknown'),
                'endpoint': instance.get('Endpoint', {}).get('Address') if instance.get('Endpoint') else None
            })
            
    except Exception as e:
        logger.warning(f"Could not enhance with RDS info: {str(e)}")
        # Continue with basic information
        
    return notification_data

def send_notification(notification_data: Dict[str, Any], event_type: str) -> None:
    """
    Send SNS notification with failover information.
    """
    try:
        # Create email message (detailed)
        email_subject = format_email_subject(notification_data)
        email_message = format_email_message(notification_data, event_type)
        
        # Create SMS message (concise)
        sms_message = format_sms_message(notification_data)
        
        # Send notification with different messages for email and SMS
        message_structure = {
            'default': sms_message,
            'email': email_message,
            'sms': sms_message
        }
        
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=email_subject,
            Message=json.dumps(message_structure),
            MessageStructure='json'
        )
        
        logger.info(f"SNS notification sent. MessageId: {response['MessageId']}")
        
    except Exception as e:
        logger.error(f"Error sending SNS notification: {str(e)}")
        raise

def format_email_subject(data: Dict[str, Any]) -> str:
    """Format email subject line."""
    resource_type = data['resource_type']
    source_id = data['source_id']
    return f"🚨 RDS Failover Alert - {resource_type}: {source_id}"

def format_email_message(data: Dict[str, Any], event_type: str) -> str:
    """Format detailed email message."""
    message = f"""
RDS FAILOVER NOTIFICATION
========================

ALERT: A failover event has occurred for your RDS resource.

Resource Details:
-----------------
• Resource Type: {data['resource_type']}
• Resource ID: {data['source_id']}
• Engine: {data.get('engine', 'Unknown')}
• Engine Version: {data.get('engine_version', 'Unknown')}
• Current Status: {data.get('status', 'Unknown')}
• Event Time: {data['event_time']}

Event Information:
------------------
• Event Type: {event_type}
• Event Categories: {', '.join(data['event_categories'])}
• Message: {data['message']}

"""
    
    # Add cluster-specific information
    if data['is_cluster']:
        message += f"""
Cluster Configuration:
---------------------
• Availability Zones: {', '.join(data.get('availability_zones', []))}
• Cluster Members: {', '.join(data.get('cluster_members', []))}
• Writer Endpoint: {data.get('writer_endpoint', 'N/A')}
• Reader Endpoint: {data.get('reader_endpoint', 'N/A')}
"""
    else:
        message += f"""
Instance Configuration:
----------------------
• Availability Zone: {data.get('availability_zone', 'Unknown')}
• Instance Class: {data.get('instance_class', 'Unknown')}
• Endpoint: {data.get('endpoint', 'N/A')}
"""
    
    message += f"""

Recommended Actions:
-------------------
1. Verify application connectivity to the database
2. Check application logs for any connection errors
3. Monitor RDS performance metrics
4. Review CloudWatch logs for additional details

This is an automated notification from your RDS monitoring system.
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    return message

def format_sms_message(data: Dict[str, Any]) -> str:
    """Format concise SMS message."""
    resource_type = data['resource_type']
    source_id = data['source_id']
    status = data.get('status', 'Unknown')
    
    return (f"RDS FAILOVER ALERT: {resource_type} '{source_id}' "
            f"has failed over. Status: {status}. Check email for details.")

def create_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create standardized Lambda response."""
    return {
        'statusCode': status_code,
        'body': json.dumps({
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
    }