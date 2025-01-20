from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from pydantic import BaseModel
from typing import List
from linkedinAPI import query
from openai import OpenAI
from hashlib import sha256
import time
import asyncio
import requests
from bs4 import BeautifulSoup
import json
from mykeys import apiKey

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

class PoditionData(BaseModel):
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

class OutputData(BaseModel):
    data: List[PoditionData]

# Function to generate a unique hash
def generate_hash(company: str, position: str) -> str:
    return sha256(f"{company}:{position}".encode()).hexdigest()


def fetch_with_retry(url, retries=3, delay_ms=2000):
    for attempt in range(1, retries + 1):
        try:
            if attempt > 1:
                print(f"Attempt {attempt} to fetch {url}")

            resp = requests.get(url)
            html = resp.text

            # Parse the HTML
            soup = BeautifulSoup(html, "html.parser")

            # Extract elements
            description = soup.select_one(
                "div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5"
            )
            description = description.get_text(strip=True) if description else None

            json_content = soup.select_one('script[type="application/ld+json"]')
            json_content = json.loads(json_content.string) if json_content else None

            salary = soup.select_one("div.salary.compensation__salary")
            salary = salary.get_text(strip=True) if salary else None

            # Build context
            context = description or ""
            if json_content:
                base_salary = json_content.get("baseSalary")
                if base_salary:
                    context += f"\nbaseSalary: {json.dumps(base_salary)}"
            elif salary:
                context += f"\nsalary: {salary}"

            # Return context if found
            if context:
                return context

            print(f"Attempt {attempt} failed: context is null.")

        except Exception as error:
            print(f"Attempt {attempt} failed with error: {error}")

        # Wait before retrying
        if attempt < retries:
            delay = random.uniform(1, delay_ms / 1000)  # Convert delay_ms to seconds
            time.sleep(delay)

    return None

def get_company_prompt(company, context):

  example_output = {
    "Mission": "It is a search engine that indexes and serves web pages.",
    "Revenue": "Product(B2C)",
    "Size": [150000, 200000],
    "Age": "27",
    "Maturity": "Consolidated",
    "Role": "Develop and optimize deep learning models for image generation",
    "Technologies": "Deep learning, Pytorch, Diffusion models, model optimization",
    "Salary": "120000$-150000$"
  }

  return f"""Summarize the following information about a job offer of the company ${company} and return it in JSON format.
  A sentence with the mission (Avoid vague marketing expressions)
  Revenue type (public, product(B2C), product(B2B) consultancy)
  Company size in aproximated number of employees (just the range)
  Company aproximated age in years
  Company maturity: one of startup(low revenue, fully deppends on investment), scaleup(sustainable revenue, gets help from investment), consolidated(high revenue, does not need investment))
  Very brief description of the role
  Key technologies and knowledge fields that they require (as a succession of keywords)
  Salary range if available (else, not specified)
  Example output with a Google offer:
  {example_output}
  Here is some context of the offer:
  {context}
  """

class JTAPI:
    def __init__(self):
        # Enable CORS
        origins = [
            "http://localhost:8080",  # Adjust the origin according to your Vue.js app's URL
        ]

        # Create the FastAPI app
        self.app = FastAPI()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,  # Allows requests from these origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all HTTP methods
            allow_headers=["*"],  # Allows all headers
        )

        self.openai = OpenAI(api_key = apiKey)
        self.app.add_api_route("/searchLI", self.searchLI, methods=["POST"], response_model=OutputData)
        self.offers = {}


    async def process_element(self, element, unique_key):
        context = fetch_with_retry(element["jobUrl"])
        if context:
            response = self.openai.beta.chat.completions.parse(
                model="gpt-4o-mini",
                store=True,
                messages=[
                    {
                        "role": "user",
                        "content": get_company_prompt(element["company"], context),
                    }
                ],
                response_format=AIOutputData,
            )
            parsed_message = response.choices[0].message.parsed
            element.update(parsed_message)
            self.ret_data.append(element)
            #db.reference(f"/{unique_key}").set(element)
            self.offers[unique_key] = element

    async def searchLI(self,body: dict):
        query_options = body.get("queryOptions", {})

        empty_results = True
        non_dup_data = {}

        # Fetch data from LinkedIn
        while empty_results and query_options.get("page", 0) < 10:
            data = query(query_options)
            for element in data:
                unique_key = generate_hash(element["company"], element["position"])
                if unique_key not in self.offers and unique_key not in non_dup_data:
                    non_dup_data[unique_key] = element

            empty_results = len(non_dup_data) == 0
            query_options["page"] += 1

        # Process data with OpenAI and fetch additional context
        gpt_proms = []
        self.ret_data = []

        for unique_key, element in non_dup_data.items():
            gpt_proms.append(self.process_element(element, unique_key))

        # Wait for all async tasks to complete
        await asyncio.gather(*gpt_proms)

        #print(self.ret_data)

        return {"data": self.ret_data}

app = JTAPI().app