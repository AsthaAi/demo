"""
Research Agent for ShopperAI
Handles product search and analysis tasks.
"""
from typing import Dict, Any, List, Optional
from tools.search_tools import ProductSearchTool, ProductAnalyzerTool
from crewai import Agent
from aztp_client import Aztp, whiteListTrustDomains
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
import os
from pydantic import Field, ConfigDict
import asyncio

load_dotenv()


class ResearchAgent(Agent):
    """Agent responsible for product research and analysis"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    secured_connection: SecureConnection = Field(default=None, exclude=True)
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)

    def __init__(self):
        """Initialize the research agent with necessary tools"""
        super().__init__(
            role='Research Agent',
            goal='Find and analyze products based on user criteria',
            backstory="""You are an expert product researcher with years of experience in 
            finding the best products that match user requirements. You have a keen eye for 
            detail and always ensure products meet the specified criteria.""",
            verbose=True
        )
        # Initialize tools after super().__init__
        self._search_tool = ProductSearchTool()
        self._analyzer_tool = ProductAnalyzerTool()

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp_id = ""  # Initialize as empty string

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        print(f"1. Issuing identity for agent: Research Agent")
        self.secured_connection = await self.aztpClient.secure_connect(
            self,
            "research-agent",
            {
                "isGlobalIdentity": False
            }
        )
        print("AZTP ID:", self.secured_connection.identity.aztp_id)

        print(f"\n2. Verifying identity for agent: Research Agent")
        self.is_valid = await self.aztpClient.verify_identity(
            self.secured_connection
        )
        print("Verified Agent:", self.is_valid)

        if self.is_valid:
            # self.identity = await self.aztpClient.get_identity(self.secured_connection)
            # print(f"Research Agent Identity verified: {self.identity}")
            # Get the AZTP ID from the secured connection
            if self.secured_connection and hasattr(self.secured_connection, 'identity'):
                self.aztp_id = self.secured_connection.identity.aztp_id
                print(f"✅ Extracted AZTP ID: {self.aztp_id}")
        else:
            raise ValueError(
                "Failed to verify identity for agent: Research Agent")

        print(
            f"\n3. Getting policy information for agent: Research Agent {self.aztp_id}")
        if self.secured_connection and hasattr(self.secured_connection, 'identity'):
            try:
                self.identity_access_policy = await self.aztpClient.get_policy(
                    self.secured_connection.identity.aztp_id
                )
                print("Identity Access Policy:", self.identity_access_policy)

                # Display policy information
                print("\nPolicy Information:")
                if isinstance(self.identity_access_policy, dict):
                    # Handle dictionary response
                    for policy in self.identity_access_policy.get('data', []):
                        print("\nPolicy Statement:",
                              policy.get('policyStatement'))
                        statement = policy.get('policyStatement', {}).get(
                            'Statement', [{}])[0]
                        if statement.get('Effect') == "Allow":
                            print("Statement Effect:", statement.get('Effect'))
                            print("Statement Actions:",
                                  statement.get('Action'))
                            if 'Condition' in statement:
                                print("Statement Conditions:",
                                      statement.get('Condition'))
                            print("Identity:", policy.get('identity'))
                else:
                    # Handle string response
                    print(self.identity_access_policy)
            except Exception as e:
                print(f"Error getting policy: {str(e)}")
        else:
            print(
                f"Warning: No valid AZTP ID available for policy retrieval. AZTP ID: {self.aztp_id}")

    def search_and_analyze(self, query: str, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for products and analyze them based on criteria

        Args:
            query: Search query string
            criteria: Dictionary of criteria to filter by

        Returns:
            List of filtered and analyzed products
        """
        # Search for products
        products = self._search_tool.run(query)

        # Analyze the products
        analyzed_products = self._analyzer_tool.run(products, criteria)
        return analyzed_products

    def get_best_match(self, query: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the best matching product based on criteria

        Args:
            query: Search query string
            criteria: Dictionary of criteria to filter by

        Returns:
            Best matching product or empty dict if none found
        """
        analyzed_products = self.search_and_analyze(query, criteria)

        if not analyzed_products:
            return {}

        # Return the first (best) product
        return analyzed_products[0]

    def analyze_products(self, products: List[Dict[str, Any]], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform detailed analysis of products

        Args:
            products: List of product dictionaries
            criteria: Dictionary of criteria to filter by

        Returns:
            Analysis results with recommendations
        """
        # Analyze the products
        analyzed_products = self._analyzer_tool.run(products, criteria)

        # Return the analysis result
        return {
            "analysis": "Analysis complete",
            "recommended_product": analyzed_products[0] if analyzed_products else {}
        }

    def get_product_details(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and format important product details

        Args:
            product: Product dictionary

        Returns:
            Formatted product details
        """
        return {
            "title": product.get("title", ""),
            "price": product.get("price", ""),
            "source": product.get("source", ""),
            "rating": product.get("rating", 0),
            "rating_count": product.get("ratingCount", 0),
            "link": product.get("link", ""),
            "delivery": product.get("delivery", ""),
            "image_url": product.get("imageUrl", ""),
            "offers": product.get("offers", "")
        }
