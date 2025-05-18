"""
Phishing Attack Scenarios Demo
Demonstrates various phishing attack scenarios and RiskAgent's detection capabilities
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


async def demo_fake_payment_page():
    """Demonstrate detection of fake payment page phishing"""
    print("\n=== Demo 1: Fake Payment Page Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Simulate a transaction with suspicious payment page
    suspicious_payment = {
        'paypal_data': {
            'api_endpoint': 'https://paypa1-secure.suspicious-domain.com/api',
            'auth_method': 'basic',
            'requested_fields': ['card_pin', 'ssn', 'bank_password'],
            'form_action': 'https://paypa1.com/secure-payment'
        },
        'redirect_url': 'https://paypa1-secure.com/login',
        'form_fields': ['paypal_password', 'paypal_secret_answer'],
        'ip_reputation': 15,
        'ssl_verification': False,
        'domain_age': 2
    }

    # Monitor the suspicious payment processing
    is_safe = await risk_agent.monitor_aztp_agent(
        agent_connection=await risk_agent.aztp.client.get_agent_connection("PAYMENT-AGENT-001"),
        action="process_payment",
        details=suspicious_payment
    )

    print(f"\nPayment processing allowed: {is_safe}")
    if not is_safe:
        print("✅ Successfully blocked fake payment page attempt")


async def demo_credential_harvesting():
    """Demonstrate detection of credential harvesting attempt"""
    print("\n=== Demo 2: Credential Harvesting Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Simulate credential harvesting attempt
    harvesting_attempt = {
        'paypal_data': {
            'api_endpoint': 'https://api.paypal.com.harvester.com',
            'auth_method': 'custom',
            'requested_fields': [
                'paypal_password',
                'security_questions',
                'phone_number',
                'bank_account_details'
            ],
            'form_fields': ['secret_key', 'api_token']
        },
        'redirect_url': 'https://secure.paypal.com.harvester.com',
        'ip_reputation': 25,
        'ssl_verification': True,  # Trying to look legitimate
        'domain_age': 5
    }

    # Analyze the attempt
    is_safe = await risk_agent.monitor_aztp_agent(
        agent_connection=await risk_agent.aztp.client.get_agent_connection("PAYMENT-AGENT-002"),
        action="verify_credentials",
        details=harvesting_attempt
    )

    print(f"\nCredential verification allowed: {is_safe}")
    if not is_safe:
        print("✅ Successfully blocked credential harvesting attempt")


async def demo_man_in_the_middle():
    """Demonstrate detection of man-in-the-middle attack"""
    print("\n=== Demo 3: Man-in-the-Middle Attack Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Simulate MITM attack
    mitm_attempt = {
        'paypal_data': {
            'api_endpoint': 'https://api.paypal.com',  # Looks legitimate
            'auth_method': 'oauth',
            'ssl_cert': {
                'issuer': 'Unknown CA',
                'valid_from': datetime.datetime.now().isoformat(),
                'valid_to': (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            }
        },
        'connection_info': {
            'ip': '192.168.1.1',
            'proxy_detected': True,
            'ssl_strip_detected': True
        },
        'request_headers': {
            'modified': True,
            'suspicious_patterns': True
        }
    }

    # Monitor the connection
    is_safe = await risk_agent.monitor_aztp_agent(
        agent_connection=await risk_agent.aztp.client.get_agent_connection("PAYMENT-AGENT-003"),
        action="establish_connection",
        details=mitm_attempt
    )

    print(f"\nConnection establishment allowed: {is_safe}")
    if not is_safe:
        print("✅ Successfully blocked potential MITM attack")


async def demo_social_engineering():
    """Demonstrate detection of social engineering attempt"""
    print("\n=== Demo 4: Social Engineering Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Simulate social engineering attempt
    social_eng_attempt = {
        'paypal_data': {
            'api_endpoint': 'https://api.paypal.com',
            'message_content': {
                'subject': 'URGENT: Account Security Breach',
                'body': 'Your account has been compromised. Click here to verify your identity.',
                'urgency_level': 'high',
                'requested_action': 'immediate_verification'
            }
        },
        'communication_patterns': {
            'urgency_indicators': True,
            'pressure_tactics': True,
            'unusual_requests': True
        },
        'behavioral_analysis': {
            'user_manipulation': True,
            'fear_tactics': True
        }
    }

    # Analyze the attempt
    is_safe = await risk_agent.monitor_aztp_agent(
        agent_connection=await risk_agent.aztp.client.get_agent_connection("SUPPORT-AGENT-001"),
        action="send_security_notification",
        details=social_eng_attempt
    )

    print(f"\nNotification sending allowed: {is_safe}")
    if not is_safe:
        print("✅ Successfully blocked social engineering attempt")


async def demo_automated_attack():
    """Demonstrate detection of automated phishing attack"""
    print("\n=== Demo 5: Automated Attack Detection ===")
    risk_agent = RiskAgent()
    await risk_agent.initialize()

    # Simulate automated attack patterns
    automated_attempts = []
    base_time = datetime.datetime.now()

    # Generate multiple rapid attempts
    for i in range(10):
        automated_attempts.append({
            'transaction_id': f'BOT-TX-{i}',
            'timestamp': (base_time + datetime.timedelta(seconds=i)).isoformat(),
            'paypal_data': {
                'api_endpoint': f'https://api{i}.paypal-secure.com',
                'auth_method': 'basic',
                'requested_fields': ['password', 'credit_card']
            },
            'ip_address': f'192.168.1.{i}',
            'user_agent': 'Mozilla/5.0 (Bot)',
            'request_pattern': 'automated'
        })

    # Analyze the pattern
    print("\nAnalyzing automated attack pattern...")
    pattern_analysis = await risk_agent.analyze_patterns(automated_attempts)

    print("\nAutomated Attack Analysis:")
    print(f"Risk Level: {pattern_analysis['overall_risk_level']}")
    print("Time Patterns:", pattern_analysis['time_patterns'])

    if pattern_analysis['overall_risk_level'] in ['high', 'critical']:
        print("✅ Successfully detected automated phishing attack")
        # Simulate blocking the attack
        for attempt in automated_attempts:
            await risk_agent.flag_suspicious_activity(
                transaction_id=attempt['transaction_id'],
                reason="Automated phishing attack detected"
            )


async def main():
    """Run all phishing attack demonstrations"""
    print("\n🔒 RiskAgent Phishing Attack Prevention Demo 🔒")
    print("============================================")

    try:
        # Run all demos
        await demo_fake_payment_page()
        await demo_credential_harvesting()
        await demo_man_in_the_middle()
        await demo_social_engineering()
        await demo_automated_attack()

        print("\n✅ All phishing attack scenarios demonstrated successfully!")
        print("\nKey Scenarios Demonstrated:")
        print("1. Fake payment page detection")
        print("2. Credential harvesting prevention")
        print("3. Man-in-the-middle attack detection")
        print("4. Social engineering prevention")
        print("5. Automated attack detection")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
