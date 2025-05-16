"""
PayPal Agent for ShopperAI
Handles PayPal payment processing and transaction management.
"""
from typing import Dict, Any, Optional, List
from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
import os
from pydantic import Field, ConfigDict, BaseModel
import asyncio
import uuid
import datetime
import logging
import requests
from base64 import b64encode
from tools.payment_tool import PayPalPaymentTool
import json

# Import PayPal toolkit
try:
    from paypal_agent_toolkit.crewai.toolkit import PayPalToolkit
    from paypal_agent_toolkit.configuration import Configuration, Context
    PAYPAL_AVAILABLE = True
except ImportError:
    PAYPAL_AVAILABLE = False
    logging.warning(
        "PayPal Agent Toolkit not available. PayPal functionality will be limited.")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PayPalAgent(Agent):
    """Agent responsible for PayPal payment processing"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    paymentAgent: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    paypal_toolkit: Optional[Any] = Field(default=None, exclude=True)
    payment_tool: PayPalPaymentTool = Field(
        default_factory=PayPalPaymentTool, exclude=True)
    payment_tool_aztp_id: str = Field(default="", exclude=True)

    def __init__(self):
        """Initialize the PayPal agent with necessary tools"""
        # Initialize the agent with CrewAI first
        super().__init__(
            role='PayPal Payment Agent',
            goal='Process payments and manage PayPal transactions securely',
            backstory="""You are an expert PayPal payment processing agent with years of experience in 
            handling secure transactions. You ensure payments are processed correctly and provide clear 
            transaction confirmations with all necessary details.""",
            verbose=True
        )

        # Initialize PayPal toolkit if available
        self.paypal_toolkit = None
        if PAYPAL_AVAILABLE:
            try:
                self.paypal_toolkit = PayPalToolkit(
                    client_id=os.getenv(
                        "PAYPAL_CLIENT_ID", "AfS3ByWWWrF4ZQlGYHQxXQ9nVzXZu5Js5wOs0qXBb_Cta6iVVyTDkqH2D2f970dubOUOofFrGC6DR0R4"),
                    secret=os.getenv(
                        "PAYPAL_SECRET", "EKuCuoppyKuLbTq25joW6T5Mn8IAU_kJ46PEQc85sR351Z2S_xFwAoJIlZx22O1gx91n8CysiszzzgZU"),
                    configuration=Configuration(
                        actions={
                            "orders": {
                                "create": True,
                                "get": True,
                                "capture": True,
                            },
                            "invoices": {
                                "create": True,
                                "get": True,
                                "send": True,
                            },
                            "subscriptions": {
                                "create": True,
                                "get": True,
                                "cancel": True,
                            }
                        },
                        # Use sandbox for testing
                        context=Context(sandbox=True)
                    )
                )
                logger.info("PayPal toolkit initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PayPal toolkit: {str(e)}")
                self.paypal_toolkit = None

        # Initialize the agent with PayPal tools if available
        tools = []
        if self.paypal_toolkit:
            tools = self.paypal_toolkit.get_tools()
            logger.info(f"Added {len(tools)} PayPal tools to agent")
            # Update the agent's tools
            self.tools = tools

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp_id = ""  # Initialize as empty string

        # Initialize payment tool and store its AZTP ID
        if not hasattr(self, 'payment_tool') or self.payment_tool is None:
            self.payment_tool = PayPalPaymentTool()

        # Store payment tool's AZTP ID if available
        if hasattr(self.payment_tool, 'aztp_id'):
            self.payment_tool_aztp_id = self.payment_tool.aztp_id

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        print(f"1. Issuing identity for agent: PayPal Agent")

        # Create array of tool IDs to link
        tool_ids = []
        if self.payment_tool_aztp_id:
            tool_ids.append(self.payment_tool_aztp_id)

        self.paymentAgent = await self.aztpClient.secure_connect(
            self,
            "paypal-agent",
            {
                "isGlobalIdentity": False,
                "linkTo": tool_ids
            }
        )
        print("AZTP ID:", self.paymentAgent.identity.aztp_id)

        print(f"\n2. Verifying identity for agent: PayPal Agent")
        self.is_valid = await self.aztpClient.verify_identity(
            self.paymentAgent
        )
        print("Verified Agent:", self.is_valid)

        if self.is_valid:
            if self.paymentAgent and hasattr(self.paymentAgent, 'identity'):
                self.aztp_id = self.paymentAgent.identity.aztp_id
                print(f"✅ Extracted AZTP ID: {self.aztp_id}")
                if self.payment_tool_aztp_id:
                    print(
                        f"✅ Linked to Payment Tool with AZTP ID: {self.payment_tool_aztp_id}")
        else:
            raise ValueError(
                "Failed to verify identity for agent: PayPal Agent")

    def _log_payment_detail(self, data):
        # Always use the project root (shopping) for paymentdetail.json
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))
        payment_json_path = os.path.join(project_root, 'paymentdetail.json')
        # Read existing data
        if os.path.exists(payment_json_path):
            try:
                with open(payment_json_path, 'r') as f:
                    content = f.read().strip()
                    existing = json.loads(content) if content else []
            except Exception:
                existing = []
        else:
            existing = []
        # Append new data
        existing.append(data)
        # Write back
        with open(payment_json_path, 'w') as f:
            json.dump(existing, f, indent=2)

    def create_payment_order(self, amount, currency="USD", description="", payee_email=None):
        access_token = self.payment_tool.get_access_token()
        order_response = self.payment_tool.create_order(
            access_token, amount, currency, description, payee_email)
        approval_url = None
        for link in order_response.get('links', []):
            if link.get('rel') == 'approve':
                approval_url = link.get('href')
                break
        result = {
            'paypal_order_id': order_response.get('id'),
            'approval_url': approval_url,
            'raw_response': order_response
        }
        self._log_payment_detail({'action': 'create_order', **result})
        return result

    def capture_payment(self, order_id):
        access_token = self.payment_tool.get_access_token()
        capture_response = self.payment_tool.capture_payment(
            access_token, order_id)

        # Check if there was an error with the capture
        if isinstance(capture_response, dict) and "error" in capture_response:
            error_message = capture_response.get("error", "Unknown error")
            status = capture_response.get("status", "Unknown")

            # Get the approval URL from paymentdetail.json
            approval_url = None
            try:
                with open('shopping/paymentdetail.json', 'r') as f:
                    payment_details = json.load(f)
                    for detail in payment_details:
                        if detail.get('paypal_order_id') == order_id:
                            approval_url = detail.get('approval_url')
                            break
            except Exception as e:
                print(f"Error reading payment details: {str(e)}")

            result = {
                'error': error_message,
                'status': status,
                'paypal_order_id': order_id
            }

            if approval_url:
                result['approval_url'] = approval_url
                print(
                    f"\nOrder needs to be approved first. Please use this URL to approve the payment:")
                print(f"{approval_url}")
                print("\nAfter approval, try capturing the payment again.")

            self._log_payment_detail(
                {'action': 'capture_payment_error', **result})
            return result

        result = {
            'capture_result': capture_response,
            'paypal_order_id': order_id
        }
        self._log_payment_detail({'action': 'capture_payment', **result})
        return result

    def display_payment_success(self, capture_result: Dict[str, Any], order_details: Dict[str, Any]) -> None:
        """
        Display a formatted payment success message

        Args:
            capture_result: The result of the payment capture
            order_details: The details of the order
        """
        if not capture_result or not order_details:
            logger.warning(
                "Cannot display payment success: Missing capture result or order details")
            return

        # Extract relevant information
        order_id = capture_result.get('id', 'Unknown')
        status = capture_result.get('status', 'Unknown')

        # Get purchase unit details
        purchase_units = capture_result.get('purchase_units', [])
        if not purchase_units:
            logger.warning(
                "Cannot display payment success: No purchase units found")
            return

        purchase_unit = purchase_units[0]
        amount = purchase_unit.get('amount', {})
        currency = amount.get('currency_code', 'USD')
        value = amount.get('value', '0.00')

        # Get payment source details
        payment_source = capture_result.get('payment_source', {})
        card_details = payment_source.get('card', {})
        last_digits = card_details.get('last_digits', '****')

        # Get current date
        current_date = datetime.datetime.now().strftime("%B %d, %Y")

        # Get product details from order details
        product_name = "Unknown Product"
        if purchase_unit.get('description'):
            product_name = purchase_unit.get('description')

        # Display formatted message
        success_message = f"""
==================================================
Payment processed successfully!
==================================================
Order details: **Payment Capture Confirmation**

We are pleased to inform you that your payment has been successfully captured. Below are the transaction details:

- **Order ID:** {order_id}
- **Product Name:** {product_name}
- **Price:** ${value} {currency}
- **Quantity:** 1
- **Total Amount:** ${value} {currency}

**Transaction Details:**
- **Transaction ID:** {order_id}
- **Order Status:** {status}
- **Payment Method:** Credit Card (ending in {last_digits})
- **Transaction Date:** {current_date}
==================================================
"""
        logger.info(success_message)
        return success_message

    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Get details of a PayPal order

        Args:
            order_id: The PayPal order ID

        Returns:
            Order details
        """
        if not self.paypal_toolkit:
            logger.error("PayPal toolkit not available")
            return {
                "error": "PayPal toolkit not available",
                "status": "Failed"
            }

        try:
            # Get order details using PayPal toolkit
            result = self.paypal_toolkit.get_order(order_id)

            logger.info(f"Retrieved PayPal order details: {result}")
            return {
                "paypal_order_id": order_id,
                "transaction_id": result.get("id", order_id),
                "status": result.get("status", ""),
                "amount": result.get("amount", {}).get("value", ""),
                "currency": result.get("amount", {}).get("currency_code", ""),
                "create_time": result.get("create_time", ""),
                "update_time": result.get("update_time", "")
            }
        except Exception as e:
            logger.error(f"Error getting PayPal order details: {str(e)}")
            return {
                "error": str(e),
                "status": "Failed"
            }

    def create_invoice(self, customer_email: str, amount: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a PayPal invoice

        Args:
            customer_email: Customer's email address
            amount: Total amount for the invoice
            items: List of items to include in the invoice

        Returns:
            Invoice details
        """
        if not self.paypal_toolkit:
            logger.error("PayPal toolkit not available")
            return {
                "error": "PayPal toolkit not available",
                "status": "Failed"
            }

        try:
            # Extract numeric amount from string (e.g., "$99.99" -> "99.99")
            numeric_amount = amount.replace("$", "").strip()

            # Create invoice using PayPal toolkit
            result = self.paypal_toolkit.create_invoice(
                customer_email=customer_email,
                amount=numeric_amount,
                items=items
            )

            logger.info(f"Created PayPal invoice: {result}")
            return {
                "invoice_id": result.get("id", ""),
                "status": "Created",
                "customer_email": customer_email,
                "amount": amount,
                "items": items
            }
        except Exception as e:
            logger.error(f"Error creating PayPal invoice: {str(e)}")
            return {
                "error": str(e),
                "status": "Failed"
            }

    def get_access_token_direct(self):
        client_id = os.getenv("PAYPAL_CLIENT_ID")
        client_secret = os.getenv("PAYPAL_SECRET")
        auth = b64encode(f"{client_id}:{client_secret}".encode(
            'utf-8')).decode('utf-8')
        url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise Exception(f"Failed to get access token: {response.text}")

    def create_order_direct(self, access_token, amount, currency="USD", description="Test Product", payee_email=None):
        url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        purchase_unit = {
            "amount": {
                "currency_code": currency,
                "value": amount
            },
            "description": description
        }
        if payee_email:
            purchase_unit["payee"] = {"email_address": payee_email}
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [purchase_unit],
            "application_context": {
                "return_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
                "shipping_preference": "NO_SHIPPING"
            }
        }
        response = requests.post(url, headers=headers, json=order_data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create order: {response.text}")

    def get_order_details_direct(self, access_token, order_id):
        url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get order details: {response.text}")

    def capture_payment_direct(self, access_token, order_id):
        url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to capture payment: {response.text}")

    def display_payment_success_direct(self, capture_result, order_details):
        if not capture_result or not order_details:
            return
        order_id = capture_result.get('id', 'Unknown')
        status = capture_result.get('status', 'Unknown')
        purchase_units = capture_result.get('purchase_units', [])
        if not purchase_units:
            return
        purchase_unit = purchase_units[0]
        amount = purchase_unit.get('amount', {})
        currency = amount.get('currency_code', 'USD')
        value = amount.get('value', '0.00')
        payment_source = capture_result.get('payment_source', {})
        card_details = payment_source.get('card', {})
        last_digits = card_details.get('last_digits', '****')
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        product_name = purchase_unit.get('description', 'Test Product')
        print("\n" + "="*50)
        print("Payment processed successfully!")
        print("="*50)
        print("Order details: **Payment Capture Confirmation**\n")
        print("We are pleased to inform you that your payment has been successfully captured. Below are the transaction details:\n")
        print(f"- **Order ID:** {order_id}")
        print(f"- **Product Name:** {product_name}")
        print(f"- **Price:** ${value} {currency}")
        print(f"- **Quantity:** 1")
        print(f"- **Total Amount:** ${value} {currency}\n")
        print("**Transaction Details:**")
        print(f"- **Transaction ID:** {order_id}")
        print(f"- **Order Status:** {status}")
        print(f"- **Payment Method:** Credit Card (ending in {last_digits})")
        print(f"- **Transaction Date:** {current_date}")
        print("="*50)
