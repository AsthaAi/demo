1. Scenario: A Busy eCommerce Day
   A merchant uses a dashboard powered by multiple AI agents, each with a clear, secure identity and scope of responsibility.

2. Cast of AI Agents
   OrderManagerAgent: Processes and tracks orders.
   CustomerSupportAgent: Handles refund requests and FAQs.
   PromotionsAgent: Suggests personalized discounts.
   RiskAgent: Detects and flags suspicious orders.

3. IAM in Action
   Scoped Access Control:
   • RiskAgent can view transaction patterns, but not PII unless escalated.
   • PromotionsAgent can write to promo campaigns but cannot access order databases.
   Delegated Authorization:
   • CustomerSupportAgent escalates a complex refund to the merchant, who approves it via a secure IAM interface.
   Dynamic Trust:
   • If an agent behavior deviates (e.g. too many API calls), IAM revokes or limits access in real time.

4. New Scenarios: Agent Access Control Edge Cases

   a. Unauthorized Agent Attempt
   A "MaliciousAgent" (lacking a valid identity) attempts to connect to the PayPalAgent.
   • Expected Outcome:
   PayPalAgent immediately rejects the connection, returning an "Unauthorized" error due to missing or invalid identity credentials.

   b. Cross-TrustDomain Policy Violation
   A "MarketAgent" (with a valid identity, but belonging to a different trust domain) tries to interact with PayPalAgent.
   • Expected Outcome:
   PayPalAgent denies the request, returning a "Policy Violation" error because MarketAgent's trust domain is not permitted by PayPalAgent's access policy.

5. PayPalAgent Secure Communication Method

   PayPalAgent exposes a communication method that accepts an aztp_id and data from another agent.

   Process:

   1. Policy & Trust Domain Check:
      - The method checks:
        • Whether the aztp_id is present (valid identity).
        • Whether the requested action is allowed for the agent (using is_action_allowed).
        • Whether the agent's trustDomain matches the policy requirements.
      - If the aztp_id is missing, it returns an "Unauthorized access" error.
      - If the aztp_id is present but fails policy or trust domain checks, it returns an error message indicating a policy violation.
      - If all checks pass, it prints "Connection successful."
   2. Error Handling:
      - Any unsuccessful policy or trust domain check results in a clear error message ("Policy violation").
      - Only missing aztp_id results in "Unauthorized access."

   Example Scenarios:

   - If MaliciousAgent (no identity) tries to connect, the method returns "Unauthorized access."
   - If MarketAgent (wrong trust domain) tries to connect, the method returns "Policy violation."
   - If a valid agent with correct trust domain and permissions connects, the method prints "Connection successful."
