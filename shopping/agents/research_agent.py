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
import json
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError

load_dotenv()


class ResearchAgent(Agent):
    """Agent responsible for product research and analysis"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    researchAgent: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    # Add fields for tool AZTP IDs (without leading underscores)
    search_tool_aztp_id: str = Field(default="", exclude=True)
    analyzer_tool_aztp_id: str = Field(default="", exclude=True)

    # Add memory storage
    search_memory: Dict[str, Dict[str, Any]] = {}
    analysis_memory: Dict[str, Dict[str, Any]] = {}

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

        # Store tool AZTP IDs after initialization
        self.search_tool_aztp_id = self._search_tool.aztp_id
        self.analyzer_tool_aztp_id = self._analyzer_tool.aztp_id

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.iam_utils = IAMUtils()  # Initialize IAM utilities
        self.aztp_id = ""  # Initialize as empty string
        self.is_initialized = False

    async def initialize(self):
        """Initialize the agent and its tools"""
        if not self.is_initialized:
            # Initialize tools first
            await self._search_tool.initialize()
            await self._analyzer_tool.initialize()

            # Then initialize the agent's identity
            await self._initialize_identity()
            self.is_initialized = True
        return self

    def get_all_aztp_ids(self) -> Dict[str, str]:
        """Get all AZTP IDs associated with this agent and its tools"""
        return {
            "research_agent": self.aztp_id,
            "search_tool": self.search_tool_aztp_id,
            "analyzer_tool": self.analyzer_tool_aztp_id
        }

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        try:
            print(f"1. Issuing identity for agent: Research Agent")

            # Store tool IDs before creating research agent's identity
            self.search_tool_aztp_id = self._search_tool.aztp_id if hasattr(
                self._search_tool, 'aztp_id') else ""
            self.analyzer_tool_aztp_id = self._analyzer_tool.aztp_id if hasattr(
                self._analyzer_tool, 'aztp_id') else ""

            # Create array of tool IDs to link
            tool_ids = []
            if self.search_tool_aztp_id:
                tool_ids.append(self.search_tool_aztp_id)
            if self.analyzer_tool_aztp_id:
                tool_ids.append(self.analyzer_tool_aztp_id)

            # Create research agent identity without linkTo
            self.researchAgent = await self.aztpClient.secure_connect(
                self,
                "research-agent",
                {
                    "isGlobalIdentity": False
                }
            )

            # Link research agent with each tool identity
            print("\nLinking research agent with tool identities...")
            for tool_id in tool_ids:
                try:
                    link_result = await self.aztpClient.link_identities(
                        self.researchAgent.identity.aztp_id,
                        tool_id,
                        "linked"
                    )
                    print(
                        f"Successfully linked research agent with tool ID: {tool_id}")
                    print(f"Link result: {link_result}")
                except Exception as e:
                    print(
                        f"Error linking research agent with tool ID {tool_id}: {str(e)}")

            print("AZTP ID:", self.researchAgent.identity.aztp_id)

            print(f"\n2. Verifying identity for agent: Research Agent")
            self.is_valid = await self.aztpClient.verify_identity(
                self.researchAgent
            )
            print("Verified Agent:", self.is_valid)

            if self.is_valid:
                if self.researchAgent and hasattr(self.researchAgent, 'identity'):
                    self.aztp_id = self.researchAgent.identity.aztp_id
                    print(f"✅ Extracted AZTP ID: {self.aztp_id}")
            else:
                raise ValueError(
                    "Failed to verify identity for agent: Research Agent")

            # Verify research access before proceeding
            print(
                f"\n3. Verifying access permissions for Research Agent {self.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="research_products",
                policy_code="policy:c4e88b812bc0",
                operation_name="Product Research"
            )

            print("\n✅ Research agent initialized successfully")

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to initialize research agent: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution

    def _get_memory_key(self, query: str, criteria: Dict[str, Any]) -> str:
        """Generate a unique key for memory storage"""
        criteria_str = f"{criteria.get('max_price', '')}_{criteria.get('min_rating', '')}"
        return f"{query}_{criteria_str}"

    def search_and_analyze(self, query: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search for products and analyze them based on criteria"""
        print(f"\n=== ResearchAgent.search_and_analyze ===")
        print(f"Query: {query}")
        print(f"Criteria: {criteria}")

        # Get the absolute path to the shopping directory
        shopping_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        product_json_path = os.path.join(shopping_dir, 'product.json')
        print(f"Will save results to: {product_json_path}")

        # Initialize default result structure
        empty_result = {
            "raw_products": [],
            "filtered_products": [],
            "top_products": [],
            "best_match": None
        }

        # Check if we have cached results for this query
        cache_key = f"{query}_{str(criteria)}"
        if cache_key in self.search_memory:
            print(f"Found cached results for query: {query}")
            result = self.search_memory[cache_key]
            # Save cached results to product.json
            try:
                # Ensure the file exists and is writable
                with open(product_json_path, 'w+') as f:
                    json.dump(result, f, indent=2)
                    f.flush()  # Force write to disk
                    os.fsync(f.fileno())  # Ensure it's written to disk
                print("Cached results saved to product.json")
                return result
            except Exception as e:
                print(f"Error saving cached results: {str(e)}")
                return result  # Still return the results even if saving fails

        print("No cached results found, performing new search")

        # Search for products
        print("Running product search...")
        try:
            search_results = self._search_tool.run(query)
            print(
                f"[DEBUG] Raw data received from search tool: {search_results}")
        except Exception as e:
            print(f"Error during product search: {e}")
            print("Using sample products as fallback")
            search_results = self._create_sample_products(query)

        # Process search results and get structured data
        result = empty_result

        if isinstance(search_results, str):
            # Process string results with GPT
            processed_results = self._process_text_results_with_gpt(
                search_results, query)
            if processed_results:
                result = {
                    "raw_products": processed_results,
                    "filtered_products": processed_results,
                    "top_products": processed_results[:5],
                    "best_match": processed_results[0] if processed_results else None
                }
        elif isinstance(search_results, list):
            # Process list results directly
            products = []
            for item in search_results:
                if isinstance(item, dict):
                    product = {
                        "name": item.get("title", item.get("name", "")),
                        "price": item.get("price", ""),
                        "rating": item.get("rating", ""),
                        "brand": item.get("brand", ""),
                        "description": item.get("description", ""),
                        "link": item.get("link", ""),
                        "image": item.get("thumbnail", "")
                    }
                    products.append(product)

            # If no products found, use sample data
            if not products:
                print("No products found from search, using sample data")
                products = self._create_sample_products(query)

            # Filter products based on criteria
            filtered_products = [
                p for p in products if self._meets_criteria(p, criteria)]

            # If no products meet criteria, use all products
            if not filtered_products:
                print("No products meet criteria, using all products")
                filtered_products = products

            # Sort products by rating and price
            filtered_products.sort(key=lambda x: (
                float(str(x.get("rating", "0")).split("/")[0]),
                -float(str(x.get("price", "0")).replace("$", "").replace(",", ""))
            ), reverse=True)

            result = {
                "raw_products": products,
                "filtered_products": filtered_products,
                "top_products": filtered_products[:5],
                "best_match": filtered_products[0] if filtered_products else None
            }

        # If still no results, use sample data
        if not result["raw_products"]:
            print("No results found, using sample data")
            sample_products = self._create_sample_products(query)
            result = {
                "raw_products": sample_products,
                "filtered_products": sample_products,
                "top_products": sample_products[:5],
                "best_match": sample_products[0] if sample_products else None
            }

        # Save results to product.json with proper error handling
        try:
            # Ensure the file exists and is writable
            with open(product_json_path, 'w+') as f:
                json.dump(result, f, indent=2)
                f.flush()  # Force write to disk
                os.fsync(f.fileno())  # Ensure it's written to disk
            print("Results saved to product.json")
        except Exception as e:
            print(f"Error saving results to file: {str(e)}")
            print("Continuing with in-memory results")

        # Store in memory
        self.search_memory[cache_key] = result
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
        Perform detailed analysis of products and assign 'best', 'mid-range', and 'premium' flags based on real data.

        Args:
            products: List of product dictionaries
            criteria: Dictionary of criteria to filter by

        Returns:
            Analysis results with recommendations and flags
        """
        memory_key = self._get_memory_key(str(products), criteria)

        # Check if we have cached analysis
        if memory_key in self.analysis_memory:
            print("Using cached analysis results...")
            return self.analysis_memory[memory_key]

        # If products is empty, create sample data (only fallback)
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

        # Remove any products with missing price or rating
        filtered_products = [p for p in analyzed_products if p.get(
            'price') and p.get('rating')]
        if not filtered_products:
            filtered_products = analyzed_products

        # Convert price and rating to float for sorting
        def parse_price(p):
            price_str = str(p.get('price', '0')).replace(
                '$', '').replace(',', '')
            try:
                return float(price_str)
            except Exception:
                return 0.0

        def parse_rating(p):
            rating_str = str(p.get('rating', '0'))
            if '/' in rating_str:
                rating_str = rating_str.split('/')[0]
            try:
                return float(rating_str)
            except Exception:
                return 0.0

        # Sort by rating (desc), then price (asc)
        sorted_by_rating = sorted(filtered_products, key=lambda x: (
            parse_rating(x), -parse_price(x)), reverse=True)
        # Sort by price (asc)
        sorted_by_price = sorted(filtered_products, key=parse_price)
        # Sort by price (desc) for premium
        sorted_by_price_desc = sorted(
            filtered_products, key=parse_price, reverse=True)

        # Assign flags
        top_products = []
        used_indices = set()
        # Best: highest rating
        if sorted_by_rating:
            best = sorted_by_rating[0]
            best_flagged = best.copy()
            best_flagged['flag'] = 'best'
            top_products.append(best_flagged)
            used_indices.add(filtered_products.index(best))
        # Mid-range: median price
        if sorted_by_price:
            mid_idx = len(sorted_by_price) // 2
            mid = sorted_by_price[mid_idx]
            if filtered_products.index(mid) not in used_indices:
                mid_flagged = mid.copy()
                mid_flagged['flag'] = 'mid-range'
                top_products.append(mid_flagged)
                used_indices.add(filtered_products.index(mid))
        # Premium: highest price
        if sorted_by_price_desc:
            premium = sorted_by_price_desc[0]
            if filtered_products.index(premium) not in used_indices:
                premium_flagged = premium.copy()
                premium_flagged['flag'] = 'premium'
                top_products.append(premium_flagged)
                used_indices.add(filtered_products.index(premium))

        # If less than 3, fill with next best by rating
        i = 1
        while len(top_products) < 3 and i < len(sorted_by_rating):
            candidate = sorted_by_rating[i]
            if filtered_products.index(candidate) not in used_indices:
                candidate_flagged = candidate.copy()
                candidate_flagged['flag'] = 'other'
                top_products.append(candidate_flagged)
                used_indices.add(filtered_products.index(candidate))
            i += 1

        # Format output
        result = {
            "top_products": [
                {
                    "name": p.get('title', p.get('name', '')),
                    "brand": p.get('brand', ''),
                    "price": p.get('price', ''),
                    "rating": p.get('rating', ''),
                    "link": p.get('link', ''),
                    "flag": p.get('flag', '')
                }
                for p in top_products
            ],
            "best_match": {
                "name": top_products[0].get('title', top_products[0].get('name', '')) if top_products else '',
                "brand": top_products[0].get('brand', '') if top_products else '',
                "price": top_products[0].get('price', '') if top_products else '',
                "rating": top_products[0].get('rating', '') if top_products else '',
                "link": top_products[0].get('link', '') if top_products else '',
                "flag": top_products[0].get('flag', '') if top_products else ''
            }
        }

        # Store in memory
        self.analysis_memory[memory_key] = result

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
        # Create sample data based on common product queries
        if "iphone" in query.lower():
            return [
                {
                    "name": "iPhone SE (2020)",
                    "price": "399.99",
                    "rating": "4.5",
                    "description": "A powerful 4.7-inch iPhone with A13 Bionic chip",
                    "link": "https://example.com/iphone-se",
                    "brand": "Apple",
                    "color": "Black"
                },
                {
                    "name": "iPhone 11 (Refurbished)",
                    "price": "479.99",
                    "rating": "4.3",
                    "description": "6.1-inch Liquid Retina display, dual cameras",
                    "link": "https://example.com/iphone-11",
                    "brand": "Apple",
                    "color": "White"
                },
                {
                    "name": "iPhone XR (Refurbished)",
                    "price": "399.99",
                    "rating": "4.2",
                    "description": "6.1-inch Liquid Retina display, great battery life",
                    "link": "https://example.com/iphone-xr",
                    "brand": "Apple",
                    "color": "Blue"
                }
            ]
        elif "laptop" in query.lower():
            return [
                {
                    "name": "Dell XPS 13",
                    "price": "999.99",
                    "rating": "4.7",
                    "description": "13-inch ultrabook with InfinityEdge display",
                    "link": "https://example.com/dell-xps-13",
                    "brand": "Dell",
                    "color": "Silver"
                },
                {
                    "name": "MacBook Air M1",
                    "price": "899.99",
                    "rating": "4.8",
                    "description": "13-inch laptop with Apple M1 chip",
                    "link": "https://example.com/macbook-air",
                    "brand": "Apple",
                    "color": "Space Gray"
                },
                {
                    "name": "Lenovo ThinkPad X1",
                    "price": "1199.99",
                    "rating": "4.6",
                    "description": "14-inch business laptop with great keyboard",
                    "link": "https://example.com/thinkpad-x1",
                    "brand": "Lenovo",
                    "color": "Black"
                }
            ]
        else:
            # Generic sample products
            return [
                {
                    "name": f"{query} - Premium Model",
                    "price": "499.99",
                    "rating": "4.8",
                    "description": f"High-end {query} with premium features",
                    "link": "https://example.com/premium",
                    "brand": "PremiumBrand",
                    "color": "Black"
                },
                {
                    "name": f"{query} - Mid Range",
                    "price": "299.99",
                    "rating": "4.5",
                    "description": f"Great value {query} for most users",
                    "link": "https://example.com/midrange",
                    "brand": "ValueBrand",
                    "color": "Silver"
                },
                {
                    "name": f"{query} - Budget Option",
                    "price": "199.99",
                    "rating": "4.2",
                    "description": f"Affordable {query} with good features",
                    "link": "https://example.com/budget",
                    "brand": "BasicBrand",
                    "color": "White"
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
