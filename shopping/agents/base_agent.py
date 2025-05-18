"""
Base Agent Class for ShopperAI
Provides common functionality and secure communication for all agents
"""
from crewai import Agent
from typing import Dict, Any, Optional
from aztp_client import Aztp
import asyncio
import uuid
import os
from dotenv import load_dotenv

load_dotenv()


class BaseAgent(Agent):
    """Base agent class with secure communication capabilities"""

    def __init__(self, **kwargs):
        """Initialize the base agent"""
        super().__init__(**kwargs)

        # Initialize AZTP client
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")
        self.aztpClient = Aztp(api_key=api_key)

        # Initialize agent properties
        self.agent_type = kwargs.get(
            'role', 'unknown').lower().replace(' ', '_')
        self.secured_connection = None
        self.aztp_id = ""
        self.is_initialized = False

    async def initialize(self):
        """Initialize the agent and set up secure connection"""
        try:
            print(f"\nInitializing agent: {self.agent_type}")

            # Each agent type should override these settings
            connection_settings = self.get_connection_settings()

            # Establish secure connection
            self.secured_connection = await self.aztpClient.secure_connect(
                self,
                self.agent_type,
                connection_settings
            )

            # Store AZTP ID
            if self.secured_connection and hasattr(self.secured_connection, 'identity'):
                self.aztp_id = self.secured_connection.identity.aztp_id
                print(
                    f"✅ Secured connection established. AZTP ID: {self.aztp_id}")

            # Verify identity
            self.is_valid = await self.aztpClient.verify_identity(self.secured_connection)
            if not self.is_valid:
                raise ValueError(
                    f"Failed to verify identity for agent: {self.agent_type}")

            self.is_initialized = True
            print(f"✅ Agent {self.agent_type} initialized successfully")

        except Exception as e:
            print(f"❌ Error initializing agent {self.agent_type}: {str(e)}")
            raise

    def get_connection_settings(self) -> Dict[str, Any]:
        """
        Get agent-specific connection settings.
        Should be overridden by each agent type.

        Returns:
            Dict containing connection settings
        """
        return {
            "isGlobalIdentity": False
        }

    async def communicate(
        self,
        target_agent_id: str,
        message: Any,
        communication_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Communicate with another agent through secure connection

        Args:
            target_agent_id: AZTP ID of the target agent
            message: Message or data to send
            communication_type: Type of communication
            details: Additional communication details

        Returns:
            Optional[Dict[str, Any]]: Response from target agent if successful
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # Get target agent's secure connection
            target_connection = await self.aztpClient.get_agent_connection(target_agent_id)
            if not target_connection:
                print(
                    f"❌ Could not establish connection with agent {target_agent_id}")
                return None

            # Send message through secure channel
            response = await self.aztpClient.send_secure_message(
                self.secured_connection,
                target_connection,
                {
                    "message": message,
                    "type": communication_type,
                    "details": details or {},
                    "timestamp": asyncio.get_event_loop().time()
                }
            )

            return response

        except Exception as e:
            print(f"❌ Communication error: {str(e)}")
            return None

    async def handle_revocation_notice(self, notification: Dict[str, Any]):
        """
        Handle notification of another agent's identity revocation

        Args:
            notification: Dictionary containing revocation details
        """
        try:
            revoked_agent = notification.get("agent_id")
            reason = notification.get("reason")
            print(f"📢 Received revocation notice for agent {revoked_agent}")
            print(f"Reason: {reason}")

            # Remove any stored connections or references to the revoked agent
            # Specific cleanup will be implemented by child classes
            pass

        except Exception as e:
            print(f"❌ Error handling revocation notice: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of this agent"""
        return {
            "agent_type": self.agent_type,
            "aztp_id": self.aztp_id,
            "is_initialized": self.is_initialized,
            "is_valid": getattr(self, 'is_valid', False)
        }
