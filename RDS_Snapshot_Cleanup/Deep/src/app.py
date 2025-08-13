import boto3
from datetime import datetime, timedelta
import os

# Initialize clients
rds_client = boto3.client('rds')
sns_client = boto3.client('sns')

def lambda_handler(event, context):
    # Configuration
    snapshot_name_filter = "insuranceplatform-prod-deployment-"
    retention_tag_key = "RetentionDays"
    default_retention_days = 35
    
    # Get current time
    now = datetime.utcnow()
    
    # Find all manual snapshots with our naming pattern
    snapshots_to_delete = []
    response = rds_client.describe_db_cluster_snapshots(
        SnapshotType='manual'
    )
    
    for snapshot in response['DBClusterSnapshots']:
        # Check if snapshot matches our naming pattern
        if snapshot_name_filter.lower() in snapshot['DBClusterSnapshotIdentifier'].lower():
            # Get snapshot creation time
            create_time = snapshot['SnapshotCreateTime'].replace(tzinfo=None)
            age = (now - create_time).days
            
            # Get retention days from tags (default to 35 if not found)
            retention_days = default_retention_days
            tags = rds_client.list_tags_for_resource(
                ResourceName=snapshot['DBClusterSnapshotArn']
            )['TagList']
            
            for tag in tags:
                if tag['Key'] == retention_tag_key:
                    try:
                        retention_days = int(tag['Value'])
                    except ValueError:
                        pass  # Use default if tag value isn't a number
            
            # Check if snapshot is older than retention period
            if age > retention_days:
                snapshots_to_delete.append({
                    'SnapshotId': snapshot['DBClusterSnapshotIdentifier'],
                    'CreateTime': str(snapshot['SnapshotCreateTime']),
                    'AgeDays': age,
                    'ClusterId': snapshot['DBClusterIdentifier']
                })
    
    # Delete old snapshots and collect results
    deletion_results = []
    for snapshot in snapshots_to_delete:
        try:
            rds_client.delete_db_cluster_snapshot(
                DBClusterSnapshotIdentifier=snapshot['SnapshotId']
            )
            deletion_results.append({
                'Status': 'SUCCESS',
                'Message': f"Deleted snapshot {snapshot['SnapshotId']} (created {snapshot['CreateTime']}, age {snapshot['AgeDays']} days)",
                **snapshot
            })
        except Exception as e:
            deletion_results.append({
                'Status': 'FAILED',
                'Message': f"Failed to delete snapshot {snapshot['SnapshotId']}: {str(e)}",
                **snapshot
            })
    
    # Send SNS notification
    if deletion_results:
        message = "RDS Snapshot Cleanup Results\n\n"
        message += f"Total snapshots processed: {len(snapshots_to_delete)}\n"
        message += f"Successful deletions: {len([r for r in deletion_results if r['Status'] == 'SUCCESS'])}\n"
        message += f"Failed deletions: {len([r for r in deletion_results if r['Status'] == 'FAILED'])}\n\n"
        
        message += "Details:\n"
        for result in deletion_results:
            message += f"- {result['Message']}\n"
        
        sns_topic_arn = os.environ['SNS_TOPIC_ARN']
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject="RDS Snapshot Cleanup Report",
            Message=message
        )
    
    return {
        'statusCode': 200,
        'body': {
            'processed_snapshots': len(snapshots_to_delete),
            'successful_deletions': len([r for r in deletion_results if r['Status'] == 'SUCCESS']),
            'failed_deletions': len([r for r in deletion_results if r['Status'] == 'FAILED'])
        }
    }
