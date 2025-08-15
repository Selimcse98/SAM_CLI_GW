# RDS Failover Notification System

A serverless AWS solution that monitors RDS database failover events and sends notifications via email and SMS using AWS Lambda, EventBridge, and SNS.

## Architecture

- **EventBridge Rule**: Captures RDS failover events
- **Lambda Function**: Processes events and enriches them with additional RDS information
- **SNS Topic**: Sends notifications to email and SMS subscribers
- **CloudWatch Logs**: Stores function logs for monitoring

## Features

- ✅ Automatic detection of RDS DB Instance and DB Cluster failover events
- ✅ Detailed email notifications with cluster/instance information
- ✅ Concise SMS alerts for immediate notification
- ✅ Enhanced notifications with RDS metadata (engine, version, endpoints, etc.)
- ✅ Support for both Aurora clusters and standalone RDS instances
- ✅ Configurable environments (dev/staging/prod)
- ✅ Comprehensive logging and error handling

## File Structure

```
rds-failover-notifications/
├── template.yaml              # SAM template
├── src/
│   ├── handler.py            # Lambda function code
│   └── requirements.txt      # Python dependencies
├── deploy.sh                 # Deployment script
├── test-notification.sh      # Testing script (auto-generated)
└── README.md                 # This file
```

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **AWS SAM CLI** installed
3. **Python 3.11** or later
4. **jq** for JSON processing (optional, for testing)

### Required AWS Permissions

Your AWS credentials need the following permissions:
- CloudFormation full access
- Lambda full access
- SNS full access
- EventBridge full access
- RDS read permissions
- IAM permissions to create roles and policies

## Quick Start

### 1. Clone and Setup

```bash
# Create project directory
mkdir rds-failover-notifications
cd rds-failover-notifications

# Create the SAM application structure
mkdir src

# Copy the provided files to their respective locations:
# - template.yaml (root directory)
# - src/handler.py
# - src/requirements.txt
# - deploy.sh (root directory, make executable)
```

### 2. Deploy the Application

```bash
# Make deployment script executable
chmod +x deploy.sh

# Deploy to development environment
./deploy.sh

# Deploy to production environment
./deploy.sh --environment prod --region us-west-2
```

### 3. Confirm Subscriptions

After deployment:
1. Check email inboxes for SNS subscription confirmation emails
2. Check mobile phones for SMS confirmation messages
3. Confirm all subscriptions

### 4. Test the System

```bash
# The deployment script creates a test script
./test-notification.sh

# Or test with a specific function name
./test-notification.sh --function-name rds-failover-notification-prod
```

## Configuration

### Email Subscribers

Currently configured for:
- selimcse98@gmail.com
- mmiah@guidewire.com

### SMS Subscribers

Currently configured for Australian mobile numbers:
- +61469214498
- +61469218933

To modify subscribers, update the `template.yaml` file before deployment.

### Environment Variables

The Lambda function uses these environment variables:
- `SNS_TOPIC_ARN`: ARN of the SNS topic (auto-configured)
- `LOG_LEVEL`: Logging level (default: INFO)

## Event Patterns

The system monitors these RDS events:

```json
{
  "source": ["aws.rds"],
  "detail-type": [
    "RDS DB Instance Event",
    "RDS DB Cluster Event"
  ],
  "detail": {
    "EventCategories": ["failover"],
    "SourceType": ["db-instance", "db-cluster"]
  }
}
```

## Notification Format

### Email Notifications (Detailed)

```
RDS FAILOVER NOTIFICATION
========================

ALERT: A failover event has occurred for your RDS resource.

Resource Details:
-----------------
• Resource Type: DB Cluster
• Resource ID: my-aurora-cluster
• Engine: aurora-mysql
• Engine Version: 8.0.mysql_aurora.3.02.0
• Current Status: available
• Event Time: 2024-01-01T12:00:00Z

Event Information:
------------------
• Event Type: RDS DB Cluster Event
• Event Categories: failover
• Message: Completed failover to DB instance: my-aurora-cluster-1

Cluster Configuration:
---------------------
• Availability Zones: us-east-1a, us-east-1b
• Cluster Members: my-aurora-cluster-1, my-aurora-cluster-2
• Writer Endpoint: my-aurora-cluster.cluster-xyz.us-east-1.rds.amazonaws.com
• Reader Endpoint: my-aurora-cluster.cluster-ro-xyz.us-east-1.rds.amazonaws.com

Recommended Actions:
-------------------
1. Verify application connectivity to the database
2. Check application logs for any connection errors
3. Monitor RDS performance metrics
4. Review CloudWatch logs for additional details
```

### SMS Notifications (Concise)

```
RDS FAILOVER ALERT: DB Cluster 'my-aurora-cluster' has failed over. Status: available. Check email for details.
```

## Monitoring and Troubleshooting

### View Logs

```bash
# Tail Lambda function logs
aws logs tail '/aws/lambda/rds-failover-notification-dev' --follow

# View specific log events
aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/rds-failover-notification'
```

### Common Issues

1. **SNS subscriptions not confirmed**
   - Check email/SMS for confirmation messages
   - Subscriptions must be confirmed to receive notifications

2. **Lambda function timeout**
   - Default timeout is 30 seconds
   - Increase in `template.yaml` if needed

3. **Permission errors**
   - Ensure Lambda has proper IAM permissions for RDS describe operations
   - Check CloudWatch logs for specific error messages

4. **No notifications received**
   - Verify EventBridge rule is enabled
   - Check Lambda function logs
   - Confirm SNS topic and subscriptions are active

## Deployment Options

### Environment-Specific Deployments

```bash
# Development
./deploy.sh --environment dev

# Staging  
./deploy.sh --environment staging

# Production
./deploy.sh --environment prod --region us-west-2
```

### Manual Deployment

```bash
# Build the application
sam build

# Deploy with guided setup
sam deploy --guided

# Deploy with parameters
sam deploy \
  --stack-name rds-failover-notifications-prod \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides Environment=prod
```

## Customization

### Adding More Subscribers

Edit `template.yaml` and add new subscription resources:

```yaml
AdditionalEmailSubscription:
  Type: AWS::SNS::Subscription
  Properties:
    TopicArn: !Ref RDSFailoverTopic
    Protocol: email
    Endpoint: new-email@company.com
```

### Modifying Event Patterns

Update the EventBridge rule pattern in `template.yaml`:

```yaml
Events:
  RDSFailoverEvent:
    Type: EventBridgeRule
    Properties:
      Pattern:
        source: ["aws.rds"]
        detail-type: ["RDS DB Instance Event"]
        detail:
          EventCategories: ["failover", "failure"]
```

### Custom Message Formatting

Modify the `format_email_message()` and `format_sms_message()` functions in `src/handler.py`.

## Security Considerations

- Lambda function follows least-privilege access
- SNS topic is not publicly accessible
- CloudWatch logs have retention policies
- All communications use AWS managed encryption

## Cost Optimization

- Lambda function uses ARM64 architecture for better price-performance
- CloudWatch logs have 14-day retention
- SNS charges apply per message sent
- EventBridge rules have no additional charges for AWS service events

## Support and Maintenance

### Updating the Function

```bash
# Modify src/handler.py as needed
# Redeploy
./deploy.sh
```

### Deleting the Stack

```bash
aws cloudformation delete-stack --stack-name rds-failover-notifications-dev
```

### Monitoring Costs

- Monitor SNS usage in AWS Cost Explorer
- Set up billing alerts for unexpected charges
- Review CloudWatch logs retention settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.