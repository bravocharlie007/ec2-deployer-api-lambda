from client.AwsClients import Ec2Client
from logger.Ec2DeployerLogger import logger
from exception.Ec2DeployerErrors import Ec2DeployerUserMaxInstanceQuotaExceededException
from util import Constants
from util.Ec2DeployerUtils import Ec2DeployerUtils
import json
from datetime import datetime

class Ec2DeployerService:

    def __init__(self):
        logger.info("Initialized Ec2DeployerService")

    def launch_ec2_instance(self, instance_pave_request_model):
        logger.info(f"In launch_ec2_instance of Ec2DeployerService")
        user = instance_pave_request_model.user
        request_id = instance_pave_request_model.request_id
        image_id = instance_pave_request_model.image_id
        instance_type = instance_pave_request_model.instance_type
        count = int(instance_pave_request_model.count) if instance_pave_request_model.count else 1
        max_count = count
        min_count = count
        
        # SECURITY FIX: Audit logging - Log the request attempt
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "launch_ec2_instance_attempt",
            "user": user,
            "request_id": request_id,
            "instance_type": instance_type,
            "image_id": image_id,
            "count": count
        }
        logger.info(f"AUDIT: {json.dumps(audit_data)}")
        
        # TODO: Implement real user quota tracking with DynamoDB
        # For now, keeping existing logic but noting the security issue
        current_user_number = 0  # SECURITY ISSUE: This should query actual user instance count
        if current_user_number >= Constants.USER_MAX_INSTANCE_QUOTA:
            # SECURITY FIX: Audit logging - Log quota exceeded
            audit_fail = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "launch_ec2_instance_denied",
                "user": user, 
                "request_id": request_id,
                "reason": "quota_exceeded",
                "current_count": current_user_number,
                "quota_limit": Constants.USER_MAX_INSTANCE_QUOTA
            }
            logger.warning(f"AUDIT: {json.dumps(audit_fail)}")
            raise Ec2DeployerUserMaxInstanceQuotaExceededException(f"User {user} has already exceeded the maximum allowed number of instances per user of {Constants.USER_MAX_INSTANCE_QUOTA}")
        else:
            logger.info(f"User {user} has not exceeded the maximum allowed number of instances per user, proceeding.")
            
        ec2_deployer_util = Ec2DeployerUtils()
        tags = ec2_deployer_util.generate_ec2_tags(request_id=request_id, user=user)
        
        try:
            # Store information in RDS tables of instances and users
            ec2_client = Ec2Client()
            response = ec2_client.launch_instance(instance_type, image_id, tags, max_count, min_count)
            instance_id = response["Instances"][0]["InstanceId"]
            
            # SECURITY FIX: Audit logging - Log successful instance creation
            audit_success = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "launch_ec2_instance_success",
                "user": user,
                "request_id": request_id,
                "instance_id": instance_id,
                "instance_type": instance_type,
                "image_id": image_id
            }
            logger.info(f"AUDIT: {json.dumps(audit_success)}")
            logger.info(f"Successfully launched instance with instance id: {instance_id}")
            
            return response
            
        except Exception as e:
            # SECURITY FIX: Audit logging - Log failed instance creation
            audit_error = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "launch_ec2_instance_failed",
                "user": user,
                "request_id": request_id,
                "error": str(e),
                "instance_type": instance_type,
                "image_id": image_id
            }
            logger.error(f"AUDIT: {json.dumps(audit_error)}")
            raise  # Re-raise the exception after logging


if __name__ == '__main__':
    instance_type = 't2.micro'
    ami = 'ami-056841b896a354b00'
    count = 1
    service = Ec2DeployerService()
    # Note: This test code needs to be updated to use the new model structure
    # service.launch_ec2_instance(instance_type, ami, count)