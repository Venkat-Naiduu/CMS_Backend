from crewai import Crew
from agents.fraud_checker import fraud_agent, fraud_task

crew = Crew(
    agents=[fraud_agent],
    tasks=[fraud_task]
)

result = crew.kickoff()
print("\n--- Final Output ---")
print(result)
