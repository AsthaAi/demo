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
    secured_connection: SecureConnection = Field(default=None, exclude=True)
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    paypal_toolkit: Optional[Any] = Field(default=None, exclude=True)

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
                    client_id=os.getenv("PAYPAL_CLIENT_ID"),
                    secret=os.getenv("PAYPAL_SECRET"),
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

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        print(f"1. Issuing identity for agent: PayPal Agent")
        self.secured_connection = await self.aztpClient.secure_connect(
            self,
            "paypal-agent",
            {
                "isGlobalIdentity": False
            }
        )
        print("AZTP ID:", self.secured_connection.identity.aztp_id)

        print(f"\n2. Verifying identity for agent: PayPal Agent")
        self.is_valid = await self.aztpClient.verify_identity(
            self.secured_connection
        )
        print("Verified Agent:", self.is_valid)

        if self.is_valid:
            if self.secured_connection and hasattr(self.secured_connection, 'identity'):
                self.aztp_id = self.secured_connection.identity.aztp_id
                print(f"✅ Extracted AZTP ID: {self.aztp_id}")
        else:
            raise ValueError(
                "Failed to verify identity for agent: PayPal Agent")

    def _generate_transaction_id(self) -> str:
        """
        Generate a unique transaction ID

        Returns:
            A unique transaction ID string
        """
        # Generate a UUID and take the first 8 characters
        transaction_id = str(uuid.uuid4())[:8].upper()
        # Add a timestamp component for additional uniqueness
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        return f"PAY-{transaction_id}-{timestamp}"

    def create_payment_order(self, amount: str, currency: str = "USD", description: str = "") -> Dict[str, Any]:
        """
        Create a new PayPal order

        Args:
            amount: The amount to charge
            currency: The currency code (default: USD)
            description: Description of the order

        Returns:
            Order details including ID and status
        """
        if not self.paypal_toolkit:
            logger.error("PayPal toolkit not available")
            return {
                "error": "PayPal toolkit not available",
                "transaction_id": self._generate_transaction_id(),
                "status": "Failed"
            }

        try:
            # Extract numeric amount from string (e.g., "$99.99" -> "99.99")
            numeric_amount = amount.replace("$", "").strip()

            # Create order using PayPal toolkit
            result = self.paypal_toolkit.create_order(
                amount=numeric_amount,
                currency=currency,
                description=description
            )

            logger.info(f"Created PayPal order: {result}")
            return {
                "transaction_id": self._generate_transaction_id(),
                "paypal_order_id": result.get("id", ""),
                "status": "Created",
                "amount": amount,
                "currency": currency,
                "description": description
            }
        except Exception as e:
            logger.error(f"Error creating PayPal order: {str(e)}")
            return {
                "error": str(e),
                "transaction_id": self._generate_transaction_id(),
                "status": "Failed"
            }

    def capture_payment(self, order_id: str) -> Dict[str, Any]:
        """
        Capture payment for an authorized order

        Args:
            order_id: The PayPal order ID

        Returns:
            Payment capture details
        """
        if not self.paypal_toolkit:
            logger.error("PayPal toolkit not available")
            return {
                "error": "PayPal toolkit not available",
                "transaction_id": self._generate_transaction_id(),
                "status": "Failed"
            }

        try:
            # Capture payment using PayPal toolkit
            result = self.paypal_toolkit.capture_order(order_id)

            logger.info(f"Captured PayPal payment: {result}")
            return {
                "transaction_id": self._generate_transaction_id(),
                "paypal_order_id": order_id,
                "status": "Completed",
                "capture_id": result.get("id", ""),
                "amount": result.get("amount", {}).get("value", ""),
                "currency": result.get("amount", {}).get("currency_code", "")
            }
        except Exception as e:
            logger.error(f"Error capturing PayPal payment: {str(e)}")
            return {
                "error": str(e),
                "transaction_id": self._generate_transaction_id(),
                "status": "Failed"
            }

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
                "transaction_id": self._generate_transaction_id(),
                "status": "Failed"
            }

        try:
            # Get order details using PayPal toolkit
            result = self.paypal_toolkit.get_order(order_id)

            logger.info(f"Retrieved PayPal order details: {result}")
            return {
                "transaction_id": self._generate_transaction_id(),
                "paypal_order_id": order_id,
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
                "transaction_id": self._generate_transaction_id(),
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
                "transaction_id": self._generate_transaction_id(),
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
                "transaction_id": self._generate_transaction_id(),
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
                "transaction_id": self._generate_transaction_id(),
                "status": "Failed"
            }
