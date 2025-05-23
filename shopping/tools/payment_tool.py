import os
import requests
from base64 import b64encode
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from pydantic import Field, ConfigDict, BaseModel
import asyncio
from typing import Dict, Any, Optional
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
import json
from urllib.parse import quote

# Load environment variables
load_dotenv()


class PayPalPaymentTool(BaseModel):
    """Tool for handling PayPal payment operations"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    paymentTool: SecureConnection = Field(
        default=None, exclude=True, alias="secured_connection")
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)
    verbose: bool = Field(default=True, exclude=True)

    def __init__(self, verbose=True):
        """Initialize the PayPal payment tool"""
        super().__init__()

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.iam_utils = IAMUtils()  # Initialize IAM utilities
        self.aztp_id = ""  # Initialize as empty string
        self.is_initialized = False
        self.verbose = verbose

    async def initialize(self):
        """Initialize the tool's identity"""
        if not self.is_initialized:
            await self._initialize_identity()
            self.is_initialized = True
        return self

    async def _initialize_identity(self):
        """Initialize the tool's identity asynchronously"""
        try:
            if self.verbose:
                print(f"1. Issuing identity for tool: PayPal Payment Tool")

            # Create secure connection
            self.paymentTool = await self.aztpClient.secure_connect(
                self,
                "paypal-payment-tool",
                {
                    "isGlobalIdentity": False
                }
            )

            # Store the identity
            if hasattr(self.paymentTool, 'identity'):
                self.aztp_id = self.paymentTool.identity.aztp_id
                if self.verbose:
                    print(f"✅ Identity issued successfully")
                    print(f"AZTP ID: {self.aztp_id}")
            else:
                if self.verbose:
                    print("Warning: No AZTP ID received from secure_connect")
                self.aztp_id = ""

            # Verify payment access before proceeding
            if self.verbose:
                print(
                    f"\n2. Verifying access permissions for PayPal Payment Tool {self.aztp_id}")
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="payment_processing",
                policy_code="policy:3ee68df2c5e7",
                operation_name="Payment Processing"
            )

            if self.verbose:
                print("\n✅ PayPal payment tool initialized successfully")

        except Exception as e:
            print(f"Error initializing identity: {str(e)}")
            raise

    async def get_access_token(self):
        try:
            # Verify access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="get_access_token",
                policy_code="policy:3ee68df2c5e7",
                operation_name="Get PayPal Access Token"
            )

            client_id = os.getenv("PAYPAL_CLIENT_ID")
            client_secret = os.getenv("PAYPAL_SECRET")

            if not client_id or not client_secret:
                raise ValueError("PayPal credentials not properly configured")

            auth = b64encode(f"{client_id}:{client_secret}".encode(
                'utf-8')).decode('utf-8')
            url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {"grant_type": "client_credentials"}
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()
            print(f"[PayPalPaymentTool] Access token obtained successfully")
            return result["access_token"]
        except Exception as e:
            print(f"[PayPalPaymentTool] Error getting access token: {str(e)}")
            raise

    async def create_order(self, access_token, amount, currency="USD", description="Test Product", payee_email=None, return_url=None, cancel_url=None):
        try:
            # Verify access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="create_order",
                policy_code="policy:3ee68df2c5e7",
                operation_name="Create PayPal Order"
            )

            # Validate payee email if provided
            if payee_email and not '@' in payee_email:
                raise ValueError("Invalid payee email address format")

            # Generate a unique timestamp-based ID for sandbox testing
            import time
            import uuid
            unique_id = f"ORDER_{int(time.time())}_{str(uuid.uuid4())[:8]}"

            url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # Ensure amount is properly formatted for PayPal
            # Remove any currency symbols and convert to string with exactly 2 decimal places
            amount_str = str(float(str(amount).replace('$', '').strip()))
            if '.' not in amount_str:
                amount_str = f"{amount_str}.00"
            elif len(amount_str.split('.')[1]) == 1:
                amount_str = f"{amount_str}0"
            elif len(amount_str.split('.')[1]) > 2:
                amount_str = f"{float(amount_str):.2f}"

            purchase_unit = {
                "reference_id": unique_id,
                "amount": {
                    "currency_code": currency,
                    "value": amount_str
                },
                "description": description
            }

            # Add payee information if email is provided
            if payee_email:
                purchase_unit["payee"] = {
                    "email_address": payee_email
                }
                print(
                    f"[PayPalPaymentTool] Setting up payment to merchant: {payee_email}")

            # Set default URLs if not provided
            if not return_url:
                return_url = "https://example.com/success"
            if not cancel_url:
                cancel_url = "https://example.com/cancel"

            # Create the order first to get the PayPal order ID
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [purchase_unit],
                "application_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW"
                }
            }

            print(
                f"[PayPalPaymentTool] Creating order with data: {json.dumps(order_data, indent=2)}")
            response = requests.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            order_response = response.json()

            # Get the PayPal order ID from the response
            paypal_order_id = order_response.get('id')
            print(f"[PayPalPaymentTool] Created order with ID: {paypal_order_id}")

            # Update the return URL with the PayPal order ID
            if '?' in return_url:
                return_url = f"{return_url}&transaction_id={paypal_order_id}"
            else:
                return_url = f"{return_url}?transaction_id={paypal_order_id}"

            # Create a new order with the updated return URL
            order_data["application_context"]["return_url"] = return_url
            response = requests.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            order_response = response.json()

            # Extract and add the approval URL to the response
            for link in order_response.get('links', []):
                if link.get('rel') == 'approve':
                    order_response['approval_url'] = link.get('href')
                    print(
                        f"[PayPalPaymentTool] Approval URL: {link.get('href')}")
                    break

            return order_response

        except Exception as e:
            print(f"[PayPalPaymentTool] Error creating order: {str(e)}")
            raise

    async def get_order_status(self, access_token, order_id):
        """Get the current status of a PayPal order"""
        try:
            # Verify access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="get_order_status",
                policy_code="policy:3ee68df2c5e7",
                operation_name="Get PayPal Order Status"
            )

            url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            order_details = response.json()
            print(
                f"[PayPalPaymentTool] Order {order_id} status: {order_details.get('status')}")
            return order_details
        except Exception as e:
            print(f"[PayPalPaymentTool] Error getting order status: {str(e)}")
            raise

    async def capture_payment(self, access_token, order_id):
        try:
            # Verify access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="capture_payment",
                policy_code="policy:3ee68df2c5e7",
                operation_name="Capture PayPal Payment"
            )

            # First check the order status
            order_details = await self.get_order_status(access_token, order_id)
            status = order_details.get('status')

            if status != 'APPROVED':
                print(
                    f"[PayPalPaymentTool] Cannot capture payment: Order status is {status}, not APPROVED")
                print(
                    "[PayPalPaymentTool] Please approve the order first using the approval URL")
                return {"error": f"Order status is {status}, not APPROVED", "status": status}

            url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            capture_response = response.json()
            print(
                f"[PayPalPaymentTool] Successfully captured payment for order {order_id}")
            return capture_response
        except Exception as e:
            print(f"[PayPalPaymentTool] Error capturing payment: {str(e)}")
            raise

    async def get_order_by_transaction_id(self, access_token, transaction_id):
        """Get order details using transaction ID"""
        try:
            # Verify access before proceeding
            await self.iam_utils.verify_access_or_raise(
                agent_id=self.aztp_id,
                action="get_order_status",
                policy_code="policy:3ee68df2c5e7",
                operation_name="Get PayPal Order by Transaction ID"
            )

            # In PayPal sandbox, we can use the transaction_id directly as the order_id
            # since it's the same value in the sandbox environment
            url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{transaction_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            order_details = response.json()
            
            print(f"[PayPalPaymentTool] Retrieved order details for transaction {transaction_id}")
            return order_details
            
        except Exception as e:
            print(f"[PayPalPaymentTool] Error getting order by transaction ID: {str(e)}")
            raise
