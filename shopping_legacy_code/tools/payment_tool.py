import os
import requests
from base64 import b64encode
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from pydantic import Field, ConfigDict, BaseModel
import asyncio
from typing import Dict, Any, Optional

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
    identity_access_policy: Optional[Dict[str, Any]] = Field(
        default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)

    def __init__(self):
        """Initialize the PayPal payment tool"""
        super().__init__()

        # Initialize the client with API key from environment
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp_id = ""  # Initialize as empty string

        # Run the async initialization
        asyncio.run(self._initialize_identity())

    async def _initialize_identity(self):
        """Initialize the tool's identity asynchronously"""
        print(f"1. Issuing identity for tool: PayPal Payment Tool")
        self.paymentTool = await self.aztpClient.secure_connect(
            self,
            "paypal-payment-tool",
            {
                "isGlobalIdentity": False
            }
        )
        print("AZTP ID:", self.paymentTool.identity.aztp_id)

        print(f"\n2. Verifying identity for tool: PayPal Payment Tool")
        self.is_valid = await self.aztpClient.verify_identity(
            self.paymentTool
        )
        print("Verified Tool:", self.is_valid)

        if self.is_valid:
            if self.paymentTool and hasattr(self.paymentTool, 'identity'):
                self.aztp_id = self.paymentTool.identity.aztp_id
                print(f"✅ Extracted AZTP ID: {self.aztp_id}")
        else:
            raise ValueError(
                "Failed to verify identity for tool: PayPal Payment Tool")

        print(
            f"\n3. Getting policy information for tool: PayPal Payment Tool {self.aztp_id}")
        if self.paymentTool and hasattr(self.paymentTool, 'identity'):
            try:
                self.identity_access_policy = await self.aztpClient.get_policy(
                    self.paymentTool.identity.aztp_id
                )
                # Display policy information
                print("\nPolicy Information:")
                if isinstance(self.identity_access_policy, dict):
                    # Handle dictionary response
                    for policy in self.identity_access_policy.get('data', []):
                        print("\nPolicy Statement:",
                              policy.get('policyStatement'))
                        statement = policy.get('policyStatement', {}).get(
                            'Statement', [{}])[0]
                        if statement.get('Effect') == "Allow":
                            print("Statement Effect:", statement.get('Effect'))
                            print("Statement Actions:",
                                  statement.get('Action'))
                            if 'Condition' in statement:
                                print("Statement Conditions:",
                                      statement.get('Condition'))
                            print("Identity:", policy.get('identity'))
                else:
                    # Handle string response
                    print(self.identity_access_policy)
            except Exception as e:
                print(f"Error getting policy: {str(e)}")
        else:
            print(
                f"Warning: No valid AZTP ID available for policy retrieval. AZTP ID: {self.aztp_id}")

    def get_access_token(self):
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
        response.raise_for_status()
        print(f"[PayPalPaymentTool] Access token response: {response.json()}")
        return response.json()["access_token"]

    def create_order(self, access_token, amount, currency="USD", description="Test Product", payee_email=None):
        url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        purchase_unit = {
            "amount": {"currency_code": currency, "value": amount},
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
        response.raise_for_status()
        order_response = response.json()
        print(f"[PayPalPaymentTool] Create order response: {order_response}")
        print(
            f"[PayPalPaymentTool] Created order ID: {order_response.get('id')}")
        for link in order_response.get('links', []):
            if link.get('rel') == 'approve':
                print(f"[PayPalPaymentTool] Approval URL: {link.get('href')}")
        return order_response

    def get_order_status(self, access_token, order_id):
        """Get the current status of a PayPal order"""
        url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        order_details = response.json()
        print(
            f"[PayPalPaymentTool] Order status: {order_details.get('status')}")
        return order_details

    def capture_payment(self, access_token, order_id):
        # First check the order status
        order_details = self.get_order_status(access_token, order_id)
        status = order_details.get('status')

        if status != 'APPROVED':
            print(
                f"[PayPalPaymentTool] Cannot capture payment: Order status is {status}, not APPROVED")
            print(
                f"[PayPalPaymentTool] Please approve the order first using the approval URL")
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
            f"[PayPalPaymentTool] Capture payment response: {capture_response}")
        return capture_response
