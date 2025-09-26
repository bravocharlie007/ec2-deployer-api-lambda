from logger.Ec2DeployerLogger import logger
from util import Constants
from util.Ec2DeployerUtils import Ec2DeployerUtils
import boto3


class Ec2Client:

    def __init__(self):
        logger.info('Initialized EC2 client')
        # SECURITY FIX: Use Lambda execution role instead of hardcoded profile
        # boto3.setup_default_session(profile_name=Constants.EC2_PROFILE)  # REMOVED
        self.ec2_client = boto3.client('ec2')  # Uses Lambda execution role automatically


    @Ec2DeployerUtils.debug_log
    def describe_instances(self):
        logger.info('Describing EC2 instances')
        response = self.ec2_client.describe_instances()
        return response

    @Ec2DeployerUtils.debug_log
    def launch_instance(self, instance_type: str, image_id: str, tags, max_count: int =1, min_count: int=1):
        logger.info('Launching EC2 instance')
        logger.info(f"{tags=}")
        response = self.ec2_client.run_instances(InstanceType=instance_type, ImageId=image_id, MaxCount=max_count, MinCount=min_count, TagSpecifications=tags)
        return response

    @Ec2DeployerUtils.debug_log
    def stop_instance(self, instance_id: str):
        logger.info(f"Stopping Instance {instance_id}")
        response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
        return response


    @Ec2DeployerUtils.debug_log
    def start_instance(self, instance_id: str):
        logger.info(f"Starting instance {instance_id}")
        response = self.ec2_client.start_instances(InstanceIds=[instance_id])
        return response

    @Ec2DeployerUtils.debug_log
    def terminate_instance(self, instance_id):
        logger.info(f"Terminating instance {instance_id}")
        response = self.ec2_client.terminate_instances(InstanceIds=[instance_id])
        return response

def generate_power(exponent):
    def power(func):
        def inner_power(*args):
            base = func(*args)
            return base ** exponent
        return inner_power
    return power




@Ec2DeployerUtils.debug_log
@generate_power(2)
@Ec2DeployerUtils.debug_log
def raise_two(n):
    return n


def main(**kwargs):
    print({**kwargs})


if __name__ == '__main__':
    ec2 = Ec2Client()
    # ec2.describe_instances()
    # response = raise_two(3)
    # print(response)
    instance_type='t2.micro'
    image_id = 'ami-056841b896a354b00'
    instance_id = "i-03ecb5fbdd16527a8"
    # launch_response = ec2.launch_instance(image_id=image_id, instance_type=instance_type)
    # print(launch_response)
    # ec2.stop_instance(instance_id)
    # ec2.start_instance(instance_id)
    # ec2.terminate_instance(instance_id)
    main(color1='blue',color2='red')