# EC2 Deployer API Lambda

A serverless AWS Lambda function that provides a REST API for launching and managing EC2 instances through HTTP requests. Built with Python using AWS Lambda Powertools for enhanced observability and API handling.

## Architecture Overview

This is a serverless microservice deployed as an AWS Lambda function that serves as an API gateway for EC2 instance management. The architecture follows a layered approach with clear separation of concerns:

```
┌─────────────────┐
│  Application    │  ← Application Load Balancer (ALB)
│  Load Balancer  │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   AWS Lambda    │  ← lambda_handler (main entry point)
│   Function      │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Controller    │  ← Ec2DeployerController + Resolver
│     Layer       │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Service       │  ← Ec2DeployerService (Business Logic)
│     Layer       │
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Client        │  ← Ec2Client (AWS SDK Wrapper)
│     Layer       │
└─────────┬───────┘
          │
┌─────────▼───────┐
│     AWS         │  ← EC2 Service
│   Services      │
└─────────────────┘
```

### Layer Breakdown

- **Lambda Handler** (`ec2_deployer_api_lambda.py`): Main entry point handling AWS Lambda events
- **Controller Layer** (`api/`): HTTP request routing and response handling
- **Service Layer** (`service/`): Business logic and validation
- **Client Layer** (`client/`): AWS SDK interactions and API calls
- **Models** (`model/`): Data transfer objects and request/response structures
- **Utilities** (`util/`): Shared utilities, constants, and helper functions
- **Exceptions** (`exception/`): Custom exception classes
- **Logging** (`logger/`): Centralized logging configuration

## Features

- **EC2 Instance Launching**: Create new EC2 instances with configurable parameters
- **User Quota Management**: Enforce per-user instance limits (currently set to 1)
- **Request Tracking**: Unique request IDs for traceability
- **Resource Tagging**: Automatic tagging of instances with user and request metadata
- **Health Check Endpoint**: Basic health monitoring
- **Structured Logging**: Comprehensive logging using AWS Lambda Powertools
- **Error Handling**: Centralized exception handling with proper HTTP status codes

## API Endpoints

### Health Check
```http
GET /deployer/v1/instances/ping
```
Returns service health status.

**Response:**
```json
{
  "status": "HEALTHY"
}
```

### Launch EC2 Instance
```http
POST /deployer/v1/instances
```

**Request Body:**
```json
{
  "instanceType": "t2.micro",
  "imageId": "ami-056841b896a354b00",
  "count": "1",
  "user": "username"
}
```

**Response (202 Accepted):**
```json
{
  "Instances": [
    {
      "InstanceId": "i-1234567890abcdef0",
      ...
    }
  ],
  ...
}
```

## Dependencies

### Core Dependencies
- **boto3**: AWS SDK for Python
- **aws-lambda-powertools**: Enhanced Lambda capabilities including:
  - API Gateway event handling
  - Structured logging
  - Request parsing and validation
  - Distributed tracing

### Python Standard Library
- `json`: JSON parsing and serialization
- `uuid`: Unique identifier generation
- `traceback`: Error stack trace handling
- `logging`: Standard Python logging

## Configuration

Configuration is managed through `src/util/Constants.py`:

```python
EC2_PROFILE = "CharlesIC"              # AWS Profile name
USER_MAX_INSTANCE_QUOTA = 1            # Max instances per user
PRE_FIX_EC2_DEPLOYER = "EDR-"         # Request ID prefix
EC2_DEPLOYER_PATH_PREFIX = "deployer/v1/instances"  # API path prefix
```

## Project Structure

```
src/
├── ec2_deployer_api_lambda.py        # Lambda entry point
├── api/
│   ├── Ec2DeployerController.py       # API request handlers
│   └── Ec2DeployerControllerResolver.py # Route resolution
├── service/
│   └── Ec2DeployerService.py          # Business logic
├── client/
│   └── AwsClients.py                  # AWS API clients
├── model/
│   └── InstancePaveRequestModel.py    # Data models
├── exception/
│   └── Ec2DeployerErrors.py           # Custom exceptions
├── logger/
│   └── Ec2DeployerLogger.py           # Logging configuration
└── util/
    ├── Constants.py                   # Configuration constants
    └── Ec2DeployerUtils.py            # Utility functions
```

## Deployment Requirements

### AWS Permissions
The Lambda function requires the following IAM permissions:
- `ec2:RunInstances` - Launch EC2 instances
- `ec2:DescribeInstances` - Query instance information  
- `ec2:StartInstances` - Start stopped instances
- `ec2:StopInstances` - Stop running instances
- `ec2:TerminateInstances` - Terminate instances
- `ec2:CreateTags` - Tag resources

### Lambda Configuration
- **Runtime**: Python 3.x
- **Handler**: `ec2_deployer_api_lambda.lambda_handler`
- **Event Source**: Application Load Balancer (ALB)
- **Memory**: 128MB+ (recommended)
- **Timeout**: 30+ seconds (for EC2 API calls)

### Environment Setup
The application expects AWS credentials to be configured, either through:
- Lambda execution role (recommended for production)
- AWS profile named "CharlesIC" (current configuration)
- Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

## Security Considerations & Concerns

⚠️ **CRITICAL SECURITY ISSUES IDENTIFIED:**

1. **Authentication/Authorization Missing**
   - No visible authentication mechanism
   - Any client with network access can launch EC2 instances
   - **Recommendation**: Implement API Gateway with authentication (API keys, IAM, Cognito)

2. **Hardcoded AWS Profile**
   - AWS profile "CharlesIC" is hardcoded in `Constants.py`
   - **Recommendation**: Use Lambda execution roles instead of profiles

3. **User Quota Not Enforced**
   - Code sets `current_user_number = 0` without actual user tracking
   - Quota validation is bypassed
   - **Recommendation**: Implement proper user tracking (DynamoDB, RDS)

4. **Input Validation Insufficient**
   - Minimal validation beyond Pydantic model parsing
   - No validation of AMI IDs, instance types, or user names
   - **Recommendation**: Add comprehensive input validation

5. **No Rate Limiting**
   - No protection against abuse or excessive requests
   - **Recommendation**: Implement API Gateway throttling

6. **Sensitive Data Exposure**
   - Full AWS API responses returned to clients
   - May expose sensitive instance metadata
   - **Recommendation**: Filter response data

7. **Error Information Disclosure**
   - Detailed exception information returned to clients
   - May reveal system internals
   - **Recommendation**: Return generic error messages to clients

8. **No Audit Trail**
   - No persistent logging of instance creation events
   - **Recommendation**: Implement CloudTrail and persistent audit logs

## Workspace Dependencies

This appears to be a standalone Lambda function without explicit workspace dependencies. However, it integrates with:

- **AWS EC2 Service**: Core dependency for instance management
- **AWS CloudWatch**: For logging (via Lambda Powertools)
- **AWS X-Ray**: For distributed tracing (configured but may need enabling)
- **Application Load Balancer**: For HTTP request routing

## Usage Examples

### Development/Testing
The service includes test runners in several files:
```python
# Test EC2 client functionality
python src/client/AwsClients.py

# Test service functionality  
python src/service/Ec2DeployerService.py

# Test utility functions
python src/util/Ec2DeployerUtils.py
```

### Production Deployment
Deploy as AWS Lambda function with ALB trigger for production use.

## Monitoring and Observability

- **AWS Lambda Powertools**: Structured logging and tracing
- **CloudWatch Logs**: Centralized log aggregation
- **X-Ray Tracing**: Distributed request tracing (if enabled)
- **Health Check Endpoint**: Basic service availability monitoring

## Notes

This codebase appears to be approximately 2+ years old based on the commit history. Consider updating dependencies and implementing the security recommendations before production deployment.