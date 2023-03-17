from client.AwsClients import Ec2Client
from logger.Ec2DeployerLogger import logger
from exception.Ec2DeployerErrors import Ec2DeployerUserMaxInstanceQuotaExceededException
from util import Constants
from util.Ec2DeployerUtils import Ec2DeployerUtils
class Ec2DeployerService:

    def __init__(self):
        logger.info("Initialized Ec2DeployerService")

    def launch_ec2_instance(self, instance_pave_request_model):
        logger.info(f"In launch_ec2_instance of Ec2DeployerService")
        user = instance_pave_request_model.user
        request_id = instance_pave_request_model.request_id
        image_id = instance_pave_request_model.image_id
        instance_type = instance_pave_request_model.instance_type
        max_count = count
        min_count = count
        # get current user instance number
        current_user_number = 0
        if current_user_number >= Constants.USER_MAX_INSTANCE_QUOTA:
            raise Ec2DeployerUserMaxInstanceQuotaExceededException(f"User {user} has already exceeded the maximum allowed number of instances per user of {Constants.USER_MAX_INSTANCE_QUOTA}")
        else:
            logger.info(f"User {user} has not exceeded the maximum allowed number of instances per user, proceeding.")
        ec2_deployer_util = Ec2DeployerUtils()

        tags = ec2_deployer_util.generate_ec2_tags(request_id=request_id, user=user)
        # Store information in RDS tables of instances and users
        ec2_client = Ec2Client()
        response = ec2_client.launch_instance(instance_type, image_id, tags, max_count, min_count)
        instance_id = response["Instances"][0]["InstanceId"]
        logger.info(f"Successfully launched instance with instance id: {instance_id}")
        return response


if __name__ == '__main__':
    instance_type = 't2.micro'
    ami = 'ami-056841b896a354b00'
    count = 1
    service = Ec2DeployerService()
    service.launch_ec2_instance(instance_type, ami, count)