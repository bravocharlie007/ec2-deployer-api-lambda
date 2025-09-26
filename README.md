# EC2 Deployer API Lambda

A serverless AWS Lambda function that provides a REST API for launching and managing EC2 instances through HTTP requests. Built with Python using AWS Lambda Powertools for enhanced observability and API handling.

## Architecture Overview

This is a serverless microservice deployed as an AWS Lambda function that serves as an API gateway for EC2 instance management. The architecture follows a layered approach with clear separation of concerns.

### A) Previous/Original Design Architecture

```
┌─────────────────┐
│     Internet    │
└─────────┬───────┘
          │ HTTP Request (No Auth!)
┌─────────▼───────┐
│  Application    │ ← ALB (Application Load Balancer)
│  Load Balancer  │   Routes requests to Lambda
└─────────┬───────┘
          │ ALB Event
┌─────────▼───────┐
│   AWS Lambda    │ ← lambda_handler()
│   Function      │   Entry point with X-Ray tracing
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Controller      │ ← Ec2DeployerControllerResolver
│ Resolver        │   Routes based on path prefix
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Ec2Deployer     │ ← ApiGatewayResolver (Powertools)
│ Controller      │   GET /ping, POST /instances  
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Ec2Deployer     │ ← Business logic layer
│ Service         │   Quota check (bypassed!), tagging
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Ec2Client     │ ← boto3 wrapper
│                 │   Uses hardcoded "CharlesIC" profile!
└─────────┬───────┘
          │ boto3 calls
┌─────────▼───────┐
│   AWS EC2       │ ← run_instances()
│   Service       │   Creates actual EC2 instances
└─────────────────┘

❌ VULNERABILITIES IN ORIGINAL DESIGN:
- No authentication at any layer
- Hardcoded AWS profile instead of IAM roles  
- Quota bypass (current_user_number = 0)
- Returns full AWS API responses
- Detailed error messages exposed
- No audit logging
```

### B) Current Secure Design Architecture (After Security Fixes)

```
┌─────────────────┐
│     Internet    │
└─────────┬───────┘
          │ HTTP + API Key Required
┌─────────▼───────┐
│  Application    │ ← ALB with API key validation
│  Load Balancer  │   Routes authenticated requests
└─────────┬───────┘
          │ Validated ALB Event
┌─────────▼───────┐
│   AWS Lambda    │ ← lambda_handler() + IAM execution role
│   Function      │   X-Ray tracing, enhanced logging
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Auth Validator  │ ← API key validation middleware
│                 │   Rejects unauthenticated requests
└─────────┬───────┘
          │ Authenticated request
┌─────────▼───────┐
│ Input Validator │ ← Username, AMI ID, instance type validation
│                 │   Sanitization and bounds checking
└─────────┬───────┘
          │ Clean, validated inputs
┌─────────▼───────┐
│ Controller      │ ← Filtered responses, generic error messages
│ (Enhanced)      │   No sensitive data exposure
└─────────┬───────┘
          │
┌─────────▼───────┐
│ Service         │ ← Comprehensive audit logging
│ (Enhanced)      │   Structured security events
└─────────┬───────┘
          │
┌─────────▼───────┐
│   Ec2Client     │ ← IAM execution role (no hardcoded profile)
│  (Secured)      │   Least privilege permissions
└─────────┬───────┘
          │ Controlled AWS calls
┌─────────▼───────┐    ┌─────────────────┐
│   AWS EC2       │    │   CloudWatch    │ ← Structured audit logs
│   Service       │    │     Logs        │   Security event tracking
└─────────────────┘    └─────────────────┘

✅ SECURITY IMPROVEMENTS IMPLEMENTED:
- API key authentication requirement
- IAM execution roles instead of hardcoded profiles
- Input validation (username, AMI ID, instance type)
- Filtered API responses (no sensitive data)
- Generic error messages (no information disclosure)
- Comprehensive audit logging for security events
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

### 🛡️ **SECURITY FIXES IMPLEMENTED:**

#### 1. **Authentication Added** ✅
- **Issue**: No authentication mechanism - anyone with network access could launch EC2 instances
- **Fix**: Added API key validation middleware in controller
- **Implementation**: Requests now require `x-api-key` header with minimum 10-character key
- **Note**: This is a basic implementation; production should use AWS API Gateway with proper authentication (JWT, OAuth, IAM)

#### 2. **Hardcoded AWS Profile Removed** ✅
- **Issue**: AWS profile "CharlesIC" was hardcoded in `Constants.py` 
- **Fix**: Removed hardcoded profile; now uses Lambda execution role automatically
- **Implementation**: Modified `Ec2Client` constructor to use default boto3 credentials (Lambda execution role)
- **Benefit**: Follows AWS security best practices and eliminates credential management issues

#### 4. **Input Validation Added** ✅ (Partial - Username Only)
- **Issue**: No validation of AMI IDs, instance types, or user names
- **Fix**: Added comprehensive validation for usernames, AMI IDs, and instance types
- **Implementation**: 
  - Username: Alphanumeric with hyphens/underscores, 3-32 characters
  - AMI ID: Must match AWS AMI format (`ami-[0-9a-f]{8,17}`)
  - Instance Type: Must be from allowed list (t2.micro, t2.small, etc.)

#### 6. **Information Disclosure Fixed** ✅
- **Issue**: Detailed error messages and full AWS API responses exposed sensitive system information
- **Fix**: Implemented response filtering and generic error messages
- **Implementation**:
  - `filter_aws_response()`: Only returns essential instance information (ID, state, type, launch time, tags)
  - `handle_errors()`: Returns generic error messages instead of detailed exceptions
  - Sensitive AWS metadata is now filtered out before returning to clients

#### 7. **Audit Trail Added** ✅
- **Issue**: No persistent logging of instance creation events
- **Fix**: Comprehensive structured audit logging implemented
- **Implementation**:
  - Logs all instance launch attempts with timestamp, user, request ID
  - Logs quota violations and denial reasons
  - Logs successful instance creations with instance IDs
  - Logs failed operations with error context
  - Uses structured JSON format for easy parsing and alerting
- **Format**: `AUDIT: {"timestamp": "ISO8601", "action": "event_type", "user": "username", ...}`

#### 8. **Sensitive Data Exposure Mitigated** ✅
- **Issue**: Full AWS responses could expose sensitive instance metadata
- **Fix**: Response filtering ensures only safe data is returned
- **Implementation**: `filter_aws_response()` method whitelist-filters responses to include only:
  - Instance ID, State, Type, Launch Time, Tags
  - Removes: Security groups, network interfaces, IAM profiles, etc.

### ⚠️ **REMAINING SECURITY ISSUES (Require Architecture Changes):**

#### 3. **Bypassed Quota System** ⚠️
- **Issue**: User quota validation not implemented (always sets `current_user_number = 0`)
- **Current State**: Added TODO comment and audit logging for quota checks
- **Required Fix**: Implement DynamoDB table to track user instance counts
- **Why Not Fixed**: Requires infrastructure changes (DynamoDB table, IAM permissions)

#### 5. **No Rate Limiting** ⚠️  
- **Issue**: Vulnerable to abuse and resource exhaustion
- **Required Fix**: Implement API Gateway with throttling policies
- **Why Not Fixed**: Requires infrastructure changes (API Gateway deployment, not just ALB)

### **Security Recommendations for Production:**

1. **Replace Basic API Key with Proper Authentication**:
   - Deploy AWS API Gateway with Cognito User Pools or IAM authentication
   - Implement JWT tokens with proper expiration and refresh logic
   - Add multi-factor authentication (MFA) for admin operations

2. **Implement Real Quota Tracking**:
   ```python
   # Add DynamoDB table: user-instance-quotas
   # Structure: {user_id: str, instance_count: int, last_updated: timestamp}
   ```

3. **Add Rate Limiting**:
   - API Gateway throttling: 10 requests/minute per API key
   - CloudFront with WAF for additional DDoS protection

4. **Enhanced Monitoring**:
   - CloudWatch alarms on failed authentication attempts
   - AWS Config rules for compliance monitoring
   - CloudTrail for comprehensive API audit logging

5. **Network Security**:
   - VPC endpoints for private AWS API communication
   - Security groups with minimal required access
   - NACLs for additional network-level controls

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