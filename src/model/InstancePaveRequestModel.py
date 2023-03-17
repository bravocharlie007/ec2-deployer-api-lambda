from aws_lambda_powertools.utilities.parser import BaseModel, Field
from typing import Optional

class InstancePaveRequestModel(BaseModel):
    instance_type: str = Field(alias="instanceType")
    image_id: str = Field(alias="imageId")
    request_id: str = Field(alias="requestId")
    count: str
    user: str