import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Task
from langchain_openai import ChatOpenAI
from paypal_agent_toolkit.crewai.toolkit import PayPalToolkit
from paypal_agent_toolkit.shared.configuration import Configuration, Context
from langchain.tools import Tool
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Set up PayPal configuration to enable only the required tools
paypal_actions = {
    "orders": {"create": True, "capture": True, "get": True}
}
paypal_context = Context.default()  # or Context(sandbox=True)
paypal_config = Configuration(actions=paypal_actions, context=paypal_context)

# Initialize PayPal toolkit with credentials and configuration
toolkit = PayPalToolkit(
    client_id=os.getenv('PAYPAL_CLIENT_ID'),
    secret=os.getenv('PAYPAL_SECRET'),
    configuration=paypal_config
)

# Create wrapper functions for PayPal tools


def create_order_wrapper(input_str: str) -> str:
    """Create a PayPal order with the given details"""
    try:
        # Parse the input string to extract order details
        # For now, we'll use a simple format: "amount currency description"
        parts = input_str.split()
        if len(parts) >= 3:
            amount = float(parts[0])
            currency = parts[1]
            description = ' '.join(parts[2:])
            result = toolkit.get_tools()[0].run({
                "amount": amount,
                "currency": currency,
                "description": description
            })
            return str(result)
        return "Invalid input format. Please provide: amount currency description"
    except Exception as e:
        return f"Error creating order: {str(e)}"


def pay_order_wrapper(order_id: str) -> str:
    """Pay for a PayPal order"""
    try:
        result = toolkit.get_tools()[1].run({"order_id": order_id})
        return str(result)
    except Exception as e:
        return f"Error paying order: {str(e)}"


def get_order_details_wrapper(order_id: str) -> str:
    """Get details of a PayPal order"""
    try:
        result = toolkit.get_tools()[2].run({"order_id": order_id})
        return str(result)
    except Exception as e:
        return f"Error getting order details: {str(e)}"


# Define tools
tools = [
    {
        "name": "create_order",
        "description": "Create a new PayPal order. Input format: 'amount currency description'",
        "function": create_order_wrapper
    },
    {
        "name": "pay_order",
        "description": "Pay for an existing PayPal order using its ID",
        "function": pay_order_wrapper
    },
    {
        "name": "get_order_details",
        "description": "Get details of an existing PayPal order using its ID",
        "function": get_order_details_wrapper
    }
]

# Initialize the language model
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.7
)

# Create the agent
agent = Agent(
    role="PayPal Payment Assistant",
    goal="Help users with PayPal payment processing",
    backstory="I am an AI assistant specialized in handling PayPal payments and orders",
    tools=tools,
    llm=llm,
    verbose=True
)

# Create a task
task = Task(
    description="""
    Create a PayPal order for the following items:
    - Product 1: $50.00
    - Product 2: $75.00
    Apply a 10% discount and add $10.00 shipping cost.
    Use USD as the currency.
    """,
    agent=agent
)

# Create and run the crew
crew = Crew(
    agents=[agent],
    tasks=[task]
)

result = crew.kickoff()
print("\nResult:", result)
