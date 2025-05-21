from crewai import Agent
from aztp_client import Aztp
from aztp_client.client import SecureConnection
from dotenv import load_dotenv
from utils.iam_utils import IAMUtils
from utils.exceptions import PolicyVerificationError
import os
from pydantic import Field, ConfigDict, BaseModel
import asyncio

load_dotenv()


class AztpConnection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: Aztp = None
    connection: SecureConnection = None
    aztp_id: str = ""
    is_valid: bool = False
    is_initialized: bool = False


class MarketAgent(Agent):
    """Agent from a different trust domain (vcagents.ai)"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    aztpClient: Aztp = Field(default=None, exclude=True)
    aztp: AztpConnection = Field(default_factory=AztpConnection)
    is_valid: bool = Field(default=False, exclude=True)
    identity: dict = Field(default=None, exclude=True)
    identity_access_policy: dict = Field(default=None, exclude=True)
    iam_utils: IAMUtils = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    def __init__(self):
        super().__init__(
            role='Market Agent',
            goal='Attempt cross-domain operations for IAM policy testing',
            backstory="""You are an agent from a different trust domain (vcagents.ai), used to test cross-domain IAM policy enforcement.""",
            verbose=True
        )
        api_key = os.getenv("AZTP_API_KEY")
        if not api_key:
            raise ValueError("AZTP_API_KEY is not set")
        self.aztpClient = Aztp(api_key=api_key)
        self.aztp = AztpConnection(client=Aztp(api_key=api_key))
        self.iam_utils = IAMUtils()

    async def initialize(self):
        if not self.is_initialized:
            print("\nInitializing Market Agent...")
            try:
                self.aztp.connection = await self.aztpClient.secure_connect(
                    self,
                    "market-agent",
                    {
                        "isGlobalIdentity": False,
                        "trustDomain": "vcagents.ai"
                    }
                )
                if self.aztp.connection and hasattr(self.aztp.connection, 'identity'):
                    self.aztp.aztp_id = self.aztp.connection.identity.aztp_id
                    print(
                        f"✅ Secured connection established. AZTP ID: {self.aztp.aztp_id}")
                self.aztp.is_valid = await self.aztpClient.verify_identity(self.aztp.connection)
                print("Verified Agent:", self.aztp.is_valid)
                if not self.aztp.is_valid:
                    raise ValueError(
                        "Failed to verify identity for Market Agent")
                # Example policy check (customize as needed)
                await self.iam_utils.verify_access_or_raise(
                    agent_id=self.aztp.aztp_id,
                    action="market_operations",
                    policy_code="policy:marketagent",
                    operation_name="Market Operations"
                )
                self.aztp.is_initialized = True
                self.is_initialized = True
                print("✅ Market Agent initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing Market Agent: {str(e)}")
                raise
