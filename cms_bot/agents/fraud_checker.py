import os
import pandas as pd
from crewai import Agent, Task
from openai import AzureOpenAI 
from langchain_openai import AzureChatOpenAI   
from crewai_tools import FileReadTool
from dotenv import load_dotenv

load_dotenv()

llm = AzureChatOpenAI(
    api_key = os.getenv("AZURE_OPENAI_API_KEY"),
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    model = None

)


surgeries_df = pd.read_csv("data/surgeries.csv")
pmjay_df = pd.read_csv("data/pm_jay.csv")

with open("extracted/claim_001.txt", "r", encoding="utf-8") as f:
    claim_text = f.read()

fraud_agent = Agent(
    role="Insurance Fraud Investigator",
    goal="Analyze claim and identify fraudulent or overbilled treatments",
    backstory=(
        "You are an experienced medical claim auditor. "
        "Your job is to carefully verify the patient's hospital discharge summary against government-approved packages. "
        "You will detect mismatches in procedure names, billing overcharges, or false entries."
    ),
    llm = llm,
    allow_delegation=False,
    verbose=True
    
)

fraud_task = Task(
    description=(
        f"Analyze this patient discharge data:\n\n{claim_text}\n\n"
        "Compare it against PM-JAY and Surgeries datasets. "
        "Check if the claimed procedures match valid package names or codes. "
        "Also verify if the claimed costs are over the allowed price range."
    ),
    expected_output="A report listing valid or invalid procedures, any overbilling cases, and a fraud probability rating (low, medium, high).",
    agent=fraud_agent
)
