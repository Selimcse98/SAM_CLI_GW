
sam init --name eventbridge-rule-monitor --runtime python3.9 --app-template hello-world
% sam init --name eventbridge-rule-monitor --runtime python3.9 --app-template hello-world
Based on your selections, the only Template available is Hello World Example.
We will proceed to selecting the Template as Hello World Example.
Based on your selections, the only Package type available is Zip.
We will proceed to selecting the Package type as Zip.
Based on your selections, the only dependency manager available is pip.
We will proceed copying the template using pip.
Would you like to enable X-Ray tracing on the function(s) in your application?  [y/N]: n
Would you like to enable monitoring using CloudWatch Application Insights?
For more info, please view https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-application-insights.html [y/N]: n
Would you like to set Structured Logging in JSON format on your Lambda functions?  [y/N]: n                                                                                                                                                                                                                
Cloning from https://github.com/aws/aws-sam-cli-app-templates (process may take a moment)                                                                                                                       
    -----------------------
    Generating application:
    -----------------------
    Name: eventbridge-rule-monitor
    Runtime: python3.9
    Architectures: x86_64
    Dependency Manager: pip
    Application Template: hello-world
    Output Directory: .
    Configuration file: eventbridge-rule-monitor/samconfig.toml
    Next steps can be found in the README file at eventbridge-rule-monitor/README.md    
Commands you can use next
=========================
[*] Create pipeline: cd eventbridge-rule-monitor && sam pipeline init --bootstrap
[*] Validate SAM template: cd eventbridge-rule-monitor && sam validate
[*] Test Function in the Cloud: cd eventbridge-rule-monitor && sam sync --stack-name {stack-name} --watch
SAM CLI update available (1.142.1); (1.136.0 installed)
To download: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html

% sam build
Building codeuri: /Users/mmiah/SAM_AWS/Monitor_Event_Rule/Deep/src runtime: python3.9 architecture: x86_64 functions: EventBridgeRuleMonitorFunction                                                            
requirements.txt file not found. Continuing the build without dependencies.                                                                                                                                     
 Running PythonPipBuilder:CopySource                                                                                                                                                                            
Build Succeeded
Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml
Commands you can use next
=========================
[*] Validate SAM template: sam validate
[*] Invoke Function: sam local invoke
[*] Test Function in the Cloud: sam sync --stack-name {{stack-name}} --watch
[*] Deploy: sam deploy --guided

# sam deploy --profile gwre-is-gore-dev --region ca-central-1
% sam deploy --guided --profile gwre-is-cloudops-dev --stack-name weekly-cost-tracker --region us-east-2 --confirm-changeset --disable-rollback --capabilities CAPABILITY_IAM --save-params --config-file samconfig.toml --config-env default
# sam deploy --profile gwre-is-cloudops-dev --stack-name weekly-cost-tracker --region us-east-2 --no-confirm-changeset --disable-rollback --capabilities CAPABILITY_IAM --save-params --config-file samconfig.toml --config-env default
% cat samconfig.toml 

mmiah@mmiah-TVWRVF2LNH Monitor_Event_Rule % sam delete --profile gwre-is-icare-dev --region ap-southeast-2 --stack-name Monitor-Event-Rule-D
	Are you sure you want to delete the stack Monitor-Event-Rule-D in the region ap-southeast-2 ? [y/N]: y
	Do you want to delete the template file 075e4066d028ae711c5505b72e7d3206.template in S3? [y/N]: y
        - Deleting S3 object with key cefe9259a607b74d95a11133963010bf                                                                                                                                          
        - Deleting S3 object with key 075e4066d028ae711c5505b72e7d3206.template                                                                                                                                 
	- Deleting Cloudformation stack Monitor-Event-Rule-D
Deleted successfully

% aws lambda invoke --function-name weekly_cost_tracker --profile gwre-is-cloudops-dev output.txt
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
% cat output.txt | jq
{
  "statusCode": 200,
  "body": "Total cost for last week: $1056.44\nTotal cost for two weeks ago: $1136.58\nDifference in cost: $80.14\nCost difference is within acceptable limits."
}

% sam deploy --profile gwre-is-icare-dev --region ap-southeast-2 --stack-name Monitor_Event_Rule-D --confirm-changeset --disable-rollback --capabilities CAPABILITY_IAM --save-params --config-file samconfig.toml --config-env default --resolve-s3
Saved parameters to config file 'samconfig.toml' under environment 'default': {'stack_name': 'Monitor_Event_Rule-D', 'confirm_changeset': True, 'disable_rollback': True, 'capabilities': ('CAPABILITY_IAM',),  
'resolve_s3': True}
		Managed S3 bucket: aws-sam-cli-managed-default-samclisourcebucket-4p3e5qf1wkfk
		A different default S3 bucket can be set in samconfig.toml
		Or by specifying --s3-bucket explicitly.
	Uploading to fb91b012b8141cb7ba395cada8cd3653  693 / 693  (100.00%)
	Deploying with following values
	===============================
	Stack name                   : Monitor_Event_Rule-D
	Region                       : ap-southeast-2
	Confirm changeset            : True
	Disable rollback             : True
	Deployment s3 bucket         : aws-sam-cli-managed-default-samclisourcebucket-4p3e5qf1wkfk
	Capabilities                 : ["CAPABILITY_IAM"]
	Parameter overrides          : {}
	Signing Profiles             : {}
Initiating deployment
=====================
Error: Failed to create/update the stack: Monitor_Event_Rule-D, An error occurred (ValidationError) when calling the DescribeStacks operation: 1 validation error detected: Value 'Monitor_Event_Rule-D' at 'stackName' failed to satisfy constraint: Member must satisfy regular expression pattern: [a-zA-Z][-a-zA-Z0-9]*|arn:[-a-zA-Z0-9:/._+]*

% sam deploy --profile gwre-is-icare-dev --region ap-southeast-2 --stack-name Monitor-Event-Rule-D --confirm-changeset --disable-rollback --capabilities CAPABILITY_IAM --save-params --config-file samconfig.toml --config-env default --resolve-s3
Saved parameters to config file 'samconfig.toml' under environment 'default': {'stack_name': 'Monitor-Event-Rule-D', 'confirm_changeset': True, 'disable_rollback': True, 'capabilities': ('CAPABILITY_IAM',),  
'resolve_s3': True}
		Managed S3 bucket: aws-sam-cli-managed-default-samclisourcebucket-4p3e5qf1wkfk
		A different default S3 bucket can be set in samconfig.toml
		Or by specifying --s3-bucket explicitly.
File with same data already exists at fb91b012b8141cb7ba395cada8cd3653, skipping upload
	Deploying with following values
	===============================
	Stack name                   : Monitor-Event-Rule-D
	Region                       : ap-southeast-2
	Confirm changeset            : True
	Disable rollback             : True
	Deployment s3 bucket         : aws-sam-cli-managed-default-samclisourcebucket-4p3e5qf1wkfk
	Capabilities                 : ["CAPABILITY_IAM"]
	Parameter overrides          : {}
	Signing Profiles             : {}
Initiating deployment
=====================
	Uploading to ac5b2fb99f43d96e384ed64bbd532d9f.template  2453 / 2453  (100.00%)
Waiting for changeset to be created..
CloudFormation stack changeset
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Operation                                           LogicalResourceId                                   ResourceType                                        Replacement                                       
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
+ Add                                               EventBridgeRuleChangeTopic                          AWS::SNS::Topic                                     N/A                                               
+ Add                                               EventBridgeRuleMonitorFunctionRole                  AWS::IAM::Role                                      N/A                                               
+ Add                                               EventBridgeRuleMonitorFunction                      AWS::Lambda::Function                               N/A                                               
+ Add                                               EventBridgeRuleMonitorPermission                    AWS::Lambda::Permission                             N/A                                               
+ Add                                               EventBridgeRuleMonitorRule                          AWS::Events::Rule                                   N/A                                               
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Changeset created successfully. arn:aws:cloudformation:ap-southeast-2:018244321036:changeSet/samcli-deploy1753705609/e971749a-a842-4e0f-b1d3-a761a0823a2f
Previewing CloudFormation changeset before deployment
======================================================
Deploy this changeset? [y/N]: y
2025-07-28 22:27:04 - Waiting for stack create/update to complete
CloudFormation events from stack operations (refresh every 5.0 seconds)
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ResourceStatus                                      ResourceType                                        LogicalResourceId                                   ResourceStatusReason                              
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
CREATE_IN_PROGRESS                                  AWS::CloudFormation::Stack                          Monitor-Event-Rule-D                                User Initiated                                    
CREATE_IN_PROGRESS                                  AWS::SNS::Topic                                     EventBridgeRuleChangeTopic                          -                                                 
CREATE_IN_PROGRESS                                  AWS::SNS::Topic                                     EventBridgeRuleChangeTopic                          Resource creation Initiated                       
CREATE_COMPLETE                                     AWS::SNS::Topic                                     EventBridgeRuleChangeTopic                          -                                                 
CREATE_IN_PROGRESS                                  AWS::IAM::Role                                      EventBridgeRuleMonitorFunctionRole                  -                                                 
CREATE_IN_PROGRESS                                  AWS::IAM::Role                                      EventBridgeRuleMonitorFunctionRole                  Resource creation Initiated                       
CREATE_COMPLETE                                     AWS::IAM::Role                                      EventBridgeRuleMonitorFunctionRole                  -                                                 
CREATE_IN_PROGRESS                                  AWS::Lambda::Function                               EventBridgeRuleMonitorFunction                      -                                                 
CREATE_IN_PROGRESS                                  AWS::Lambda::Function                               EventBridgeRuleMonitorFunction                      Resource creation Initiated                       
CREATE_COMPLETE                                     AWS::Lambda::Function                               EventBridgeRuleMonitorFunction                      -                                                 
CREATE_IN_PROGRESS                                  AWS::Events::Rule                                   EventBridgeRuleMonitorRule                          -                                                 
CREATE_IN_PROGRESS                                  AWS::Events::Rule                                   EventBridgeRuleMonitorRule                          Resource creation Initiated                       
CREATE_COMPLETE                                     AWS::Events::Rule                                   EventBridgeRuleMonitorRule                          -                                                 
CREATE_IN_PROGRESS                                  AWS::Lambda::Permission                             EventBridgeRuleMonitorPermission                    -                                                 
CREATE_IN_PROGRESS                                  AWS::Lambda::Permission                             EventBridgeRuleMonitorPermission                    Resource creation Initiated                       
CREATE_COMPLETE                                     AWS::Lambda::Permission                             EventBridgeRuleMonitorPermission                    -                                                 
CREATE_COMPLETE                                     AWS::CloudFormation::Stack                          Monitor-Event-Rule-D                                -                                                 
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
CloudFormation outputs from deployed stack
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Outputs                                                                                                                                                                                                     
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Key                 EventBridgeRuleChangeTopicArn                                                                                                                                                           
Description         ARN of the SNS topic for notifications                                                                                                                                                  
Value               arn:aws:sns:ap-southeast-2:018244321036:EventBridgeRuleChangeNotifications                                                                                                              
Key                 EventBridgeRuleMonitorFunctionArn                                                                                                                                                       
Description         ARN of the monitoring Lambda function                                                                                                                                                   
Value               arn:aws:lambda:ap-southeast-2:018244321036:function:Monitor-Event-Rule-D-EventBridgeRuleMonitorFunctio-cDFh5FG7sr99                                                                     
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
Successfully created/updated stack - Monitor-Event-Rule-D in ap-southeast-2
