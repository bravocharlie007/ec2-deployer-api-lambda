from logger.Ec2DeployerLogger import logger
from service.Ec2DeployerService import Ec2DeployerService
from service.SecurityService import SecurityService
from util import Constants
from model.InstancePaveRequestModel import InstancePaveRequestModel
from model.IpWhitelistRequestModel import IpWhitelistRequestModel
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

    @app.post(Constants.EC2_DEPLOYER_PATH_PREFIX + '/gaming/whitelist-ip')
    def whitelist_gaming_ip():
        """
        Allow brothers to whitelist their IPs for gaming access
        """
        logger.info("Inside Ec2DeployerController whitelist_gaming_ip")
        security_service = SecurityService()
        
        json_body = app.current_event.json_body
        
        # Auto-detect client IP if not provided
        if 'ipAddress' not in json_body or not json_body['ipAddress']:
            client_ip = security_service.get_current_client_ip(app.current_event.raw_event)
            if client_ip:
                json_body['ipAddress'] = client_ip
                logger.info(f"Auto-detected client IP: {client_ip}")
        
        ip_whitelist_request: IpWhitelistRequestModel = parse(event=json_body, model=IpWhitelistRequestModel)
        
        return Ec2DeployerController.getResponse(security_service.whitelist_gaming_access, 200, ip_whitelist_request)

    @app.get(Constants.EC2_DEPLOYER_PATH_PREFIX + '/gaming/my-ip')
    def get_client_ip():
        """
        Return the client's IP address for gaming access whitelisting
        """
        logger.info("Inside Ec2DeployerController get_client_ip")
        security_service = SecurityService()
        
        client_ip = security_service.get_current_client_ip(app.current_event.raw_event)
        
        response_body = {
            'client_ip': client_ip,
            'message': 'Use this IP address for gaming access whitelisting'
        }
        
        return Response(
            status_code=200,
            content_type="application/json", 
            body=json.dumps(response_body)
        )


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

