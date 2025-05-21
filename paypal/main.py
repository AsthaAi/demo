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

# Get PayPal tools by name
paypal_tools = {tool.name: tool for tool in toolkit.get_tools()}

# Menu for secure communication


def secure_communicate_menu():
    print("\nSecure Communication with PayPalAgent")
    print("1. FakeAgent tries to communicate")
    print("2. MarketAgent tries to communicate")
    choice = input("Choose an option (1 or 2): ").strip()
    if choice == "1":
        # FakeAgent: No identity, should return Unauthorized
        result = run_async(paypal_agent.secure_communicate(
            fake_agent, data={}, action="payment_processing"))
        print("FakeAgent result:", result)
    elif choice == "2":
        # MarketAgent: Different trust domain, should return Policy violation
        run_async(market_agent.initialize())
        result = run_async(paypal_agent.secure_communicate(
            market_agent, data={}, action="payment_processing"))
        print("MarketAgent result:", result)
    else:
        print("Invalid option.")


def create_order_wrapper(input_str: str) -> str:
    """Create a PayPal order with the given details"""
    try:
        # Parse the input string to extract order details
        # Format: "amount currency description"
        parts = input_str.split()
        if len(parts) >= 3:
            amount = float(parts[0])
            currency = parts[1].upper()  # Ensure currency is uppercase
            description = ' '.join(parts[2:])

            # Validate currency
            # Add more supported currencies as needed
            if currency not in ['USD', 'EUR', 'GBP']:
                return "Invalid currency. Supported currencies: USD, EUR, GBP"

            # Validate amount
            if amount <= 0:
                return "Amount must be greater than 0"

            if 'create_order' not in paypal_tools:
                return "Create order tool not available"

            result = paypal_tools['create_order'].run({
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "description": description,
                "intent": "CAPTURE"
            })
            return str(result)
        return "Invalid input format. Please provide: amount currency description"
    except Exception as e:
        return f"Error creating order: {str(e)}"


def pay_order_wrapper(order_id: str) -> str:
    """Pay for a PayPal order"""
    try:
        if 'capture_order' not in paypal_tools:
            return "Capture order tool not available"

        result = paypal_tools['capture_order'].run({
            "order_id": order_id
        })
        return str(result)
    except Exception as e:
        return f"Error paying order: {str(e)}"


def get_order_details_wrapper(order_id: str) -> str:
    """Get details of a PayPal order"""
    try:
        if 'get_order' not in paypal_tools:
            return "Get order tool not available"

        result = paypal_tools['get_order'].run({
            "order_id": order_id
        })
        return str(result)
    except Exception as e:
        return f"Error getting order details: {str(e)}"


# Define tools as LangChain Tool objects
tools = [
    Tool(
        name="create_order",
        description="Create a new PayPal order. Input format: 'amount currency description' (e.g., '10.99 USD Product description')",
        func=create_order_wrapper
    ),
    Tool(
        name="pay_order",
        description="Pay for an existing PayPal order using its ID",
        func=pay_order_wrapper
    ),
    Tool(
        name="get_order_details",
        description="Get details of an existing PayPal order using its ID",
        func=get_order_details_wrapper
    )
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

# Add secure communication test
secure_communicate_menu()
