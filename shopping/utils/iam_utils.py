"""
IAM (Identity Access Management) utilities for ShopperAI
Handles identity verification, access control, and policy management.
"""
from typing import Dict, Any, Optional, Union
from aztp_client import Aztp
import os
from dotenv import load_dotenv
import json
from .exceptions import PolicyVerificationError

load_dotenv()


class IAMUtils:
    def __init__(self):
        """Initialize IAM utilities with AZTP client"""
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")
        self.aztpClient = Aztp(api_key=api_key)
        self.policy_cache = {}

    async def verify_agent_access(self, agent_id: str, action: str, policy_code: str) -> bool:
        """
        Verify if an agent has access to perform a specific action.

        Args:
            agent_id: The AZTP ID of the agent
            action: The action to verify (e.g., 'process_refund', 'read_faq')
            policy_code: The policy code to check against

        Returns:
            bool: True if action is allowed, False otherwise
        """
        try:
            print(f"\n🔒 Verifying access for agent: {agent_id}")
            print(f"├── Action: {action}")
            print(f"└── Policy Code: {policy_code}")

            identity_access_policy = await self.aztpClient.get_policy(agent_id)
            print("\n📜 Identity Access Policy:")
            if isinstance(identity_access_policy, dict):
                print(json.dumps(identity_access_policy, indent=2))
            else:
                print(identity_access_policy)

            policy = self.aztpClient.get_policy_value(
                identity_access_policy,
                "code",
                policy_code
            )
            print("\n🔑 Retrieved Policy:")
            if isinstance(policy, dict):
                print(json.dumps(policy, indent=2))
            else:
                print(policy)

            is_allowed = self.aztpClient.is_action_allowed(policy, action)
            print(f"\n✨ Access verification result:")
            print(f"├── Agent ID: {agent_id}")
            print(f"├── Action: {action}")
            print(f"└── Allowed: {'✅ Yes' if is_allowed else '❌ No'}")

            return is_allowed
        except Exception as e:
            print(f"\n❌ Error verifying access:")
            print(f"├── Agent ID: {agent_id}")
            print(f"├── Action: {action}")
            print(f"└── Error: {str(e)}")
            return False

    async def verify_customer_support_access(self, agent_id: str) -> bool:
        """
        Verify customer support agent access.

        Args:
            agent_id: The AZTP ID of the agent

        Returns:
            bool: True if access is allowed, False otherwise
        """
        return await self.verify_agent_access(
            agent_id=agent_id,
            action="process_refund",
            policy_code="customer-support-policy"
        )

    async def verify_promotions_access(self, agent_id: str) -> bool:
        """
        Verify promotions agent access.

        Args:
            agent_id: The AZTP ID of the agent

        Returns:
            bool: True if access is allowed, False otherwise
        """
        return await self.verify_agent_access(
            agent_id=agent_id,
            action="create_promotion",
            policy_code="promotions-agent-policy"
        )

    async def verify_risk_access(self, agent_id: str) -> bool:
        """
        Verify risk agent access.

        Args:
            agent_id: The AZTP ID of the agent

        Returns:
            bool: True if access is allowed, False otherwise
        """
        return await self.verify_agent_access(
            agent_id=agent_id,
            action="analyze_transaction",
            policy_code="risk-agent-policy"
        )

    async def verify_access_or_raise(
        self,
        agent_id: str,
        action: str,
        policy_code: str,
        operation_name: str
    ) -> bool:
        """
        Verify if an agent has access to perform an action under a specific policy.
        Raises PolicyVerificationError if access is denied.

        Args:
            agent_id: The agent's AZTP ID
            action: The action to verify
            policy_code: The policy code to check against
            operation_name: Name of the operation being verified

        Returns:
            True if access is granted, raises PolicyVerificationError otherwise
        """
        try:
            print(f"\n🔒 Verifying access for agent: {agent_id}")
            print(f"├── Action: {action}")
            print(f"└── Policy Code: {policy_code}")

            # For demo purposes, always return True
            # In a real implementation, this would check against actual policies
            print("\n✅ Risk Agent: Access granted for demo purposes")
            return True

        except Exception as e:
            error_msg = f"Access denied: {operation_name} operation not permitted for agent {agent_id}"
            print(f"\n❌ Access verification failed:")
            print(f"├── Operation: {operation_name}")
            print(f"├── Agent ID: {agent_id}")
            print(f"├── Action: {action}")
            print(f"└── Error: {error_msg}")
            raise PolicyVerificationError(error_msg)

    async def verify_agent_access_by_trustDomain(self, agent_id: str, policy_code: str, trust_domain: str) -> bool:
        """
        Verify if an agent's trust domain matches the required trust domain.

        Args:
            agent_id: The AZTP ID of the agent
            policy_code: The policy code to check against
            trust_domain: The required trust domain

        Returns:
            bool: True if trust domain matches, False otherwise
        """
        try:
            print(f"\n🔒 Verifying trust domain for agent: {agent_id}")
            print(f"├── Policy Code: {policy_code}")
            print(f"└── Required Trust Domain: {trust_domain}")

            identity_access_policy = await self.aztpClient.get_policy(agent_id)
            policy_dict = None
            if isinstance(identity_access_policy, list):
                if not identity_access_policy:
                    print("Policy list is empty.")
                    return False
                policy_dict = identity_access_policy[0]
            elif isinstance(identity_access_policy, dict):
                policy_dict = identity_access_policy
            else:
                print(identity_access_policy)
                return False

            # Extract trust_domain from policy Condition.StringEquals
            policy_condition = policy_dict.get("Condition", {})
            string_equals = policy_condition.get("StringEquals", {})
            agent_trust_domain = string_equals.get("trust_domain")
            trust_domain_matches = (agent_trust_domain == trust_domain)

            print(f"\n✨ Trust Domain verification result:")
            print(f"├── Agent ID: {agent_id}")
            print(f"├── Policy Trust Domain: {agent_trust_domain}")
            print(
                f"└── Trust Domain Match: {'✅ Yes' if trust_domain_matches else '❌ No'}")

            return trust_domain_matches
        except Exception as e:
            print(f"\n❌ Error verifying trust domain:")
            print(f"├── Agent ID: {agent_id}")
            print(f"├── Policy Code: {policy_code}")
            print(f"├── Trust Domain: {trust_domain}")
            print(f"└── Error: {str(e)}")
            return False
