"""
Demo script to show the payment success message format
"""
from datetime import datetime


def display_payment_success_demo():
    """Display a demo payment success message"""
    # Sample data
    order_id = "TXN123456789"
    status = "COMPLETED"
    currency = "USD"
    value = "499.00"
    last_digits = "1234"
    current_date = datetime.now().strftime("%B %d, %Y")

    # Display formatted message
    print("\n" + "="*50)
    print("Payment processed successfully!")
    print("="*50)
    print("Order details: **Payment Capture Confirmation**\n")
    print("We are pleased to inform you that your payment has been successfully captured. Below are the transaction details:\n")

    print(f"- **Order ID:** {order_id}")
    print(f"- **Product Name:** iPhone 11 - 64GB")
    print(f"- **Price:** ${value} {currency}")
    print(f"- **Quantity:** 1")
    print(f"- **Total Amount:** ${value} {currency}\n")

    print("**Transaction Details:**")
    print(f"- **Transaction ID:** {order_id}")
    print(f"- **Order Status:** {status}")
    print(f"- **Payment Method:** Credit Card (ending in {last_digits})")
    print(f"- **Transaction Date:** {current_date}")
    print("="*50)

    print("\nThis is a demo of the payment success message format.")
    print("In a real application, this would be displayed after successfully capturing a payment.")


if __name__ == "__main__":
    display_payment_success_demo()
