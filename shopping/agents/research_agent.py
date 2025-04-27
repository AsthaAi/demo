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
import re

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

    # Add memory storage
    _search_memory: Dict[str, Dict[str, Any]] = {}
    _analysis_memory: Dict[str, Dict[str, Any]] = {}

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
                # print("Identity Access Policy:", self.identity_access_policy)

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

    def _get_memory_key(self, query: str, criteria: Dict[str, Any]) -> str:
        """Generate a unique key for memory storage"""
        criteria_str = f"{criteria.get('max_price', '')}_{criteria.get('min_rating', '')}"
        return f"{query}_{criteria_str}"

    def search_and_analyze(self, query: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for products and analyze them based on criteria

        Args:
            query: Search query
            criteria: Search criteria (max_price, min_rating)

        Returns:
            Dictionary with search results and analysis
        """
        # Check memory first
        memory_key = self._get_memory_key(query, criteria)
        if memory_key in self._search_memory:
            print("Using cached search results...")
            return self._search_memory[memory_key]

        # Search for products
        search_results = self._search_tool.run(query)

        # If search_results is a string, use GPT-3.5-turbo to process it
        if isinstance(search_results, str):
            print("Processing text-based search results with GPT-3.5-turbo...")
            search_results = self._process_text_results_with_gpt(
                search_results, query)

        # If search_results is empty or not a list, create sample data
        if not search_results or not isinstance(search_results, list):
            print("No search results found, creating sample data...")
            search_results = self._create_sample_products(query)

        # Extract structured product data
        products = []
        for result in search_results:
            # Extract price and convert to float
            price_str = result.get("price", "0")
            price = self._extract_price(price_str)

            # Extract rating and convert to float
            rating_str = result.get("rating", "0")
            rating = self._extract_rating(rating_str)

            # Create structured product object
            product = {
                "name": result.get("title", "Unknown Product"),
                "brand": self._extract_brand(result.get("title", "")),
                "price": price_str,
                "price_value": price,
                "rating": rating,
                "rating_value": float(rating),
                "description": result.get("description", ""),
                "link": result.get("link", ""),
                "color": self._extract_color(result)
            }
            products.append(product)

        # Filter products based on criteria
        filtered_products = [
            p for p in products
            if p["price_value"] <= criteria.get("max_price", float("inf"))
            and p["rating_value"] >= criteria.get("min_rating", 0)
        ]

        # Sort by rating (highest first)
        filtered_products.sort(key=lambda x: x["rating_value"], reverse=True)

        # Get top products (limit to 5)
        top_products = filtered_products[:5]

        # Find best match (highest rating within budget)
        best_match = None
        if top_products:
            best_match = top_products[0]

        # Create structured response
        result = {
            "query": query,
            "criteria": criteria,
            "raw_products": products,
            "filtered_products": filtered_products,
            "top_products": top_products,
            "best_match": best_match,
            "total_found": len(products),
            "total_matching_criteria": len(filtered_products)
        }

        # Store in memory
        self._search_memory[memory_key] = result

        return result

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
        return analyzed_products["best_match"]

    def analyze_products(self, products: List[Dict[str, Any]], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform detailed analysis of products

        Args:
            products: List of product dictionaries
            criteria: Dictionary of criteria to filter by

        Returns:
            Analysis results with recommendations
        """
        memory_key = self._get_memory_key(str(products), criteria)

        # Check if we have cached analysis
        if memory_key in self._analysis_memory:
            print("Using cached analysis results...")
            return self._analysis_memory[memory_key]

        # If products is empty, create sample data
        if not products:
            print("No products provided for analysis, creating sample data...")
            products = self._create_sample_products("sample")

        # First return all raw products
        raw_products = [self.get_product_details(
            product) for product in products]

        # Then analyze the products
        analyzed_products = self._analyzer_tool.run(products, criteria)

        # If analyzed_products is a string, use GPT-3.5-turbo to process it
        if isinstance(analyzed_products, str):
            print("Processing text-based analysis results with GPT-3.5-turbo...")
            analyzed_products = self._process_text_results_with_gpt(
                analyzed_products, "analysis")

        # If analyzed_products is empty or not a list, use the raw products
        if not analyzed_products or not isinstance(analyzed_products, list):
            print("No analysis results, using raw products...")
            analyzed_products = raw_products

        # Sort products by rating and price
        sorted_products = sorted(
            analyzed_products,
            key=lambda x: (
                float(x.get('rating', 0)),
                -float(x.get('price', '0').replace('$', '').replace(',', ''))
            ),
            reverse=True
        )

        # Get top 3 products
        top_products = sorted_products[:3]

        # Create result structure
        result = {
            "top_products": [
                {
                    "name": product.get('title', ''),
                    "brand": product.get('title', '').split()[0],
                    "price": product.get('price', ''),
                    "rating": product.get('rating', ''),
                    "link": product.get('link', '')
                }
                for product in top_products
            ],
            "best_match": {
                "name": top_products[0].get('title', '') if top_products else '',
                "brand": top_products[0].get('title', '').split()[0] if top_products else '',
                "price": top_products[0].get('price', '') if top_products else '',
                "rating": top_products[0].get('rating', '') if top_products else '',
                "link": top_products[0].get('link', '') if top_products else ''
            }
        }

        # Store in memory
        self._analysis_memory[memory_key] = result

        return result

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

    def _process_text_results_with_gpt(self, text_results: str, query: str) -> List[Dict[str, Any]]:
        """
        Process text-based search results using GPT-3.5-turbo to extract structured product data

        Args:
            text_results: Text-based search results
            query: Original search query

        Returns:
            List of structured product dictionaries
        """
        try:
            import openai

            # Set up OpenAI API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                print("OPENAI_API_KEY not found, using sample data")
                return self._create_sample_products(query)

            openai.api_key = openai_api_key

            # Create a prompt for GPT-3.5-turbo
            prompt = f"""
            I have search results for the query "{query}". Please extract product information from the following text and format it as a JSON array of product objects.
            Each product should have the following fields: title, price, rating, description, link, brand, color.
            
            Search results:
            {text_results}
            
            Format the response as a valid JSON array. Example format:
            [
                {{
                    "title": "Product Name",
                    "price": "$99.99",
                    "rating": "4.5",
                    "description": "Product description",
                    "link": "https://example.com/product",
                    "brand": "Brand Name",
                    "color": "Color"
                }},
                ...
            ]
            
            Only include the JSON array in your response, nothing else.
            """

            # Call GPT-3.5-turbo
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured product data from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )

            # Extract the JSON from the response
            json_text = response.choices[0].message.content.strip()

            # Parse the JSON
            import json
            try:
                products = json.loads(json_text)
                if isinstance(products, list) and products:
                    print(
                        f"Successfully extracted {len(products)} products using GPT-3.5-turbo")
                    return products
                else:
                    print("GPT-3.5-turbo returned empty or invalid product list")
                    return self._create_sample_products(query)
            except json.JSONDecodeError:
                print("Failed to parse JSON from GPT-3.5-turbo response")
                return self._create_sample_products(query)

        except Exception as e:
            print(f"Error processing text results with GPT-3.5-turbo: {e}")
            return self._create_sample_products(query)

    def _create_sample_products(self, query: str) -> List[Dict[str, Any]]:
        """
        Create sample product data for testing or fallback

        Args:
            query: Search query

        Returns:
            List of sample product dictionaries
        """
        return [
            {
                "title": f"{query} - Sample Product 1",
                "price": "$99.99",
                "rating": "4.5",
                "description": f"A sample {query} product with good ratings",
                "link": "https://example.com/product1",
                "brand": "SampleBrand",
                "color": "Black"
            },
            {
                "title": f"{query} - Sample Product 2",
                "price": "$149.99",
                "rating": "4.2",
                "description": f"Another sample {query} product",
                "link": "https://example.com/product2",
                "brand": "AnotherBrand",
                "color": "White"
            },
            {
                "title": f"{query} - Sample Product 3",
                "price": "$199.99",
                "rating": "4.8",
                "description": f"Premium sample {query} product",
                "link": "https://example.com/product3",
                "brand": "PremiumBrand",
                "color": "Silver"
            }
        ]
