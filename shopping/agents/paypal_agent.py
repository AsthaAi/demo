"""
PayPal Agent for ShopperAI
Handles PayPal payment processing and transaction management.
"""
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
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
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
from agents.risk_agent import write_demo_tracker

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


class AztpConnection(BaseModel):
    """AZTP connection state"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Optional[Aztp] = None
    connection: Optional[SecureConnection] = None
    aztp_id: str = ""
    is_valid: bool = False
    is_initialized: bool = False


class PayPalAgent(Agent):
    """Agent responsible for PayPal payment processing"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    aztp: AztpConnection = Field(default_factory=AztpConnection)
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    paypal_toolkit: Optional[Any] = Field(default=None, exclude=True)
    payment_tool: PayPalPaymentTool = Field(
        default_factory=PayPalPaymentTool, exclude=True)
    payment_tool_aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)
    risk_agent: Optional[Any] = Field(
        default=None, exclude=True)  # Will be set by ShopperAI

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

        # Initialize AZTP connection
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp = AztpConnection(
            client=Aztp(api_key=api_key)
        )
        self.iam_utils = IAMUtils()  # Initialize IAM utilities
        self.is_initialized = False

        # Initialize payment tool and store its AZTP ID
        if not hasattr(self, 'payment_tool') or self.payment_tool is None:
            self.payment_tool = PayPalPaymentTool()

        # Store payment tool's AZTP ID if available
        if hasattr(self.payment_tool, 'aztp_id'):
            self.payment_tool_aztp_id = self.payment_tool.aztp_id

    async def initialize(self):
        """Initialize the agent and its tools"""
        if not self.is_initialized:
            # Initialize payment tool first
            if hasattr(self.payment_tool, 'initialize'):
                await self.payment_tool.initialize()

            # Then initialize the agent's identity
            await self._initialize_identity()
            self.is_initialized = True
        return self

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        try:
            print(f"1. Issuing identity for agent: PayPal Agent")

            # Create array of tool IDs to link
            tool_ids = []
            if self.payment_tool_aztp_id:
                tool_ids.append(self.payment_tool_aztp_id)

            # Create payment agent identity without linkTo
            self.aztp.connection = await self.aztpClient.secure_connect(
                self,
                "paypal-agent",
                {
                    "isGlobalIdentity": False,
                    "trustLevel": "high",
                    "department": "Payment"
                }
            )

            # Link payment agent with payment tool identity
            print("\nLinking payment agent with payment tool identity...")
            for tool_id in tool_ids:
                try:
                    link_result = await self.aztpClient.link_identities(
                        self.aztp.connection.identity.aztp_id,
                        tool_id,
                        "linked"
                    )
                    print(
                        f"Successfully linked payment agent with tool ID: {tool_id}")
                    print(f"Link result: {link_result}")
                except Exception as e:
                    print(
                        f"Error linking payment agent with tool ID {tool_id}: {str(e)}")

            print("AZTP ID:", self.aztp.connection.identity.aztp_id)

            print(f"\n2. Verifying identity for agent: PayPal Agent")
            self.aztp.is_valid = await self.aztpClient.verify_identity(
                self.aztp.connection
            )
            print("Verified Agent:", self.aztp.is_valid)

            if self.aztp.is_valid:
                if self.aztp.connection and hasattr(self.aztp.connection, 'identity'):
                    self.aztp.aztp_id = self.aztp.connection.identity.aztp_id
                    print(f"✅ Extracted AZTP ID: {self.aztp.aztp_id}")
            else:
                raise ValueError(
                    "Failed to verify identity for agent: PayPal Agent\nAZTP-ID-E-001 - Identity has been revoked"
                )

            # Verify payment processing access before proceeding
            print(
                f"\n3. Verifying access permissions for PayPal Agent {self.aztp.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="payment_processing",
                policy_code="policy:a07507f6fe70",
                operation_name="Payment Processing"
            )

            print("\n✅ PayPal agent initialized successfully")

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to initialize payment agent: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution

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

    async def create_payment_order(self, amount, currency="USD", description="", payee_email=None, return_url=None, cancel_url=None):
        """Create a PayPal payment order"""
        if not self.is_initialized:
            await self.initialize()

        try:
            access_token = await self.payment_tool.get_access_token()
            order_data = await self.payment_tool.create_order(
                access_token=access_token,
                amount=amount,
                currency=currency,
                description=description,
                payee_email=payee_email,
                return_url=return_url,
                cancel_url=cancel_url
            )

            # Log the order creation
            self._log_payment_detail({
                "action": "create_order",
                "paypal_order_id": order_data.get("id"),
                "approval_url": order_data.get("approval_url"),
                "raw_response": order_data
            })

            return order_data
        except Exception as e:
            print(f"Error creating payment order: {str(e)}")
            raise

    async def capture_payment(self, order_id):
        """Capture a PayPal payment"""
        if not self.is_initialized:
            await self.initialize()

        try:
            access_token = await self.payment_tool.get_access_token()
            capture_data = await self.payment_tool.capture_payment(access_token, order_id)

            # Log the payment capture
            if isinstance(capture_data, dict):
                if "error" in capture_data:
                    # Log capture error
                    self._log_payment_detail({
                        "action": "capture_payment_error",
                        "error": capture_data.get("error"),
                        "status": capture_data.get("status"),
                        "paypal_order_id": order_id
                    })
                else:
                    # Log successful capture
                    self._log_payment_detail({
                        "action": "capture_payment",
                        "capture_result": capture_data,
                        "paypal_order_id": order_id
                    })

            return capture_data
        except Exception as e:
            print(f"Error capturing payment: {str(e)}")
            raise

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

    async def process_payment(self, transaction_data: Dict[str, Any], risk_rejected: bool = False) -> Dict[str, Any]:
        """Process a payment through PayPal"""
        try:
            # Add agent ID and risk rejection flag to transaction data
            transaction_data['paypal_agent_id'] = self.aztp.aztp_id
            transaction_data['risk_rejected'] = risk_rejected

            # If risk was rejected, check risk level first
            if risk_rejected:
                # Analyze transaction risk
                risk_analysis = await self.risk_agent.analyze_transaction(transaction_data)

                # If demo logic returns allowed or revoked, return it directly
                if risk_analysis.get('status') in ['allowed', 'revoked']:
                    return risk_analysis

                # If risk level is high/critical, revoke PayPal agent (legacy fallback)
                if risk_analysis['risk_level'] in ['high', 'critical']:
                    print(
                        f"\n🛑 User rejected high-risk transaction. Revoking PayPal agent...")
                    await self.risk_agent._revoke_agent_identity(
                        self.aztp.aztp_id,  # Only pass agent_id
                        "User rejected high-risk transaction"  # Only pass reason
                    )
                    print(
                        "[DEBUG] Updating demo tracker to True from PayPalAgent (risk rejection)")
                    write_demo_tracker({'__default__': True})
                    return {
                        'status': 'failed',
                        'error': 'Transaction cancelled - PayPal agent revoked due to risk rejection',
                        'revoked': True
                    }

                # Even if risk isn't high enough for revocation, still cancel
                return {
                    'status': 'cancelled',
                    'message': 'Transaction cancelled by user due to risk',
                    'revoked': False
                }

            # For non-rejected transactions, proceed with normal flow
            risk_analysis = await self.risk_agent.analyze_transaction(transaction_data)

            # If demo logic returns allowed or revoked, return it directly
            if risk_analysis.get('status') in ['allowed', 'revoked']:
                return risk_analysis

            # If transaction was revoked, stop processing (legacy fallback)
            if risk_analysis.get('status') == 'revoked':
                print(f"\n❌ {risk_analysis['message']}")
                return {
                    'status': 'failed',
                    'error': risk_analysis['message'],
                    'revoked': True
                }

            # Create PayPal order
            order_result = await self.create_paypal_order(transaction_data)

            # Process the order
            payment_result = await self.process_paypal_order(order_result)

            return payment_result

        except Exception as e:
            error_msg = f"Failed to process payment: {str(e)}"
            print(f"\n❌ {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'revoked': False
            }

    async def secure_communicate(self, aztp_id: str, data: dict, action: str) -> str:
        """
        Securely communicate with PayPalAgent by checking aztp_id and policy using IAMUtils.

        Args:
            aztp_id: The AZTP identity of the calling agent
            data: Data sent by the calling agent
            action: The action the calling agent wants to perform

        Returns:
            str: Result message (success or error)
        """
        try:
            if not aztp_id:
                print(
                    "[INFO] An agent without identity attempted to communicate with PayPalAgent.")
                return "Unauthorized access: No identity has been issued to this agent."
            print(
                f"[INFO] Agent {aztp_id} is attempting to communicate with PayPalAgent.")
            try:
                parsed_url = urlparse(aztp_id)
                domain = parsed_url.netloc
                print(domain)
                result = await self.iam_utils.verify_agent_access_by_trustDomain(
                    agent_id=aztp_id,
                    policy_code="policy:a07507f6fe70",
                    trust_domain=domain,
                    action="paypal_operations"
                )
                if not result:
                    return "This agent does not have access to the PayPal agent due to a failed trust domain verification—either because of misconfiguration or an untrusted domain. If you believe this is an error, please contact our support agent and create a ticket; we'll resolve it as soon as possible."
            except Exception as e:
                return f"Policy violation: {str(e)}"
            print("Connection successful.")
            return "Connection successful."
        except Exception as e:
            return f"Unauthorized access: {str(e)}"
