from logger.Ec2DeployerLogger import logger
from util import Constants
from exception.Ec2DeployerErrors import Ec2DeployerInvalidHttpPathException
from api.Ec2DeployerController import Ec2DeployerController
class Ec2DeployerControllerResolver:

    def __init__(self):
        logger.info("Initialized Ec2DeployerControllerResolver")

    def resolve(self, event):
        path = event['path']
        logger.info(f"Path is: {path}")
        controller = None
        if path.startswith(Constants.EC2_DEPLOYER_PATH_PREFIX):
            controller = Ec2DeployerController()
        else:
            raise Ec2DeployerInvalidHttpPathException("Invalid Path - Unable to resolve Controller")
        return controller