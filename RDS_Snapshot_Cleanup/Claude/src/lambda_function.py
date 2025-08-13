import json
import boto3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RdsSnapshotCleaner:
    def __init__(self):
        self.sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        self.snapshot_filter = os.environ.get('SNAPSHOT_FILTER', 'insuranceplatform-prod-deployment-')
        self.default_retention_days = int(os.environ.get('DEFAULT_RETENTION_DAYS', '35'))
        self.environment = os.environ.get('ENVIRONMENT', 'prod')
        
        # Initialize AWS clients
        self.rds_client = boto3.client('rds')
        self.sns_client = boto3.client('sns')
        
        # Track cleanup results
        self.deleted_cluster_snapshots = []
        self.deleted_instance_snapshots = []
        self.failed_deletions = []
        self.total_snapshots_checked = 0
    
    def get_retention_days_from_tags(self, resource_arn: str) -> int:
        """Get retention days from resource tags, fallback to default"""
        try:
            response = self.rds_client.list_tags_for_resource(ResourceName=resource_arn)
            tags = response.get('TagList', [])
            
            for tag in tags:
                if tag['Key'] == 'RetentionDays':
                    return int(tag['Value'])
                    
        except Exception as e:
            logger.warning(f"Could not retrieve tags for {resource_arn}: {str(e)}")
        
        return self.default_retention_days
    
    def is_snapshot_expired(self, snapshot_create_time: datetime, retention_days: int) -> bool:
        """Check if snapshot is older than retention period"""
        # Remove timezone info for comparison
        if snapshot_create_time.tzinfo:
            snapshot_create_time = snapshot_create_time.replace(tzinfo=None)
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return snapshot_create_time < cutoff_date
    
    def cleanup_cluster_snapshots(self) -> List[Dict]:
        """Clean up RDS cluster snapshots"""
        logger.info("Starting cluster snapshot cleanup...")
        
        try:
            # Get all manual cluster snapshots
            paginator = self.rds_client.get_paginator('describe_db_cluster_snapshots')
            page_iterator = paginator.paginate(
                SnapshotType='manual',
                IncludeShared=False,
                IncludePublic=False
            )
            
            for page in page_iterator:
                for snapshot in page['DBClusterSnapshots']:
                    self.total_snapshots_checked += 1
                    snapshot_id = snapshot['DBClusterSnapshotIdentifier']
                    
                    # Filter snapshots by name pattern
                    if self.snapshot_filter not in snapshot_id:
                        continue
                    
                    logger.info(f"Processing cluster snapshot: {snapshot_id}")
                    
                    # Get retention days from tags
                    snapshot_arn = snapshot['DBClusterSnapshotArn']
                    retention_days = self.get_retention_days_from_tags(snapshot_arn)
                    
                    # Check if snapshot is expired
                    create_time = snapshot['SnapshotCreateTime']
                    if self.is_snapshot_expired(create_time, retention_days):
                        try:
                            logger.info(f"Deleting expired cluster snapshot: {snapshot_id}")
                            self.rds_client.delete_db_cluster_snapshot(
                                DBClusterSnapshotIdentifier=snapshot_id
                            )
                            
                            self.deleted_cluster_snapshots.append({
                                'snapshot_id': snapshot_id,
                                'cluster_id': snapshot['DBClusterIdentifier'],
                                'create_time': create_time.isoformat(),
                                'retention_days': retention_days,
                                'size_gb': snapshot.get('AllocatedStorage', 'N/A')
                            })
                            
                        except Exception as e:
                            error_msg = f"Failed to delete cluster snapshot {snapshot_id}: {str(e)}"
                            logger.error(error_msg)
                            self.failed_deletions.append({
                                'snapshot_id': snapshot_id,
                                'type': 'cluster',
                                'error': str(e)
                            })
                    else:
                        logger.info(f"Cluster snapshot {snapshot_id} not expired (age: {(datetime.utcnow() - create_time.replace(tzinfo=None)).days} days, retention: {retention_days} days)")
                        
        except Exception as e:
            logger.error(f"Error during cluster snapshot cleanup: {str(e)}")
            raise
    
    def cleanup_instance_snapshots(self) -> List[Dict]:
        """Clean up RDS instance snapshots"""
        logger.info("Starting instance snapshot cleanup...")
        
        try:
            # Get all manual instance snapshots
            paginator = self.rds_client.get_paginator('describe_db_snapshots')
            page_iterator = paginator.paginate(
                SnapshotType='manual',
                IncludeShared=False,
                IncludePublic=False
            )
            
            for page in page_iterator:
                for snapshot in page['DBSnapshots']:
                    self.total_snapshots_checked += 1
                    snapshot_id = snapshot['DBSnapshotIdentifier']
                    
                    # Filter snapshots by name pattern
                    if self.snapshot_filter not in snapshot_id:
                        continue
                    
                    logger.info(f"Processing instance snapshot: {snapshot_id}")
                    
                    # Get retention days from tags
                    snapshot_arn = snapshot['DBSnapshotArn']
                    retention_days = self.get_retention_days_from_tags(snapshot_arn)
                    
                    # Check if snapshot is expired
                    create_time = snapshot['SnapshotCreateTime']
                    if self.is_snapshot_expired(create_time, retention_days):
                        try:
                            logger.info(f"Deleting expired instance snapshot: {snapshot_id}")
                            self.rds_client.delete_db_snapshot(
                                DBSnapshotIdentifier=snapshot_id
                            )
                            
                            self.deleted_instance_snapshots.append({
                                'snapshot_id': snapshot_id,
                                'instance_id': snapshot['DBInstanceIdentifier'],
                                'create_time': create_time.isoformat(),
                                'retention_days': retention_days,
                                'size_gb': snapshot.get('AllocatedStorage', 'N/A')
                            })
                            
                        except Exception as e:
                            error_msg = f"Failed to delete instance snapshot {snapshot_id}: {str(e)}"
                            logger.error(error_msg)
                            self.failed_deletions.append({
                                'snapshot_id': snapshot_id,
                                'type': 'instance',
                                'error': str(e)
                            })
                    else:
                        logger.info(f"Instance snapshot {snapshot_id} not expired (age: {(datetime.utcnow() - create_time.replace(tzinfo=None)).days} days, retention: {retention_days} days)")
                        
        except Exception as e:
            logger.error(f"Error during instance snapshot cleanup: {str(e)}")
            raise
    
    def send_notification(self):
        """Send SNS notification with cleanup results"""
        if not self.sns_topic_arn:
            logger.warning("SNS_TOPIC_ARN not configured, skipping notification")
            return
        
        total_deleted = len(self.deleted_cluster_snapshots) + len(self.deleted_instance_snapshots)
        total_failed = len(self.failed_deletions)
        
        # Create notification message
        subject = f"RDS Snapshot Cleanup Report - {self.environment.upper()}"
        
        message_parts = [
            f"RDS Snapshot Cleanup Completed - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"Environment: {self.environment.upper()}",
            f"Filter: {self.snapshot_filter}",
            "",
            "SUMMARY:",
            f"• Total snapshots checked: {self.total_snapshots_checked}",
            f"• Successfully deleted: {total_deleted}",
            f"• Failed deletions: {total_failed}",
            ""
        ]
        
        # Add deleted cluster snapshots
        if self.deleted_cluster_snapshots:
            message_parts.append("DELETED CLUSTER SNAPSHOTS:")
            for snapshot in self.deleted_cluster_snapshots:
                message_parts.append(
                    f"• {snapshot['snapshot_id']} (Cluster: {snapshot['cluster_id']}, "
                    f"Created: {snapshot['create_time']}, Size: {snapshot['size_gb']}GB)"
                )
            message_parts.append("")
        
        # Add deleted instance snapshots
        if self.deleted_instance_snapshots:
            message_parts.append("DELETED INSTANCE SNAPSHOTS:")
            for snapshot in self.deleted_instance_snapshots:
                message_parts.append(
                    f"• {snapshot['snapshot_id']} (Instance: {snapshot['instance_id']}, "
                    f"Created: {snapshot['create_time']}, Size: {snapshot['size_gb']}GB)"
                )
            message_parts.append("")
        
        # Add failed deletions
        if self.failed_deletions:
            message_parts.append("FAILED DELETIONS:")
            for failure in self.failed_deletions:
                message_parts.append(
                    f"• {failure['snapshot_id']} ({failure['type']}): {failure['error']}"
                )
            message_parts.append("")
        
        # Add summary message
        if total_deleted == 0 and total_failed == 0:
            message_parts.append("No expired snapshots found for cleanup.")
        
        message = "\n".join(message_parts)
        
        try:
            self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Subject=subject,
                Message=message
            )
            logger.info("Notification sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    def run_cleanup(self) -> Dict:
        """Execute the complete cleanup process"""
        logger.info(f"Starting RDS snapshot cleanup with filter: {self.snapshot_filter}")
        
        try:
            # Clean up cluster snapshots
            self.cleanup_cluster_snapshots()
            
            # Clean up instance snapshots
            self.cleanup_instance_snapshots()
            
            # Send notification
            self.send_notification()
            
            # Prepare response
            result = {
                'status': 'completed',
                'total_snapshots_checked': self.total_snapshots_checked,
                'deleted_cluster_snapshots': len(self.deleted_cluster_snapshots),
                'deleted_instance_snapshots': len(self.deleted_instance_snapshots),
                'failed_deletions': len(self.failed_deletions),
                'deleted_snapshots': self.deleted_cluster_snapshots + self.deleted_instance_snapshots,
                'errors': self.failed_deletions
            }
            
            logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Cleanup process failed: {str(e)}"
            logger.error(error_msg)
            
            # Send error notification
            if self.sns_topic_arn:
                try:
                    self.sns_client.publish(
                        TopicArn=self.sns_topic_arn,
                        Subject=f"RDS Snapshot Cleanup FAILED - {self.environment.upper()}",
                        Message=f"RDS Snapshot cleanup failed with error:\n\n{error_msg}"
                    )
                except Exception as sns_error:
                    logger.error(f"Failed to send error notification: {str(sns_error)}")
            
            raise


def lambda_handler(event, context):
    """Lambda entry point"""
    logger.info(f"Starting RDS snapshot cleanup lambda. Event: {json.dumps(event)}")
    
    try:
        cleaner = RdsSnapshotCleaner()
        result = cleaner.run_cleanup()
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'failed',
                'error': str(e)
            })
        }


# For testing locally
if __name__ == "__main__":
    # Set environment variables for local testing
    os.environ['SNAPSHOT_FILTER'] = 'insuranceplatform-prod-deployment-'
    os.environ['DEFAULT_RETENTION_DAYS'] = '35'
    os.environ['ENVIRONMENT'] = 'dev'
    
    # Mock event and context for testing
    test_event = {}
    test_context = type('MockContext', (), {
        'function_name': 'test-function',
        'function_version': '1',
        'memory_limit_in_mb': 512
    })()
    
    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))