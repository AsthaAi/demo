"""
ShopperAI Main Orchestration
Coordinates all agents to provide a seamless shopping experience.
"""
from typing import Dict, Any, List
import os
from agents.research_agent import ResearchAgent
from agents.tasks import ResearchTasks
from dotenv import load_dotenv
from crewai import Crew, Task
from textwrap import dedent

load_dotenv()


class ShopperAgents:
    """Class to create and manage all ShopperAI agents"""

    def research_agent(self):
        """Create and return the research agent"""
        return ResearchAgent()


class ShopperAI:
    """Main ShopperAI class that orchestrates all agents"""

    def __init__(self, query: str, criteria: Dict[str, Any]):
        self.query = query
        self.criteria = criteria
        self.agents = ShopperAgents()
        self.tasks = ResearchTasks()

    def run(self):
        """Run the complete shopping flow"""
        # Initialize agents
        research_agent = self.agents.research_agent()

        # Create tasks
        search_task = Task(
            description=f"""Search for products matching: {self.query} with criteria: {self.criteria}
            Use the search_and_analyze method to find and analyze products.
            Return a list of products that match the criteria.""",
            agent=research_agent,
            expected_output="A list of products matching the search criteria"
        )

        analyze_task = Task(
            description=f"""Analyze the search results and find the best match based on criteria: {self.criteria}
            Use the analyze_products method to analyze the products and return recommendations.""",
            agent=research_agent,
            expected_output="A detailed analysis of the products with recommendations"
        )

        # Create and run the crew
        crew = Crew(
            agents=[research_agent],
            tasks=[search_task, analyze_task],
            verbose=True
        )

        result = crew.kickoff()
        return result


def main():
    """Example usage of ShopperAI"""
    print("## Welcome to ShopperAI")
    print("------------------------")

    query = input(dedent("""
    What would you like to search for?
    """))

    max_price = float(input(dedent("""
    What is your maximum budget?
    """)))

    min_rating = float(input(dedent("""
    What is your minimum required rating (0-5)?
    """)))

    criteria = {
        "max_price": max_price,
        "min_rating": min_rating
    }

    shopper = ShopperAI(query, criteria)
    result = shopper.run()

    print("\n\n##############################")
    print("## Here is your Shopping Results")
    print("##############################")
    print(result)


if __name__ == "__main__":
    main()
