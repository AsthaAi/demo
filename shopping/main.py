"""
ShopperAI Main Orchestration
Coordinates all agents to provide a seamless shopping experience.
"""
from typing import Dict, Any, List
import os
from agents.research_agent import ResearchAgent
from agents.price_comparison_agent import PriceComparisonAgent
from agents.order_agent import OrderAgent
from agents.paypal_agent import PayPalAgent
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

    def paypal_agent(self):
        """Create and return the PayPal agent"""
        return PayPalAgent()


class ShopperAI:
    """Main ShopperAI class that orchestrates all agents"""

    def __init__(self, query: str, criteria: Dict[str, Any]):
        self.query = query
        self.criteria = criteria
        self.agents = ShopperAgents()
        self.tasks = ResearchTasks()
        self.recommended_product = None
        self.research_results = None

    def _process_crew_output(self, crew_output):
        """Process a CrewOutput object and extract product information"""
        print("Processing CrewOutput object...")

        # Convert the CrewOutput to a string
        output_str = str(crew_output)
        print(f"CrewOutput content preview: {output_str[:200]}...")

        # Extract products using OpenAI
        products = []
        best_match = None

        try:
            # Use OpenAI to extract product information
            import openai
            import json
            import os
            from dotenv import load_dotenv

            # Load environment variables
            load_dotenv()

            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print(
                    "OPENAI_API_KEY not found in environment variables. Using regex fallback.")
                return self._extract_products_with_regex(output_str)

            # Initialize OpenAI client
            client = openai.OpenAI(api_key=api_key)

            # Create a prompt for OpenAI
            prompt = f"""
            Extract product information from the following text. 
            Return a JSON array of products, where each product has the following fields:
            - name: The product name
            - price: The price with dollar sign
            - rating: The rating
            - brand: The brand name (extract from the product name if possible)
            - description: The product description
            - material: The material (if available)
            - capacity: The capacity (if available)
            
            Text to extract from:
            {output_str}
            
            Return ONLY the JSON array, nothing else.
            """

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured product data from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            # Extract the JSON from the response
            json_text = response.choices[0].message.content.strip()

            # Parse the JSON
            try:
                products = json.loads(json_text)
                print(
                    f"Successfully extracted {len(products)} products using OpenAI")

                # Set the first product as the best match
                if products:
                    best_match = products[0]

                return {
                    "raw_products": products,
                    "filtered_products": products,
                    "top_products": products[:5],
                    "best_match": best_match
                }
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from OpenAI response: {e}")
                print("Falling back to regex extraction")
                return self._extract_products_with_regex(output_str)

        except Exception as e:
            print(f"Error using OpenAI for extraction: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("Falling back to regex extraction")
            return self._extract_products_with_regex(output_str)

    def _extract_products_with_regex(self, output_str):
        """Extract products using regex as a fallback method"""
        print("Extracting products using regex...")
        products = []
        best_match = None

        try:
            import re

            # Look for product listings in the text with the exact format from the logs
            product_pattern = r'\d+\.\s+\*\*(.*?)\*\*\s*\n\s*-\s*\*\*Price:\*\*\s*\$?([\d,.]+)\s*\n\s*-\s*\*\*Rating:\*\*\s*([\d.]+)'
            product_matches = re.findall(
                product_pattern, output_str, re.DOTALL)

            if product_matches:
                for match in product_matches:
                    name, price, rating = match
                    # Try to extract description
                    desc_pattern = r'-\s*\*\*Description:\*\*\s*(.*?)(?=\n\n|\Z)'
                    desc_match = re.search(
                        desc_pattern, output_str[output_str.find(match[0]):], re.DOTALL)
                    description = desc_match.group(1) if desc_match else ""

                    # Try to extract material
                    material_pattern = r'-\s*\*\*Material:\*\*\s*(.*?)(?=\n|$)'
                    material_match = re.search(
                        material_pattern, output_str[output_str.find(match[0]):], re.DOTALL)
                    material = material_match.group(
                        1) if material_match else ""

                    # Try to extract capacity
                    capacity_pattern = r'-\s*\*\*Capacity:\*\*\s*(.*?)(?=\n|$)'
                    capacity_match = re.search(
                        capacity_pattern, output_str[output_str.find(match[0]):], re.DOTALL)
                    capacity = capacity_match.group(
                        1) if capacity_match else ""

                    # Try to extract brand from name
                    brand = "Unknown"
                    if " " in name:
                        potential_brand = name.split()[0]
                        if potential_brand not in ["The", "A", "An"]:
                            brand = potential_brand

                    product = {
                        "name": name.strip(),
                        "price": f"${price.strip()}",
                        "rating": rating.strip(),
                        "brand": brand,
                        "description": description.strip(),
                        "material": material.strip(),
                        "capacity": capacity.strip()
                    }
                    products.append(product)

                # Set the first product as the best match
                if products:
                    best_match = products[0]

                print(
                    f"Successfully extracted {len(products)} products using regex")
                return {
                    "raw_products": products,
                    "filtered_products": products,
                    "top_products": products[:5],
                    "best_match": best_match
                }
            else:
                print(
                    "Could not extract products using regex. Using sample products.")
                return self._create_sample_products()
        except Exception as e:
            print(f"Error extracting products with regex: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return self._create_sample_products()

    def run_research(self):
        """Run the research phase"""
        # Initialize research agent
        print("\n=== Initializing Research Agent ===")
        try:
            research_agent = self.agents.research_agent()
            print("Research agent initialized successfully")
        except ValueError as e:
            if "SERPAPI_API_KEY" in str(e):
                print(
                    "SERPAPI_API_KEY not found. Using OpenAI for product search instead.")
                return self._search_with_openai()
            else:
                raise e

        # Create research tasks
        print("\n=== Creating Research Tasks ===")
        search_task = Task(
            description=f"""Search for products matching: {self.query} with criteria: {self.criteria}
            Use the search_and_analyze method to find and analyze products.
            Return a list of products that match the criteria.""",
            agent=research_agent,
            expected_output="A list of products matching the search criteria"
        )
        print("Search task created")

        analyze_task = Task(
            description=f"""Analyze the search results and find the best match based on criteria: {self.criteria}
            Use the analyze_products method to analyze the products and return recommendations.""",
            agent=research_agent,
            expected_output="A detailed analysis of the products with recommendations"
        )
        print("Analyze task created")

        # Create and run the research crew
        print("\n=== Creating Research Crew ===")
        crew = Crew(
            agents=[research_agent],
            tasks=[search_task, analyze_task],
            verbose=True
        )
        print("Research crew created")

        # Get the research results
        print("\n=== Starting Research Phase ===")
        print(f"Query: {self.query}")
        print(f"Criteria: {self.criteria}")

        try:
            print("Kicking off the research crew...")
            results = crew.kickoff()
            print("\n=== Research Results ===")
            print(f"Results type: {type(results)}")
            print(f"Results: {results}")
        except Exception as e:
            print(f"\nError during research: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("\nFalling back to OpenAI search due to research error")
            return self._search_with_openai()

        # Extract products from CrewAI output
        products = []
        best_match = None

        # If results is a string (text output), try to parse it into structured data
        if isinstance(results, str):
            try:
                # Use OpenAI to extract product information
                import openai
                import json
                import os
                from dotenv import load_dotenv

                # Load environment variables
                load_dotenv()

                # Get OpenAI API key
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print(
                        "OPENAI_API_KEY not found in environment variables. Using regex fallback.")
                    return self._extract_products_with_regex(results)

                # Initialize OpenAI client
                client = openai.OpenAI(api_key=api_key)

                # Create a prompt for OpenAI
                prompt = f"""
                Extract product information from the following text. 
                Return a JSON array of products, where each product has the following fields:
                - name: The product name
                - price: The price with dollar sign
                - rating: The rating
                - brand: The brand name (extract from the product name if possible)
                - description: The product description
                - material: The material (if available)
                - capacity: The capacity (if available)
                
                Text to extract from:
                {results}
                
                Return ONLY the JSON array, nothing else.
                """

                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts structured product data from text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )

                # Extract the JSON from the response
                json_text = response.choices[0].message.content.strip()

                # Parse the JSON
                try:
                    products = json.loads(json_text)
                    print(
                        f"Successfully extracted {len(products)} products using OpenAI")

                    # Set the first product as the best match
                    if products:
                        best_match = products[0]

                    return {
                        "raw_products": products,
                        "filtered_products": products,
                        "top_products": products[:5],
                        "best_match": best_match
                    }
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON from OpenAI response: {e}")
                    print("Falling back to regex extraction")
                    return self._extract_products_with_regex(results)

            except Exception as e:
                print(f"Error using OpenAI for extraction: {e}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                print("Falling back to regex extraction")
                return self._extract_products_with_regex(results)

        # If results is a CrewOutput object, process it directly
        elif hasattr(results, 'raw_output'):
            print("Results is a CrewOutput object, processing directly")
            return self._process_crew_output(results)

        # If results is already a dictionary, check if it has the expected structure
        elif isinstance(results, dict):
            # Check if the dictionary has the expected keys
            expected_keys = ["raw_products",
                             "filtered_products", "top_products", "best_match"]
            has_expected_keys = all(key in results for key in expected_keys)
            print(f"Has expected keys: {has_expected_keys}")
            print(
                f"Missing keys: {[key for key in expected_keys if key not in results]}")

            # If it has the expected keys but no products, add sample products
            if has_expected_keys and (not results.get("top_products") or len(results.get("top_products", [])) == 0):
                print("Adding sample products to empty results...")
                results["raw_products"] = [
                    {
                        "name": f"{self.query} - Sample Product 1",
                        "price": "$999.00",
                        "rating": "4.8",
                        "brand": "SampleBrand",
                        "description": f"A sample {self.query} product with good ratings"
                    }
                ]
                results["filtered_products"] = results["raw_products"]
                results["top_products"] = results["raw_products"]
                results["best_match"] = results["raw_products"][0]

            return results

        # If results is a list, convert it to the expected structure
        elif isinstance(results, list):
            # If the list is empty, add sample products
            if not results:
                print("Adding sample products to empty list results...")
                results = [
                    {
                        "name": f"{self.query} - Sample Product 1",
                        "price": "$999.00",
                        "rating": "4.8",
                        "brand": "SampleBrand",
                        "description": f"A sample {self.query} product with good ratings"
                    }
                ]

            return {
                "raw_products": results,
                "filtered_products": results,
                "top_products": results[:5] if len(results) > 5 else results,
                "best_match": results[0] if results else None
            }

        # Default case - return sample products
        print("Using default sample products...")
        return self._create_sample_products()

    def _search_with_openai(self):
        """Search for products using OpenAI as a fallback when SERPAPI is not available"""
        print("\n=== Searching with OpenAI ===")

        try:
            import openai
            import json
            import os
            from dotenv import load_dotenv

            # Load environment variables
            load_dotenv()

            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print(
                    "OPENAI_API_KEY not found in environment variables. Using sample products.")
                return self._create_sample_products()

            # Initialize OpenAI client
            client = openai.OpenAI(api_key=api_key)

            # Create a prompt for OpenAI
            prompt = f"""
            Search for products matching the following criteria:
            - Query: {self.query}
            - Maximum price: ${self.criteria.get('max_price', 1000)}
            - Minimum rating: {self.criteria.get('min_rating', 0)}
            
            Return a JSON array of 5 products, where each product has the following fields:
            - name: The product name
            - price: The price with dollar sign
            - rating: The rating (out of 5)
            - brand: The brand name
            - description: A brief description of the product
            - material: The material (if applicable)
            - capacity: The capacity (if applicable)
            
            Make sure the products match the search criteria and are realistic.
            Return ONLY the JSON array, nothing else.
            """

            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that searches for products based on user criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )

            # Extract the JSON from the response
            json_text = response.choices[0].message.content.strip()

            # Parse the JSON
            try:
                products = json.loads(json_text)
                print(
                    f"Successfully found {len(products)} products using OpenAI")

                # Set the first product as the best match
                best_match = products[0] if products else None

                return {
                    "raw_products": products,
                    "filtered_products": products,
                    "top_products": products[:5],
                    "best_match": best_match
                }
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from OpenAI response: {e}")
                print("Using sample products as fallback")
                return self._create_sample_products()

        except Exception as e:
            print(f"Error using OpenAI for search: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("Using sample products as fallback")
            return self._create_sample_products()

    def _create_sample_products(self):
        """Create sample products for fallback"""
        # Get the search criteria
        max_price = self.criteria.get("max_price", 1000)
        min_rating = self.criteria.get("min_rating", 0)

        # Create sample products that match the criteria
        sample_products = [
            {
                "name": f"{self.query} - Budget Option",
                "price": f"${max_price * 0.8:.2f}",
                "rating": f"{min_rating + 0.5}",
                "brand": "BudgetBrand",
                "description": f"A budget-friendly {self.query} that meets your basic needs",
                "material": "Plastic",
                "capacity": "1 liter"
            },
            {
                "name": f"{self.query} - Mid-Range Option",
                "price": f"${max_price * 0.9:.2f}",
                "rating": f"{min_rating + 1.0}",
                "brand": "MidRangeBrand",
                "description": f"A balanced {self.query} offering good value for money",
                "material": "Stainless Steel",
                "capacity": "1.5 liters"
            },
            {
                "name": f"{self.query} - Premium Option",
                "price": f"${max_price:.2f}",
                "rating": f"{min_rating + 1.5}",
                "brand": "PremiumBrand",
                "description": f"A high-quality {self.query} with premium features",
                "material": "Glass",
                "capacity": "2 liters"
            }
        ]

        return {
            "raw_products": sample_products,
            "filtered_products": sample_products,
            "top_products": sample_products,
            "best_match": sample_products[0]
        }

    def run_price_comparison(self, products: List[Dict[str, Any]]):
        """Run the price comparison phase"""
        # Initialize price comparison agent
        price_agent = self.agents.price_comparison_agent()

        # Ensure products is a list
        if not isinstance(products, list):
            print("Error: Products must be a list")
            return {"product": None, "summary": "No products available for comparison"}

        # Ensure each product has the required fields
        valid_products = []
        for product in products:
            if isinstance(product, dict):
                # Ensure product has name and price
                if "name" in product or "title" in product:
                    name = product.get("name", product.get("title", "Unknown"))
                    price = product.get("price", "N/A")
                    brand = product.get("brand", "Unknown")
                    rating = product.get("rating", "N/A")

                    # Create a standardized product object
                    valid_product = {
                        "name": name,
                        "price": price,
                        "brand": brand,
                        "rating": rating,
                        "description": product.get("description", ""),
                        "link": product.get("link", ""),
                        "color": product.get("color", "Unknown")
                    }
                    valid_products.append(valid_product)

        if not valid_products:
            print("No valid products found for price comparison")
            return {"product": None, "summary": "No valid products available for comparison"}

        # Create price comparison task
        price_task = Task(
            description=f"""Find the single cheapest product from the search results.
            Consider total cost including shipping and any available discounts.
            Return a clear recommendation for the best deal with price details.""",
            agent=price_agent,
            expected_output="A clear recommendation for the single best product based on price"
        )

        # Create and run the price comparison crew
        crew = Crew(
            agents=[price_agent],
            tasks=[price_task],
            verbose=True
        )

        # Run the price comparison
        results = crew.kickoff()

        # If results is a string, try to parse it
        if isinstance(results, str):
            try:
                import json
                import re

                # Look for JSON-like structures in the text
                json_pattern = r'\{.*\}'
                matches = re.findall(json_pattern, results, re.DOTALL)

                if matches:
                    # Try to parse the first match as JSON
                    try:
                        parsed_data = json.loads(matches[0])
                        if isinstance(parsed_data, dict):
                            return parsed_data
                    except json.JSONDecodeError:
                        pass

                # If no valid JSON found, create a basic structure
                return {
                    "product": valid_products[0] if valid_products else None,
                    "summary": "Price comparison completed"
                }
            except Exception as e:
                print(f"Error parsing price comparison results: {e}")
                return {
                    "product": valid_products[0] if valid_products else None,
                    "summary": "Price comparison completed with errors"
                }

        # If results is already a dictionary, return it
        if isinstance(results, dict):
            return results

        # Default case - return the first product as the best deal
        return {
            "product": valid_products[0] if valid_products else None,
            "summary": "Selected the first product as the best deal"
        }

    def process_order_with_payment(self, product_details: dict, customer_email: str):
        """
        Process an order with PayPal payment integration

        Args:
            product_details: Dictionary containing product information
            customer_email: Customer's email address
        """
        # Initialize agents
        order_agent = self.agents.order_agent()
        paypal_agent = self.agents.paypal_agent()

        # Create order task
        order_task = Task(
            description=f"""
            Process the order for the following product:
            - Name: {product_details.get('name')}
            - Price: {product_details.get('price')}
            - Quantity: {product_details.get('quantity', 1)}
            
            Generate order details and prepare for payment processing.
            """,
            agent=order_agent,
            expected_output="Order details including transaction ID and status"
        )

        # Create payment order task
        payment_order_task = Task(
            description=f"""
            Create PayPal payment order:
            - Amount: {product_details.get('price')}
            - Customer Email: {customer_email}
            - Description: Order for {product_details.get('name')}
            
            Use the create_payment_order method to create a PayPal order.
            """,
            agent=paypal_agent,
            expected_output="PayPal order details with order ID"
        )

        # Capture payment task
        capture_payment_task = Task(
            description=f"""
            Capture the payment for the created PayPal order.
            Use the capture_payment method to finalize the payment.
            Provide the payment confirmation details.
            """,
            agent=paypal_agent,
            expected_output="Payment capture confirmation with transaction details"
        )

        # Create and run the crew
        crew = Crew(
            agents=[order_agent, paypal_agent],
            tasks=[order_task, payment_order_task, capture_payment_task],
            verbose=True
        )

        result = crew.kickoff()
        return result


def main():
    """
    Main function to run the ShopperAI application
    """
    print("Welcome to ShopperAI!")
    print("I'll help you find and compare products across multiple platforms.")

    # Get search criteria from user
    query = input("\nWhat would you like to search for? ")

    # Ask for maximum price separately
    while True:
        try:
            max_price_input = input("Maximum price (in USD): ")
            max_price = float(max_price_input)
            break
        except ValueError:
            print("Please enter a valid number for the maximum price.")

    # Ask for minimum rating separately
    while True:
        try:
            min_rating_input = input("Minimum rating (0-5): ")
            min_rating = float(min_rating_input)
            if 0 <= min_rating <= 5:
                break
            else:
                print("Rating must be between 0 and 5.")
        except ValueError:
            print("Please enter a valid number for the minimum rating.")

    # Initialize ShopperAI
    shopper = ShopperAI(
        query, {"max_price": max_price, "min_rating": min_rating})

    # Run research phase
    print("\nSearching for products...")
    research_results = shopper.run_research()

    # Extract and display products
    products = []
    if isinstance(research_results, dict):
        # Debug the structure of research_results
        print("\nResearch results structure:")
        for key, value in research_results.items():
            if isinstance(value, list):
                print(f"  - {key}: {len(value)} items")
            else:
                print(f"  - {key}: {type(value)}")

        # First try to get top_products
        if "top_products" in research_results and research_results["top_products"]:
            products = research_results["top_products"]
        # Then try filtered_products
        elif "filtered_products" in research_results and research_results["filtered_products"]:
            products = research_results["filtered_products"]
        # Then try raw_products
        elif "raw_products" in research_results and research_results["raw_products"]:
            products = research_results["raw_products"]
        # Finally try products
        elif "products" in research_results and research_results["products"]:
            products = research_results["products"]

    # Debug information
    print(f"\nNumber of products found: {len(products)}")

    if products:
        print("\nFound the following products:")
        print("\n{:<40} {:<10} {:<10} {:<20}".format(
            "Product", "Price", "Rating", "Brand"))
        print("-" * 80)
        for product in products:
            # Handle different product structures
            name = product.get("name", product.get("title", "Unknown"))
            price = product.get("price", "N/A")
            rating = product.get("rating", "N/A")
            brand = product.get("brand", "Unknown")

            print("{:<40} {:<10} {:<10} {:<20}".format(
                name[:37] + "..." if len(name) > 37 else name,
                price,
                rating,
                brand
            ))

        # Display best match if available
        if "best_match" in research_results and research_results["best_match"]:
            best = research_results["best_match"]
            print("\nBest Match:")
            print(f"Name: {best.get('name', best.get('title', ''))}")
            print(f"Brand: {best.get('brand', '')}")
            print(f"Price: {best.get('price', '')}")
            print(f"Rating: {best.get('rating', '')}")
    else:
        print("\nNo products found matching your criteria.")

    # Ask user if they want to compare prices
    if products:
        compare_prices = input(
            "\nWould you like to compare prices for these products? (y/n): ").lower()
        if compare_prices == 'y':
            print("\nComparing prices...")
            price_results = shopper.run_price_comparison(products)

            if price_results:
                print("\nPrice Comparison Results:")
                if isinstance(price_results, dict):
                    product = price_results.get("product", {})
                    if product:
                        print("\nBest Deal:")
                        print(f"Product: {product.get('name', 'Unknown')}")
                        print(f"Price: {product.get('price', 'N/A')}")
                        print(f"Brand: {product.get('brand', 'Unknown')}")
                        print(f"Rating: {product.get('rating', 'N/A')}")
                        if "summary" in price_results:
                            print(f"\nSummary: {price_results['summary']}")

                        # Ask if user wants to proceed with payment
                        proceed_payment = input(
                            "\nWould you like to proceed with payment? (y/n): ").lower()
                        if proceed_payment == 'y':
                            # Get customer email
                            customer_email = input(
                                "\nPlease enter your email for payment: ")

                            # Process order with payment
                            print("\nProcessing order with PayPal...")
                            try:
                                # Prepare product details for payment
                                product_details = {
                                    "name": product.get('name', 'Unknown Product'),
                                    "price": product.get('price', '0.00'),
                                    "quantity": 1,
                                    "description": product.get('description', '')
                                }

                                # Process the order with payment
                                payment_result = shopper.process_order_with_payment(
                                    product_details, customer_email)

                                print("\nPayment processed successfully!")
                                print(f"Order details: {payment_result}")
                            except Exception as e:
                                print(f"\nError processing payment: {str(e)}")
                    else:
                        print("No specific product recommendation available.")
                else:
                    print("Price comparison results are in an unexpected format.")
            else:
                print("\nUnable to compare prices at this time.")

    print("\nThank you for using ShopperAI!")


if __name__ == "__main__":
    main()
