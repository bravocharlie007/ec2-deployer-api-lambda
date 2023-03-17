from aws_lambda_powertools import Tracer
from api.Ec2DeployerControllerResolver import Ec2DeployerControllerResolver
from exception.Ec2DeployerErrors import Ec2DeployerInvalidHttpPathException
from logger.Ec2DeployerLogger import logger

tracer=Tracer(service="ec2-deployer-api-lambda")

def invoke_controller(controller, alb_model):
    if controller is not None:
        response = controller.execute_endpoint(alb_model)
    else:
        raise Ec2DeployerInvalidHttpPathException("Invalid Path - Unable to resolve Controller")
    return response

@tracer.capture_lambda_handler
def lambda_handler(event, context):
    logger.info(f"Received Event: {event}")
    controller_resolver = Ec2DeployerControllerResolver()
    controller = controller_resolver.resolve(event)
    response = controller.resolve(event, context)
    logger.info(f"Response is: {response}")
    return response