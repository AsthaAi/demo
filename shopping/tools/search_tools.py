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
from utils.iam_utils import IAMUtils
import json

load_dotenv()


class ProductSearchTool:
    """Tool for searching products"""

    def __init__(self, verbose=True):
        """Initialize the search tool"""
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp_id = ""
        self.is_initialized = False
        self.verbose = verbose
        self.api_key = api_key  # Store for search API use

    async def initialize(self):
        """Initialize the tool's identity"""
        if not self.is_initialized:
            await self._initialize_identity()
            self.is_initialized = True
        return self

    async def _initialize_identity(self):
        """Initialize the tool's identity asynchronously"""
        try:
            if self.verbose:
                print(f"1. Issuing identity for tool: Product Search Tool")

            # Create secure connection
            self.searchTool = await self.aztpClient.secure_connect(
                self,
                "product-search-tool",
                {
                    "isGlobalIdentity": False
                }
            )

            # Store the identity
            if hasattr(self.searchTool, 'identity'):
                self.aztp_id = self.searchTool.identity.aztp_id
                if self.verbose:
                    print(f"✅ Identity issued successfully")
                    print(f"AZTP ID: {self.aztp_id}")
            else:
                if self.verbose:
                    print("Warning: No AZTP ID received from secure_connect")
                self.aztp_id = ""

            # Verify search access before proceeding
            if self.verbose:
                print(
                    f"\n2. Verifying access permissions for Product Search Tool {self.aztp_id}")
            iam_utils = IAMUtils()
            await iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="search_products",
                policy_code="policy:1842da0b59ef",
                operation_name="Product Search"
            )

            if self.verbose:
                print("\n✅ Product search tool initialized successfully")

        except Exception as e:
            print(f"Error initializing identity: {str(e)}")
            raise

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

            if "shopping_results" in results:
                products = results["shopping_results"]
                print(f"Found {len(products)} products")
                return products
            else:
                print("No 'shopping_results' found in the API response")
                if "error" in results:
                    print(f"API Error: {results['error']}")
                return []
        except Exception as e:
            print(f"Error searching for products: {str(e)}")
            return []


class ProductAnalyzerTool:
    """Tool for analyzing product data"""

    def __init__(self, verbose=True):
        """Initialize the analyzer tool"""
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp_id = ""
        self.is_initialized = False
        self.verbose = verbose

    async def initialize(self):
        """Initialize the tool's identity"""
        if not self.is_initialized:
            await self._initialize_identity()
            self.is_initialized = True
        return self

    async def _initialize_identity(self):
        """Initialize the tool's identity asynchronously"""
        try:
            if self.verbose:
                print(f"1. Issuing identity for tool: Product Analyzer Tool")

            # Create secure connection
            self.analyzerTool = await self.aztpClient.secure_connect(
                self,
                "product-analyzer-tool",
                {
                    "isGlobalIdentity": False
                }
            )

            # Store the identity
            if hasattr(self.analyzerTool, 'identity'):
                self.aztp_id = self.analyzerTool.identity.aztp_id
                if self.verbose:
                    print(f"✅ Identity issued successfully")
                    print(f"AZTP ID: {self.aztp_id}")
            else:
                if self.verbose:
                    print("Warning: No AZTP ID received from secure_connect")
                self.aztp_id = ""

            # Verify analyzer access before proceeding
            if self.verbose:
                print(
                    f"\n2. Verifying access permissions for Product Analyzer Tool {self.aztp_id}")
            iam_utils = IAMUtils()
            await iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="analyze_products",
                policy_code="policy:2665686cb11b",
                operation_name="Product Analysis"
            )

            if self.verbose:
                print("\n✅ Product analyzer tool initialized successfully")

        except Exception as e:
            print(f"Error initializing identity: {str(e)}")
            raise

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
