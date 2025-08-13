import boto3
import os
from datetime import datetime, timezone, timedelta

FILTER_PREFIX = "insuranceplatform-prod-deployment-"
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
RETENTION_TAG_KEY = "RetentionDays"

def lambda_handler(event, context):
    rds = boto3.client("rds")
    sns = boto3.client("sns")

    deleted_snapshots = []

    # Get all manual snapshots
    snapshots = rds.describe_db_cluster_snapshots(SnapshotType="manual")["DBClusterSnapshots"]

    for snapshot in snapshots:
        snapshot_id = snapshot["DBClusterSnapshotIdentifier"]
        create_time = snapshot["SnapshotCreateTime"]
        tags = rds.list_tags_for_resource(ResourceName=snapshot["DBClusterSnapshotArn"])["TagList"]

        # Filter by name prefix
        if not snapshot_id.startswith(FILTER_PREFIX):
            continue

        # Get RetentionDays tag
        retention_days = next((int(tag["Value"]) for tag in tags if tag["Key"] == RETENTION_TAG_KEY), None)
        if retention_days is None:
            continue

        # Check if snapshot is older than retention
        age = datetime.now(timezone.utc) - create_time
        if age > timedelta(days=retention_days):
            try:
                rds.delete_db_cluster_snapshot(DBClusterSnapshotIdentifier=snapshot_id)
                deleted_snapshots.append(snapshot_id)
            except Exception as e:
                print(f"Failed to delete {snapshot_id}: {str(e)}")

    # Send SNS notification
    if deleted_snapshots:
        message = f"The following RDS snapshots were deleted:\n" + "\n".join(deleted_snapshots)
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject="RDS Snapshot Cleanup", Message=message)
    else:
        print("No snapshots deleted today.")
