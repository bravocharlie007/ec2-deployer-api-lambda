from aws_lambda_powertools.utilities.parser import BaseModel, Field
from typing import Optional

class IpWhitelistRequestModel(BaseModel):
    ip_address: str = Field(alias="ipAddress")
    user_name: str = Field(alias="userName") 
    description: Optional[str] = None
    duration_hours: int = Field(alias="durationHours", default=24)
    protocols: list = Field(default=["ssh", "rdp"])