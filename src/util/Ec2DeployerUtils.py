import traceback
import json
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

    @staticmethod
    def handle_errors(status_code, status_description, exception):
        body = {}
        body['statusDescription'] = status_description
        logger.error(f"Exception: {str(exception)} Traceback log for exception {str(traceback.format_exc())}")
        body["exception"] = str(exception)
        return Response(
            status_code=status_code,
            content_type="application/json",
            body=json.dumps(body)
        )


if __name__ == "__main__":
    utils = Ec2DeployerUtils()
    print(utils.generate_tags(color1='vlue', color2='red'))