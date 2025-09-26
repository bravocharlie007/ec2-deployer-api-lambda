# Removed hardcoded AWS profile - now uses Lambda execution role
# EC2_PROFILE = "CharlesIC"  # SECURITY FIX: Use IAM execution role instead
USER_MAX_INSTANCE_QUOTA = 1
PRE_FIX_EC2_DEPLOYER = "EDR-"

EC2_DEPLOYER_PATH_PREFIX = "deployer/v1/instances"

# Security configuration
REQUIRED_API_KEY_HEADER = "x-api-key"
ALLOWED_INSTANCE_TYPES = ["t2.micro", "t2.small", "t2.medium", "t3.micro", "t3.small", "t3.medium"]
ALLOWED_AMI_PATTERN = r"^ami-[0-9a-f]{8,17}$"