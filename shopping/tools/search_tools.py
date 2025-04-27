"""
Search Tools for ShopperAI
"""
import os
from typing import Dict, List, Any, Optional
from serpapi import GoogleSearch
from dotenv import load_dotenv
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from pydantic import Field, ConfigDict
import asyncio

load_dotenv()


class ProductSearchTool:
    """Tool for searching products using Google Serper API"""

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
        """Initialize the search tool"""
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable is not set")

        # Initialize AZTP client
        aztp_api_key = os.getenv("AZTP_API_KEY")
        if not aztp_api_key:
            raise ValueError("AZTP_API_KEY environment variable is not set")

        self.aztpClient = Aztp(api_key=aztp_api_key)
        self.aztp_id = ""  # Initialize as empty string

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the tool's identity asynchronously"""
        print(f"1. Issuing identity for tool: Product Search Tool")
        self.secured_connection = await self.aztpClient.secure_connect(
            self,
            "product-search-tool",
            {
                "isGlobalIdentity": False
            }
        )
        print("AZTP ID:", self.secured_connection.identity.aztp_id)

        print(f"\n2. Verifying identity for tool: Product Search Tool")
        self.is_valid = await self.aztpClient.verify_identity(
            self.secured_connection
        )
        print("Verified Tool:", self.is_valid)

        if self.is_valid:
            # self.identity = await self.aztpClient.get_identity(self.secured_connection)
            # print(f"Product Search Tool Identity verified: {self.identity}")
            # Get the AZTP ID from the secured connection
            if self.secured_connection and hasattr(self.secured_connection, 'identity'):
                self.aztp_id = self.secured_connection.identity.aztp_id
                print(f"✅ Extracted AZTP ID: {self.aztp_id}")
        else:
            raise ValueError(
                "Failed to verify identity for tool: Product Search Tool")

        print(
            f"\n3. Getting policy information for tool: Product Search Tool {self.aztp_id}")
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

    def run(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for products using Google Serper API

        Args:
            query: Search query string

        Returns:
            List of product dictionaries
        """
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": self.api_key,
            "location": "United States",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en"
        }

        try:
            print(f"Searching for products with query: '{query}'")
            search = GoogleSearch(params)
            results = search.get_dict()

            # Log the structure of the results for debugging
            print(
                f"Search results keys: {list(results.keys()) if isinstance(results, dict) else 'Not a dictionary'}")

            if "shopping_results" in results:
                products = results["shopping_results"]
                print(f"Found {len(products)} products")
                return products
            else:
                print("No 'shopping_results' found in the API response")
                # Check if there's an error message in the response
                if "error" in results:
                    print(f"API Error: {results['error']}")
                return []
        except Exception as e:
            print(f"Error searching for products: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []


class ProductAnalyzerTool:
    """Tool for analyzing product search results"""

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
        """Initialize the analyzer tool"""
        # Initialize AZTP client
        aztp_api_key = os.getenv("AZTP_API_KEY")
        if not aztp_api_key:
            raise ValueError("AZTP_API_KEY environment variable is not set")

        self.aztpClient = Aztp(api_key=aztp_api_key)
        self.aztp_id = ""  # Initialize as empty string

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the tool's identity asynchronously"""
        print(f"1. Issuing identity for tool: Product Analyzer Tool")
        self.secured_connection = await self.aztpClient.secure_connect(
            self,
            "product-analyzer-tool",
            {
                "isGlobalIdentity": False
            }
        )
        print("AZTP ID:", self.secured_connection.identity.aztp_id)

        print(f"\n2. Verifying identity for tool: Product Analyzer Tool")
        self.is_valid = await self.aztpClient.verify_identity(
            self.secured_connection
        )
        print("Verified Tool:", self.is_valid)

        if self.is_valid:
            # self.identity = await self.aztpClient.get_identity(self.secured_connection)
            # print(f"Product Analyzer Tool Identity verified: {self.identity}")
            # Get the AZTP ID from the secured connection
            if self.secured_connection and hasattr(self.secured_connection, 'identity'):
                self.aztp_id = self.secured_connection.identity.aztp_id
                print(f"✅ Extracted AZTP ID: {self.aztp_id}")
        else:
            raise ValueError(
                "Failed to verify identity for tool: Product Analyzer Tool")

        print(
            f"\n3. Getting policy information for tool: Product Analyzer Tool {self.aztp_id}")
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

    def run(self, products: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze products based on given criteria

        Args:
            products: List of product dictionaries
            criteria: Dictionary of criteria to filter by

        Returns:
            List of filtered and analyzed products
        """
        if not products:
            return []

        analyzed_products = []
        max_price = criteria.get("max_price", float("inf"))
        min_rating = criteria.get("min_rating", 0)

        for product in products:
            # Extract price
            try:
                price = float(product.get("price", "0").replace(
                    "$", "").replace(",", ""))
            except (ValueError, AttributeError):
                price = 0

            # Extract rating
            try:
                rating = float(product.get("rating", 0))
            except (ValueError, TypeError):
                rating = 0

            # Check if product meets criteria
            if price <= max_price and rating >= min_rating:
                analyzed_products.append({
                    "title": product.get("title", ""),
                    "price": product.get("price", ""),
                    "rating": rating,
                    "rating_count": product.get("reviews", 0),
                    "source": product.get("source", ""),
                    "link": product.get("link", ""),
                    "image": product.get("thumbnail", ""),
                    "description": product.get("description", "")
                })

        # Sort by rating and price
        analyzed_products.sort(
            key=lambda x: (-x["rating"], float(x["price"].replace("$", "").replace(",", ""))))
        return analyzed_products
