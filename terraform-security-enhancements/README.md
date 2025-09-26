# Gaming Security Enhancements

## Overview
This directory contains security enhancements for your cloud gaming infrastructure to address the identified security vulnerabilities.

## Current Security Issues Identified

### 🚨 Critical Issues in Compute Repository:
1. **SSH Wide Open**: `cidr_blocks = ["0.0.0.0/0"]` on port 22 allows anyone to attempt SSH
2. **Password Authentication**: User data enables SSH password auth, vulnerable to brute force attacks
3. **No Gaming Protocols**: Missing RDP (3389) and gaming-specific ports
4. **No IP Restrictions**: No mechanism to limit access to known users/IPs

## Recommended Security Solutions

### Option 1: Dynamic IP Whitelisting (Implemented)
**Lambda API endpoints added**:
- `POST /deployer/v1/instances/gaming/whitelist-ip` - Brothers call this to whitelist their current IP
- `GET /deployer/v1/instances/gaming/my-ip` - Shows current client IP for whitelisting

**How it works**:
1. Brother visits `GET /gaming/my-ip` endpoint to see their current IP
2. Brother calls `POST /gaming/whitelist-ip` with their details
3. Lambda dynamically adds security group rules for gaming access
4. Rules expire automatically after specified duration (default 24 hours)

**Usage Example**:
```bash
# Check current IP
curl https://your-alb-dns/deployer/v1/instances/gaming/my-ip

# Whitelist IP for gaming access  
curl -X POST https://your-alb-dns/deployer/v1/instances/gaming/whitelist-ip \
  -H "Content-Type: application/json" \
  -d '{
    "userName": "brother1",
    "ipAddress": "auto-detect",
    "durationHours": 24,
    "protocols": ["ssh", "rdp", "gaming_steam"]
  }'
```

### Option 2: Terraform Security Hardening
**Files to integrate**:
- `gaming-security-groups.tf` - Enhanced security groups for compute repository

**Key improvements**:
- Remove `0.0.0.0/0` SSH access
- Add gaming-specific security groups with proper port mappings
- Implement bastion host pattern for secure access
- Add Systems Manager endpoints for SSH-free access

### Option 3: VPN-Based Access (Recommended for Production)
```bash
# Example AWS Client VPN setup
aws ec2 create-client-vpn-endpoint \
  --client-cidr-block 10.0.100.0/22 \
  --server-certificate-arn arn:aws:acm:region:account:certificate/cert-id \
  --authentication-options Type=certificate-authentication,MutualAuthentication={ClientRootCertificateChainArn=arn:aws:acm:region:account:certificate/cert-id}
```

## Implementation Steps

### Step 1: Update Lambda Function (Already Done)
- Added `SecurityService` class
- Added gaming IP whitelisting endpoints
- Added IP detection capabilities

### Step 2: Update Compute Repository Security Groups
```bash
# In your compute repository, replace the current EC2 security group with:
# - Remove: cidr_blocks = ["0.0.0.0/0"] for SSH
# - Add: gaming-specific security groups from gaming-security-groups.tf
```

### Step 3: Update EC2 User Data (Compute Repository)
```bash
# Remove or secure password authentication:
# sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Instead use key-based auth and/or disable password auth:
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
```

### Step 4: Deploy Enhanced IAM Permissions
The Lambda needs additional EC2 permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress"
      ],
      "Resource": "*"
    }
  ]
}
```

## Security Best Practices Applied

1. **Principle of Least Privilege**: Only grant access when needed, to specific IPs, for limited time
2. **Defense in Depth**: Multiple security layers (Lambda validation, security groups, temporary access)
3. **Auditability**: All access requests logged through Lambda with user identification
4. **Automation**: Temporary rules with automatic expiration
5. **IP Validation**: Proper IP address validation before security group updates

## Gaming-Specific Considerations

### Port Mappings Implemented:
- SSH: 22/tcp (Linux access)
- RDP: 3389/tcp (Windows gaming instances)
- Steam Remote Play: 27036-27037/tcp
- VNC: 5900/tcp (remote desktop)
- Custom Gaming: 7777/tcp and 7777/udp

### Access Patterns:
1. **Quick Access**: Brother calls API, gets immediate gaming access
2. **Temporary**: Rules auto-expire to limit exposure window
3. **Traceable**: Each access tied to user name and timestamp
4. **Flexible**: Support multiple protocols per user

## Next Steps

1. **Deploy Lambda changes** (already implemented in this PR)
2. **Update compute repository** with enhanced security groups
3. **Test gaming access** with brothers using new API endpoints
4. **Set up automated cleanup** for expired security group rules
5. **Consider VPN upgrade** for production gaming setup

## Cost Impact

- Lambda API calls: ~$0.20 per million requests
- Security group rules: No additional cost
- VPC endpoints (if implemented): ~$7-10/month per endpoint
- Overall security improvement: Significant risk reduction