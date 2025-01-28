from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from linkedinAPI import query
import time
import asyncio
import requests
from bs4 import BeautifulSoup
import json
from io_formats import AIOutputData, OutputData
from db_manager import DBManager
from qdrant_manager import QdrantManager
from chatbot import Chatbot
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
import os

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
    "Salary": "120000$-150000$",
    "Summary":"" 
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
  General summary of the offer. One or two paragraphs that contain the information of the role, requirements and benefits of the job
  
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

        self.model = ChatOpenAI(model="gpt-4o-mini",temperature=0)
        self.search_model = self.model.with_structured_output(AIOutputData)

        self.app.add_api_route("/searchLI", self.searchLI, methods=["POST"], response_model=OutputData)
        self.app.add_api_route("/loadAll", self.loadAll, methods=["GET"], response_model=OutputData)
        self.app.add_api_route("/likeJob", self.likeJob, methods=["PUT"])
        self.app.add_api_route("/dislikeJob", self.dislikeJob, methods=["PUT"])
        self.app.add_api_route("/askBot", self.askBot, methods=["POST"])
        self.app.add_api_route("/openConversation", self.openConversation, methods=["POST"])

        self.db = DBManager()
        self.qd = QdrantManager()

        self.chatbot = Chatbot(self.model, self.db, self.qd)
        
    async def process_element(self, element):
        context = fetch_with_retry(element["jobUrl"])
        if context:
            parsed_message = self.search_model.invoke([
                    HumanMessage(get_company_prompt(element["company"], context))
                ],
                response_format=AIOutputData,
            )
            element.update(parsed_message)
            element['liked'] = False
            element['disliked'] = False
            self.ret_data.append(element)
            self.context_data.append(context)

    def loadAll(self):
        return {"data": self.db.loadAll()}

    def likeJob(self,body:dict):
        self.db.likeJob(**body)

    def dislikeJob(self,body:dict):
        self.db.dislikeJob(**body)

    def askBot(self,body:dict):
        print(body)
        return {"data":self.chatbot(body['query'])}

    def openConversation(self,body:dict):
        message_history = self.chatbot.open_conversation(body['company'],body['position'])
        return {"messages":message_history}

    async def searchLI(self,body: dict):
        query_options = body.get("queryOptions", {})

        empty_results = True
        non_dup_data = {}

        n_jobs_search = int(query_options['limit'])
        n_missing_jobs = n_jobs_search
        # Fetch data from LinkedIn
        while n_missing_jobs>0 and query_options.get("page", 0) < 20:
            data = query(query_options)
            for element in data:
                primary_key = (element["company"], element["position"])
                if not self.db.load(*primary_key) and primary_key not in non_dup_data:
                    non_dup_data[primary_key] = element

            n_missing_jobs = n_jobs_search-len(non_dup_data)
            if n_missing_jobs>0:
                query_options['limit'] = str(n_missing_jobs)
            query_options["page"] += 1

        # Process data with OpenAI and fetch additional context
        gpt_proms = []
        self.ret_data = []
        self.context_data = []

        for element in non_dup_data.values():
            gpt_proms.append(self.process_element(element))

        # Wait for all async tasks to complete
        await asyncio.gather(*gpt_proms)

        #print(self.ret_data)
        self.db.save(self.ret_data)
        self.qd.addVectors(self.context_data,[(job['company'], job['position']) for job in self.ret_data])

        return {"data": self.ret_data}

app = JTAPI().app