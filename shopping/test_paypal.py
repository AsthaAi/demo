"""
Test script to verify PayPal integration
"""
import os
from dotenv import load_dotenv
from paypal_agent_toolkit.crewai.toolkit import PayPalToolkit
from paypal_agent_toolkit.shared.configuration import Configuration, Context
from agents.paypal_agent import PayPalAgent


def test_paypal_setup():
    # Load environment variables
    load_dotenv()

    # Get PayPal credentials
    client_id = os.getenv(
        "PAYPAL_CLIENT_ID", "AfS3ByWWWrF4ZQlGYHQxXQ9nVzXZu5Js5wOs0qXBb_Cta6iVVyTDkqH2D2f970dubOUOofFrGC6DR0R4")
    secret = os.getenv(
        "PAYPAL_SECRET", "EKuCuoppyKuLbTq25joW6T5Mn8IAU_kJ46PEQc85sR351Z2S_xFwAoJIlZx22O1gx91n8CysiszzzgZU")

    print("\nPayPal Credentials Check:")
    print(f"Client ID exists: {'Yes' if client_id else 'No'}")
    print(f"Secret exists: {'Yes' if secret else 'No'}")

    if client_id and secret:
        try:
            # Initialize PayPal toolkit
            paypal_toolkit = PayPalToolkit(
                client_id=client_id,
                secret=secret,
                configuration=Configuration(
                    actions={
                        "orders": {
                            "create": True,
                            "get": True,
                            "capture": True,
                        }
                    },
                    context=Context(sandbox=True)
                )
            )
            print("\nPayPal Toolkit initialized successfully!")
            return True
        except Exception as e:
            print(f"\nError initializing PayPal Toolkit: {str(e)}")
            return False
    else:
        print("\nPayPal credentials are missing in .env file")
        return False


def test_paypal_direct_api():
    print("\nTesting direct PayPal API methods in PayPalAgent...")
    agent = PayPalAgent()
    try:
        access_token = agent.get_access_token_direct()
        print("Access token obtained successfully!")
        order = agent.create_order_direct(
            access_token, amount="10.00", currency="USD", description="Direct API Test Product")
        print("Order created successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Order Status: {order['status']}")
        # Print approval URL for manual browser test
        for link in order.get('links', []):
            if link.get('rel') == 'approve':
                print(f"Approval URL: {link['href']}")
                break
        return True
    except Exception as e:
        print(f"Error in direct PayPal API test: {str(e)}")
        return False


def test_paypal_agent_direct_flow():
    print("\nTesting PayPalAgent direct PayPal API flow...")
    agent = PayPalAgent()
    try:
        access_token = agent.get_access_token_direct()
        print("Access token obtained successfully!")
        order = agent.create_order_direct(access_token, amount="10.00", currency="USD",
                                          description="Direct API Test Product", payee_email="somit.shrestha-buyer@gmail.com")
        print("Order created successfully!")
        print(f"Order ID: {order['id']}")
        print(f"Order Status: {order['status']}")
        # Print approval URL for manual browser test
        approval_url = None
        for link in order.get('links', []):
            if link.get('rel') == 'approve':
                approval_url = link['href']
                print(f"Approval URL: {approval_url}")
                break
        if not approval_url:
            print("No approval URL found. Order response:", order)
            return False
        input("\nOpen the above approval URL in your browser, approve the payment, then press Enter to continue...")
        order_id = order['id']
        order_details = agent.get_order_details_direct(access_token, order_id)
        capture_result = agent.capture_payment_direct(access_token, order_id)
        agent.display_payment_success_direct(capture_result, order_details)
        return True
    except Exception as e:
        print(f"Error in PayPalAgent direct API test: {str(e)}")
        return False


if __name__ == "__main__":
    test_paypal_setup()
    test_paypal_direct_api()
    test_paypal_agent_direct_flow()
