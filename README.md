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

### Application Load Balancer Integration
This Lambda function is specifically designed to receive events from an Application Load Balancer (ALB):

```python
# Configured for ALB events in Ec2DeployerController.py
app = ApiGatewayResolver(proxy_type=ProxyEventType.ALBEvent)
```

**ALB Requirements:**
- ALB must be configured with Lambda target
- Health check endpoint: `/deployer/v1/instances/ping`
- Request routing to Lambda function
- Proper security group configuration allowing HTTP/HTTPS traffic
- SSL termination at ALB (recommended for production)

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

## Workspace Dependencies and Infrastructure Order

### Current State Analysis
After reviewing the available repositories in the bravocharlie007 organization, this appears to be a **standalone Lambda function** that currently handles only the EC2 deployment API layer. The related infrastructure components mentioned (compute, vpc, nlb/alb) are not found as separate repositories in the current GitHub organization.

### Missing Infrastructure Components
Based on the problem statement, the following components should exist but are not accessible:
- **Compute Repository**: Handles NLB/ALB infrastructure provisioning
- **VPC Repository**: Manages network infrastructure and VPC configuration
- **Current Repository (ec2-deployer-api-lambda)**: Provides the API layer for EC2 instance management

### Recommended Workspace Structure
For a complete infrastructure deployment, the following repository structure is recommended:

```
Infrastructure Workspace (Multi-Repository)
├── vpc-infrastructure/           ← VPC, subnets, routing, security groups
├── compute-infrastructure/       ← ALB/NLB, target groups, listeners
├── ec2-deployer-api-lambda/     ← API Lambda function (this repository)
└── deployment-orchestration/     ← Terraform/CloudFormation orchestration
```

### Deployment Order of Operations
When all workspace components are available, follow this deployment sequence:

#### Phase 1: Foundation Infrastructure
1. **VPC Repository** (Deploy First)
   - VPC creation with CIDR blocks
   - Public/Private subnets across AZs
   - Internet Gateway and NAT Gateways
   - Route Tables and routing rules
   - Security Groups and NACLs
   - VPC Endpoints (if needed)

#### Phase 2: Load Balancer Infrastructure  
2. **Compute Repository** (Deploy Second)
   - Application Load Balancer (ALB) creation
   - Target Groups configuration
   - Listeners and routing rules
   - SSL/TLS certificates (ACM)
   - Security Groups for ALB
   - Health check configuration

#### Phase 3: Application Layer
3. **EC2 Deployer API Lambda** (Deploy Third - This Repository)
   - Lambda function deployment
   - Lambda execution role and policies
   - ALB target group registration
   - API Gateway integration (if used)
   - CloudWatch log groups
   - X-Ray tracing configuration

#### Phase 4: Integration Testing
4. **End-to-End Validation**
   - ALB health check validation
   - API endpoint accessibility testing
   - EC2 instance launching verification
   - Security group and network connectivity testing

### Dependencies and Outputs
Each workspace component should export necessary values for downstream dependencies:

**VPC Repository Outputs:**
- VPC ID
- Public/Private Subnet IDs
- Security Group IDs
- Route Table IDs

**Compute Repository Outputs:**
- ALB ARN and DNS name
- Target Group ARNs
- Listener ARNs
- ALB Security Group IDs

**Current Repository Dependencies:**
- VPC outputs for Lambda deployment
- ALB outputs for event source configuration
- Appropriate IAM permissions for EC2 operations

### Current Integration Status
This repository currently integrates with:

- **AWS EC2 Service**: Direct API calls for instance management
- **Application Load Balancer**: Configured as event source (ProxyEventType.ALBEvent)
- **AWS CloudWatch**: For logging via Lambda Powertools
- **AWS X-Ray**: For distributed tracing (configured but may need enabling)

### Infrastructure Deployment Notes
⚠️ **Important**: The infrastructure components (VPC, ALB/NLB) referenced in the problem statement are not currently accessible for review. This may indicate:
- Components exist in a different GitHub organization
- Infrastructure managed through different tools (Terraform Cloud, AWS CDK, etc.)
- Components are private repositories requiring different access permissions
- Infrastructure provisioned manually or through AWS Console

## Potential Code Changes When Integrating with Other Workspaces

### VPC Integration Considerations
When the VPC repository is available, consider these modifications:

1. **Subnet Selection Logic** (`Ec2DeployerService.py`):
   - Add subnet ID parameter to instance launch requests
   - Implement subnet selection based on availability zones
   - Add VPC security group assignments

2. **Security Group Management**:
   - Reference VPC-managed security groups instead of defaults
   - Implement security group validation logic

### ALB/NLB Integration Considerations  
When the compute repository is available, potential changes include:

1. **Health Check Endpoint Enhancement**:
   - Add more comprehensive health checks
   - Include dependency validation (EC2 service, IAM permissions)
   - Add load balancer-specific health metrics

2. **Request Routing Optimization**:
   - Optimize for ALB event processing
   - Add proper error handling for ALB-specific scenarios
   - Implement request/response transformation if needed

3. **Target Group Integration**:
   - Add logic for dynamic target group registration if creating instances that need ALB registration
   - Implement health check configurations for launched instances

### Configuration Management
When all repositories are integrated:

1. **Environment-Specific Configuration**:
   - Replace hardcoded values in `Constants.py` with environment variables
   - Implement parameter store or secrets manager integration
   - Add environment-specific AWS profiles or IAM roles

2. **Cross-Repository Communication**:
   - Implement shared configuration management
   - Add service discovery mechanisms
   - Establish inter-service authentication patterns

### Rationale for Changes
Each modification addresses specific integration points:
- **VPC changes**: Enable proper network isolation and security
- **ALB changes**: Optimize load balancer integration and routing
- **Configuration changes**: Support multiple environments and reduce hardcoded values
- **Communication changes**: Enable secure and reliable inter-service communication

### Recommendations for Complete Implementation
1. **Create Missing Repositories**: Establish the vpc-infrastructure and compute-infrastructure repositories
2. **Implement Infrastructure as Code**: Use Terraform or CloudFormation for consistent deployments
3. **Establish CI/CD Pipeline**: Automate the deployment order across all workspaces
4. **Add Integration Tests**: Validate cross-workspace dependencies
5. **Document Inter-Repository Dependencies**: Clearly specify required outputs and inputs
6. **Review Security Configurations**: Ensure proper IAM roles, security groups, and network ACLs across all workspaces

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