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
After reviewing the available repositories in the bravocharlie007 organization, this Lambda function is part of a **three-repository infrastructure workspace** consisting of:

### Discovered Infrastructure Components
The complete infrastructure consists of these repositories:
- **VPC Repository** (https://github.com/bravocharlie007/vpc): Manages network infrastructure, VPC, subnets, IGW, and route tables
- **Compute Repository** (https://github.com/bravocharlie007/compute): Handles ALB/NLB infrastructure, EC2 instances, security groups, and EIPs
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
Based on the actual repository analysis, follow this deployment sequence:

#### Phase 1: Foundation Infrastructure (VPC Repository)
**Repository**: https://github.com/bravocharlie007/vpc
1. **VPC Infrastructure**:
   - VPC creation with 15.0.0.0/16 CIDR block
   - 2 public subnets (PublicSubnet01, PublicSubnet02) across AZs
   - 1 private subnet (PrivateSubnet02) 
   - Internet Gateway and public route table
   - Route table associations for all subnets
   - Comprehensive resource tagging with deployment IDs

**Key Outputs**:
- `vpc_id`: Used by compute and Lambda resources
- `subnet_id_list`: Required for ALB and EC2 placement
- `subnet_id_map`: Subnet lookup by type
- `igw_id`, `rt_id`: Network routing references
- `root_deployment_id`: Cross-workspace deployment tracking

#### Phase 2: Load Balancer & Compute Infrastructure (Compute Repository)  
**Repository**: https://github.com/bravocharlie007/compute
2. **Application Load Balancer & EC2 Infrastructure**:
   - Application Load Balancer (ALB) in public subnets
   - ALB target group with health checks
   - HTTP listener (port 80) with path-based routing
   - Security groups for ALB (internet access) and EC2 (ALB-only access)
   - 2x t3.micro EC2 instances with Apache HTTP servers
   - Elastic IP addresses for each instance
   - Target group attachments for load balancing

**Dependencies**: 
- Uses `terraform_remote_state` to reference VPC workspace
- Requires VPC outputs: `vpc_id`, `subnet_id_list`

**Key Outputs**:
- `alb_dns_name`: Load balancer endpoint
- `ec2_instances`: Instance details with IPs and ENIs
- `alb_zone_id`: For Route 53 integration
- `tg_attachments`: Target group configuration

#### Phase 3: API Lambda Function (Current Repository)
**Repository**: https://github.com/bravocharlie007/ec2-deployer-api-lambda
3. **EC2 Deployer API Lambda**:
   - Lambda function deployment with ALB event source
   - Lambda execution role with EC2 management permissions
   - CloudWatch log groups and X-Ray tracing
   - Integration with existing ALB from compute workspace

**Dependencies**:
- ALB from compute repository as event source
- VPC from vpc repository for Lambda deployment (if VPC-enabled)
- IAM permissions for EC2 operations in target VPC/subnets

#### Phase 4: Integration & Testing
4. **End-to-End Validation**:
   - ALB health check validation (compute repository)
   - Lambda function registration with ALB target
   - API endpoint accessibility through ALB DNS name
   - EC2 instance launching via Lambda API
   - Cross-workspace resource connectivity testing

### Dependencies and Outputs
Based on the actual repository analysis, here are the cross-workspace dependencies:

**VPC Repository Outputs** (consumed by compute and Lambda):
```hcl
output "vpc_id"              # VPC identifier for all resources
output "subnet_id_list"      # List of subnet IDs for ALB and EC2 placement  
output "subnet_id_map"       # Subnet lookup by type (Public/Private)
output "igw_id"              # Internet Gateway ID
output "rt_id"               # Route Table ID
output "root_deployment_id"  # Cross-workspace deployment tracking
```

**Compute Repository Outputs** (consumed by Lambda):
```hcl
output "alb_dns_name"        # Load balancer endpoint for API access
output "ec2_instances"       # Instance details with IPs and network interfaces
output "alb_zone_id"         # Route 53 hosted zone ID
output "subnet_ids"          # Subnet references from VPC workspace
output "tg_attachments"      # Target group attachment IDs
```

**Current Repository Dependencies**:
- **VPC Integration**: Uses VPC ID and subnet IDs for Lambda deployment context
- **ALB Integration**: ALB DNS name serves as API endpoint, ALB events trigger Lambda function
- **IAM Permissions**: Requires EC2 management permissions within the VPC scope

### Current Integration Status
This repository currently integrates with the following infrastructure:

**From VPC Repository** (https://github.com/bravocharlie007/vpc):
- **Network Foundation**: VPC with 15.0.0.0/16 CIDR
- **Subnet Architecture**: 2 public subnets + 1 private subnet across AZs
- **Routing**: Internet Gateway with public route table
- **Tagging Strategy**: Consistent resource tagging with deployment tracking

**From Compute Repository** (https://github.com/bravocharlie007/compute):
- **Application Load Balancer**: Internet-facing ALB distributing traffic
- **Target Infrastructure**: 2x t3.micro EC2 instances with Apache
- **Security Configuration**: Layered security groups (ALB → internet, EC2 → ALB only)
- **Health Monitoring**: ALB target group with health checks
- **Static Addressing**: Elastic IPs for consistent instance access

**Lambda Integration Points**:
- **Event Source**: Configured for ALB events (ProxyEventType.ALBEvent)
- **API Endpoints**: `/deployer/v1/instances` for EC2 management
- **Health Check**: `/deployer/v1/instances/ping` endpoint
- **AWS Services**: Direct EC2 API calls for instance lifecycle management
- **Observability**: CloudWatch logging and X-Ray tracing capabilities

### Infrastructure Deployment Notes
✅ **Updated Analysis**: The infrastructure components referenced are now accessible and analyzed:

**VPC Repository**: https://github.com/bravocharlie007/vpc
- Terraform-based VPC infrastructure with comprehensive networking setup
- Uses Terraform Cloud remote state with organization "EC2-DEPLOYER-DEV"
- Provides foundational network resources for compute layer

**Compute Repository**: https://github.com/bravocharlie007/compute  
- Complete ALB + EC2 infrastructure with security groups and EIPs
- Uses `terraform_remote_state` to consume VPC workspace outputs
- Manages load balancer, target groups, and EC2 instances with Apache

**Workspace Integration Pattern**:
- VPC workspace deploys first, provides remote state outputs
- Compute workspace consumes VPC state, deploys ALB + EC2 infrastructure  
- Lambda function (this repo) integrates with ALB for API event handling
- All components use consistent tagging and deployment ID tracking

## Potential Code Changes for Better Integration

### VPC Integration Enhancements
Based on the VPC repository analysis, consider these modifications to `Ec2DeployerService.py`:

1. **Subnet Selection Logic**:
   ```python
   # Add subnet parameter to InstancePaveRequestModel
   # Implement logic to select appropriate subnet from VPC workspace outputs
   def select_target_subnet(self, placement_preference="public"):
       # Logic to choose from subnet_id_list based on availability and type
       return selected_subnet_id
   ```

2. **VPC-Aware Security Group Assignment**:
   ```python
   # Reference VPC-managed security groups from compute workspace
   def get_vpc_security_groups(self, vpc_id):
       # Query security groups created by compute workspace
       return security_group_ids
   ```

**Rationale**: The VPC repository creates specific subnets (PublicSubnet01, PublicSubnet02, PrivateSubnet02) that should be used for proper instance placement and network isolation.

### ALB Integration Optimizations
Based on the compute repository's ALB configuration, enhance integration:

1. **Target Group Integration** (`Ec2DeployerService.py`):
   ```python
   def register_with_alb_target_group(self, instance_id, target_group_arn):
       # Auto-register launched instances with existing ALB target group
       # This would enable load balancing for API-launched instances
       pass
   ```

2. **Health Check Endpoint Enhancement** (`Ec2DeployerController.py`):
   ```python
   @app.get(Constants.EC2_DEPLOYER_PATH_PREFIX+'/health')
   def enhanced_health_check():
       # Add ALB connectivity validation
       # Check VPC accessibility
       # Validate EC2 service permissions
       return comprehensive_health_status
   ```

**Rationale**: The compute repository's ALB expects specific health check patterns and target group configurations that this Lambda could leverage for launched instances.

### Configuration Management Integration
When integrated with the workspace pattern:

1. **Environment-Specific Configuration**:
   ```python
   # Replace Constants.py hardcoded values with Terraform outputs
   EC2_PROFILE = os.environ.get('AWS_EXECUTION_ROLE') 
   VPC_ID = os.environ.get('VPC_ID')  # From VPC workspace
   SUBNET_IDS = os.environ.get('SUBNET_IDS').split(',')  # From VPC workspace
   ALB_TARGET_GROUP_ARN = os.environ.get('TARGET_GROUP_ARN')  # From compute workspace
   ```

2. **Cross-Workspace State Integration**:
   ```python
   # Add Terraform remote state client for dynamic configuration
   def get_workspace_outputs(workspace_name):
       # Integrate with Terraform Cloud API to fetch workspace outputs
       return workspace_state
   ```

**Rationale**: Both VPC and compute repositories use Terraform Cloud with organization "EC2-DEPLOYER-DEV" and environment-based workspaces, enabling dynamic configuration lookup.

### Rationale for Each Suggested Change

**VPC Integration Changes**:
- **Subnet Selection**: The VPC repository creates 3 specific subnets with different purposes (2 public, 1 private). Instance placement should respect this architecture for proper network isolation and routing.
- **Security Group Integration**: The compute repository creates security groups that allow ALB→EC2 communication. Lambda-launched instances should use the same security groups for consistency.

**ALB Integration Changes**:
- **Target Group Registration**: The compute repository's ALB expects instances in specific target groups. API-launched instances could benefit from automatic load balancing by joining these target groups.
- **Health Check Enhancement**: The existing ALB has health check patterns (`/var/www/html/index.html`). The Lambda health check should validate connectivity to these systems.

**Configuration Changes**:
- **Environment Variables**: Both repositories use Terraform Cloud with consistent tagging and deployment IDs. The Lambda should integrate with this pattern rather than using hardcoded values.
- **Remote State Integration**: The compute repository successfully uses `terraform_remote_state` to consume VPC outputs. The Lambda could use similar patterns for dynamic configuration.

**Cross-Workspace Communication**:
- **Deployment ID Consistency**: Both repositories use `root_deployment_id` for resource tracking. The Lambda should participate in this tracking system.
- **Tagging Alignment**: All resources should follow the same tagging strategy used across VPC and compute workspaces for unified resource management.

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