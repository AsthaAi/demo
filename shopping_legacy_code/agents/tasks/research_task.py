"""
Research Task for ShopperAI
Defines the task for the research agent to find and analyze products.
"""
from typing import Dict, Any, List
from crewai import Task


class ResearchTask:
    """Task for researching products based on user criteria"""

    @staticmethod
    def create_search_task(query: str, criteria: Dict[str, Any]) -> Task:
        """
        Create a task for searching and analyzing products

        Args:
            query: Search query string
            criteria: Dictionary of criteria to filter by

        Returns:
            Task object for the research agent
        """
        return Task(
            description=f"""
            Search for products matching the query: "{query}"
            
            Filter products based on the following criteria:
            - Maximum price: ${criteria.get('max_price', 'any')}
            - Minimum rating: {criteria.get('min_rating', 'any')}
            
            Analyze the results and return the best matches.
            Consider factors like price, rating, and availability.
            
            Return a list of products that best match the criteria.
            """,
            agent_role="Product Research Specialist",
            expected_output="""
            A list of products that match the search criteria, sorted by relevance.
            Each product should include:
            - Title
            - Price
            - Source
            - Rating
            - Link
            - Delivery information
            """
        )

    @staticmethod
    def create_analysis_task(products: List[Dict[str, Any]], criteria: Dict[str, Any]) -> Task:
        """
        Create a task for analyzing product results

        Args:
            products: List of product dictionaries
            criteria: Dictionary of criteria to filter by

        Returns:
            Task object for the research agent
        """
        return Task(
            description=f"""
            Analyze the following products based on these criteria:
            - Maximum price: ${criteria.get('max_price', 'any')}
            - Minimum rating: {criteria.get('min_rating', 'any')}
            
            Products to analyze:
            {products}
            
            Provide a detailed analysis of each product, highlighting:
            1. Value for money
            2. Quality based on ratings
            3. Reliability of the seller
            4. Shipping options and costs
            
            Recommend the best product based on the analysis.
            """,
            agent_role="Product Research Specialist",
            expected_output="""
            A detailed analysis of each product and a recommendation for the best option.
            Include a summary of why the recommended product is the best choice.
            """
        )
