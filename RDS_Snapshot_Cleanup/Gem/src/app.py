import os
import boto3
from datetime import datetime, timedelta, timezone
import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Boto3 clients outside the handler for reuse
rds_client = boto3.client('rds')
sns_client = boto3.client('sns')

# Get environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
SNAPSHOT_FILTER = os.environ.get('SNAPSHOT_FILTER')
RETENTION_TAG_KEY = "RetentionDays"

def lambda_handler(event, context):
    """
    Main handler to find and delete expired RDS manual snapshots.
    """
    logger.info(f"Starting RDS snapshot cleanup process. Filtering for snapshots containing: '{SNAPSHOT_FILTER}'")

    if not SNAPSHOT_FILTER:
        logger.error("SNAPSHOT_FILTER environment variable not set. Exiting.")
        return {'statusCode': 500, 'body': 'SNAPSHOT_FILTER not set.'}

    snapshots_to_delete = []
    
    try:
        paginator = rds_client.get_paginator('describe_db_cluster_snapshots')
        page_iterator = paginator.paginate(SnapshotType='manual')

        for page in page_iterator:
            for snapshot in page['DBClusterSnapshots']:
                snapshot_id = snapshot['DBClusterSnapshotIdentifier']
                snapshot_arn = snapshot['DBClusterSnapshotArn']

                # 1. Filter by name
                if SNAPSHOT_FILTER not in snapshot_id:
                    continue

                logger.info(f"Checking snapshot: {snapshot_id}")

                # 2. Get tags and check for retention policy
                tags = rds_client.list_tags_for_resource(ResourceName=snapshot_arn).get('TagList', [])
                retention_days_str = next((tag['Value'] for tag in tags if tag['Key'] == RETENTION_TAG_KEY), None)

                if not retention_days_str or not retention_days_str.isdigit():
                    logger.warning(f"Snapshot {snapshot_id} has no valid '{RETENTION_TAG_KEY}' tag. Skipping.")
                    continue

                # 3. Check if the snapshot is expired
                retention_days = int(retention_days_str)
                create_time = snapshot['SnapshotCreateTime']
                
                # Ensure we are using timezone-aware datetimes for comparison
                now = datetime.now(timezone.utc)
                expiration_date = create_time + timedelta(days=retention_days)

                if now > expiration_date:
                    logger.info(f"Snapshot {snapshot_id} created on {create_time} has EXPIRED. Adding to deletion list.")
                    snapshots_to_delete.append(snapshot_id)
                else:
                    logger.info(f"Snapshot {snapshot_id} is not yet expired (expires on {expiration_date.date()}).")

        # 4. Delete snapshots and send notification
        if snapshots_to_delete:
            delete_snapshots(snapshots_to_delete)
        else:
            logger.info("No expired snapshots found to delete.")

        return {
            'statusCode': 200,
            'body': json.dumps(f'Cleanup complete. Deleted {len(snapshots_to_delete)} snapshots.')
        }
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        # Optionally send an error notification
        send_notification("RDS Snapshot Cleanup FAILED", f"The Lambda function failed with an error: {str(e)}")
        raise e


def delete_snapshots(snapshot_ids):
    """
    Deletes a list of snapshots and sends a notification.
    """
    deleted_list = []
    failed_list = []
    
    logger.info(f"Preparing to delete {len(snapshot_ids)} snapshots: {', '.join(snapshot_ids)}")
    
    for snapshot_id in snapshot_ids:
        try:
            rds_client.delete_db_cluster_snapshot(DBClusterSnapshotIdentifier=snapshot_id)
            logger.info(f"Successfully initiated deletion for {snapshot_id}")
            deleted_list.append(snapshot_id)
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {str(e)}")
            failed_list.append(f"{snapshot_id}: {str(e)}")
            
    # Prepare and send the final report
    subject = f"RDS Snapshot Deletion Report: {len(deleted_list)} Deleted"
    message = "RDS automated snapshot cleanup process has completed.\n\n"
    if deleted_list:
        message += "--- DELETED SNAPSHOTS ---\n" + "\n".join(deleted_list) + "\n\n"
    if failed_list:
        message += "--- FAILED DELETIONS ---\n" + "\n".join(failed_list) + "\n\n"
        
    send_notification(subject, message)


def send_notification(subject, message):
    """
    Sends a notification to the configured SNS topic.
    """
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not set. Skipping notification.")
        return
        
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        logger.info("Successfully sent notification.")
    except Exception as e:
        logger.error(f"Failed to send SNS notification: {str(e)}")