"""
ShopperAI Main Orchestration
Coordinates all agents to provide a seamless shopping experience.
"""
from typing import Dict, Any, List
import os
from agents.research_agent import ResearchAgent
# from agents.price_comparison_agent import PriceComparisonAgent  # Temporarily disabled
from agents.order_agent import OrderAgent
from agents.paypal_agent import PayPalAgent
from agents.promotions_agent import PromotionsAgent
from agents.customer_support_agent import CustomerSupportAgent
from agents.risk_agent import RiskAgent
from agents.tasks import ResearchTasks
from utils.agent_middleware import agent_middleware
from dotenv import load_dotenv
from crewai import Crew, Task
from textwrap import dedent
import json
import asyncio
from datetime import datetime, timedelta
import uuid
import platform
from agents.malicious_agent import MaliciousAgent
from agents.market_agent import MarketAgent

load_dotenv()


class ShopperAgents:
    """Class to create and manage all ShopperAI agents"""

    def __init__(self):
        """Initialize ShopperAgents with middleware"""
        self._initialized = False
        self._agents = {}

    async def initialize(self):
        """Initialize the middleware and prepare agents"""
        if not self._initialized:
            # Initialize the middleware first
            await agent_middleware.initialize()
            self._initialized = True
            print("✅ ShopperAgents initialized with security middleware")

    async def _get_agent(self, agent_type: str, create_func):
        """Get or create an agent of the specified type"""
        if not self._initialized:
            await self.initialize()

        if agent_type not in self._agents:
            agent = create_func()
            await agent.initialize()  # This will now use the secure initialization
            self._agents[agent_type] = agent

        return self._agents[agent_type]

    async def research_agent(self):
        """Create and return the research agent"""
        return await self._get_agent('research', ResearchAgent)

    async def order_agent(self):
        """Create and return the order agent"""
        return await self._get_agent('order', OrderAgent)

    async def paypal_agent(self):
        """Create and return the PayPal agent"""
        return await self._get_agent('paypal', PayPalAgent)

    async def promotions_agent(self):
        """Create and return the promotions agent"""
        return await self._get_agent('promotions', PromotionsAgent)

    async def customer_support_agent(self):
        """Create and return the customer support agent"""
        return await self._get_agent('customer_support', CustomerSupportAgent)

    async def risk_agent(self):
        """Create and return the risk agent"""
        return await self._get_agent('risk', RiskAgent)


class ShopperAI:
    """Main ShopperAI class that orchestrates all agents"""

    def __init__(self, query: str, criteria: Dict[str, Any]):
        self.query = query
        self.criteria = criteria
        self.agents = ShopperAgents()
        self.tasks = ResearchTasks()
        self.recommended_product = None
        self.research_results = None
        self.user_id = None  # Will be set when processing order

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
            research_agent = await self.agents.research_agent()
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

    # Price comparison functionality has been temporarily disabled
    # The following method will be re-enabled in a future update:
    #
    # async def run_price_comparison(self, products: List[Dict[str, Any]] = None):
    #     """Run the price comparison phase"""
    #     pass

    async def process_order_with_payment(self, product_details: dict, customer_email: str):
        """Process an order with payment"""
        try:
            # Set user_id based on email for promotions
            self.user_id = customer_email

            # Initialize Risk agent for transaction analysis
            risk_agent = await self.agents.risk_agent()
            await risk_agent.initialize()

            # Initialize PayPal agent and set risk agent
            paypal_agent = await self.agents.paypal_agent()
            paypal_agent.risk_agent = risk_agent
            await paypal_agent.initialize()

            # Prepare transaction data for risk analysis
            transaction_data = {
                'transaction_id': f"TX-{str(uuid.uuid4())[:8].upper()}",
                'amount': float(str(product_details['price']).replace('$', '')),
                'timestamp': datetime.now().isoformat(),
                'location': os.getenv('TRANSACTION_LOCATION', 'Unknown'),
                'device_info': {
                    'os': platform.system(),
                    'browser': 'API Client',
                    'is_new_device': True
                },
                'user_history': []  # In production, you'd fetch real user history
            }

            # Perform risk analysis
            print("\n[Risk Analysis]")
            risk_analysis = await risk_agent.analyze_transaction(transaction_data)

            # NEW LOGIC: Respect demo status from risk_agent
            if risk_analysis.get('status') == 'revoked':
                print(
                    f"\n🚫 {risk_analysis.get('message', 'PayPal agent revoked due to high risk.')}")
                return None
            elif risk_analysis.get('status') == 'allowed':
                print(
                    f"\n[DEMO] {risk_analysis.get('message', 'High risk detected, but payment allowed for demonstration.')}")
                # Only call with risk_rejected=False
                print(f"[DEBUG] Calling process_payment with risk_rejected=False")
                payment_result = await paypal_agent.process_payment(transaction_data, risk_rejected=False)
                # If payment_result indicates revoked, block
                if payment_result.get('status') == 'revoked':
                    print(
                        f"\n🚫 {payment_result.get('message', 'PayPal agent revoked due to high risk.')}")
                    return None
                # Otherwise, continue as normal (rest of the function)
            elif risk_analysis['risk_level'] in ['high', 'critical']:
                print("\n⚠️ High Risk Transaction Detected!")
                print(f"Risk Level: {risk_analysis['risk_level']}")
                print("\nRisk Factors:")
                for factor, level in risk_analysis['risk_factors'].items():
                    print(f"- {factor}: {level}")
                print("\nRecommendations:")
                for rec in risk_analysis['recommendations']:
                    print(f"- {rec}")
                # Automate the high-risk decision based on __default__ value
                auto_choice = read_demo_tracker_main()
                print(
                    f"[DEBUG] Auto high-risk decision based on __default__: {'y' if auto_choice else 'n'}")
                if auto_choice:
                    print(
                        f"[DEBUG] Calling process_payment with risk_rejected=False (auto accepted risk)")
                    payment_result = await paypal_agent.process_payment(transaction_data, risk_rejected=False)
                    if payment_result.get('status') == 'revoked':
                        print(
                            f"\n🚫 {payment_result.get('message', 'PayPal agent revoked due to high risk.')}")
                        return None
                    # Otherwise, continue as normal (rest of the function)
                else:
                    print(
                        f"[DEBUG] Calling process_payment with risk_rejected=True (auto rejected risk)")
                    revoke_result = await paypal_agent.process_payment(transaction_data, risk_rejected=True)
                    if revoke_result.get('revoked'):
                        print(
                            f"\n🚫 {revoke_result.get('error', 'PayPal agent revoked due to high risk.')}")
                    else:
                        print(
                            "\n🚫 Transaction blocked due to high risk. PayPal agent revoked.")
                    return None

            # Initialize Promotions agent
            promotions_agent = await self.agents.promotions_agent()
            await promotions_agent.initialize()

            # Get all available promotions
            available_promotions = []

            # 1. Get personalized discount
            shopping_history = [
                {
                    'amount': product_details['price'],
                    'category': product_details.get('category', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                }
            ]
            personal_discount = await promotions_agent.create_personalized_discount(
                self.user_id,
                shopping_history
            )
            if personal_discount:
                available_promotions.append({
                    'type': 'personal',
                    'name': 'Personal Discount',
                    'discount_percentage': personal_discount['discount_percentage'],
                    'minimum_purchase': personal_discount['minimum_purchase'],
                    'valid_until': personal_discount['valid_until']
                })

            # 2. Get active campaign promotions
            campaign_data = {
                'name': 'Current Campaigns',
                'description': 'Check active campaigns',
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(days=30)).isoformat()
            }
            campaign = await promotions_agent.create_promotion_campaign(campaign_data)
            if campaign:
                available_promotions.append({
                    'type': 'campaign',
                    'name': campaign['name'],
                    'discount_percentage': campaign.get('discount_value', 0),
                    'minimum_purchase': campaign.get('conditions', {}).get('minimum_purchase', 0),
                    'valid_until': campaign['end_date']
                })

            # Display available promotions
            if available_promotions:
                print("\n[Available Promotions]")
                for idx, promo in enumerate(available_promotions, 1):
                    print(f"\n{idx}. {promo['name']}")
                    print(f"   Discount: {promo['discount_percentage']}%")
                    print(f"   Minimum Purchase: ${promo['minimum_purchase']}")
                    print(f"   Valid Until: {promo['valid_until']}")

                # Let user select a promotion
                while True:
                    try:
                        selection = input(
                            "\nSelect a promotion number (or 0 to skip): ")
                        if selection == '0':
                            print("\nNo promotion selected.")
                            break

                        idx = int(selection) - 1
                        if 0 <= idx < len(available_promotions):
                            selected_promotion = available_promotions[idx]
                            original_price = float(product_details['price'])

                            # Check minimum purchase requirement
                            if original_price >= selected_promotion['minimum_purchase']:
                                # Apply the selected promotion
                                discount_amount = original_price * \
                                    (selected_promotion['discount_percentage'] / 100)
                                discounted_price = original_price - discount_amount

                                # Update product details with discount
                                product_details['original_price'] = original_price
                                product_details['price'] = discounted_price
                                product_details['applied_promotion'] = selected_promotion

                                print(
                                    f"\nApplied {selected_promotion['name']}")
                                print(f"Original Price: ${original_price:.2f}")
                                print(
                                    f"Discount Amount: ${discount_amount:.2f}")
                                print(f"Final Price: ${discounted_price:.2f}")
                                break
                            else:
                                print(
                                    f"\nMinimum purchase requirement (${selected_promotion['minimum_purchase']}) not met.")
                                continue
                        else:
                            print("\nInvalid selection. Please try again.")
                    except ValueError:
                        print("\nPlease enter a valid number.")
            else:
                print("\nNo promotions available at this time.")

            # Monitor PayPal agent's activities
            is_safe = await risk_agent.monitor_aztp_agent(
                agent_connection=paypal_agent.aztp.connection,
                action="create_payment",
                details={
                    "amount": float(str(product_details['price']).replace('$', '')),
                    "payee_email": customer_email,
                    "transaction_id": transaction_data['transaction_id']
                }
            )

            if not is_safe:
                print("\n❌ Payment processing blocked due to suspicious activity")
                return None

            # Get access token using the payment tool
            access_token = await paypal_agent.payment_tool.get_access_token()

            # Create PayPal order with promotion information in description
            description = product_details.get('description', '')
            if product_details.get('applied_promotion'):
                promo = product_details['applied_promotion']
                description += f"\nApplied Promotion: {promo['name']} ({promo['discount_percentage']}% off)"

            order_data = await paypal_agent.create_payment_order(
                amount=product_details['price'],
                currency="USD",
                description=description,
                payee_email=customer_email
            )

            print("\n[PayPal Order Created]")
            if product_details.get('applied_promotion'):
                promo = product_details['applied_promotion']
                print(f"\nPromotion Applied: {promo['name']}")
                print(
                    f"Original Price: ${product_details['original_price']:.2f}")
                print(f"Final Price: ${product_details['price']:.2f}")
                print(
                    f"You Save: ${product_details['original_price'] - product_details['price']:.2f}")
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
                        capture_result = await paypal_agent.capture_payment(order_data['id'])
                        print("\n[PayPal Payment Capture]")
                        print(json.dumps(capture_result, indent=2))

                        # Check if there was an error with the capture
                        if isinstance(capture_result, dict) and "error" in capture_result:
                            print(
                                "\nPayment capture failed. The order may need to be approved first.")
                            print(f"Error: {capture_result.get('error')}")
                            print(f"Status: {capture_result.get('status')}")
                        else:
                            print("\nPayment captured successfully!")
                            set_demo_tracker_default_false()
                else:
                    print("\nPayment will need to be captured after approval.")
            else:
                print("\nNo approval URL found. Cannot proceed with payment.")

            return order_data

        except Exception as e:
            print(f"\nError processing payment: {str(e)}")
            return None

    async def analyze_user_shopping_history(self, user_id: str, history: List[Dict[str, Any]] = None):
        """
        Analyze a user's shopping history for insights and personalized recommendations

        Args:
            user_id: The user's identifier (email address)
            history: Optional shopping history, if not provided uses paymentdetail.json

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Load payment history from paymentdetail.json
            project_root = os.path.dirname(os.path.abspath(__file__))
            payment_json_path = os.path.join(
                project_root, 'paymentdetail.json')

            user_payment_history = []
            if os.path.exists(payment_json_path):
                with open(payment_json_path, 'r') as f:
                    payment_data = json.load(f)

                    # Process each payment record
                    for record in payment_data:
                        # Only process completed captures
                        if record.get('action') == 'capture_payment' and \
                           isinstance(record.get('capture_result'), dict) and \
                           record['capture_result'].get('status') == 'COMPLETED':

                            capture_result = record['capture_result']

                            # Check if this payment is for the current user
                            payer_email = capture_result.get(
                                'payer', {}).get('email_address')
                            if payer_email == user_id:
                                # Extract payment details
                                for unit in capture_result.get('purchase_units', []):
                                    for capture in unit.get('payments', {}).get('captures', []):
                                        payment_info = {
                                            'amount': float(capture.get('amount', {}).get('value', 0)),
                                            'currency': capture.get('amount', {}).get('currency_code'),
                                            'timestamp': capture.get('create_time'),
                                            'transaction_id': capture.get('id'),
                                            'status': capture.get('status')
                                        }
                                        user_payment_history.append(
                                            payment_info)

            # If no payment history found and no history provided, use sample data
            if not user_payment_history and not history:
                print("\nNo payment history found, using sample data...")
                user_payment_history = [
                    {
                        'amount': 100.0,
                        'currency': 'USD',
                        'timestamp': '2024-01-01T10:00:00Z',
                        'transaction_id': 'SAMPLE1',
                        'status': 'COMPLETED'
                    },
                    {
                        'amount': 50.0,
                        'currency': 'USD',
                        'timestamp': '2024-02-01T15:30:00Z',
                        'transaction_id': 'SAMPLE2',
                        'status': 'COMPLETED'
                    }
                ]
            elif history:
                user_payment_history.extend(history)

            # Sort history by timestamp
            user_payment_history.sort(key=lambda x: x.get('timestamp', ''))

            # Initialize promotions_agent before use
            promotions_agent = await self.agents.promotions_agent()
            await promotions_agent.initialize()

            # Analyze shopping history
            analysis_results = await promotions_agent.analyze_shopping_history(
                user_id,
                user_payment_history
            )

            # Add additional insights
            analysis_results.update({
                'total_transactions': len(user_payment_history),
                'payment_history_source': 'PayPal payment records' if user_payment_history else 'Sample data',
                'date_range': {
                    'first_transaction': user_payment_history[0].get('timestamp') if user_payment_history else None,
                    'last_transaction': user_payment_history[-1].get('timestamp') if user_payment_history else None
                }
            })

            print("\n[Shopping History Analysis]")
            print(json.dumps(analysis_results, indent=2))

            return analysis_results

        except Exception as e:
            print(f"\nError analyzing shopping history: {str(e)}")
            return None

    async def create_promotion_campaign(self, campaign_data: Dict[str, Any]):
        """
        Create a new promotional campaign

        Args:
            campaign_data: Dictionary containing campaign details

        Returns:
            Dictionary containing campaign information
        """
        try:
            # Initialize Promotions agent
            promotions_agent = await self.agents.promotions_agent()
            await promotions_agent.initialize()

            # Create campaign
            campaign = await promotions_agent.create_promotion_campaign(campaign_data)

            print("\n[New Promotion Campaign Created]")
            print(json.dumps(campaign, indent=2))

            return campaign

        except Exception as e:
            print(f"\nError creating promotion campaign: {str(e)}")
            return None

    async def process_refund_request(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund request for an order

        Args:
            order_details: Dictionary containing order information including transaction ID and refund reason

        Returns:
            Dictionary containing refund confirmation details
        """
        print("\n=== Processing Refund Request ===")
        try:
            # Initialize customer support agent
            customer_support_agent = await self.agents.customer_support_agent()
            await customer_support_agent.initialize()

            # Process the refund
            refund_confirmation = await customer_support_agent.process_refund(order_details)
            print("✅ Refund processed successfully")

            return refund_confirmation

        except Exception as e:
            error_msg = f"Failed to process refund: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def get_faq_answer(self, query: str) -> Dict[str, Any]:
        """
        Get answer for a FAQ query

        Args:
            query: The customer's question

        Returns:
            Dictionary containing FAQ response
        """
        print("\n=== Processing FAQ Query ===")
        try:
            # Initialize customer support agent
            customer_support_agent = await self.agents.customer_support_agent()
            await customer_support_agent.initialize()

            # Get FAQ response
            faq_response = await customer_support_agent.get_faq_response(query)
            print("✅ FAQ response retrieved successfully")

            return faq_response

        except Exception as e:
            error_msg = f"Failed to get FAQ response: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def create_support_ticket(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a support ticket for customer issue

        Args:
            issue_details: Dictionary containing issue information

        Returns:
            Dictionary containing ticket details
        """
        print("\n=== Creating Support Ticket ===")
        try:
            # Initialize customer support agent
            customer_support_agent = await self.agents.customer_support_agent()
            await customer_support_agent.initialize()

            # Create support ticket
            ticket = await customer_support_agent.create_support_ticket(issue_details)
            print("✅ Support ticket created successfully")

            return ticket

        except Exception as e:
            error_msg = f"Failed to create support ticket: {str(e)}"
            print(f"❌ {error_msg}")
            raise


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


def read_demo_tracker_main():
    tracker_path = os.path.join(os.path.dirname(
        __file__), 'risk_demo_tracker.json')
    if not os.path.exists(tracker_path):
        return True  # Default to True if file missing
    try:
        with open(tracker_path, 'r') as f:
            data = json.load(f)
            return data.get('__default__', True)
    except Exception:
        return True


def set_demo_tracker_default_false():
    tracker_path = os.path.join(os.path.dirname(
        __file__), 'risk_demo_tracker.json')
    try:
        if os.path.exists(tracker_path):
            with open(tracker_path, 'r') as f:
                data = json.load(f)
        else:
            data = {}
        data['__default__'] = False
        with open(tracker_path, 'w') as f:
            json.dump(data, f, indent=2)
        print("[DEBUG] Set __default__ to false after successful payment capture.")
    except Exception as e:
        print(f"[DEBUG] Failed to update __default__ in tracker: {e}")


def test_write_demo_tracker():
    tracker_path = os.path.join(os.path.dirname(
        __file__), 'risk_demo_tracker.json')
    try:
        data = {'__default__': True}
        with open(tracker_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[TEST] Successfully wrote to {tracker_path}: {data}")
    except Exception as e:
        print(f"[TEST] Failed to write to {tracker_path}: {e}")


def main():
    """
    Main function to run the ShopperAI application
    """
    async def run_async():
        print("Welcome to ShopperAI!")
        print("Available actions:")
        print("1. Search and buy products")
        print("2. View your shopping history and personalized discounts")
        print("3. View active promotions")
        print("4. Customer Support")
        print("5. MaliciousAgent tries to communicate with PayPalAgent")
        print("6. MarketAgent tries to communicate with PayPalAgent")
        print("7. Exit")

        while True:
            try:
                choice = input("\nPlease select an action (1-7): ")

                if choice == "1":
                    await search_and_buy_products()
                elif choice == "2":
                    # Get user email
                    user_email = input("\nPlease enter your email address: ")
                    shopper = ShopperAI("", {})  # Initialize with empty query

                    # Analyze shopping history
                    print("\nAnalyzing your shopping history...")
                    analysis = await shopper.analyze_user_shopping_history(user_email)

                    if analysis:
                        # Check for available personalized discounts
                        promotions_agent = await shopper.agents.promotions_agent()
                        await promotions_agent.initialize()

                        # Use the analyzed history to create a personalized discount
                        if analysis.get('total_spent'):
                            history = [
                                {
                                    'amount': analysis['total_spent'],
                                    'timestamp': analysis['date_range']['last_transaction']
                                }
                            ]
                            discount = await promotions_agent.create_personalized_discount(user_email, history)

                            if discount:
                                print("\n[Your Personalized Discount]")
                                print(
                                    f"Discount: {discount['discount_percentage']}%")
                                print(f"Valid from: {discount['valid_from']}")
                                print(
                                    f"Valid until: {discount['valid_until']}")
                                print(
                                    f"Minimum purchase: ${discount['minimum_purchase']}")

                elif choice == "3":
                    # Initialize ShopperAI with empty query for accessing agents
                    shopper = ShopperAI("", {})

                    # Create a sample promotion campaign
                    campaign_data = {
                        'name': 'Summer Sale',
                        'description': 'Special discounts on summer items',
                        'start_date': datetime.now().isoformat(),
                        'end_date': (datetime.now() + timedelta(days=30)).isoformat(),
                        'discount_type': 'percentage',
                        'discount_value': 15,
                        'conditions': {
                            'minimum_purchase': 100,
                            'categories': ['summer', 'outdoor']
                        }
                    }

                    # Create the campaign
                    campaign = await shopper.create_promotion_campaign(campaign_data)

                    if campaign:
                        print("\n[Active Promotion Campaigns]")
                        print(json.dumps(campaign, indent=2))

                elif choice == "4":
                    # Customer Support Menu
                    print("\nCustomer Support Options:")
                    print("1. Request Refund")
                    print("2. FAQ Help")
                    print("3. Create Support Ticket")
                    print("4. Back to Main Menu")

                    while True:
                        support_choice = input(
                            "\nPlease select an option (1-4) or type your question directly: ")

                        if support_choice == "4":
                            break

                        # Initialize ShopperAI for customer support
                        shopper = ShopperAI("", {})

                        if support_choice == "1":
                            # Get refund details
                            transaction_id = input("\nEnter transaction ID: ")
                            reason = input("Enter refund reason: ")
                            amount = float(input("Enter refund amount: "))

                            refund_details = {
                                "transaction_id": transaction_id,
                                "reason": reason,
                                "amount": amount
                            }

                            try:
                                refund_result = await shopper.process_refund_request(refund_details)
                                print("\n[Refund Request Result]")
                                print(json.dumps(refund_result, indent=2))
                            except Exception as e:
                                print(f"\nError processing refund: {str(e)}")

                        elif support_choice == "2":
                            # Get FAQ query
                            query = input("\nWhat's your question? ")

                            try:
                                faq_result = await shopper.get_faq_answer(query)
                                print("\n[FAQ Response]")
                                print(json.dumps(faq_result, indent=2))
                            except Exception as e:
                                print(
                                    f"\nError getting FAQ response: {str(e)}")

                        elif support_choice == "3":
                            # Get ticket details
                            customer_id = input("\nEnter your customer ID: ")
                            issue_type = input(
                                "Enter issue type (Technical/Billing/General): ")
                            priority = input(
                                "Enter priority (Low/Medium/High): ")
                            description = input("Enter issue description: ")

                            ticket_details = {
                                "customer_id": customer_id,
                                "issue_type": issue_type,
                                "priority": priority,
                                "description": description
                            }

                            try:
                                ticket_result = await shopper.create_support_ticket(ticket_details)
                                print("\n[Support Ticket Created]")
                                print(json.dumps(ticket_result, indent=2))
                            except Exception as e:
                                print(
                                    f"\nError creating support ticket: {str(e)}")

                        else:
                            # Check if the query is a product search request
                            product_search_keywords = [
                                'buy', 'purchase', 'find', 'search', 'looking for']
                            is_product_search = any(
                                keyword in support_choice.lower() for keyword in product_search_keywords)

                            if is_product_search:
                                print(
                                    "\nIt looks like you're trying to search for a product. Let me help you with that.")

                                # Extract price and rating criteria if mentioned
                                import re

                                # Try to extract price
                                price_match = re.search(
                                    r'(\$?\d+(?:\.\d{2})?)', support_choice)
                                max_price = float(price_match.group(1).replace(
                                    '$', '')) if price_match else None

                                # Try to extract rating
                                rating_match = re.search(
                                    r'rating.*?(\d+(?:\.\d)?)', support_choice)
                                min_rating = float(rating_match.group(
                                    1)) if rating_match else None

                                # Extract the product query by removing criteria mentions
                                product_query = support_choice
                                if max_price:
                                    product_query = re.sub(
                                        r'\$?\d+(?:\.\d{2})?', '', product_query)
                                if min_rating:
                                    product_query = re.sub(
                                        r'rating.*?\d+(?:\.\d)?', '', product_query)

                                # Clean up the query
                                product_query = re.sub(
                                    r'\b(price|cost|under|above|rating|stars?)\b', '', product_query)
                                product_query = ' '.join(product_query.split())

                                # If criteria not found in query, ask user
                                if max_price is None:
                                    while True:
                                        try:
                                            max_price_input = input(
                                                "What's your maximum budget (in USD)? ")
                                            max_price = float(max_price_input)
                                            break
                                        except ValueError:
                                            print(
                                                "Please enter a valid number.")

                                if min_rating is None:
                                    while True:
                                        try:
                                            min_rating_input = input(
                                                "What's your minimum rating requirement (0-5)? ")
                                            min_rating = float(
                                                min_rating_input)
                                            if 0 <= min_rating <= 5:
                                                break
                                            else:
                                                print(
                                                    "Rating must be between 0 and 5.")
                                        except ValueError:
                                            print(
                                                "Please enter a valid number.")

                                # Initialize ShopperAI with search criteria
                                search_shopper = ShopperAI(
                                    product_query,
                                    {"max_price": max_price,
                                        "min_rating": min_rating}
                                )

                                # Run research phase
                                print("\nSearching for products...")
                                try:
                                    research_results = await search_shopper.run_research()

                                    # Extract and display products
                                    if isinstance(research_results, dict):
                                        best = research_results.get(
                                            "best_match")
                                        if best:
                                            print("\nBest Match:")
                                            print(
                                                f"Name: {best.get('name', best.get('title', ''))}")
                                            print(
                                                f"Price: {best.get('price', '')}")
                                            print(
                                                f"Rating: {best.get('rating', '')}")

                                            # Comment out price comparison functionality for now
                                            """
                                            # Ask if user wants to compare prices
                                            compare_prices = input(
                                                "\nWould you like to compare prices for similar products? (y/n): ").lower()
                                            if compare_prices == 'y':
                                                price_results = await search_shopper.run_price_comparison([best])
                                                if price_results and isinstance(price_results, dict):
                                                    print("\nPrice Comparison Results:")
                                                    print(json.dumps(price_results, indent=2))
                                            """

                                            print(
                                                "\nYou can proceed with the purchase by selecting option 1 from the main menu.")

                                except Exception as e:
                                    print(
                                        f"\nError searching for products: {str(e)}")
                                    # Fallback to FAQ response
                                    try:
                                        faq_result = await shopper.get_faq_answer(support_choice)
                                        print("\n[FAQ Response]")
                                        print(json.dumps(faq_result, indent=2))
                                    except Exception as faq_error:
                                        print(
                                            f"\nError getting FAQ response: {str(faq_error)}")

                            else:
                                # Handle as regular FAQ query
                                try:
                                    faq_result = await shopper.get_faq_answer(support_choice)
                                    print("\n[FAQ Response]")
                                    print(json.dumps(faq_result, indent=2))
                                except Exception as e:
                                    print(
                                        f"\nError getting FAQ response: {str(e)}")
                                    print(
                                        "\nPlease select a valid option (1-4) or ask a question.")

                elif choice == "5":
                    malicious_agent = MaliciousAgent()
                    paypal_agent = PayPalAgent()
                    aztp_id = getattr(
                        getattr(malicious_agent, 'aztp', None), 'aztp_id', None)
                    result = await paypal_agent.secure_communicate(aztp_id, data={}, action="payment_processing")
                    print("MaliciousAgent result:", result)
                elif choice == "6":
                    market_agent = MarketAgent()
                    paypal_agent = PayPalAgent()
                    await market_agent.initialize()
                    aztp_id = getattr(
                        getattr(market_agent, 'aztp', None), 'aztp_id', None)
                    result = await paypal_agent.secure_communicate(aztp_id, data={}, action="payment_processing")
                    print("MarketAgent result:", result)
                elif choice == "7":
                    print("\nThank you for using ShopperAI!")
                    break
                else:
                    print("\nInvalid choice. Please select 1-7.")

            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try again.")

    # Run the async main function
    asyncio.run(run_async())


async def search_and_buy_products():
    """Handle the product search and purchase flow"""
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
                    "name": best.get('name', best.get('title', 'Unknown Product')),
                    "price": best.get('price', '0.00'),
                    "quantity": 1,
                    "description": best.get('description', ''),
                    "payee_email": payee_email
                }

                # Process the order with payment
                payment_result = await shopper.process_order_with_payment(product_details, payee_email)

                # Only show real PayPal order ID and approval URL
                if isinstance(payment_result, dict):
                    paypal_order_id = payment_result.get("id")

                    # Get approval URL from links
                    approval_url = None
                    for link in payment_result.get('links', []):
                        if link.get('rel') == 'approve':
                            approval_url = link.get('href')
                            break

                    if paypal_order_id:
                        print(f"\nOrder ID: {paypal_order_id}")
                    if approval_url:
                        print(
                            f"\nPlease complete your payment at the following PayPal URL:\n{approval_url}")
                        print("\nInstructions:")
                        print("1. Open the above URL in your browser.")
                        print("2. Log in with your PayPal sandbox buyer account.")
                        print("3. Approve the payment to complete your order.")

                    # Wait for user to complete payment
                    input(
                        "\nPress Enter after completing the payment in your browser...")

                    # Capture the payment
                    if paypal_order_id:
                        try:
                            # Initialize a new PayPal agent for capture
                            paypal_agent = await shopper.agents.paypal_agent()
                            await paypal_agent.initialize()
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
                        except Exception as e:
                            print(f"\nError capturing payment: {str(e)}")
                else:
                    print(f"\nOrder processing failed: {payment_result}")
            except Exception as e:
                print(f"\nError processing payment: {str(e)}")

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

        # Ask user to select a product for purchase
        while True:
            try:
                selection = input(
                    "\nEnter the number of the product you want to purchase (1-{}) or 0 to cancel: ".format(len(products)))
                if selection == '0':
                    break

                idx = int(selection) - 1
                if 0 <= idx < len(products):
                    selected_product = products[idx]

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
                                "name": selected_product.get('name', selected_product.get('title', 'Unknown Product')),
                                "price": selected_product.get('price', '0.00'),
                                "quantity": 1,
                                "description": selected_product.get('description', ''),
                                "payee_email": payee_email
                            }

                            # Process the order with payment
                            payment_result = await shopper.process_order_with_payment(product_details, payee_email)

                            # Only show real PayPal order ID and approval URL
                            if isinstance(payment_result, dict):
                                paypal_order_id = payment_result.get("id")

                                # Get approval URL from links
                                approval_url = None
                                for link in payment_result.get('links', []):
                                    if link.get('rel') == 'approve':
                                        approval_url = link.get('href')
                                        break

                                if paypal_order_id:
                                    print(f"\nOrder ID: {paypal_order_id}")
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
                                    try:
                                        # Initialize a new PayPal agent for capture
                                        paypal_agent = await shopper.agents.paypal_agent()
                                        await paypal_agent.initialize()
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
                                    except Exception as e:
                                        print(
                                            f"\nError capturing payment: {str(e)}")
                            else:
                                print(
                                    f"\nOrder processing failed: {payment_result}")
                        except Exception as e:
                            print(f"\nError processing payment: {str(e)}")
                    break
                else:
                    print("\nInvalid selection. Please try again.")
            except ValueError:
                print("\nPlease enter a valid number.")

    # After payment processing
    read_latest_payment_detail()
    print("\nThank you for using ShopperAI!")


if __name__ == "__main__":
    # test_write_demo_tracker()
    main()
