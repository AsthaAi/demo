"""
Tasks for ShopperAI agents
"""
from crewai import Task
from typing import Dict, Any


class ResearchTasks:
    """Class to create research-related tasks"""

    def search_task(self, agent, query: str, criteria: Dict[str, Any]):
        """Create search task"""
        return Task(
            description=f"""Search for products matching: {query} with criteria: {criteria}
            Use the ProductSearch tool to find products and then analyze them with the ProductAnalyzer tool.
            Return a list of products that match the criteria.""",
            agent=agent,
            expected_output="A list of products matching the search criteria"
        )

    def analyze_task(self, agent, criteria: Dict[str, Any]):
        """Create analyze task"""
        return Task(
            description=f"""Analyze the search results and filter based on criteria: {criteria}
            Use the ProductAnalyzer tool to analyze the products and return the best matches.""",
            agent=agent,
            expected_output="A detailed analysis of the products with recommendations"
        )

    def checkout_task(self, agent):
        """Create checkout task"""
        return Task(
            description="""Process the checkout with the selected product.
            Review the product details and prepare for checkout.""",
            agent=agent,
            expected_output="Checkout details and confirmation"
        )
