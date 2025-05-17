"""
Order Agent for ShopperAI
Handles purchase processing and order confirmation.
"""
from typing import Dict, Any, Optional
from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
import os
from pydantic import Field, ConfigDict
import asyncio
import uuid
import datetime

load_dotenv()


class OrderAgent(Agent):
    """Agent responsible for processing orders and payments"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    orderAgent: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)

    def __init__(self):
        """Initialize the order agent with necessary tools"""
        super().__init__(
            role='Order Agent',
            goal='Process purchases and provide order confirmations',
            backstory="""You are an expert order processing agent with years of experience in 
            handling purchases and payments. You ensure secure transactions and provide clear 
            order confirmations with all necessary details.""",
            verbose=True
        )

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.iam_utils = IAMUtils()  # Initialize IAM utilities
        self.aztp_id = ""  # Initialize as empty string

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        try:
            print(f"1. Issuing identity for agent: Order Agent")
            self.orderAgent = await self.aztpClient.secure_connect(
                self,
                "order-agent",
                {
                    "isGlobalIdentity": False
                }
            )
            print("AZTP ID:", self.orderAgent.identity.aztp_id)

            print(f"\n2. Verifying identity for agent: Order Agent")
            self.is_valid = await self.aztpClient.verify_identity(
                self.orderAgent
            )
            print("Verified Agent:", self.is_valid)

            if self.is_valid:
                if self.orderAgent and hasattr(self.orderAgent, 'identity'):
                    self.aztp_id = self.orderAgent.identity.aztp_id
                    print(f"✅ Extracted AZTP ID: {self.aztp_id}")
            else:
                raise ValueError(
                    "Failed to verify identity for agent: Order Agent")

            # Verify order processing access before proceeding
            print(
                f"\n3. Verifying access permissions for Order Agent {self.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="process_orders",
                policy_code="policy:226e90937935",
                operation_name="Order Processing"
            )

            print("\n✅ Order agent initialized successfully")

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to initialize order agent: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution

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
        return f"TXN-{transaction_id}-{timestamp}"

    async def process_purchase(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a purchase for a product

        Args:
            product: Product dictionary with details

        Returns:
            Order confirmation with transaction details
        """
        try:
            # Verify order processing access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="process_orders",
                policy_code="policy:226e90937935",
                operation_name="Order Processing"
            )

            # Generate a transaction ID
            transaction_id = self._generate_transaction_id()

            # Get current timestamp
            purchase_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Extract product details
            product_name = product.get("name", "Unknown Product")
            product_brand = product.get("brand", "Unknown Brand")
            product_price = product.get("price", "Price not available")
            product_color = product.get("color", "Not specified")
            total_cost = product.get("total_cost", "$0.00")

            # Create order confirmation
            confirmation = {
                "transaction_id": transaction_id,
                "purchase_time": purchase_time,
                "status": "Completed",
                "product": {
                    "name": product_name,
                    "brand": product_brand,
                    "price": product_price,
                    "color": product_color,
                    "total_cost": total_cost
                },
                "message": f"Your order for {product_name} has been successfully processed!"
            }

            return confirmation

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to process purchase: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution
