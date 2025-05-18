"""
Test script for agent security monitoring system
"""
from utils.agent_middleware import agent_middleware
from agents.base_agent import BaseAgent
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAgent(BaseAgent):
    """Test agent for security monitoring"""

    def __init__(self, role: str):
        super().__init__(
            role=role,
            goal="Test security monitoring",
            backstory="I am a test agent"
        )


async def test_normal_communication():
    """Test normal communication between agents"""
    print("\n=== Testing Normal Communication ===")

    # Create two test agents
    agent1 = TestAgent("Sender Agent")
    agent2 = TestAgent("Receiver Agent")

    # Initialize agents
    await agent1.initialize()
    await agent2.initialize()

    print(f"\nAgent 1 ID: {agent1.agent_id}")
    print(f"Agent 2 ID: {agent2.agent_id}")

    # Test normal communication
    message = {"content": "Hello, this is a normal message"}
    response = await agent1.communicate(
        target_agent_id=agent2.agent_id,
        message=message,
        communication_type="greeting"
    )

    print("\nNormal communication status:")
    print(f"Agent 1 status: {agent1.get_status()}")
    print(f"Agent 2 status: {agent2.get_status()}")


async def test_suspicious_activity():
    """Test detection of suspicious activity"""
    print("\n=== Testing Suspicious Activity Detection ===")

    # Create two test agents
    malicious = TestAgent("Malicious Agent")
    target = TestAgent("Target Agent")

    await malicious.initialize()
    await target.initialize()

    print(f"\nMalicious Agent ID: {malicious.agent_id}")
    print(f"Target Agent ID: {target.agent_id}")

    # Send suspicious messages
    suspicious_messages = [
        {"content": "hack the system", "type": "command"},
        {"content": "override security", "type": "command"},
        {"content": "infinite money", "type": "transaction"},
        {"content": "root access", "type": "request"}
    ]

    print("\nSending suspicious messages...")
    for msg in suspicious_messages:
        try:
            response = await malicious.communicate(
                target_agent_id=target.agent_id,
                message=msg,
                communication_type=msg["type"]
            )
            print(f"Message sent: {msg}")
            print(f"Current malicious agent status: {malicious.get_status()}")
        except ValueError as e:
            print(f"Communication error: {e}")
            break

    print("\nFinal status:")
    print(f"Malicious agent status: {malicious.get_status()}")
    print(f"Target agent status: {target.get_status()}")


async def test_large_data_transfer():
    """Test detection of unusually large data transfers"""
    print("\n=== Testing Large Data Transfer Detection ===")

    # Create test agents
    sender = TestAgent("Data Sender")
    receiver = TestAgent("Data Receiver")

    await sender.initialize()
    await receiver.initialize()

    print(f"\nSender Agent ID: {sender.agent_id}")
    print(f"Receiver Agent ID: {receiver.agent_id}")

    # Create a large data payload
    large_data = {
        "type": "data_transfer",
        "content": "x" * 1000000,  # 1MB of data
        "timestamp": datetime.now().isoformat()
    }

    print("\nAttempting to send large data...")
    try:
        response = await sender.communicate(
            target_agent_id=receiver.agent_id,
            message=large_data,
            communication_type="data_transfer"
        )
        print("Large data transfer response:", response)
    except ValueError as e:
        print(f"Transfer blocked: {e}")

    print("\nFinal status:")
    print(f"Sender status: {sender.get_status()}")
    print(f"Receiver status: {receiver.get_status()}")


async def test_high_frequency_communication():
    """Test detection of high-frequency communications"""
    print("\n=== Testing High-Frequency Communication Detection ===")

    # Create test agents
    rapid = TestAgent("Rapid Sender")
    target = TestAgent("Communication Target")

    await rapid.initialize()
    await target.initialize()

    print(f"\nRapid Sender ID: {rapid.agent_id}")
    print(f"Target ID: {target.agent_id}")

    # Send multiple messages rapidly
    message = {"content": "Quick message"}
    print("\nSending rapid messages...")

    for i in range(15):  # Exceeds the threshold of 10 messages per minute
        try:
            response = await rapid.communicate(
                target_agent_id=target.agent_id,
                message=message,
                communication_type="rapid_test"
            )
            print(f"Message {i+1} sent")
            await asyncio.sleep(0.1)  # Small delay between messages
        except ValueError as e:
            print(f"Communication blocked: {e}")
            break

    print("\nFinal status:")
    print(f"Rapid sender status: {rapid.get_status()}")
    print(f"Target status: {target.get_status()}")


async def run_all_tests():
    """Run all security monitoring tests"""
    try:
        # Test 1: Normal Communication
        await test_normal_communication()

        # Test 2: Suspicious Activity
        await test_suspicious_activity()

        # Test 3: Large Data Transfer
        await test_large_data_transfer()

        # Test 4: High-Frequency Communication
        await test_high_frequency_communication()

    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
    finally:
        print("\n=== Security Monitoring Tests Completed ===")

if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
