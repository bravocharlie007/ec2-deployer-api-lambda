import logging

from aws_lambda_powertools import Logger

log = logging.getLogger()
log.setLevel(logging.INFO)
date_format = '%d-%m-%Y:%H:%M:%S'
fmt_string = '%(asctime)s, %(levelname)-8s [%(filename)s:(args):%(lineno)d]:%(message)s'
logging.basicConfig(level=logging.INFO, format=fmt_string, datefmt=date_format)
fileformatter = logging.Formatter(fmt_string)


# logger = Logger(service="ec2deployer-api-lambda", log_record_order=["message"], datefmt= date_format, logger_formatter=fmt_string)
logger = Logger(service="ec2-deployer-api-lambda", log_record_order=["message"], datefmt= date_format)