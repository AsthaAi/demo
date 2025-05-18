"""
Customer Support Agent for ShopperAI
Handles customer support operations including refunds, FAQ responses, and ticket escalations.
"""
from typing import Dict, Any, Optional, List
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


class CustomerSupportAgent(Agent):
    """Agent responsible for handling customer support operations"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    supportAgent: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    def __init__(self):
        """Initialize the customer support agent with necessary tools"""
        super().__init__(
            role='Customer Support Agent',
            goal='Handle customer support operations including refunds, FAQs, and ticket escalations',
            backstory="""You are an expert customer support agent with extensive experience in 
            handling customer inquiries, processing refunds, and managing support tickets. You ensure 
            customer satisfaction while following company policies and procedures.""",
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
        """Initialize the agent asynchronously"""
        if self.is_initialized:
            return

        await self._initialize_identity()
        self.is_initialized = True

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        try:
            print(f"1. Issuing identity for agent: Customer Support Agent")
            self.supportAgent = await self.aztpClient.secure_connect(
                self,
                "customer-support-agent",
                {
                    "isGlobalIdentity": False
                }
            )
            print("AZTP ID:", self.supportAgent.identity.aztp_id)

            print(f"\n2. Verifying identity for agent: Customer Support Agent")
            self.is_valid = await self.aztpClient.verify_identity(
                self.supportAgent
            )
            print("Verified Agent:", self.is_valid)

            if self.is_valid:
                if self.supportAgent and hasattr(self.supportAgent, 'identity'):
                    self.aztp_id = self.supportAgent.identity.aztp_id
                    print(f"✅ Extracted AZTP ID: {self.aztp_id}")
            else:
                raise ValueError(
                    "Failed to verify identity for agent: Customer Support Agent")

            # Verify customer support access before proceeding
            print(
                f"\n3. Verifying access permissions for Customer Support Agent {self.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="customer_support",
                policy_code="policy:9e9834d8cbea",
                operation_name="Customer Support Operations"
            )

            print("\n✅ Customer Support agent initialized successfully")

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to initialize customer support agent: {str(e)}"
            print(f"❌ {error_msg}")
            raise  # Re-raise the exception to stop execution

    def _generate_ticket_id(self) -> str:
        """
        Generate a unique support ticket ID

        Returns:
            A unique ticket ID string
        """
        # Generate a UUID and take the first 8 characters
        ticket_id = str(uuid.uuid4())[:8].upper()
        # Add a timestamp component for additional uniqueness
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        return f"TICKET-{ticket_id}-{timestamp}"

    async def process_refund(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a refund request for an order

        Args:
            order_details: Dictionary containing order information including transaction ID and refund reason

        Returns:
            Refund confirmation with details
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify refund processing access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="process_refund",
                policy_code="policy:9e9834d8cbea",
                operation_name="Refund Processing"
            )

            # Generate a refund ID
            refund_id = f"REF-{str(uuid.uuid4())[:8].upper()}"
            refund_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Extract order details
            transaction_id = order_details.get("transaction_id", "Unknown")
            refund_reason = order_details.get("reason", "Not specified")
            refund_amount = order_details.get("amount", 0.0)

            # Create refund confirmation
            confirmation = {
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "refund_time": refund_time,
                "status": "Processed",
                "amount": refund_amount,
                "reason": refund_reason,
                "message": "Your refund has been successfully processed."
            }

            return confirmation

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to process refund: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def get_faq_response(self, query: str) -> Dict[str, Any]:
        """
        Get response for a FAQ query

        Args:
            query: The customer's question

        Returns:
            FAQ response with relevant information
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify FAQ access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="read_faq",
                policy_code="policy:9e9834d8cbea",
                operation_name="FAQ Access"
            )

            # Here you would typically integrate with a FAQ database or knowledge base
            # For now, we'll return a simple response structure
            response = {
                "query": query,
                "response": "This is a placeholder response. In production, this would be fetched from a FAQ database.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "helpful_links": [],
                "related_topics": []
            }

            return response

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to get FAQ response: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def create_support_ticket(self, issue_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new support ticket for escalation

        Args:
            issue_details: Dictionary containing issue information

        Returns:
            Ticket details with tracking information
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify ticket creation access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="ticket_creation",
                policy_code="policy:9e9834d8cbea",
                operation_name="Ticket Creation"
            )

            ticket_id = self._generate_ticket_id()
            creation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Extract issue details
            customer_id = issue_details.get("customer_id", "Unknown")
            issue_type = issue_details.get("issue_type", "General")
            priority = issue_details.get("priority", "Medium")
            description = issue_details.get(
                "description", "No description provided")

            # Create ticket
            ticket = {
                "ticket_id": ticket_id,
                "creation_time": creation_time,
                "status": "Open",
                "customer_id": customer_id,
                "issue_type": issue_type,
                "priority": priority,
                "description": description,
                "assigned_to": "Pending Assignment",
                "estimated_response_time": "24 hours",
                "message": "Your support ticket has been created and will be addressed by our team."
            }

            return ticket

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to create support ticket: {str(e)}"
            print(f"❌ {error_msg}")
            raise
