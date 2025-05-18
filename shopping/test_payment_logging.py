"""
Test script to verify automatic payment logging functionality
"""
import asyncio
from agents.paypal_agent import PayPalAgent
import json
import os


async def test_payment_logging():
    print("\n=== Testing Automatic Payment Logging ===")

    # Initialize PayPal agent
    print("\n1. Initializing PayPal Agent...")
    agent = PayPalAgent()
    await agent.initialize()

    try:
        # Create a test order
        print("\n2. Creating test payment order...")
        order_data = await agent.create_payment_order(
            amount="10.00",
            currency="USD",
            description="Test Product for Logging",
            payee_email="somit.shrestha-facilitator@gmail.com"
        )

        print("\nOrder created:")
        print(json.dumps(order_data, indent=2))

        # Verify order was logged
        print("\n3. Verifying order creation was logged...")
        with open('paymentdetail.json', 'r') as f:
            payment_logs = json.load(f)
            latest_log = payment_logs[-1]
            print("\nLatest payment log:")
            print(json.dumps(latest_log, indent=2))

            if latest_log['action'] == 'create_order' and latest_log['paypal_order_id'] == order_data['id']:
                print("\n✅ Order creation was automatically logged!")
            else:
                print("\n❌ Order creation logging failed!")

        # Try to capture payment (will likely fail as it's not approved, but should still log)
        print("\n4. Testing payment capture logging...")
        capture_data = await agent.capture_payment(order_data['id'])

        # Verify capture was logged
        print("\n5. Verifying capture attempt was logged...")
        with open('paymentdetail.json', 'r') as f:
            payment_logs = json.load(f)
            latest_log = payment_logs[-1]
            print("\nLatest payment log:")
            print(json.dumps(latest_log, indent=2))

            if latest_log['action'] in ['capture_payment', 'capture_payment_error']:
                print("\n✅ Capture attempt was automatically logged!")
            else:
                print("\n❌ Capture logging failed!")

    except Exception as e:
        print(f"\nError during test: {str(e)}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_payment_logging())
