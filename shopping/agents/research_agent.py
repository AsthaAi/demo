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
        """Search for products and analyze them based on criteria"""
        print(f"\n=== ResearchAgent.search_and_analyze ===")
        print(f"Query: {query}")
        print(f"Criteria: {criteria}")

        # Check if we have cached results for this query
        cache_key = f"{query}_{str(criteria)}"
        if cache_key in self._search_memory:
            print(f"Found cached results for query: {query}")
            return self._search_memory[cache_key]

        print("No cached results found, performing new search")

        # Search for products
        print("Running product search...")
        search_results = self._search_tool.run(query)
        print(f"Search results type: {type(search_results)}")
        print(f"Search results: {search_results}")

        # If search results is a string, process it with GPT-3.5-turbo
        if isinstance(search_results, str):
            print("Search results is a string, processing with GPT-3.5-turbo")
            try:
                # Process the search results with GPT-3.5-turbo
                response = self._process_text_results_with_gpt(
                    search_results, query)
                print(f"GPT-3.5-turbo response type: {type(response)}")
                print(f"GPT-3.5-turbo response: {response}")

                # Try to parse the response as JSON
                try:
                    import json
                    parsed_response = json.loads(response)
                    print(
                        f"Successfully parsed response as JSON: {parsed_response}")
                    return parsed_response
                except json.JSONDecodeError as e:
                    print(f"Failed to parse response as JSON: {e}")
                    print("Creating sample data as fallback")
                    return self._create_sample_products(query)
            except Exception as e:
                print(f"Error processing search results: {e}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                print("Creating sample data as fallback")
                return self._create_sample_products(query)

        # If search results is a list, process it
        if isinstance(search_results, list):
            print(f"Search results is a list with {len(search_results)} items")

            # Extract structured product data
            products = []
            for item in search_results:
                print(f"Processing item: {item}")
                if isinstance(item, dict):
                    product = {
                        "name": item.get("title", ""),
                        "price": item.get("price", ""),
                        "rating": item.get("rating", ""),
                        "brand": item.get("brand", ""),
                        "description": item.get("description", ""),
                        "link": item.get("link", ""),
                        "image": item.get("thumbnail", "")
                    }
                    products.append(product)
                    print(f"Added product: {product}")

            print(f"Extracted {len(products)} products from search results")

            # Filter products based on criteria
            filtered_products = []
            for product in products:
                print(f"Checking product against criteria: {product}")
                if self._meets_criteria(product, criteria):
                    filtered_products.append(product)
                    print(f"Product meets criteria: {product}")
                else:
                    print(f"Product does not meet criteria: {product}")

            print(
                f"Filtered to {len(filtered_products)} products that meet criteria")

            # Sort products by rating
            filtered_products.sort(key=lambda x: float(
                x.get("rating", "0")), reverse=True)
            print(f"Sorted products by rating")

            # Get the best match
            best_match = filtered_products[0] if filtered_products else None
            print(f"Best match: {best_match}")

            # Create the results dictionary
            results = {
                "raw_products": products,
                "filtered_products": filtered_products,
                "top_products": filtered_products[:5],
                "best_match": best_match
            }

            # Store the results in memory
            self._search_memory[cache_key] = results
            print(f"Stored results in memory with key: {cache_key}")

            return results

        # If we get here, something went wrong
        print("Unexpected search results format, creating sample data")
        return self._create_sample_products(query)

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

    def _meets_criteria(self, product: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if a product meets the search criteria"""
        print(f"Checking if product meets criteria: {product}")
        print(f"Criteria: {criteria}")

        # Check price criteria
        if "max_price" in criteria:
            try:
                price_str = product.get("price", "0")
                # Remove currency symbols and convert to float
                price_str = ''.join(
                    c for c in price_str if c.isdigit() or c == '.')
                price = float(price_str) if price_str else 0

                if price > criteria["max_price"]:
                    print(
                        f"Product price {price} exceeds max_price {criteria['max_price']}")
                    return False
                print(
                    f"Product price {price} is within max_price {criteria['max_price']}")
            except (ValueError, TypeError) as e:
                print(f"Error parsing price: {e}")
                # If we can't parse the price, assume it doesn't meet criteria
                return False

        # Check rating criteria
        if "min_rating" in criteria:
            try:
                rating_str = product.get("rating", "0")
                # Extract numeric rating (e.g., "4.5/5" -> 4.5)
                rating_str = rating_str.split(
                    '/')[0] if '/' in rating_str else rating_str
                rating = float(rating_str) if rating_str else 0

                if rating < criteria["min_rating"]:
                    print(
                        f"Product rating {rating} below min_rating {criteria['min_rating']}")
                    return False
                print(
                    f"Product rating {rating} meets min_rating {criteria['min_rating']}")
            except (ValueError, TypeError) as e:
                print(f"Error parsing rating: {e}")
                # If we can't parse the rating, assume it doesn't meet criteria
                return False

        # Check brand criteria
        if "brand" in criteria and criteria["brand"]:
            product_brand = product.get("brand", "").lower()
            search_brand = criteria["brand"].lower()

            if search_brand not in product_brand:
                print(
                    f"Product brand '{product_brand}' doesn't match search brand '{search_brand}'")
                return False
            print(
                f"Product brand '{product_brand}' matches search brand '{search_brand}'")

        # All criteria passed
        print("Product meets all criteria")
        return True
