RDS Failover Notification System
This AWS SAM application creates a serverless system to automatically send notifications via Email and SMS when an AWS RDS instance or cluster failover event occurs.

Architecture
The architecture is event-driven and straightforward:

AWS RDS experiences a failover event (e.g., a primary instance becomes unresponsive, and a standby replica is promoted).

Amazon EventBridge catches the specific RDS failover event using a predefined event pattern.

The EventBridge rule triggers an AWS Lambda function.

The Lambda function processes the event, extracts key details (like the DB identifier, region, and event message), and formats a human-readable notification.

The function then publishes this notification to an Amazon SNS Topic.

The SNS Topic immediately pushes the message to all configured subscribers (in this case, two email addresses and two mobile numbers).

[AWS RDS] --(Failover Event)--> [EventBridge] --(Triggers)--> [AWS Lambda] --(Publishes)--> [SNS Topic] --(Sends To)--> [Email & SMS Subscribers]

Prerequisites
Before you begin, ensure you have the following installed and configured:

AWS CLI

AWS SAM CLI

Docker (required for sam build)

Deployment Steps
Follow these steps to deploy the application to your AWS account.

Step 1: Build the Application
From the root directory of the project, run the sam build command. This will build your Lambda function's dependencies.

sam build

Step 2: Deploy the Application
Deploy the application using the guided deployment process. This will prompt you for parameters, such as the stack name and AWS region.

sam deploy --guided

When prompted, you can accept the default parameter values for the email addresses and phone numbers, or you can enter new ones.

Note: For mobile numbers, use the E.164 format (e.g., +1 for the US, +44 for the UK, +61 for Australia).

Post-Deployment: Confirm Subscriptions
Email: AWS SNS will send a confirmation email to selimcse98@gmail.com and mmiah@guidewire.com. You must click the link in these emails to confirm the subscription and start receiving notifications.

SMS: SMS subscriptions do not require confirmation.

How to Test
The most reliable way to test this is to force a failover on a Multi-AZ RDS instance.

WARNING: This will cause a brief database outage (typically 1-2 minutes) as the failover occurs. Only perform this on a non-production database.

Identify a Multi-AZ RDS instance you can use for testing.

Use the AWS CLI to reboot the instance with the --force-failover flag. Replace <your-db-instance-identifier> with your actual DB instance ID and <your-region> with its region.

aws rds reboot-db-instance --db-instance-identifier <your-db-instance-identifier> --force-failover --region <your-region>

Within a few minutes, the failover will complete, EventBridge will trigger your Lambda, and you should receive the email and SMS notifications.

Cleaning Up
To delete the application and all the resources it created, use the sam delete command. You will be asked to confirm the deletion of the CloudFormation stack.

sam delete
