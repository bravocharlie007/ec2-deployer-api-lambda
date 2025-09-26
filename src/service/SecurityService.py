from client.AwsClients import Ec2Client
from logger.Ec2DeployerLogger import logger
from util import Constants
from util.Ec2DeployerUtils import Ec2DeployerUtils
import ipaddress
import boto3
from datetime import datetime, timedelta

class SecurityService:
    """Service for managing gaming infrastructure security"""

    def __init__(self):
        logger.info("Initialized SecurityService")
        self.ec2_client = Ec2Client()
        self.ec2_resource = boto3.resource('ec2')
        
    def whitelist_gaming_access(self, ip_whitelist_request):
        """
        Dynamically whitelist IP for gaming access (SSH, RDP, custom ports)
        """
        logger.info(f"Processing IP whitelist request for {ip_whitelist_request.user_name}")
        
        # Validate IP address
        try:
            validated_ip = ipaddress.ip_address(ip_whitelist_request.ip_address)
            cidr_block = f"{validated_ip}/32"
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_whitelist_request.ip_address}")
        
        # Get gaming security group
        gaming_sg_id = self._get_gaming_security_group()
        
        # Add temporary rules for gaming protocols
        rules_added = []
        for protocol in ip_whitelist_request.protocols:
            port_info = self._get_protocol_ports(protocol)
            rule_id = self._add_security_group_rule(
                gaming_sg_id, 
                port_info['port'], 
                cidr_block,
                port_info['protocol'],
                f"Temp access for {ip_whitelist_request.user_name} - {protocol}",
                ip_whitelist_request.duration_hours
            )
            rules_added.append({
                'rule_id': rule_id,
                'protocol': protocol,
                'port': port_info['port'],
                'expires_at': (datetime.now() + timedelta(hours=ip_whitelist_request.duration_hours)).isoformat()
            })
        
        logger.info(f"Added {len(rules_added)} security rules for {ip_whitelist_request.user_name}")
        return {
            'success': True,
            'ip_address': ip_whitelist_request.ip_address,
            'user_name': ip_whitelist_request.user_name,
            'rules_added': rules_added,
            'expires_in_hours': ip_whitelist_request.duration_hours
        }
    
    def _get_gaming_security_group(self):
        """Get or create security group for gaming access"""
        # Look for existing gaming security group
        try:
            security_groups = self.ec2_client.ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': ['gaming-access-sg']},
                    {'Name': 'description', 'Values': ['Dynamic gaming access security group']}
                ]
            )
            
            if security_groups['SecurityGroups']:
                return security_groups['SecurityGroups'][0]['GroupId']
            
            # Create new gaming security group if not exists
            return self._create_gaming_security_group()
            
        except Exception as e:
            logger.error(f"Error getting gaming security group: {str(e)}")
            raise
    
    def _create_gaming_security_group(self):
        """Create dedicated security group for gaming access"""
        # This would need VPC ID from the VPC workspace
        # For now, assuming it exists or will be created via Terraform
        logger.info("Gaming security group should be created via Terraform in compute workspace")
        raise NotImplementedError("Gaming security group should be pre-created in compute workspace")
    
    def _get_protocol_ports(self, protocol):
        """Get port mappings for gaming protocols"""
        port_mappings = {
            'ssh': {'port': 22, 'protocol': 'tcp'},
            'rdp': {'port': 3389, 'protocol': 'tcp'},
            'gaming_steam': {'port': 27036, 'protocol': 'tcp'},
            'gaming_discord': {'port': 443, 'protocol': 'tcp'},
            'vnc': {'port': 5900, 'protocol': 'tcp'},
            'custom_game_tcp': {'port': 7777, 'protocol': 'tcp'},
            'custom_game_udp': {'port': 7777, 'protocol': 'udp'}
        }
        
        if protocol not in port_mappings:
            raise ValueError(f"Unsupported protocol: {protocol}")
            
        return port_mappings[protocol]
    
    def _add_security_group_rule(self, sg_id, port, cidr_block, protocol, description, duration_hours):
        """Add temporary security group rule with expiration tracking"""
        try:
            response = self.ec2_client.ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': protocol,
                        'FromPort': port,
                        'ToPort': port,
                        'IpRanges': [
                            {
                                'CidrIp': cidr_block,
                                'Description': f"{description} (expires in {duration_hours}h)"
                            }
                        ]
                    }
                ]
            )
            
            # TODO: Store rule expiration in DynamoDB for cleanup
            # self._store_rule_expiration(sg_id, port, cidr_block, duration_hours)
            
            return f"{sg_id}:{port}:{cidr_block.replace('/', '_')}"
            
        except Exception as e:
            logger.error(f"Error adding security group rule: {str(e)}")
            raise
    
    def cleanup_expired_rules(self):
        """Clean up expired temporary security group rules"""
        # TODO: Implement cleanup based on DynamoDB expiration tracking
        logger.info("Cleanup functionality to be implemented")
        pass
    
    def get_current_client_ip(self, event):
        """Extract client IP from ALB event"""
        try:
            # ALB forwards client IP in headers
            headers = event.get('headers', {})
            
            # Check X-Forwarded-For header (ALB standard)
            forwarded_for = headers.get('x-forwarded-for', '')
            if forwarded_for:
                # Take first IP in case of multiple proxies
                client_ip = forwarded_for.split(',')[0].strip()
                return client_ip
            
            # Fallback to source IP from event
            return event.get('requestContext', {}).get('identity', {}).get('sourceIp')
            
        except Exception as e:
            logger.error(f"Error extracting client IP: {str(e)}")
            return None