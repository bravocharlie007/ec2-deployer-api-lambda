from logger.Ec2DeployerLogger import logger
from service.Ec2DeployerService import Ec2DeployerService
from util import Constants
from model.InstancePaveRequestModel import InstancePaveRequestModel
from exception.Ec2DeployerErrors import Ec2DeployerUserMaxInstanceQuotaExceededException
from util.Ec2DeployerUtils import Ec2DeployerUtils
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType, Response
from aws_lambda_powertools.utilities.parser import parse, ValidationError


import json

app = ApiGatewayResolver(proxy_type=ProxyEventType.ALBEvent)


@app.get(Constants.EC2_DEPLOYER_PATH_PREFIX+'/ping')
def ping():
    return Response(status_code=200,
                    content_type='application/json',
                    body=json.dumps({'status': 'HEALTHY'})
                    )



class Ec2DeployerController:
    """Ec2DeployerController class"""

    def __init__(self):
        logger.info("Initialized Ec2DeployerController")

    def resolve(self, event, context):
        logger.info("Inside Ec2DeployerController resolve")
        return app.resolve(event, context)

    @app.post(Constants.EC2_DEPLOYER_PATH_PREFIX)
    def submit_instance_pave_request():
        logger.info("Inside Ec2DeployerController submit_instance_pave_request")
        ec2_deployer_service = Ec2DeployerService()
        util = Ec2DeployerUtils()
        ec2_deployer_pave_request_id = util.generate_prefixed_unique_id(Constants.PRE_FIX_EC2_DEPLOYER)
        json_body = app.current_event.json_body
        json_body["requestId"] = ec2_deployer_pave_request_id

        ec2_deployer_pave_request_model: InstancePaveRequestModel = parse(event=json_body, model=InstancePaveRequestModel)

        return Ec2DeployerController.getResponse(ec2_deployer_service.launch_ec2_instance, 202, ec2_deployer_pave_request_model, ec2_deployer_pave_request_id)


    def getResponse(func, status_code, *args):
        logger.info("Inside Ec2DeployerController getResponse")
        try:
            body = func(*args)
            response = Response(
                status_code=status_code,
                content_type="application/json",
                body=json.dumps(body)
            )
        except Ec2DeployerUserMaxInstanceQuotaExceededException as e:
            response =Ec2DeployerUtils.handle_errors(403, "Forbidden", e)
        except Exception as e:
            response =Ec2DeployerUtils.handle_errors(404, "Not Found", e)

