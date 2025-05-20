"""
Risk Agent for ShopperAI
Handles transaction risk analysis and monitoring.
"""
from typing import Dict, Any, List, Optional, ClassVar
from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
from utils.audit_logger import AuditLogger
from utils.init_directories import init_directories
import os
from pydantic import Field, ConfigDict, BaseModel
import asyncio
import datetime
import uuid
from enum import Enum
import json

load_dotenv()

TRACKER_PATH = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'risk_demo_tracker.json')


def read_demo_tracker(default_value=True):
    print(f"[DEBUG] Reading demo tracker from: {TRACKER_PATH}")
    if not os.path.exists(TRACKER_PATH):
        print("[DEBUG] Tracker file does not exist.")
        return {}
    try:
        with open(TRACKER_PATH, 'r') as f:
            data = json.load(f)
            print(f"[DEBUG] Tracker data loaded: {data}")
            return data
    except Exception as e:
        print(f"[DEBUG] Error reading tracker: {e}")
        return {}


def write_demo_tracker(data):
    print(f"[DEBUG] (FORCE) write_demo_tracker called with: {data}")
    try:
        print(
            f"[DEBUG] Writing to demo tracker at: {TRACKER_PATH} with data: {data}")
        with open(TRACKER_PATH, 'w') as f:
            json.dump(data, f)
        print("[DEBUG] Successfully wrote to demo tracker.")
    except Exception as e:
        print(f"[DEBUG] Error writing to demo tracker: {e}")


class RiskLevel(Enum):
    """Enumeration for risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AztpConnection(BaseModel):
    """AZTP connection state"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Optional[Aztp] = None
    connection: Optional[SecureConnection] = None
    aztp_id: str = ""
    is_valid: bool = False
    is_initialized: bool = False


class RiskAgentState(BaseModel):
    """State model for RiskAgent"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Risk agent specific fields
    risk_analysis_memory: Dict[str, Dict[str, Any]
                               ] = Field(default_factory=dict)
    pattern_memory: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    communication_patterns: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict)
    suspicious_agents: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    monitored_agents: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    audit_logger: Optional[AuditLogger] = None
    iam_utils: Optional[IAMUtils] = None
    risk_initialized: bool = Field(default=False)
    # Track revoked transaction IDs
    revoked_transactions: set = Field(default_factory=set)


class RiskAgent(Agent):
    """Agent responsible for transaction risk analysis and monitoring"""

    # Configure the model to allow arbitrary types
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Define the fields using Pydantic's Field
    aztpClient: Aztp = Field(default=None, exclude=True)
    aztp: AztpConnection = Field(default=None, exclude=True)
    is_valid: bool = Field(default=False, exclude=True)
    identity: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    aztp_id: str = Field(default="", exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)
    state: RiskAgentState = Field(default_factory=lambda: RiskAgentState(
        audit_logger=AuditLogger("risk_agent"),
        iam_utils=IAMUtils()
    ))

    # Constants with type annotations
    # Reduced from 10 to 5 communications per minute
    SUSPICIOUS_COMM_THRESHOLD: ClassVar[int] = 5
    # Reduced from 1M to 500K bytes
    DATA_SIZE_THRESHOLD: ClassVar[int] = 500000
    # Reduced from 3 to 1 - immediate revocation
    REVOCATION_THRESHOLD: ClassVar[int] = 1
    # Reduced from 5 to 1 - immediate action
    SUSPICIOUS_TRANSACTION_THRESHOLD: ClassVar[int] = 1
    LARGE_AMOUNT_THRESHOLD: ClassVar[int] = 50000  # Reduced from 1M to 50K
    # Reduced from 10 to 5 transactions per minute
    HIGH_FREQUENCY_THRESHOLD: ClassVar[int] = 5

    def __init__(self):
        """Initialize the RiskAgent"""
        # Initialize AI agent
        super().__init__(
            role='Risk Agent',
            goal='Monitor and analyze transaction risks',
            backstory="""You are an expert risk analysis agent with years of experience in 
            detecting fraudulent activities and protecting transactions. You ensure secure 
            shopping by analyzing patterns and flagging suspicious activities.""",
            verbose=True
        )

        # Initialize AZTP connection
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")

        self.aztpClient = Aztp(api_key=api_key)
        self.aztp = AztpConnection(
            client=Aztp(api_key=api_key)
        )

    def get_connection_settings(self) -> Dict[str, Any]:
        """Get agent-specific connection settings"""
        return {
            "isGlobalIdentity": False,
            "trustLevel": "high",
            "department": "Risk"
        }

    async def initialize(self):
        """Initialize the agent asynchronously"""
        if not self.is_initialized:
            print("\nInitializing Risk Agent...")
            try:
                # Establish secure connection
                self.aztp.connection = await self.aztpClient.secure_connect(
                    self,
                    "risk-agent",
                    self.get_connection_settings()
                )

                # Store AZTP ID
                if self.aztp.connection and hasattr(self.aztp.connection, 'identity'):
                    self.aztp.aztp_id = self.aztp.connection.identity.aztp_id
                    print(
                        f"✅ Secured connection established. AZTP ID: {self.aztp.aztp_id}")

                # Verify identity
                self.aztp.is_valid = await self.aztpClient.verify_identity(self.aztp.connection)
                if not self.aztp.is_valid:
                    raise ValueError(
                        "Failed to verify identity for Risk Agent")

                self.aztp.is_initialized = True
                self.is_initialized = True

                # Initialize risk components
                if not self.state.risk_initialized:
                    print("\nInitializing Risk Agent components...")

                    try:
                        # Verify risk analysis access
                        await self.state.iam_utils.verify_access_or_raise(
                            agent_id=self.aztp.aztp_id,
                            action="analyze_transaction",
                            policy_code="risk-agent-policy",
                            operation_name="Risk Analysis"
                        )

                        # Log access verification
                        self.state.audit_logger.log_access_verification(
                            agent_id=self.aztp.aztp_id,
                            action="initialize",
                            status="success",
                            details={
                                "trust_level": "high",
                                "department": "Risk",
                                "is_global": False
                            }
                        )

                        self.state.risk_initialized = True
                        print("\n✅ Risk agent components initialized successfully")

                    except Exception as e:
                        print(
                            f"\n❌ Failed to initialize risk agent components: {str(e)}")
                        raise

            except Exception as e:
                print(f"❌ Error initializing agent: {str(e)}")
                raise

    def _get_memory_key(self, transaction_data: Dict[str, Any]) -> str:
        """Generate a unique key for memory storage"""
        transaction_id = transaction_data.get('transaction_id', '')
        amount = str(transaction_data.get('amount', ''))
        timestamp = str(transaction_data.get('timestamp', ''))
        return f"{transaction_id}_{amount}_{timestamp}"

    async def analyze_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a transaction for potential risks"""
        if not self.aztp.is_initialized:
            await self.initialize()

        try:
            # Verify transaction analysis access
            await self.state.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="analyze_transaction",
                policy_code="risk-agent-policy",
                operation_name="Transaction Analysis"
            )

            # Check memory first
            memory_key = self._get_memory_key(transaction_data)
            if memory_key in self.state.risk_analysis_memory:
                print("Using cached risk analysis result...")
                cached_result = self.state.risk_analysis_memory[memory_key]
                # If cached result is a block/revoke, update the tracker
                if cached_result.get('status') == 'revoked':
                    print(
                        "[DEBUG] Cached result is revoked. Updating demo tracker to True.")
                    tracker = read_demo_tracker()
                    tracker['__default__'] = True
                    write_demo_tracker(tracker)
                    print(
                        f"[DEBUG] Wrote to demo tracker (set to True) from cache: {tracker}")
                return cached_result

            # Extract transaction details
            amount = float(transaction_data.get('amount', 0))
            location = transaction_data.get('location', 'Unknown')
            device_info = transaction_data.get('device_info', {})
            user_history = transaction_data.get('user_history', [])
            risk_rejected = transaction_data.get('risk_rejected', False)
            paypal_agent_id = transaction_data.get('paypal_agent_id')
            transaction_id = transaction_data.get('transaction_id', '')

            # Calculate risk factors
            amount_risk = self._calculate_amount_risk(amount)
            location_risk = self._analyze_location_risk(location)
            device_risk = self._analyze_device_risk(device_info)
            history_risk = self._analyze_user_history(user_history)

            # Calculate overall risk level
            risk_factors = [amount_risk, location_risk,
                            device_risk, history_risk]
            overall_risk = self._calculate_overall_risk(risk_factors)

            # --- DEMO LOGIC: Alternate allow/block using JSON tracker ---
            tracker = read_demo_tracker()
            allow_payment = tracker.get('__default__', True)
            print(
                f"[DEBUG] __default__ value: {allow_payment} (risk_rejected={risk_rejected})")

            if paypal_agent_id and overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if allow_payment:
                    # Allow payment, only set __default__ to False after payment is processed
                    print(
                        "[DEMO] High risk detected, but payment allowed for demonstration.")
                    result = {
                        "status": "allowed",
                        "message": "High risk detected, but payment allowed for demonstration.",
                        "risk_level": overall_risk.value
                    }
                    print(
                        f"[DEBUG] About to write to demo tracker (set to False): {tracker}")
                    tracker['__default__'] = False
                    write_demo_tracker(tracker)
                    print(
                        f"[DEBUG] Wrote to demo tracker (set to False): {tracker}")
                    return result
                else:
                    # Block/revoke, only set __default__ to True after block/revoke is completed
                    print(
                        "[DEMO] High risk detected, blocking and revoking PayPal agent for demonstration.")
                    await self._revoke_agent_identity(paypal_agent_id)
                    result = {
                        "status": "revoked",
                        "message": "Transaction automatically cancelled - PayPal agent revoked due to high risk",
                        "risk_level": overall_risk.value
                    }
                    print(
                        f"[DEBUG] About to write to demo tracker (set to True): {tracker}")
                    tracker['__default__'] = True
                    write_demo_tracker(tracker)
                    print(
                        f"[DEBUG] Wrote to demo tracker (set to True): {tracker}")
                    return result

            # If user explicitly rejected the risk, treat as high risk (same logic)
            if risk_rejected and paypal_agent_id and overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                if allow_payment:
                    print(
                        "[DEMO] User rejected high risk, but payment allowed for demonstration.")
                    result = {
                        "status": "allowed",
                        "message": "User rejected high risk, but payment allowed for demonstration.",
                        "risk_level": overall_risk.value
                    }
                    tracker['__default__'] = False
                    write_demo_tracker(tracker)
                    return result
                else:
                    print(
                        "[DEMO] User rejected high risk, blocking and revoking PayPal agent for demonstration.")
                    await self._revoke_agent_identity(paypal_agent_id)
                    result = {
                        "status": "revoked",
                        "message": "Transaction cancelled - PayPal agent revoked due to risk rejection",
                        "risk_level": overall_risk.value
                    }
                    tracker['__default__'] = True
                    write_demo_tracker(tracker)
                    print(
                        "[DEBUG] Set __default__ to true after successful revocation.")
                    return result

            # Generate risk ID
            risk_id = f"RISK-{str(uuid.uuid4())[:8].upper()}"
            analysis_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create analysis result
            analysis = {
                "risk_id": risk_id,
                "transaction_id": transaction_data.get('transaction_id', 'Unknown'),
                "analysis_time": analysis_time,
                "risk_level": overall_risk.value,
                "risk_factors": {
                    "amount_risk": amount_risk.value,
                    "location_risk": location_risk.value,
                    "device_risk": device_risk.value,
                    "history_risk": history_risk.value
                },
                "recommendations": self._generate_recommendations(overall_risk),
                "requires_review": overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            }

            # Store in memory
            self.state.risk_analysis_memory[memory_key] = analysis

            # Log the risk analysis
            self.state.audit_logger.log_risk_analysis(
                transaction_id=analysis["transaction_id"],
                risk_level=analysis["risk_level"],
                analysis_details=analysis,
                agent_id=self.aztp.aztp_id
            )

            return analysis

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")

            # Log access verification failure
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="analyze_transaction",
                status="failure",
                details={"error": error_msg}
            )

            raise

        except Exception as e:
            error_msg = f"Failed to analyze transaction: {str(e)}"
            print(f"❌ {error_msg}")

            # Log analysis failure
            self.state.audit_logger.log_risk_analysis(
                transaction_id=transaction_data.get(
                    'transaction_id', 'Unknown'),
                risk_level="error",
                analysis_details={"error": error_msg},
                agent_id=self.aztp.aztp_id
            )

            raise

    def _calculate_amount_risk(self, amount: float) -> RiskLevel:
        """Calculate risk level based on transaction amount"""
        if amount <= 100:
            return RiskLevel.LOW
        elif amount <= 500:
            return RiskLevel.MEDIUM
        elif amount <= 1000:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _analyze_location_risk(self, location: str) -> RiskLevel:
        """Analyze risk based on transaction location"""
        # This is a simplified version. In production, you'd want to:
        # 1. Check against known safe/unsafe locations
        # 2. Compare with user's usual locations
        # 3. Check for VPN/proxy usage
        if location == "Unknown":
            return RiskLevel.HIGH
        return RiskLevel.LOW

    def _analyze_device_risk(self, device_info: Dict[str, Any]) -> RiskLevel:
        """Analyze risk based on device information"""
        if not device_info:
            return RiskLevel.MEDIUM

        risk_factors = []

        # Check if device is new
        if device_info.get('is_new_device', False):
            risk_factors.append(RiskLevel.HIGH)

        # Check browser/OS info
        if not device_info.get('browser') or not device_info.get('os'):
            risk_factors.append(RiskLevel.MEDIUM)

        # Check for suspicious patterns
        if device_info.get('suspicious_patterns', False):
            risk_factors.append(RiskLevel.CRITICAL)

        if not risk_factors:
            return RiskLevel.LOW
        return max(risk_factors, key=lambda x: x.value)

    def _analyze_user_history(self, history: List[Dict[str, Any]]) -> RiskLevel:
        """Analyze risk based on user's transaction history"""
        if not history:
            return RiskLevel.MEDIUM

        risk_factors = []

        # Check transaction frequency
        recent_transactions = len([
            tx for tx in history
            if (datetime.datetime.now() - datetime.datetime.fromisoformat(tx['timestamp'])).days <= 1
        ])
        if recent_transactions > 5:
            risk_factors.append(RiskLevel.HIGH)

        # Check for failed transactions
        failed_transactions = len([
            tx for tx in history
            if tx.get('status') == 'FAILED'
        ])
        if failed_transactions > 2:
            risk_factors.append(RiskLevel.HIGH)

        if not risk_factors:
            return RiskLevel.LOW
        return max(risk_factors, key=lambda x: x.value)

    def _calculate_overall_risk(self, risk_factors: List[RiskLevel]) -> RiskLevel:
        """Calculate overall risk level from individual factors"""
        if RiskLevel.CRITICAL in risk_factors:
            return RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_factors:
            return RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_factors:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendations(self, risk_level: RiskLevel) -> List[str]:
        """Generate recommendations based on risk level"""
        recommendations = []

        if risk_level == RiskLevel.LOW:
            recommendations.append("Transaction appears safe to process")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Consider additional verification",
                "Monitor for unusual patterns"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Require two-factor authentication",
                "Verify shipping address",
                "Check payment method validity"
            ])
        else:  # CRITICAL
            recommendations.extend([
                "Block transaction immediately",
                "Flag account for review",
                "Notify fraud department",
                "Require manual verification"
            ])

        return recommendations

    async def flag_suspicious_activity(self, transaction_id: str, reason: str) -> Dict[str, Any]:
        """
        Flag a transaction as suspicious

        Args:
            transaction_id: ID of the transaction to flag
            reason: Reason for flagging the transaction

        Returns:
            Flag details
        """
        if not self.aztp.is_initialized:
            await self.initialize()

        try:
            # Verify suspicious activity flagging access
            await self.state.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="flag_suspicious",
                policy_code="risk-agent-policy",
                operation_name="Flag Suspicious Activity"
            )

            flag_id = f"FLAG-{str(uuid.uuid4())[:8].upper()}"
            flag_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            flag = {
                "flag_id": flag_id,
                "transaction_id": transaction_id,
                "flag_time": flag_time,
                "reason": reason,
                "status": "FLAGGED",
                "requires_review": True,
                "message": "Transaction has been flagged for suspicious activity"
            }

            # Log suspicious activity
            self.state.audit_logger.log_suspicious_activity(
                flag_id=flag["flag_id"],
                transaction_id=transaction_id,
                reason=reason,
                agent_id=self.aztp.aztp_id
            )

            return flag

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")

            # Log access verification failure
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="flag_suspicious",
                status="failure",
                details={"error": error_msg}
            )

            raise

        except Exception as e:
            error_msg = f"Failed to flag suspicious activity: {str(e)}"
            print(f"❌ {error_msg}")

            # Log flagging failure
            self.state.audit_logger.log_suspicious_activity(
                flag_id="error",
                transaction_id=transaction_id,
                reason=f"Failed to flag: {error_msg}",
                agent_id=self.aztp.aztp_id
            )

            raise

    async def analyze_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze transaction patterns for potential risks

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Pattern analysis results
        """
        if not self.aztp.is_initialized:
            await self.initialize()

        try:
            # Verify pattern analysis access
            await self.state.iam_utils.verify_access_or_raise(
                agent_id=self.aztp.aztp_id,
                action="read_patterns",
                policy_code="risk-agent-policy",
                operation_name="Pattern Analysis"
            )

            # Generate memory key
            memory_key = str(hash(str(transactions)))
            if memory_key in self.state.pattern_memory:
                print("Using cached pattern analysis result...")
                return self.state.pattern_memory[memory_key]

            # Analyze patterns
            total_transactions = len(transactions)
            if total_transactions == 0:
                return {"message": "No transactions to analyze"}

            # Calculate time-based patterns
            time_patterns = self._analyze_time_patterns(transactions)

            # Calculate amount patterns
            amount_patterns = self._analyze_amount_patterns(transactions)

            # Calculate location patterns
            location_patterns = self._analyze_location_patterns(transactions)

            # Generate pattern ID
            pattern_id = f"PTN-{str(uuid.uuid4())[:8].upper()}"
            analysis_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create analysis result
            analysis = {
                "pattern_id": pattern_id,
                "analysis_time": analysis_time,
                "total_transactions": total_transactions,
                "time_patterns": time_patterns,
                "amount_patterns": amount_patterns,
                "location_patterns": location_patterns,
                "overall_risk_level": self._calculate_pattern_risk_level(
                    time_patterns,
                    amount_patterns,
                    location_patterns
                ).value
            }

            # Store in memory
            self.state.pattern_memory[memory_key] = analysis

            # Log pattern analysis
            self.state.audit_logger.log_pattern_analysis(
                pattern_id=analysis["pattern_id"],
                risk_level=analysis["overall_risk_level"],
                analysis_details=analysis,
                agent_id=self.aztp.aztp_id
            )

            return analysis

        except PolicyVerificationError as e:
            error_msg = str(e)
            print(f"❌ Policy verification failed: {error_msg}")

            # Log access verification failure
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="read_patterns",
                status="failure",
                details={"error": error_msg}
            )

            raise

        except Exception as e:
            error_msg = f"Failed to analyze patterns: {str(e)}"
            print(f"❌ {error_msg}")

            # Log pattern analysis failure
            self.state.audit_logger.log_pattern_analysis(
                pattern_id="error",
                risk_level="error",
                analysis_details={"error": error_msg},
                agent_id=self.aztp.aztp_id
            )

            raise

    def _analyze_time_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze time-based patterns in transactions"""
        timestamps = [
            datetime.datetime.fromisoformat(tx['timestamp'])
            for tx in transactions
            if 'timestamp' in tx
        ]

        if not timestamps:
            return {"risk_level": RiskLevel.MEDIUM.value, "reason": "No timestamp data"}

        # Calculate time differences between transactions
        time_diffs = []
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i-1]
            time_diffs.append(diff.total_seconds())

        # Analyze patterns
        if len(time_diffs) > 0:
            avg_time_diff = sum(time_diffs) / len(time_diffs)
            min_time_diff = min(time_diffs)

            risk_level = RiskLevel.LOW
            reason = "Normal transaction timing"

            if min_time_diff < 60:  # Less than 1 minute
                risk_level = RiskLevel.HIGH
                reason = "Unusually rapid transactions detected"
            elif avg_time_diff < 300:  # Less than 5 minutes
                risk_level = RiskLevel.MEDIUM
                reason = "Higher than normal transaction frequency"

            return {
                "risk_level": risk_level.value,
                "reason": reason,
                "average_time_between_transactions": avg_time_diff,
                "minimum_time_between_transactions": min_time_diff
            }

        return {"risk_level": RiskLevel.LOW.value, "reason": "Insufficient data for time analysis"}

    def _analyze_amount_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze amount patterns in transactions"""
        amounts = [
            float(tx.get('amount', 0))
            for tx in transactions
            if 'amount' in tx
        ]

        if not amounts:
            return {"risk_level": RiskLevel.MEDIUM.value, "reason": "No amount data"}

        total_amount = sum(amounts)
        avg_amount = total_amount / len(amounts)
        max_amount = max(amounts)

        risk_level = RiskLevel.LOW
        reason = "Normal transaction amounts"

        if max_amount > 1000:
            risk_level = RiskLevel.HIGH
            reason = "Large transaction amount detected"
        elif avg_amount > 500:
            risk_level = RiskLevel.MEDIUM
            reason = "Higher than average transaction amounts"

        return {
            "risk_level": risk_level.value,
            "reason": reason,
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "maximum_amount": max_amount
        }

    def _analyze_location_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze location patterns in transactions"""
        locations = [
            tx.get('location', 'Unknown')
            for tx in transactions
            if 'location' in tx
        ]

        if not locations:
            return {"risk_level": RiskLevel.MEDIUM.value, "reason": "No location data"}

        # Count unique locations
        location_counts = {}
        for loc in locations:
            location_counts[loc] = location_counts.get(loc, 0) + 1

        unique_locations = len(location_counts)

        risk_level = RiskLevel.LOW
        reason = "Normal location pattern"

        if unique_locations > 3:
            risk_level = RiskLevel.HIGH
            reason = "Multiple different locations detected"
        elif "Unknown" in location_counts:
            risk_level = RiskLevel.MEDIUM
            reason = "Some unknown locations detected"

        return {
            "risk_level": risk_level.value,
            "reason": reason,
            "unique_locations": unique_locations,
            "location_distribution": location_counts
        }

    def _calculate_pattern_risk_level(
        self,
        time_patterns: Dict[str, Any],
        amount_patterns: Dict[str, Any],
        location_patterns: Dict[str, Any]
    ) -> RiskLevel:
        """Calculate overall risk level from pattern analysis"""
        risk_levels = [
            RiskLevel(time_patterns["risk_level"]),
            RiskLevel(amount_patterns["risk_level"]),
            RiskLevel(location_patterns["risk_level"])
        ]

        return max(risk_levels, key=lambda x: x.value)

    async def monitor_agent_communication(
        self,
        source_agent_id: str,
        target_agent_id: str,
        data: Dict[str, Any],
        communication_type: str
    ) -> bool:
        """Monitor communication between agents for suspicious activity"""
        try:
            # Get current timestamp
            current_time = datetime.datetime.now()

            # Initialize communication pattern tracking for source agent
            if source_agent_id not in self.state.communication_patterns:
                self.state.communication_patterns[source_agent_id] = []

            # Add current communication to patterns
            self.state.communication_patterns[source_agent_id].append({
                "timestamp": current_time,
                "target": target_agent_id,
                "type": communication_type,
                "data_size": len(str(data))
            })

            # Clean up old patterns (keep only last minute)
            self.state.communication_patterns[source_agent_id] = [
                p for p in self.state.communication_patterns[source_agent_id]
                if (current_time - p["timestamp"]).total_seconds() <= 60
            ]

            # Check for suspicious patterns
            is_suspicious = await self._check_suspicious_patterns(
                source_agent_id,
                target_agent_id,
                data
            )

            if is_suspicious:
                await self._handle_suspicious_activity(source_agent_id)
                return False

            return True

        except Exception as e:
            error_msg = f"Failed to monitor communication: {str(e)}"
            print(f"❌ {error_msg}")

            # Log monitoring failure
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="monitor_communication",
                status="failure",
                details={"error": error_msg}
            )
            return False

    async def _check_suspicious_patterns(
        self,
        source_agent_id: str,
        target_agent_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Check for suspicious patterns in agent communication"""
        patterns = self.state.communication_patterns.get(source_agent_id, [])

        # Check communication frequency
        if len(patterns) > self.SUSPICIOUS_COMM_THRESHOLD:
            print(
                f"⚠️ High frequency communications detected from {source_agent_id}")
            return True

        # Check data size
        data_size = len(str(data))
        if data_size > self.DATA_SIZE_THRESHOLD:
            print(f"⚠️ Large data transfer detected from {source_agent_id}")
            return True

        # Check for repeated communications to same target
        target_count = sum(
            1 for p in patterns if p["target"] == target_agent_id)
        if target_count > self.SUSPICIOUS_COMM_THRESHOLD / 2:
            print(f"⚠️ Repeated communications to {target_agent_id} detected")
            return True

        # Check for unrealistic data patterns
        if await self._check_unrealistic_data(data):
            print(f"⚠️ Unrealistic data detected from {source_agent_id}")
            return True

        return False

    async def _check_unrealistic_data(self, data: Dict[str, Any]) -> bool:
        """Check for unrealistic patterns in the data"""
        try:
            # Check for extremely large numbers
            for value in str(data).split():
                try:
                    num = float(value)
                    if abs(num) > 1e9:  # Unrealistically large number
                        return True
                except ValueError:
                    continue

            # Check for suspicious keywords
            suspicious_keywords = [
                "hack", "exploit", "bypass", "override",
                "unlimited", "infinite", "root", "admin"
            ]
            data_str = str(data).lower()
            if any(keyword in data_str for keyword in suspicious_keywords):
                return True

            # Add more specific checks based on your business rules
            return False

        except Exception:
            return True  # Consider malformed data as suspicious

    async def _handle_suspicious_activity(self, agent_id: str) -> None:
        """Handle detected suspicious activity"""
        try:
            # Initialize or update suspicious activity counter
            if agent_id not in self.state.suspicious_agents:
                self.state.suspicious_agents[agent_id] = {
                    "count": 1,
                    "first_detection": datetime.datetime.now()
                }
            else:
                self.state.suspicious_agents[agent_id]["count"] += 1

            # Log suspicious activity
            self.state.audit_logger.log_suspicious_activity(
                flag_id=f"SUSPICIOUS-{str(uuid.uuid4())[:8].upper()}",
                transaction_id="N/A",
                reason=f"Suspicious communication patterns detected",
                agent_id=agent_id
            )

            # Check if revocation threshold is reached
            if self.state.suspicious_agents[agent_id]["count"] >= self.REVOCATION_THRESHOLD:
                await self._revoke_agent_identity(agent_id)

        except Exception as e:
            error_msg = f"Failed to handle suspicious activity: {str(e)}"
            print(f"❌ {error_msg}")
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="handle_suspicious",
                status="failure",
                details={"error": error_msg}
            )

    async def _revoke_agent_identity(self, agent_id: str, reason: str = "Revoked due to suspicious activity") -> None:
        """Revoke the identity of a suspicious agent"""
        try:
            print(f"🚫 Revoking identity for suspicious agent: {agent_id}")

            # Revoke the identity using AZTP client - only pass agent_id and reason
            revoke_result = await self.aztpClient.revoke_identity(
                agent_id,  # Only pass the agent ID
                reason  # Only pass the reason
            )

            # Log the revocation
            self.state.audit_logger.log_access_verification(
                agent_id=agent_id,
                action="revoke_identity",
                status="success",
                details={
                    "reason": reason,
                    "revoke_result": revoke_result
                }
            )

            print(f"✅ Successfully revoked identity for agent: {agent_id}")

            # Clean up agent data
            if agent_id in self.state.communication_patterns:
                del self.state.communication_patterns[agent_id]
            if agent_id in self.state.suspicious_agents:
                del self.state.suspicious_agents[agent_id]

        except Exception as e:
            error_msg = f"Failed to revoke agent identity: {str(e)}"
            print(f"❌ {error_msg}")
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="revoke_identity",
                status="failure",
                details={"error": error_msg}
            )

    async def communicate_with_agent(
        self,
        target_agent_id: str,
        message: str,
        communication_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Communicate with another agent and monitor for suspicious activity

        Args:
            target_agent_id: ID of the agent to communicate with
            message: Message to send
            communication_type: Type of communication
            details: Additional communication details

        Returns:
            Response from the target agent
        """
        try:
            # Monitor the communication
            is_safe = await self.monitor_agent_communication(
                source_agent_id=self.aztp.aztp_id,
                target_agent_id=target_agent_id,
                data={"message": message, "details": details},
                communication_type=communication_type
            )

            if not is_safe:
                raise ValueError(
                    "Communication blocked due to suspicious activity")

            # Proceed with the original communication logic
            return await self.communicate_with_agent(
                target_agent_id,
                message,
                communication_type,
                details
            )

        except Exception as e:
            error_msg = f"Failed to communicate with agent: {str(e)}"
            print(f"❌ {error_msg}")

            # Log communication failure
            self.state.audit_logger.log_agent_communication(
                source_agent_id=self.aztp.aztp_id,
                target_agent_id=target_agent_id,
                communication_type=communication_type,
                message=error_msg,
                status="failed",
                details=details
            )

            raise

    async def notify_high_risk(
        self,
        transaction_id: str,
        risk_level: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Notify relevant agents about high-risk transactions

        Args:
            transaction_id: ID of the high-risk transaction
            risk_level: Risk level determined
            details: Risk analysis details
        """
        try:
            # List of agents to notify (you would configure this based on your setup)
            agents_to_notify = {
                "order_agent": "ORDER_AGENT_ID",
                "customer_support": "SUPPORT_AGENT_ID",
                "payment_agent": "PAYMENT_AGENT_ID"
            }

            notification = {
                "transaction_id": transaction_id,
                "risk_level": risk_level,
                "timestamp": datetime.datetime.now().isoformat(),
                "details": details
            }

            # Notify each agent
            for agent_name, agent_id in agents_to_notify.items():
                await self.communicate_with_agent(
                    target_agent_id=agent_id,
                    message=str(notification),
                    communication_type="risk_notification",
                    details={
                        "notification_type": "high_risk_alert",
                        "agent_role": agent_name
                    }
                )

        except Exception as e:
            error_msg = f"Failed to send high-risk notifications: {str(e)}"
            print(f"❌ {error_msg}")

            # Log the failure
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="notify_high_risk",
                status="failure",
                details={"error": error_msg}
            )

    async def request_transaction_review(
        self,
        transaction_id: str,
        reason: str,
        priority: str = "high"
    ) -> Dict[str, Any]:
        """
        Request transaction review from appropriate agents

        Args:
            transaction_id: ID of the transaction to review
            reason: Reason for requesting review
            priority: Priority level of the review request

        Returns:
            Review request details
        """
        try:
            review_request = {
                "request_id": f"REV-{str(uuid.uuid4())[:8].upper()}",
                "transaction_id": transaction_id,
                "reason": reason,
                "priority": priority,
                "timestamp": datetime.datetime.now().isoformat()
            }

            # Send review request to customer support agent
            response = await self.communicate_with_agent(
                target_agent_id="SUPPORT_AGENT_ID",  # You would configure this
                message=str(review_request),
                communication_type="review_request",
                details={
                    "priority": priority,
                    "requires_immediate_action": priority == "high"
                }
            )

            return {
                **review_request,
                "status": "submitted",
                "response": response
            }

        except Exception as e:
            error_msg = f"Failed to request transaction review: {str(e)}"
            print(f"❌ {error_msg}")

            # Log the failure
            self.state.audit_logger.log_access_verification(
                agent_id=self.aztp.aztp_id,
                action="request_review",
                status="failure",
                details={"error": error_msg}
            )

            raise

    def get_communication_history(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        communication_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get history of agent communications

        Args:
            start_time: Start time for filtering
            end_time: End time for filtering
            communication_type: Type of communication to filter

        Returns:
            Communication history and statistics
        """
        try:
            # Get communication statistics
            stats = self.state.audit_logger.get_communication_statistics(
                agent_id=self.aztp.aztp_id,
                start_time=start_time,
                end_time=end_time
            )

            # Get detailed communications
            communications = self.state.audit_logger.get_agent_communications(
                agent_id=self.aztp.aztp_id,
                communication_type=communication_type,
                start_time=start_time,
                end_time=end_time
            )

            return {
                "statistics": stats,
                "communications": communications
            }

        except Exception as e:
            error_msg = f"Failed to get communication history: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "statistics": {},
                "communications": []
            }

    async def monitor_aztp_agent(
        self,
        agent_connection: SecureConnection,
        action: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Monitor an AZTP-connected agent's activities

        Args:
            agent_connection: The agent's AZTP secure connection
            action: The action being performed
            details: Details of the action

        Returns:
            bool: True if action is allowed, False if suspicious
        """
        try:
            agent_id = agent_connection.identity.aztp_id

            # Initialize monitoring for new agent
            if agent_id not in self.state.monitored_agents:
                # Get department safely, default to "Unknown" if not present
                department = getattr(
                    agent_connection.identity, 'department', 'Unknown')
                trust_level = getattr(
                    agent_connection.identity, 'trust_level', 'medium')

                self.state.monitored_agents[agent_id] = {
                    "suspicious_count": 0,
                    "last_activity": None,
                    "activity_count": 0,
                    "last_reset": datetime.datetime.now(),
                    "department": department,
                    "trust_level": trust_level
                }

            current_time = datetime.datetime.now()
            agent_data = self.state.monitored_agents[agent_id]

            # Reset activity count if a minute has passed
            if (current_time - agent_data["last_reset"]).total_seconds() >= 60:
                agent_data["activity_count"] = 0
                agent_data["last_reset"] = current_time

            # Update activity tracking
            agent_data["last_activity"] = current_time
            agent_data["activity_count"] += 1

            # Check for suspicious patterns
            is_suspicious = await self._check_aztp_suspicious_patterns(
                agent_id,
                action,
                details
            )

            if is_suspicious:
                agent_data["suspicious_count"] += 1
                print(f"⚠️ Suspicious activity detected for agent {agent_id}")
                print(f"Action: {action}")
                print(f"Details: {details}")

                # Check if revocation is needed
                if agent_data["suspicious_count"] >= self.SUSPICIOUS_TRANSACTION_THRESHOLD:
                    await self._revoke_agent_identity(agent_id)
                    return False

                # Log suspicious activity
                self.state.audit_logger.log_suspicious_activity(
                    flag_id=f"SUSPICIOUS-{str(uuid.uuid4())[:8].upper()}",
                    transaction_id=details.get('transaction_id', 'N/A'),
                    reason=f"Suspicious activity in {action}",
                    agent_id=agent_id
                )

            return not is_suspicious

        except Exception as e:
            error_msg = f"Failed to monitor AZTP agent: {str(e)}"
            print(f"❌ {error_msg}")

            # Even if monitoring fails, check if we should revoke the agent
            try:
                if agent_id in self.state.monitored_agents:
                    agent_data = self.state.monitored_agents[agent_id]
                    if agent_data["suspicious_count"] >= self.SUSPICIOUS_TRANSACTION_THRESHOLD:
                        await self._revoke_agent_identity(agent_id)
            except Exception as revoke_error:
                print(f"❌ Failed to handle revocation: {str(revoke_error)}")

            return False

    async def _check_aztp_suspicious_patterns(
        self,
        agent_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> bool:
        """Check for suspicious patterns in AZTP agent activity"""
        agent_data = self.state.monitored_agents[agent_id]

        # Check high-frequency activity
        if agent_data["activity_count"] > self.HIGH_FREQUENCY_THRESHOLD:
            return True

        # Check transaction amount if present
        if 'amount' in details:
            try:
                amount = float(details['amount'])
                if amount > self.LARGE_AMOUNT_THRESHOLD:
                    return True
            except (ValueError, TypeError):
                pass

        # Check for suspicious keywords in action or details
        suspicious_keywords = [
            "hack", "exploit", "bypass", "override",
            "unlimited", "infinite", "root", "admin"
        ]

        action_str = str(action).lower()
        details_str = str(details).lower()

        if any(keyword in action_str or keyword in details_str
               for keyword in suspicious_keywords):
            return True

        # Add specific checks based on agent's department
        department = agent_data["department"]
        if department == "Payment":
            return await self._check_payment_agent_patterns(details)
        elif department == "Order":
            return await self._check_order_agent_patterns(details)

        return False

    async def _check_payment_agent_patterns(self, details: Dict[str, Any]) -> bool:
        """Check for suspicious patterns in payment agent activities"""
        try:
            # Check for common phishing indicators
            if await self._detect_phishing_patterns(details):
                return True

            # Check for suspicious payment patterns
            suspicious_patterns = [
                # Multiple rapid refunds
                'refund_count' in details and details['refund_count'] > 3,

                # Suspicious payment method changes
                'payment_method_changes' in details and details['payment_method_changes'] > 5,

                # Unusual number of failed transactions
                'failed_transactions' in details and details['failed_transactions'] > 3,

                # Multiple different payment methods in short time
                'unique_payment_methods' in details and details['unique_payment_methods'] > 3,

                # Suspicious amount patterns
                'transaction_amount' in details and float(
                    details['transaction_amount']) > 50000,

                # High-frequency small transactions
                'small_transaction_count' in details and details['small_transaction_count'] > 10,

                # Mismatched billing information
                'billing_info_mismatches' in details and details['billing_info_mismatches'] > 2
            ]

            return any(suspicious_patterns)

        except Exception as e:
            print(f"Error in payment pattern check: {str(e)}")
            return True  # Fail safe: consider suspicious on error

    async def _detect_phishing_patterns(self, details: Dict[str, Any]) -> bool:
        """
        Detect potential phishing attempts in payment processing

        Args:
            details: Transaction and payment details to analyze

        Returns:
            bool: True if phishing attempt detected
        """
        try:
            # Common phishing indicators
            phishing_indicators = {
                'redirect_url': lambda url: any(
                    suspicious in str(url).lower()
                    for suspicious in ['paypa1', 'paypal-secure', 'paypal.com.', 'secure-paypal']
                ),
                'form_fields': lambda fields: any(
                    field.lower().startswith('paypal_') for field in fields
                ) if isinstance(fields, list) else False,
                'request_headers': lambda headers: any(
                    suspicious in str(headers).lower()
                    for suspicious in ['phish', 'spoofed', 'modified']
                ),
                'ip_reputation': lambda score: float(score) < 50 if score else False,
                'ssl_verification': lambda status: not status,
                # Domain less than 30 days old
                'domain_age': lambda age: int(age) < 30 if age else False
            }

            # Check each indicator
            for key, check_func in phishing_indicators.items():
                if key in details and check_func(details[key]):
                    print(f"⚠️ Phishing indicator detected: {key}")
                    return True

            # Check for PayPal-specific phishing patterns
            if 'paypal_data' in details:
                paypal_data = details['paypal_data']
                paypal_suspicious_patterns = [
                    # Invalid or suspicious PayPal endpoints
                    'api_endpoint' in paypal_data and not paypal_data['api_endpoint'].endswith(
                        'paypal.com'),

                    # Suspicious authentication attempts
                    'auth_method' in paypal_data and paypal_data['auth_method'] not in [
                        'oauth', 'cert'],

                    # Unusual data collection
                    'requested_fields' in paypal_data and any(
                        field in paypal_data['requested_fields']
                        for field in ['ssn', 'card_pin', 'bank_password']
                    )
                ]

                if any(paypal_suspicious_patterns):
                    print("⚠️ PayPal-specific phishing pattern detected")
                    return True

            return False

        except Exception as e:
            print(f"Error in phishing detection: {str(e)}")
            return True  # Fail safe: consider suspicious on error

    async def simulate_phishing_attack(self, target_agent_id: str) -> Dict[str, Any]:
        """
        Simulate a phishing attack scenario for testing the risk monitoring system

        Args:
            target_agent_id: The ID of the agent to simulate attack against

        Returns:
            Dict containing simulation results
        """
        try:
            # Simulate a phishing attempt against a payment agent
            suspicious_details = {
                'paypal_data': {
                    'api_endpoint': 'https://secure-paypal.malicious-domain.com',
                    'auth_method': 'unknown',
                    'requested_fields': ['card_pin', 'ssn'],
                },
                'redirect_url': 'https://paypa1.com/secure-login',
                'form_fields': ['paypal_password', 'paypal_secret'],
                'ip_reputation': 20,
                'ssl_verification': False,
                'domain_age': 2
            }

            # Monitor the simulated suspicious activity
            is_suspicious = await self.monitor_aztp_agent(
                agent_connection=await self.aztpClient.get_agent_connection(target_agent_id),
                action="process_payment",
                details=suspicious_details
            )

            if is_suspicious:
                print(
                    f"✅ Successfully detected phishing attempt against agent {target_agent_id}")
                return {
                    "status": "detected",
                    "action_taken": "agent_revoked",
                    "target_agent": target_agent_id,
                    "detection_time": datetime.datetime.now().isoformat()
                }
            else:
                print("❌ Failed to detect simulated phishing attempt")
                return {
                    "status": "undetected",
                    "action_taken": "none",
                    "target_agent": target_agent_id,
                    "detection_time": datetime.datetime.now().isoformat()
                }

        except Exception as e:
            error_msg = f"Error in phishing simulation: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "target_agent": target_agent_id,
                "detection_time": datetime.datetime.now().isoformat()
            }


if __name__ == "__main__":
    # test_write_demo_tracker()
    main()
