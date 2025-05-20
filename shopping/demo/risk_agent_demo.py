"""
Risk Agent Demo Script
Demonstrates various security scenarios and RiskAgent's capabilities
"""
import asyncio
import datetime
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import from shopping
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))

try:
    from agents.risk_agent import RiskAgent
    from aztp_client.client import SecureConnection
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you have installed all requirements from requirements.txt")
    sys.exit(1)


async def demo_normal_transaction():
    """Demonstrate normal, low-risk transaction processing"""
    print("\n=== Demo 1: Normal Transaction Processing ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Create a normal transaction
    normal_transaction = {
        'transaction_id': 'TX-NORMAL-001',
        'amount': 50.00,
        'timestamp': datetime.datetime.now().isoformat(),
        'location': 'New York',
        'device_info': {
            'os': 'macOS',
            'browser': 'Chrome',
            'is_new_device': False
        },
        'user_history': [
            {
                'amount': 45.00,
                'timestamp': (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
                'status': 'COMPLETED'
            }
        ]
    }

    print("\nAnalyzing normal transaction...")
    result = await risk_agent.analyze_transaction(normal_transaction)
    print("\nRisk Analysis Result:")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Risk Factors:")
    for factor, level in result['risk_factors'].items():
        print(f"- {factor}: {level}")


async def demo_suspicious_transaction():
    """Demonstrate detection of suspicious transaction patterns"""
    print("\n=== Demo 2: Suspicious Transaction Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Create suspicious transactions (high frequency, large amounts)
    suspicious_transactions = []
    base_time = datetime.datetime.now()

    for i in range(6):  # Create 6 rapid transactions
        suspicious_transactions.append({
            'transaction_id': f'TX-SUSP-00{i}',
            'amount': 2000.00,  # Large amount
            # 30 seconds apart
            'timestamp': (base_time + datetime.timedelta(seconds=30 * i)).isoformat(),
            # Multiple locations
            'location': ['New York', 'London', 'Tokyo', 'Sydney'][i % 4],
            'device_info': {
                'os': 'Windows',
                'browser': 'Chrome',
                'is_new_device': True
            }
        })

    print("\nAnalyzing suspicious transaction patterns...")
    pattern_analysis = await risk_agent.analyze_patterns(suspicious_transactions)
    print("\nPattern Analysis Result:")
    print(f"Overall Risk Level: {pattern_analysis['overall_risk_level']}")
    print("\nTime Patterns:")
    print(pattern_analysis['time_patterns'])
    print("\nLocation Patterns:")
    print(pattern_analysis['location_patterns'])


async def demo_phishing_detection():
    """Demonstrate phishing attempt detection"""
    print("\n=== Demo 3: Phishing Attack Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Simulate a phishing attempt
    print("\nSimulating phishing attack...")
    phishing_result = await risk_agent.simulate_phishing_attack("PAYMENT-AGENT-001")
    print("\nPhishing Detection Result:")
    print(f"Status: {phishing_result['status']}")
    print(f"Action Taken: {phishing_result['action_taken']}")


async def demo_agent_monitoring():
    """Demonstrate monitoring of agent communications"""
    print("\n=== Demo 4: Agent Communication Monitoring ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Monitor normal agent communication
    print("\nMonitoring normal agent communication...")
    normal_comm_result = await risk_agent.monitor_agent_communication(
        source_agent_id="AGENT-001",
        target_agent_id="AGENT-002",
        data={"message": "Hello", "type": "greeting"},
        communication_type="normal"
    )
    print(f"Normal communication allowed: {normal_comm_result}")

    # Monitor suspicious agent communication
    print("\nMonitoring suspicious agent communication...")
    suspicious_data = {
        "message": "hack override admin access",
        "payload": "x" * 1000000  # Large data payload
    }
    suspicious_comm_result = await risk_agent.monitor_agent_communication(
        source_agent_id="AGENT-003",
        target_agent_id="AGENT-004",
        data=suspicious_data,
        communication_type="suspicious"
    )
    print(f"Suspicious communication allowed: {suspicious_comm_result}")


async def demo_high_risk_notification():
    """Demonstrate high-risk transaction notification system"""
    print("\n=== Demo 5: High-Risk Transaction Notification ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Create a high-risk transaction
    high_risk_transaction = {
        'transaction_id': 'TX-HIGH-001',
        'amount': 50000.00,  # Very large amount
        'timestamp': datetime.datetime.now().isoformat(),
        'location': 'Unknown',
        'device_info': {
            'os': 'Unknown',
            'browser': 'Unknown',
            'is_new_device': True,
            'suspicious_patterns': True
        }
    }

    # Analyze and notify
    print("\nAnalyzing high-risk transaction...")
    analysis = await risk_agent.analyze_transaction(high_risk_transaction)

    if analysis['risk_level'] in ['high', 'critical']:
        print("\nSending high-risk notifications...")
        await risk_agent.notify_high_risk(
            transaction_id=high_risk_transaction['transaction_id'],
            risk_level=analysis['risk_level'],
            details=analysis
        )


async def main():
    """Run all demos"""
    print("\n🔒 RiskAgent Capability Demonstration 🔒")
    print("=======================================")

    try:
        # Run all demos
        await demo_normal_transaction()
        await demo_suspicious_transaction()
        await demo_phishing_detection()
        await demo_agent_monitoring()
        await demo_high_risk_notification()

        print("\n✅ All demonstrations completed successfully!")
        print("\nKey Features Demonstrated:")
        print("1. Normal transaction risk analysis")
        print("2. Suspicious pattern detection")
        print("3. Phishing attack prevention")
        print("4. Agent communication monitoring")
        print("5. High-risk notification system")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
