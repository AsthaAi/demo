"""
Promotions Agent for ShopperAI
Handles promotional activities and personalized discounts.
"""
from typing import Dict, Any, List, Optional
from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
import os
from pydantic import Field, ConfigDict
import asyncio
from datetime import datetime, timedelta
import json

load_dotenv()


class PromotionsAgent(Agent):
    """Agent responsible for managing promotional activities and personalized discounts"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    promotionsAgent: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    # Add memory storage for promotions
    _active_promotions: Dict[str, Dict[str, Any]] = {}
    _user_discount_history: Dict[str, List[Dict[str, Any]]] = {}
    _campaign_metrics: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        """Initialize the promotions agent with necessary tools"""
        super().__init__(
            role='Promotions Agent',
            goal='Create and manage personalized promotions and discount campaigns',
            backstory="""You are an expert in promotional marketing and personalization. 
            You analyze customer shopping patterns to create targeted discounts and manage 
            promotional campaigns effectively. Your focus is on maximizing customer engagement 
            while maintaining profitable promotional strategies.""",
            verbose=True
        )

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.iam_utils = IAMUtils()
        self.aztp_id = ""

    async def initialize(self):
        """Initialize the agent's identity asynchronously"""
        if self.is_initialized:
            return

        await self._initialize_identity()
        self.is_initialized = True

    async def _initialize_identity(self):
        """Initialize the agent's identity asynchronously"""
        try:
            print(f"1. Issuing identity for agent: Promotions Agent")
            self.promotionsAgent = await self.aztpClient.secure_connect(
                self,
                "promotions-agent",
                {
                    "isGlobalIdentity": False
                }
            )
            print("AZTP ID:", self.promotionsAgent.identity.aztp_id)

            print(f"\n2. Verifying identity for agent: Promotions Agent")
            self.is_valid = await self.aztpClient.verify_identity(
                self.promotionsAgent
            )
            print("Verified Agent:", self.is_valid)

            if self.is_valid:
                if self.promotionsAgent and hasattr(self.promotionsAgent, 'identity'):
                    self.aztp_id = self.promotionsAgent.identity.aztp_id
                    print(f"✅ Extracted AZTP ID: {self.aztp_id}")
            else:
                raise ValueError(
                    "Failed to verify identity for agent: Promotions Agent")

            # Verify promotions access before proceeding
            print(
                f"\n3. Verifying access permissions for Promotions Agent {self.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="create_promotion",
                policy_code="policy:182a30a9c944",
                operation_name="Promotions Management"
            )

            print("\n✅ Promotions agent initialized successfully")

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise  # Re-raise the exception to stop execution

        except Exception as e:
            error_msg = f"Failed to initialize promotions agent: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def create_personalized_discount(self, user_id: str, shopping_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a personalized discount based on user's shopping history

        Args:
            user_id: Unique identifier for the user
            shopping_history: List of user's past purchases and interactions

        Returns:
            Dictionary containing personalized discount details
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify discount creation access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="discount_creation",
                policy_code="policy:182a30a9c944",
                operation_name="Discount Creation"
            )

            # Analyze shopping patterns
            total_spent = sum(item.get('amount', 0)
                              for item in shopping_history)
            purchase_frequency = len(shopping_history) / \
                30  # purchases per month

            # Calculate discount percentage based on user behavior
            base_discount = 5  # Base discount percentage
            if total_spent > 1000:
                base_discount += 5
            if purchase_frequency > 5:
                base_discount += 3

            # Cap maximum discount
            final_discount = min(base_discount, 15)

            discount = {
                'user_id': user_id,
                'discount_percentage': final_discount,
                'valid_from': datetime.now().isoformat(),
                'valid_until': (datetime.now() + timedelta(days=7)).isoformat(),
                'minimum_purchase': 50.0,
                'created_at': datetime.now().isoformat()
            }

            # Store in history
            if user_id not in self._user_discount_history:
                self._user_discount_history[user_id] = []
            self._user_discount_history[user_id].append(discount)

            return discount

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to create personalized discount: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def create_promotion_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and manage a promotion campaign

        Args:
            campaign_data: Dictionary containing campaign details

        Returns:
            Dictionary containing campaign information and status
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify campaign creation access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="campaign_creation",
                policy_code="policy:182a30a9c944",
                operation_name="Campaign Creation"
            )

            campaign_id = f"camp_{int(datetime.now().timestamp())}"

            campaign = {
                'campaign_id': campaign_id,
                'name': campaign_data.get('name', 'Unnamed Campaign'),
                'description': campaign_data.get('description', ''),
                'start_date': campaign_data.get('start_date', datetime.now().isoformat()),
                'end_date': campaign_data.get('end_date'),
                'discount_type': campaign_data.get('discount_type', 'percentage'),
                'discount_value': campaign_data.get('discount_value', 10),
                'conditions': campaign_data.get('conditions', {}),
                'status': 'active',
                'created_at': datetime.now().isoformat()
            }

            # Store campaign
            self._active_promotions[campaign_id] = campaign

            # Initialize metrics
            self._campaign_metrics[campaign_id] = {
                'impressions': 0,
                'redemptions': 0,
                'total_discount_amount': 0.0
            }

            return campaign

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to create promotion campaign: {str(e)}"
            print(f"❌ {error_msg}")
            raise

    async def analyze_shopping_history(self, user_id: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze user's shopping history for insights

        Args:
            user_id: Unique identifier for the user
            history: List of user's shopping history

        Returns:
            Dictionary containing analysis results and recommendations
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Verify history analysis access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="read_history",
                policy_code="policy:182a30a9c944",
                operation_name="History Analysis"
            )

            # Analyze purchase patterns
            total_purchases = len(history)
            total_spent = sum(item.get('amount', 0) for item in history)
            avg_purchase = total_spent / total_purchases if total_purchases > 0 else 0

            # Category analysis
            category_counts = {}
            for item in history:
                category = item.get('category', 'unknown')
                category_counts[category] = category_counts.get(
                    category, 0) + 1

            # Find favorite category
            favorite_category = max(category_counts.items(), key=lambda x: x[1])[
                0] if category_counts else None

            analysis = {
                'user_id': user_id,
                'total_purchases': total_purchases,
                'total_spent': total_spent,
                'average_purchase': avg_purchase,
                'favorite_category': favorite_category,
                'category_distribution': category_counts,
                'analyzed_at': datetime.now().isoformat()
            }

            return analysis

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Failed to analyze shopping history: {str(e)}"
            print(f"❌ {error_msg}")
            raise
