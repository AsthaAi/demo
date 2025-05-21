from crewai import Agent


class MaliciousAgent(Agent):
    """Simulates an agent without a valid identity for security testing."""

    def __init__(self):
        super().__init__(
            role='Malicious Agent',
            goal='Attempt unauthorized access for IAM testing',
            backstory="""You are a test agent with no identity, used to verify that the system correctly rejects unauthorized access attempts.""",
            verbose=True
        )
    # No aztp, no IAM, no identity
