import os
import requests
from base64 import b64encode


class PayPalPaymentTool:
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
