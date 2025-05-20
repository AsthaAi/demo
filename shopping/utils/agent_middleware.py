"""
Agent Communication Middleware
Handles secure communication between agents with risk monitoring
"""
from typing import Dict, Any, Optional, Set
from agents.risk_agent import RiskAgent
from utils.init_directories import init_directories
import asyncio
from datetime import datetime

# Initialize required directories
init_directories()


class AgentMiddleware:
    """Middleware for handling agent communications with risk monitoring"""

    def __init__(self):
        """Initialize the middleware"""
        self._risk_agent = None  # Will be initialized asynchronously
        self._initialized = False
        self._active_agents: Set[str] = set()
        self._revoked_agents: Set[str] = set()
        self._agent_sessions: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the middleware and risk agent"""
        if not self._initialized:
            try:
                print("\nInitializing Agent Middleware...")
                # Create and initialize risk agent
                self._risk_agent = RiskAgent()
                await self._risk_agent.initialize()
                self._initialized = True
                print("✅ Agent middleware initialized with risk monitoring")
            except Exception as e:
                print(f"❌ Failed to initialize agent middleware: {str(e)}")
                # Clean up if initialization fails
                self._risk_agent = None
                self._initialized = False
                raise

    async def register_agent(self, agent_id: str, agent_type: str) -> bool:
        """Register a new agent with the middleware"""
        try:
            if not self._initialized:
                await self.initialize()

            if agent_id in self._revoked_agents:
                print(
                    f"⚠️ Attempted registration of revoked agent: {agent_id}")
                return False

            self._active_agents.add(agent_id)
            self._agent_sessions[agent_id] = {
                "type": agent_type,
                "registration_time": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "communication_count": 0,
                "suspicious_activities": 0
            }
            return True
        except Exception as e:
            print(f"❌ Failed to register agent {agent_id}: {str(e)}")
            return False

    async def handle_revocation(self, agent_id: str, reason: str):
        """Handle the revocation of an agent's identity"""
        try:
            self._active_agents.discard(agent_id)
            self._revoked_agents.add(agent_id)

            if agent_id in self._agent_sessions:
                self._agent_sessions[agent_id].update({
                    "revocation_time": datetime.now().isoformat(),
                    "revocation_reason": reason,
                    "status": "revoked"
                })

            print(f"🚫 Agent {agent_id} has been revoked. Reason: {reason}")

            # Notify other active agents
            notification = {
                "event": "agent_revoked",
                "agent_id": agent_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }

            for other_agent_id in self._active_agents:
                if other_agent_id != agent_id:
                    try:
                        await self._risk_agent.communicate_with_agent(
                            target_agent_id=other_agent_id,
                            message=notification,
                            communication_type="revocation_notice",
                            details={"priority": "high"}
                        )
                    except Exception as e:
                        print(
                            f"❌ Failed to notify agent {other_agent_id}: {str(e)}")

        except Exception as e:
            print(
                f"❌ Error handling revocation for agent {agent_id}: {str(e)}")

    async def route_communication(
        self,
        source_agent_id: str,
        target_agent_id: str,
        message: Any,
        communication_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Route and monitor communication between agents"""
        if not self._initialized:
            await self.initialize()

        # Validate agents
        if source_agent_id not in self._active_agents or target_agent_id not in self._active_agents:
            print(f"⚠️ Communication blocked: Unregistered or inactive agent")
            return None

        if source_agent_id in self._revoked_agents or target_agent_id in self._revoked_agents:
            print(f"⚠️ Communication blocked: Revoked agent involved")
            return None

        try:
            # Update session data
            if source_agent_id in self._agent_sessions:
                self._agent_sessions[source_agent_id].update({
                    "last_activity": datetime.now().isoformat(),
                    "communication_count": self._agent_sessions[source_agent_id]["communication_count"] + 1
                })

            # Monitor communication
            is_safe = await self._risk_agent.monitor_agent_communication(
                source_agent_id=source_agent_id,
                target_agent_id=target_agent_id,
                data={
                    "message": message,
                    "type": communication_type,
                    "timestamp": datetime.now().isoformat(),
                    "details": details or {}
                },
                communication_type=communication_type
            )

            if not is_safe:
                print(
                    f"⚠️ Suspicious communication detected from {source_agent_id}")
                if source_agent_id in self._agent_sessions:
                    self._agent_sessions[source_agent_id]["suspicious_activities"] += 1
                    if self._agent_sessions[source_agent_id]["suspicious_activities"] >= 3:
                        await self.handle_revocation(
                            source_agent_id,
                            "Multiple suspicious communications detected"
                        )
                return None

            # Process communication
            return await self._risk_agent.communicate_with_agent(
                target_agent_id=target_agent_id,
                message=message,
                communication_type=communication_type,
                details=details
            )

        except Exception as e:
            print(f"❌ Error in communication: {str(e)}")
            return None

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the current status and session information for an agent"""
        status = "unknown"
        if agent_id in self._revoked_agents:
            status = "revoked"
        elif agent_id in self._active_agents:
            status = "active"

        return {
            "status": status,
            "session_info": self._agent_sessions.get(agent_id, {}),
            "is_revoked": agent_id in self._revoked_agents,
            "is_active": agent_id in self._active_agents
        }


# Global middleware instance
agent_middleware = AgentMiddleware()
