"""
Test script to verify PayPal sandbox payment processing
"""
import os
import json
import requests
from dotenv import load_dotenv
from base64 import b64encode
from datetime import datetime


def get_access_token(client_id, client_secret):
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


def capture_payment(access_token, order_id):
    """Capture a payment for an approved order"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    capture_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
    capture_response = requests.post(capture_url, headers=headers)

    if capture_response.status_code != 201:
        print(f"\nError capturing payment: {capture_response.text}")
        return None

    return capture_response.json()


def display_payment_success(capture_result, order_details):
    """Display a formatted payment success message"""
    if not capture_result or not order_details:
        return

    # Extract relevant information
    order_id = capture_result.get('id', 'Unknown')
    status = capture_result.get('status', 'Unknown')

    # Get purchase unit details
    purchase_units = capture_result.get('purchase_units', [])
    if not purchase_units:
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
    current_date = datetime.now().strftime("%B %d, %Y")

    # Display formatted message
    print("\n" + "="*50)
    print("Payment processed successfully!")
    print("="*50)
    print("Order details: **Payment Capture Confirmation**\n")
    print("We are pleased to inform you that your payment has been successfully captured. Below are the transaction details:\n")

    print(f"- **Order ID:** {order_id}")
    print(f"- **Product Name:** Test Product")
    print(f"- **Price:** ${value} {currency}")
    print(f"- **Quantity:** 1")
    print(f"- **Total Amount:** ${value} {currency}\n")

    print("**Transaction Details:**")
    print(f"- **Transaction ID:** {order_id}")
    print(f"- **Order Status:** {status}")
    print(f"- **Payment Method:** Credit Card (ending in {last_digits})")
    print(f"- **Transaction Date:** {current_date}")
    print("="*50)


def test_sandbox_payment():
    # Load environment variables
    load_dotenv()

    # Get PayPal credentials
    client_id = os.getenv(
        "PAYPAL_CLIENT_ID", "AfS3ByWWWrF4ZQlGYHQxXQ9nVzXZu5Js5wOs0qXBb_Cta6iVVyTDkqH2D2f970dubOUOofFrGC6DR0R4")
    secret = os.getenv(
        "PAYPAL_SECRET", "EKuCuoppyKuLbTq25joW6T5Mn8IAU_kJ46PEQc85sR351Z2S_xFwAoJIlZx22O1gx91n8CysiszzzgZU")

    try:
        # Get access token
        print("\nGetting access token...")
        access_token = get_access_token(client_id, secret)
        print("Access token obtained successfully!")

        # Create order
        print("\nCreating test order...")
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": "10.00"
                },
                "description": "Test Product",
                "payee": {
                    "email_address": "somit.shrestha-buyer@gmail.com"
                }
            }],
            "application_context": {
                "return_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
                "shipping_preference": "NO_SHIPPING"
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Create order
        create_order_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        create_response = requests.post(
            create_order_url, headers=headers, json=order_data)

        if create_response.status_code != 201:
            print(f"\nError creating order: {create_response.text}")
            return False

        create_order_result = create_response.json()
        print("\nOrder created successfully!")
        print(f"Order ID: {create_order_result['id']}")
        print(f"Order Status: {create_order_result['status']}")

        # Get order details
        print("\nFetching order details...")
        get_order_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{create_order_result['id']}"
        get_response = requests.get(get_order_url, headers=headers)

        if get_response.status_code != 200:
            print(f"\nError getting order details: {get_response.text}")
            return False

        order_details = get_response.json()
        print(f"Order Details Status: {order_details['status']}")

        # Print checkout URL
        print("\nTo complete this payment in sandbox:")
        for link in create_order_result['links']:
            if link['rel'] == 'approve':
                print(f"1. Open this URL in your browser: {link['href']}")
                print(
                    "2. Log in with your sandbox PayPal account (somit.shrestha-buyer@gmail.com)")
                print("3. Approve the payment")
                print("\nAfter approval, you can capture the payment using the order ID")
                break

        # Ask if user wants to capture the payment
        capture_order_id = input(
            "\nEnter the order ID to capture payment (or press Enter to skip): ")
        if capture_order_id:
            print("\nCapturing payment...")
            capture_result = capture_payment(access_token, capture_order_id)
            if capture_result:
                display_payment_success(capture_result, order_details)
            else:
                print(
                    "\nFailed to capture payment. Make sure the order is approved first.")

        return True

    except Exception as e:
        print(f"\nError during sandbox payment test: {str(e)}")
        return False


if __name__ == "__main__":
    test_sandbox_payment()
