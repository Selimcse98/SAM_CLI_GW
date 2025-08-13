# Lambda function to delete expired RDS snapshots
import boto3
import os
from datetime import datetime, timezone, timedelta
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants
RETENTION_TAG_KEY = "RetentionDays"
FILTER_STRING = "insuranceplatform-prod-deployment-"
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]  # Set this in your SAM template or environment

def lambda_handler(event, context):
    deleted_snapshots = []
    regions = ["us-east-1", "us-west-2", "ap-southeast-2", "eu-west-2"]  # Add your regions here

    for region in regions:
        rds_client = boto3.client("rds", region_name=region)
        
        # Get all manual DB cluster snapshots
        paginator = rds_client.get_paginator("describe_db_cluster_snapshots")
        page_iterator = paginator.paginate(SnapshotType="manual")

        for page in page_iterator:
            for snapshot in page["DBClusterSnapshots"]:
                snapshot_id = snapshot["DBClusterSnapshotIdentifier"]
                snapshot_name = snapshot_id.lower()

                # Only delete snapshots that match the naming pattern
                if FILTER_STRING not in snapshot_name:
                    continue

                # Check tags for RetentionDays
                tags = rds_client.list_tags_for_resource(
                    ResourceName=snapshot["DBClusterSnapshotArn"]
                ).get("TagList", [])

                retention_days = None
                for tag in tags:
                    if tag["Key"] == RETENTION_TAG_KEY:
                        try:
                            retention_days = int(tag["Value"])
                        except ValueError:
                            logger.warning(f"Invalid retention tag value for snapshot {snapshot_id}")

                if not retention_days:
                    continue

                # Check snapshot age
                snapshot_time = snapshot["SnapshotCreateTime"]
                expiry_time = snapshot_time + timedelta(days=retention_days)
                print(f'expiry_time: {expiry_time} for snapshot_id {snapshot_id}')
                if expiry_time < datetime.now(timezone.utc):
                    try:
                        # rds_client.delete_db_cluster_snapshot(DBClusterSnapshotIdentifier=snapshot_id)
                        deleted_snapshots.append(f"{snapshot_id} ({region})")
                        logger.info(f"Deleted snapshot: {snapshot_id} in {region}")
                    except Exception as e:
                        logger.error(f"Failed to delete snapshot {snapshot_id}: {str(e)}")

    # Notify via SNS
    send_sns_notification(deleted_snapshots)

def send_sns_notification(snapshot_list):
    sns_client = boto3.client("sns")
    if not snapshot_list:
        message = "No expired RDS snapshots were found for deletion today."
    else:
        message = "The following RDS snapshots were deleted:\n\n" + "\n".join(snapshot_list)

    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="RDS Snapshot Cleanup Notification",
        Message=message
    )
