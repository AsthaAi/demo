"""
Test script to demonstrate the payment success message in the PayPal agent
"""
import os
import json
from dotenv import load_dotenv
from agents.paypal_agent import PayPalAgent


def test_payment_success_agent():
    """Test the payment success message in the PayPal agent"""
    # Load environment variables
    load_dotenv()

    # Initialize the PayPal agent
    paypal_agent = PayPalAgent()

    # Create a sample product
    product = {
        "name": "iPhone 11 - 64GB",
        "price": "499.00",
        "quantity": 1,
        "description": "iPhone 11 - 64GB"
    }

    # Create a payment order
    print("\nCreating payment order...")
    order_result = paypal_agent.create_payment_order(
        amount=product["price"],
        currency="USD",
        description=product["description"]
    )

    if "error" in order_result:
        print(f"Error creating order: {order_result['error']}")
        return

    order_id = order_result.get("id")
    print(f"Order created successfully! Order ID: {order_id}")

    # Get order details
    print("\nGetting order details...")
    order_details = paypal_agent.get_order_details(order_id)

    if "error" in order_details:
        print(f"Error getting order details: {order_details['error']}")
        return

    print(f"Order status: {order_details.get('status')}")

    # Display the payment success message
    print("\nDisplaying payment success message...")
    success_message = paypal_agent.display_payment_success(
        order_details, order_details)

    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_payment_success_agent()
