"""
Price Comparison Agent for ShopperAI
Handles price analysis and comparison tasks.
"""
from typing import Dict, Any, List, Optional
from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
import os
from pydantic import Field, ConfigDict
import asyncio
import re

load_dotenv()


class PriceComparisonAgent(Agent):
    """Agent responsible for price comparison and analysis"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    priceAgent: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    # Add memory storage
    _comparison_memory: Dict[str, Dict[str, Any]] = {}
    _best_deal_memory: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        """Initialize the price comparison agent with necessary tools"""
        super().__init__(
            role='Price Comparison Agent',
            goal='Find the cheapest product and provide a clear price recommendation',
            backstory="""You are an expert price analyst focused on finding the absolute best deal. 
            You analyze prices carefully, considering all costs, and recommend only the single best 
            product based on price. Your recommendations are clear, concise, and focused on helping 
            users save money.""",
            verbose=True
        )

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.iam_utils = IAMUtils()  # Initialize IAM utilities
        self.aztp_id = ""  # Initialize as empty string

    async def initialize(self):
        """Initialize the agent's identity asynchronously"""
        if self.is_initialized:
            return

        await self._initialize_identity()
        self.is_initialized = True

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        try:
            print(f"1. Issuing identity for agent: Price Comparison Agent")
            self.priceAgent = await self.aztpClient.secure_connect(
                self,
                "price-comparison-agent",
                {
                    "isGlobalIdentity": False
                }
            )
            print("AZTP ID:", self.priceAgent.identity.aztp_id)

            print(f"\n2. Verifying identity for agent: Price Comparison Agent")
            self.is_valid = await self.aztpClient.verify_identity(
                self.priceAgent
            )
            print("Verified Agent:", self.is_valid)

            if self.is_valid:
                if self.priceAgent and hasattr(self.priceAgent, 'identity'):
                    self.aztp_id = self.priceAgent.identity.aztp_id
                    print(f"✅ Extracted AZTP ID: {self.aztp_id}")
            else:
                raise ValueError(
                    "Failed to verify identity for agent: Price Comparison Agent")

            # Verify price comparison access before proceeding
            print(
                f"\n3. Verifying access permissions for Price Comparison Agent {self.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="compare_prices",
                policy_code="policy:c047c5e5ec66",
                operation_name="Price Comparison"
            )

            print("\n✅ Price comparison agent initialized successfully")

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to initialize price comparison agent: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution

    def _extract_price(self, price_str: str) -> float:
        """
        Extract numerical price value from price string

        Args:
            price_str: Price string (e.g., "$123.45" or "123.45")

        Returns:
            Float value of the price
        """
        if not price_str:
            return 0.0

        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _calculate_total_cost(self, product: Dict[str, Any]) -> float:
        """
        Calculate total cost including shipping

        Args:
            product: Product dictionary

        Returns:
            Total cost as float
        """
        base_price = self._extract_price(product.get("price", "0"))
        shipping = self._extract_price(product.get("delivery", "0"))
        return base_price + shipping

    def _extract_brand(self, title: str) -> str:
        """
        Extract brand name from product title

        Args:
            title: Product title

        Returns:
            Brand name or "Unknown" if not found
        """
        if not title:
            return "Unknown"

        # Common brand patterns (first word is often the brand)
        words = title.split()
        if words:
            return words[0]
        return "Unknown"

    def _extract_color(self, product: Dict[str, Any]) -> str:
        """
        Extract color information from product

        Args:
            product: Product dictionary

        Returns:
            Color information or "Not specified" if not found
        """
        # Check if color is directly available
        if "color" in product and product["color"]:
            return product["color"]

        # Try to extract color from title
        title = product.get("title", "")
        if not title:
            return "Not specified"

        # Common color keywords
        color_keywords = ["black", "white", "red", "blue", "green", "yellow", "purple",
                          "orange", "brown", "gray", "grey", "silver", "gold", "pink"]

        for color in color_keywords:
            if color.lower() in title.lower():
                return color.capitalize()

        return "Not specified"

    def _get_memory_key(self, products: List[Dict[str, Any]]) -> str:
        """Generate a unique key for memory storage based on product details"""
        # Create a unique key based on product titles and prices
        key_parts = []
        for product in products:
            title = product.get('title', '')
            price = product.get('price', '')
            key_parts.append(f"{title}_{price}")
        return "_".join(sorted(key_parts))

    async def find_best_deal(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find the single best deal from a list of products

        Args:
            products: List of product dictionaries

        Returns:
            Best deal product with price analysis
        """
        try:
            # Verify price comparison access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="compare_prices",
                policy_code="policy:c047c5e5ec66",
                operation_name="Price Comparison"
            )

            if not products:
                return {}

            # Check memory first
            memory_key = self._get_memory_key(products)
            if memory_key in self._best_deal_memory:
                print("Using cached best deal result...")
                return self._best_deal_memory[memory_key]

            # Calculate total cost for each product
            products_with_total = []
            for product in products:
                total_cost = self._calculate_total_cost(product)
                product_copy = product.copy()
                product_copy["total_cost"] = total_cost
                products_with_total.append(product_copy)

            # Sort by total cost
            sorted_products = sorted(
                products_with_total, key=lambda x: x["total_cost"])

            # Get the cheapest product
            best_deal = sorted_products[0]

            # Add price analysis
            best_deal["price_analysis"] = {
                "base_price": self._extract_price(best_deal.get("price", "0")),
                "shipping_cost": self._extract_price(best_deal.get("delivery", "0")),
                "total_cost": best_deal["total_cost"],
                "price_rank": 1,
                "total_products_compared": len(products),
                "savings_vs_average": self._calculate_savings_vs_average(products_with_total)
            }

            # Store in memory
            self._best_deal_memory[memory_key] = best_deal

            return best_deal

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to find best deal: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution

    def _calculate_savings_vs_average(self, products: List[Dict[str, Any]]) -> float:
        """
        Calculate savings compared to average price

        Args:
            products: List of products with total cost

        Returns:
            Amount saved compared to average
        """
        if not products:
            return 0.0

        total_costs = [p["total_cost"] for p in products]
        average_cost = sum(total_costs) / len(total_costs)
        cheapest_cost = min(total_costs)

        return average_cost - cheapest_cost

    async def recommend_best_product(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Recommend the single best product based on price

        Args:
            products: List of product dictionaries

        Returns:
            Recommendation with the best product and price details
        """
        try:
            # Verify price comparison access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="compare_prices",
                policy_code="policy:c047c5e5ec66",
                operation_name="Price Comparison"
            )

            if not products:
                return {
                    "error": "No products to analyze",
                    "recommendation": None
                }

            # Check memory first
            memory_key = self._get_memory_key(products)
            if memory_key in self._comparison_memory:
                print("Using cached price comparison result...")
                return self._comparison_memory[memory_key]

            # Find the best deal
            best_deal = await self.find_best_deal(products)

            if not best_deal:
                return {
                    "error": "Could not find a suitable product",
                    "recommendation": None
                }

            # Extract product details
            title = best_deal.get("title", "Unknown Product")
            brand = self._extract_brand(title)
            price = best_deal.get("price", "Price not available")
            color = self._extract_color(best_deal)
            total_cost = f"${best_deal.get('total_cost', 0):.2f}"

            # Create a focused recommendation with just the requested details
            recommendation = {
                "product": {
                    "name": title,
                    "brand": brand,
                    "price": price,
                    "color": color,
                    "total_cost": total_cost,
                    "rating": best_deal.get("rating", "N/A")
                },
                "summary": f"The best deal is {title} ({brand}) in {color} at {price} (total cost: {total_cost})."
            }

            # Store in memory
            self._comparison_memory[memory_key] = recommendation

            return recommendation

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to recommend best product: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution
