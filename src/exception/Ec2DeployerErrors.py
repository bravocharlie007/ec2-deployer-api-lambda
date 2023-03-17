from logger.Ec2DeployerLogger import logger

class Ec2DeployerException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'{self.message}'

class Ec2DeployerLogException(Ec2DeployerException):
    def __init__(self, message):
        self.message = message
        logger.error(self.message)


class Ec2DeployerUserMaxInstanceQuotaExceededException(Ec2DeployerLogException):
    pass

class Ec2DeployerInvalidHttpPathException(Ec2DeployerLogException):
    pass