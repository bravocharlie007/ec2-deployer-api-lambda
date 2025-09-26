# Gaming Security Enhancements for Compute Repository
# Add these resources to your compute repository main.tf

# Enhanced gaming security group with restricted access
resource "aws_security_group" "gaming_access_sg" {
  name        = "gaming-access-sg"
  description = "Dynamic gaming access security group"
  vpc_id      = data.terraform_remote_state.vpc.outputs.vpc_id
  
  tags = merge(local.common_tags, {
    "Name" = "gaming-access-sg"
    "Purpose" = "Dynamic gaming access control"
  })
}