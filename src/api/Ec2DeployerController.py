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

# SECURITY FIX: Add basic API key authentication middleware
def validate_api_key():
    """Basic API key validation - should be enhanced with proper auth system"""
    headers = app.current_event.headers or {}
    api_key = headers.get(Constants.REQUIRED_API_KEY_HEADER) or headers.get(Constants.REQUIRED_API_KEY_HEADER.lower())
    
    if not api_key:
        logger.warning("Missing API key in request")
        return False
    
    # In production, validate against secure key storage (e.g., AWS Secrets Manager)
    # For now, this is a placeholder that accepts any non-empty key
    # TODO: Implement proper authentication (JWT, OAuth, etc.)
    if len(api_key) < 10:  # Minimum key length check
        logger.warning("Invalid API key format")
        return False
        
    logger.info("API key validation passed")
    return True


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
        
        # SECURITY FIX: Add authentication check
        if not validate_api_key():
            return Response(
                status_code=401,
                content_type="application/json",
                body=json.dumps({"error": "Authentication required", "statusDescription": "Unauthorized"})
            )
        
        # SECURITY FIX: Add input validation
        util = Ec2DeployerUtils()
        try:
            json_body = app.current_event.json_body
            if not json_body:
                return Response(
                    status_code=400,
                    content_type="application/json", 
                    body=json.dumps({"error": "Request body required", "statusDescription": "Bad Request"})
                )
            
            # Validate inputs before processing
            username = json_body.get('user', '')
            ami_id = json_body.get('imageId', '')
            instance_type = json_body.get('instanceType', '')
            
            if not util.validate_username(username):
                return Response(
                    status_code=400,
                    content_type="application/json",
                    body=json.dumps({"error": "Invalid username format", "statusDescription": "Bad Request"})
                )
                
            if not util.validate_ami_id(ami_id):
                return Response(
                    status_code=400,
                    content_type="application/json", 
                    body=json.dumps({"error": "Invalid AMI ID format", "statusDescription": "Bad Request"})
                )
                
            if not util.validate_instance_type(instance_type):
                return Response(
                    status_code=400,
                    content_type="application/json",
                    body=json.dumps({"error": "Invalid or not allowed instance type", "statusDescription": "Bad Request"})
                )
            
            ec2_deployer_service = Ec2DeployerService()
            ec2_deployer_pave_request_id = util.generate_prefixed_unique_id(Constants.PRE_FIX_EC2_DEPLOYER)
            json_body["requestId"] = ec2_deployer_pave_request_id

            ec2_deployer_pave_request_model: InstancePaveRequestModel = parse(event=json_body, model=InstancePaveRequestModel)

            return Ec2DeployerController.getResponse(ec2_deployer_service.launch_ec2_instance, 202, ec2_deployer_pave_request_model, ec2_deployer_pave_request_id)
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response(
                status_code=400,
                content_type="application/json",
                body=json.dumps({"error": "Invalid request format", "statusDescription": "Bad Request"})
            )


    def getResponse(func, status_code, *args):
        logger.info("Inside Ec2DeployerController getResponse")
        try:
            body = func(*args)
            
            # SECURITY FIX: Filter sensitive data from response
            filtered_body = Ec2DeployerUtils.filter_aws_response(body)
            
            response = Response(
                status_code=status_code,
                content_type="application/json",
                body=json.dumps(filtered_body, default=str)  # Handle datetime serialization
            )
        except Ec2DeployerUserMaxInstanceQuotaExceededException as e:
            response = Ec2DeployerUtils.handle_errors(403, "Forbidden", e)
        except Exception as e:
            # SECURITY FIX: Use generic error handling
            response = Ec2DeployerUtils.handle_errors(500, "Internal Server Error", e)
        
        return response
