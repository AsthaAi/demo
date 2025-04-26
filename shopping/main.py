"""
ShopperAI Main Orchestration
Coordinates all agents to provide a seamless shopping experience.
"""
from typing import Dict, Any, List
import os
from agents.research_agent import ResearchAgent
from agents.price_comparison_agent import PriceComparisonAgent
from agents.order_agent import OrderAgent
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

    def price_comparison_agent(self):
        """Create and return the price comparison agent"""
        return PriceComparisonAgent()

    def order_agent(self):
        """Create and return the order agent"""
        return OrderAgent()


class ShopperAI:
    """Main ShopperAI class that orchestrates all agents"""

    def __init__(self, query: str, criteria: Dict[str, Any]):
        self.query = query
        self.criteria = criteria
        self.agents = ShopperAgents()
        self.tasks = ResearchTasks()
        self.recommended_product = None

    def run(self):
        """Run the complete shopping flow"""
        # Initialize agents
        research_agent = self.agents.research_agent()
        price_agent = self.agents.price_comparison_agent()

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

        price_recommendation_task = Task(
            description=f"""Find the single cheapest product from the search results.
            Consider total cost including shipping and any available discounts.
            Return a clear recommendation for the best deal with price details.""",
            agent=price_agent,
            expected_output="A clear recommendation for the single best product based on price"
        )

        # Create and run the crew
        crew = Crew(
            agents=[research_agent, price_agent],
            tasks=[search_task, analyze_task, price_recommendation_task],
            verbose=True
        )

        result = crew.kickoff()

        # Extract the recommended product from the result
        if isinstance(result, dict):
            if "recommendation" in result:
                if isinstance(result["recommendation"], dict) and "product" in result["recommendation"]:
                    self.recommended_product = result["recommendation"]["product"]
                elif isinstance(result["recommendation"], str):
                    # If recommendation is a string, try to extract product from the result
                    if "product" in result:
                        self.recommended_product = result["product"]
            elif "product" in result:
                self.recommended_product = result["product"]

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

    # Ask if the user wants to buy the recommended product
    print("\n🛒 Purchase Option:")
    buy_choice = input(
        "Do you want to buy the recommended product? (Type 'yes' or 'y' to confirm): ").lower()

    if buy_choice == "yes" or buy_choice == "y":
        print("\n✅ Great choice! Processing your purchase...")

        # Initialize the order agent
        order_agent = shopper.agents.order_agent()

        # Process the purchase
        if shopper.recommended_product:
            confirmation = order_agent.process_purchase(
                shopper.recommended_product)

            # Display order confirmation
            print("\n\n##############################")
            print("## Order Confirmation")
            print("##############################")
            print(f"Transaction ID: {confirmation['transaction_id']}")
            print(f"Purchase Time: {confirmation['purchase_time']}")
            print(f"Status: {confirmation['status']}")
            print(
                f"Product: {confirmation['product']['name']} ({confirmation['product']['brand']})")
            print(f"Price: {confirmation['product']['price']}")
            print(f"Color: {confirmation['product']['color']}")
            print(f"Total Cost: {confirmation['product']['total_cost']}")
            print(f"\n{confirmation['message']}")
        else:
            print("Sorry, we couldn't process your purchase. No product was recommended.")
    else:
        print("\n❌ No problem! You can continue browsing or try a different search.")


if __name__ == "__main__":
    main()
