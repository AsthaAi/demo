"""
Example of integrating PayPal Agent with OrderAgent
"""
from crewai import Crew, Task
from agents.order_agent import OrderAgent
from agents.paypal_agent import PayPalAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def process_order_with_payment(product_details: dict, customer_email: str):
    """
    Process an order with PayPal payment integration

    Args:
        product_details: Dictionary containing product information
        customer_email: Customer's email address
    """
    # Initialize agents
    order_agent = OrderAgent()
    paypal_agent = PayPalAgent()

    # Create tasks
    order_task = Task(
        description=f"""
        Process the order for the following product:
        - Name: {product_details.get('name')}
        - Price: {product_details.get('price')}
        - Quantity: {product_details.get('quantity', 1)}
        
        Generate order details and prepare for payment processing.
        """,
        agent=order_agent
    )

    payment_task = Task(
        description=f"""
        Create and process PayPal payment for the order:
        - Amount: {product_details.get('price')}
        - Customer Email: {customer_email}
        - Description: Order for {product_details.get('name')}
        
        Create a PayPal order and capture the payment.
        """,
        agent=paypal_agent
    )

    # Create and run the crew
    crew = Crew(
        agents=[order_agent, paypal_agent],
        tasks=[order_task, payment_task],
        verbose=True
    )

    result = crew.kickoff()
    return result


if __name__ == "__main__":
    # Example usage
    product = {
        "name": "Premium Widget",
        "price": "99.99",
        "quantity": 1,
        "description": "High-quality premium widget"
    }

    customer_email = "customer@example.com"

    try:
        result = process_order_with_payment(product, customer_email)
        print("Order processed successfully:", result)
    except Exception as e:
        print(f"Error processing order: {str(e)}")
