1. Create new SAM project
sam init
% sam init

You can preselect a particular runtime or package type when using the `sam init` experience.
Call `sam init --help` to learn more.

Which template source would you like to use?
	1 - AWS Quick Start Templates
	2 - Custom Template Location
Choice: 1

Choose an AWS Quick Start application template
	1 - Hello World Example
	2 - Data processing
	3 - Hello World Example with Powertools for AWS Lambda
	4 - Multi-step workflow
	5 - Scheduled task
	6 - Standalone function
	7 - Serverless API
	8 - Infrastructure event management
	9 - Lambda Response Streaming
	10 - GraphQLApi Hello World Example
	11 - Full Stack
	12 - Lambda EFS example
	13 - Serverless Connector Hello World Example
	14 - Multi-step workflow with Connectors
	15 - DynamoDB Example
	16 - Machine Learning
Template: 1

Use the most popular runtime and package type? (python3.13 and zip) [y/N]: y

Would you like to enable X-Ray tracing on the function(s) in your application?  [y/N]: n

Would you like to enable monitoring using CloudWatch Application Insights?
For more info, please view https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-application-insights.html [y/N]: n

Would you like to set Structured Logging in JSON format on your Lambda functions?  [y/N]: n

Project name [sam-app]: eventbridge-rule-monitor

    -----------------------
    Generating application:
    -----------------------
    Name: eventbridge-rule-monitor
    Runtime: python3.13
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

2. Directory structure
eventbridge-rule-monitor/
│
├── template.yaml
├── README.md
├── eventbridge_rule_monitor/
│   └── app.py
└── tests/

sam build
sam deploy --guided

