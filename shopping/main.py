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
import json
import asyncio

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

        # Get the absolute path to the shopping directory
        shopping_dir = os.path.dirname(os.path.abspath(__file__))
        product_json_path = os.path.join(shopping_dir, 'product.json')
        print(f"Will save results to: {product_json_path}")

        # Initialize default result
        result = {
            "raw_products": [],
            "filtered_products": [],
            "top_products": [],
            "best_match": None
        }

        try:
            # Convert the CrewOutput to a string
            output_str = str(crew_output)
            print(f"CrewOutput content preview: {output_str[:200]}...")

            # Try to find JSON in the output
            import re
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, output_str)

            if matches:
                for match in matches:
                    try:
                        parsed_data = json.loads(match)
                        if isinstance(parsed_data, dict):
                            # Check if it has the expected structure
                            if all(key in parsed_data for key in ["raw_products", "filtered_products", "top_products", "best_match"]):
                                result = parsed_data
                                print("Successfully parsed crew output as JSON")
                                break
                    except json.JSONDecodeError:
                        continue

            # Save results to product.json
            try:
                with open(product_json_path, 'w') as f:
                    json.dump(result, f, indent=2)
                    f.flush()  # Force write to disk
                    os.fsync(f.fileno())  # Ensure it's written to disk
                print("Results saved to product.json")
            except Exception as e:
                print(f"Error saving results to file: {e}")
                print("Continuing with in-memory results")

            return result

        except Exception as e:
            print(f"Error in _process_crew_output: {e}")
            print("Using default result structure")
            return result

    async def run_research(self):
        """Run the research phase"""
        # Initialize research agent
        print("\n=== Initializing Research Agent ===")
        try:
            research_agent = self.agents.research_agent()
            # Properly await initialization
            await research_agent.initialize()
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
Return ONLY a valid JSON object with the following structure (no explanation, no markdown, no summary):
{{
  \"raw_products\": [...],
  \"filtered_products\": [...],
  \"top_products\": [...],
  \"best_match\": ...
}}
Do not return any explanation or summary, only the JSON object.""",
            agent=research_agent,
            expected_output="A JSON object with keys: raw_products, filtered_products, top_products, best_match. No explanation, only JSON."
        )
        print("Search task created")

        analyze_task = Task(
            description=f"""Analyze the search results and find the best match based on criteria: {self.criteria}
Use the analyze_products method to analyze the products and return recommendations.
Return ONLY a valid JSON object with the following structure (no explanation, no markdown, no summary):
{{
  \"raw_products\": [...],
  \"filtered_products\": [...],
  \"top_products\": [...],
  \"best_match\": ...
}}
Do not return any explanation or summary, only the JSON object.""",
            agent=research_agent,
            expected_output="A JSON object with keys: raw_products, filtered_products, top_products, best_match. No explanation, only JSON."
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
            crew_output = crew.kickoff()

            # Process crew output
            result = self._process_crew_output(crew_output)

            # Verify the result structure
            if not isinstance(result, dict):
                print("Invalid result structure, using default")
                result = {
                    "raw_products": [],
                    "filtered_products": [],
                    "top_products": [],
                    "best_match": None
                }

            # Ensure all required keys exist
            for key in ["raw_products", "filtered_products", "top_products", "best_match"]:
                if key not in result:
                    result[key] = [] if key != "best_match" else None

            return result

        except Exception as e:
            print(f"\nError during research: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("\nFalling back to OpenAI search due to research error")
            return self._search_with_openai()

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

    def load_research_results(self):
        """Load research results from products.json file"""
        try:
            shopping_dir = os.path.dirname(os.path.abspath(__file__))
            product_json_path = os.path.join(shopping_dir, 'product.json')
            with open(product_json_path, 'r') as f:
                data = json.load(f)
            print("[DEBUG] Loaded research results from product.json:")
            print(json.dumps(data, indent=2))
            return data
        except Exception as e:
            print(f"[DEBUG] Failed to load products.json: {e}")
            return {
                "raw_products": [],
                "filtered_products": [],
                "top_products": [],
                "best_match": None
            }

    def run_price_comparison(self, products: List[Dict[str, Any]] = None):
        """Run the price comparison phase"""
        # Initialize price comparison agent
        price_agent = self.agents.price_comparison_agent()

        # If no products provided, try to load from file
        if products is None or not products:
            print(
                "[DEBUG] No products provided to price comparison, loading from products.json...")
            data = self.load_research_results()
            # Try to get best_match first, then fall back to top_products
            if data.get("best_match"):
                products = [data["best_match"]]
            else:
                products = data.get("top_products", [])

        # Ensure products is a list
        if not isinstance(products, list):
            print("Error: Products must be a list")
            return {"product": None, "summary": "No products available for comparison"}

        # Ensure each product has the required fields
        valid_products = []
        for product in products:
            if isinstance(product, dict):
                # Handle both product_name and name/title fields
                name = product.get("product_name", product.get(
                    "name", product.get("title", "Unknown")))
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

    async def process_order_with_payment(self, product_details: dict, customer_email: str):
        """
        Process an order with PayPal payment integration

        Args:
            product_details: Dictionary containing product information
            customer_email: Customer's email address
        """
        try:
            # Initialize PayPal agent
            paypal_agent = self.agents.paypal_agent()
            await paypal_agent.initialize()  # Initialize the agent

            # Get access token
            access_token = await paypal_agent.get_access_token()

            # Create PayPal order
            order_data = await paypal_agent.create_payment_order(
                amount=product_details['price'],
                currency="USD",
                description=product_details.get('description', ''),
                payee_email=customer_email
            )

            print("\n[PayPal Order Created]")
            print(json.dumps(order_data, indent=2))

            # Get the approval URL
            approval_url = None
            for link in order_data.get('links', []):
                if link.get('rel') == 'approve':
                    approval_url = link.get('href')
                    break

            if approval_url:
                print(
                    f"\nPlease complete your payment at the following PayPal URL:\n{approval_url}")
                print("\nInstructions:")
                print("1. Open the above URL in your browser.")
                print("2. Log in with your PayPal sandbox buyer account.")
                print("3. Approve the payment to complete your order.")
                print("\nAfter approval, the payment will be captured automatically.")

                # Ask if user wants to proceed with capture now or later
                capture_now = input(
                    "\nDo you want to capture the payment now? (y/n): ").lower()
                if capture_now == 'y':
                    # Use order_data.id instead of paypal_order_id
                    if order_data.get('id'):
                        capture_data = await paypal_agent.capture_payment(order_data['id'])
                        print("\n[PayPal Payment Capture]")
                        print(json.dumps(capture_data, indent=2))

                        # Check if there was an error with the capture
                        if isinstance(capture_data, dict) and "error" in capture_data:
                            print(
                                "\nPayment capture failed. The order may need to be approved first.")
                            print(f"Error: {capture_data.get('error')}")
                            print(f"Status: {capture_data.get('status')}")
                        else:
                            print("\nPayment captured successfully!")
                else:
                    print("\nPayment will need to be captured after approval.")
            else:
                print("\nNo approval URL found. Cannot proceed with payment.")

            return order_data

        except Exception as e:
            print(f"\nError processing payment: {str(e)}")
            return None


def read_latest_payment_detail():
    project_root = os.path.dirname(os.path.abspath(__file__))
    payment_json_path = os.path.join(project_root, 'paymentdetail.json')
    if not os.path.exists(payment_json_path):
        print("No payment details recorded yet.")
        return
    try:
        with open(payment_json_path, 'r') as f:
            content = f.read().strip()
            if not content:
                print("No payment details recorded yet.")
                return
            data = json.loads(content)
            if not data:
                print("No payment details recorded yet.")
                return
            latest = data[-1]
            print("\n[Latest PayPal Payment Detail]")
            print(json.dumps(latest, indent=2))
    except Exception as e:
        print(f"Error reading paymentdetail.json: {e}")


def main():
    """
    Main function to run the ShopperAI application
    """
    async def run_async():
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
        research_results = await shopper.run_research()

        # Extract and display products
        products = []
        best = None
        if isinstance(research_results, dict):
            if research_results.get("best_match") and research_results["best_match"]:
                best = research_results["best_match"]
                products = [best]
            elif research_results.get("top_products") and research_results["top_products"]:
                products = research_results["top_products"]
            elif research_results.get("filtered_products") and research_results["filtered_products"]:
                products = research_results["filtered_products"]
            elif research_results.get("raw_products") and research_results["raw_products"]:
                products = research_results["raw_products"]

        if best:
            print("\nBest Match:")
            print(f"Name: {best.get('name', best.get('title', ''))}")
            print(f"Price: {best.get('price', '')}")
            print(f"Rating: {best.get('rating', '')}")
        elif products:
            print("\nFound the following products:")
            print("\n{:<40} {:<10} {:<10}".format(
                "Product", "Price", "Rating"))
            print("-" * 80)
            for product in products:
                name = product.get("name", product.get("title", "Unknown"))
                price = product.get("price", "N/A")
                rating = product.get("rating", "N/A")
                print("{:<40} {:<10} {:<10}".format(
                    name[:37] + "..." if len(name) > 37 else name,
                    price,
                    rating
                ))
        else:
            print("\nNo products found matching your criteria.")

        # Ask user if they want to compare prices
        if products:
            compare_prices = input(
                "\nWould you like to compare prices for these products? (y/n): ").lower()
            if compare_prices == 'y':
                print("\nComparing prices...")
                if isinstance(research_results, dict):
                    if research_results.get("best_match"):
                        products_to_compare = [research_results["best_match"]]
                    elif research_results.get("top_products"):
                        products_to_compare = research_results["top_products"]
                    elif research_results.get("filtered_products"):
                        products_to_compare = research_results["filtered_products"]
                    else:
                        products_to_compare = research_results.get(
                            "raw_products", [])
                else:
                    products_to_compare = products

                price_results = shopper.run_price_comparison(
                    products_to_compare)

                if price_results:
                    print("\nPrice Comparison Results:")
                    if isinstance(price_results, dict):
                        product = price_results.get("product", {})
                        if product:
                            print("\nBest Deal:")
                            print(f"Product: {product.get('name', 'Unknown')}")
                            print(f"Price: {product.get('price', 'N/A')}")
                            print(f"Rating: {product.get('rating', 'N/A')}")
                            if "summary" in price_results:
                                print(f"\nSummary: {price_results['summary']}")

                            # Ask if user wants to proceed with payment
                            proceed_payment = input(
                                "\nWould you like to proceed with payment? (y/n): ").lower()
                            if proceed_payment == 'y':
                                # Get merchant/business email
                                payee_email = input(
                                    "\nPlease enter the merchant/business PayPal email address to receive payment: ")

                                # Process order with payment
                                print("\nProcessing order with PayPal...")
                                try:
                                    # Prepare product details for payment
                                    product_details = {
                                        "name": product.get('name', 'Unknown Product'),
                                        "price": product.get('price', '0.00'),
                                        "quantity": 1,
                                        "description": product.get('description', ''),
                                        "payee_email": payee_email
                                    }

                                    # Process the order with payment
                                    payment_result = await shopper.process_order_with_payment(product_details, payee_email)

                                    # Only show real PayPal order ID and approval URL
                                    if isinstance(payment_result, dict):
                                        paypal_order_id = payment_result.get(
                                            "id")

                                        # Get approval URL from links
                                        approval_url = None
                                        for link in payment_result.get('links', []):
                                            if link.get('rel') == 'approve':
                                                approval_url = link.get('href')
                                                break

                                        if paypal_order_id:
                                            print(
                                                f"\nOrder ID: {paypal_order_id}")
                                        if approval_url:
                                            print(
                                                f"\nPlease complete your payment at the following PayPal URL:\n{approval_url}")
                                            print("\nInstructions:")
                                            print(
                                                "1. Open the above URL in your browser.")
                                            print(
                                                "2. Log in with your PayPal sandbox buyer account.")
                                            print(
                                                "3. Approve the payment to complete your order.")

                                        # Wait for user to complete payment
                                        input(
                                            "\nPress Enter after completing the payment in your browser...")

                                        # Capture the payment
                                        if paypal_order_id:
                                            capture_result = await paypal_agent.capture_payment(paypal_order_id)
                                            if capture_result:
                                                if capture_result.get('status') == 'COMPLETED':
                                                    print(
                                                        "\nPayment captured successfully!")
                                                    print(
                                                        f"Transaction ID: {capture_result.get('id')}")
                                                    print(
                                                        f"Status: {capture_result.get('status')}")
                                                else:
                                                    print(
                                                        "\nPayment capture failed or is incomplete.")
                                                    print(
                                                        f"Status: {capture_result.get('status')}")
                                    else:
                                        print(
                                            f"\nOrder processing failed: {payment_result}")
                                except Exception as e:
                                    print(
                                        f"\nError processing payment: {str(e)}")
                        else:
                            print("No specific product recommendation available.")
                    else:
                        print("Price comparison results are in an unexpected format.")
                else:
                    print("\nUnable to compare prices at this time.")

        # After payment processing
        read_latest_payment_detail()
        print("\nThank you for using ShopperAI!")

    # Run the async main function
    asyncio.run(run_async())


if __name__ == "__main__":
    main()
