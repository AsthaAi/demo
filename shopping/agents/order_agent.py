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
from pydantic import Field, ConfigDict, BaseModel
import asyncio
import uuid
import datetime

load_dotenv()


class AztpConnection(BaseModel):
    """AZTP connection state"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Optional[Aztp] = None
    connection: Optional[SecureConnection] = None
    aztp_id: str = ""
    is_valid: bool = False
    is_initialized: bool = False


class OrderAgent(Agent):
    """Agent responsible for processing orders and payments"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    aztp: AztpConnection = Field(default_factory=AztpConnection)
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

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

        # Initialize AZTP connection
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp = AztpConnection(
            client=Aztp(api_key=api_key)
        )
        self.iam_utils = IAMUtils()

    async def initialize(self):
        """Initialize the agent asynchronously"""
        if not self.is_initialized:
            print("\nInitializing Order Agent...")
            try:
                # Establish secure connection
                self.aztp.connection = await self.aztpClient.secure_connect(
                    self,
                    "order-agent",
                    {
                        "isGlobalIdentity": False,
                        "trustLevel": "high",
                        "department": "Order"
                    }
                )

                # Store AZTP ID
                if self.aztp.connection and hasattr(self.aztp.connection, 'identity'):
                    self.aztp.aztp_id = self.aztp.connection.identity.aztp_id
                    print(
                        f"✅ Secured connection established. AZTP ID: {self.aztp.aztp_id}")

                # Verify identity
                self.aztp.is_valid = await self.aztpClient.verify_identity(self.aztp.connection)
                if not self.aztp.is_valid:
                    raise ValueError(
                        "Failed to verify identity for Order Agent")

                # Verify order processing access
                await self.iam_utils.verify_access_or_raise(
                    agent_id=self.aztp.aztp_id,
                    action="order_processing",
                    policy_code="policy:8d4e29f7a3b5",
                    operation_name="Order Processing"
                )

                self.aztp.is_initialized = True
                self.is_initialized = True
                print("✅ Order Agent initialized successfully")

            except Exception as e:
                print(f"❌ Error initializing Order Agent: {str(e)}")
                raise

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
                agent_id=self.aztp.aztp_id,
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
