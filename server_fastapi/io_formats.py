from pydantic import BaseModel
from typing import List

# Define the data structure for the output JSON
class AIOutputData(BaseModel):
    Mission: str
    Revenue: str
    Size: List[int]
    Age: int
    Maturity: str
    Role: str
    Technologies: str
    Salary: str
    Summary: str

class PositionData(BaseModel):
    position: str
    company: str
    location: str
    date: str
    salary: str
    jobUrl: str
    companyLogo: str
    agoTime: str
    Mission: str
    Revenue: str
    Size: List[int]
    Age: int
    Maturity: str
    Role: str
    Technologies: str
    Salary: str
    Summary: str
    liked: bool
    disliked: bool

class OutputData(BaseModel):
    data: List[PositionData]