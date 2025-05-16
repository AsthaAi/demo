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
