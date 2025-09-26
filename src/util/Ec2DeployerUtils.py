import traceback
import json
import re
from aws_lambda_powertools.event_handler.api_gateway import Response
from logger.Ec2DeployerLogger import logger
import uuid

class Ec2DeployerUtils():
    
    def __init__(self):
        logger.info('Initializer Ec2DeployerUtils')

    def debug_log(func):
        def _debug(*args, **kwargs):
            result = func(*args, **kwargs)
            logger.info(
                f"{func.__name__}(args: {args}, kwargs: {kwargs}) -> {result}"
            )
            return result
        return _debug

    def generate_prefixed_unique_id(self, prefix):
        logger.info("In generate_prefixed_unique_id of Ec2DeployerUtils")
        uuid_str = prefix + str(uuid.uuid4())
        return uuid_str

    def generate_tag_list(self, **kwargs):
        return [{'Key': key, 'Value': value} for key, value in {**kwargs}.items()]

    def generate_ec2_tags(self, **kwargs):
        tag_list = self.generate_tag_list(**kwargs)
        return [{'ResourceType': 'instance', 'Tags': tag_list}]

    # SECURITY FIX: Add input validation methods
    def validate_username(self, username: str) -> bool:
        """Validate username: alphanumeric, hyphens, underscores, 3-32 chars"""
        if not username or not isinstance(username, str):
            return False
        pattern = r'^[a-zA-Z0-9_-]{3,32}$'
        return bool(re.match(pattern, username))
    
    def validate_ami_id(self, ami_id: str) -> bool:
        """Validate AMI ID format"""
        if not ami_id or not isinstance(ami_id, str):
            return False
        from util import Constants
        return bool(re.match(Constants.ALLOWED_AMI_PATTERN, ami_id))
    
    def validate_instance_type(self, instance_type: str) -> bool:
        """Validate instance type against allowed list"""
        if not instance_type or not isinstance(instance_type, str):
            return False
        from util import Constants
        return instance_type in Constants.ALLOWED_INSTANCE_TYPES

    @staticmethod
    def handle_errors(status_code, status_description, exception):
        body = {}
        body['statusDescription'] = status_description
        
        # SECURITY FIX: Don't expose detailed exception information
        logger.error(f"Exception: {str(exception)} Traceback log for exception {str(traceback.format_exc())}")
        
        # Return generic error message instead of detailed exception
        if status_code >= 500:
            body["error"] = "Internal server error occurred"
        elif status_code == 403:
            body["error"] = "Access denied"
        elif status_code == 400:
            body["error"] = "Invalid request"
        else:
            body["error"] = "Request could not be processed"
            
        return Response(
            status_code=status_code,
            content_type="application/json",
            body=json.dumps(body)
        )

    @staticmethod
    def filter_aws_response(aws_response):
        """SECURITY FIX: Filter sensitive data from AWS responses"""
        if not isinstance(aws_response, dict):
            return aws_response
            
        # Only return essential instance information
        filtered_response = {}
        if 'Instances' in aws_response and isinstance(aws_response['Instances'], list):
            filtered_instances = []
            for instance in aws_response['Instances']:
                filtered_instance = {
                    'InstanceId': instance.get('InstanceId'),
                    'State': instance.get('State', {}).get('Name'),
                    'InstanceType': instance.get('InstanceType'),
                    'LaunchTime': instance.get('LaunchTime'),
                    'Tags': instance.get('Tags', [])
                }
                filtered_instances.append(filtered_instance)
            filtered_response['Instances'] = filtered_instances
            
        return filtered_response if filtered_response else {'message': 'Instance operation completed'}


if __name__ == "__main__":
    utils = Ec2DeployerUtils()
    print(utils.generate_tags(color1='vlue', color2='red'))