# ShopperAI Agents Overview

ShopperAI is built on a modular, agent-based architecture. Each **agent** is responsible for a specific aspect of the shopping experience, working together to provide a seamless, secure, and intelligent service for users.

Below is a detailed explanation of each agent, their responsibilities (JD: Job Description), and how they interact within the ShopperAI system.

---

## 1. ResearchAgent

**Role:**  
The ResearchAgent is responsible for searching and analyzing products based on user queries and criteria.

**Responsibilities:**

- Searches for products using external APIs (e.g., SERPAPI, OpenAI) or fallback sample data.
- Analyzes product data to filter, rank, and recommend the best matches.
- Returns structured product information (raw, filtered, top products, and best match) for further processing.

**Typical Flow:**

- Receives a search query and criteria (e.g., max price, min rating).
- Gathers product data from online sources.
- Processes and structures the results for the user or other agents.

---

## 2. OrderAgent

**Role:**  
The OrderAgent manages the order placement process, ensuring that selected products are correctly prepared for purchase.

**Responsibilities:**

- Handles order creation and validation.
- Prepares order details for payment processing.
- May interact with inventory or merchant systems (future expansion).

**Typical Flow:**

- Receives selected product details.
- Validates and prepares the order for payment.

---

## 3. PayPalAgent

**Role:**  
The PayPalAgent handles all payment-related operations, ensuring secure and smooth transactions via PayPal.

**Responsibilities:**

- Initiates and manages PayPal payment orders.
- Handles payment approval and capture.
- Integrates with risk analysis to ensure transaction safety.
- Logs payment details for history and auditing.
- Enforces secure communication: Only agents with valid identity and correct trust domain can interact.

**Typical Flow:**

- Receives order and user details.
- Creates a PayPal payment order and provides the approval URL.
- Captures payment after user approval.
- Records transaction details for future reference.

---

## 4. PromotionsAgent

**Role:**  
The PromotionsAgent manages discounts, campaigns, and personalized offers for users.

**Responsibilities:**

- Creates and manages promotional campaigns (e.g., seasonal sales).
- Generates personalized discounts based on user shopping history.
- Analyzes user purchase patterns to optimize offers.
- Validates and applies promotions during checkout.

**Typical Flow:**

- Checks for available promotions and personalized discounts.
- Applies eligible promotions to the user's order.
- Provides details about active campaigns and user-specific offers.

---

## 5. CustomerSupportAgent

**Role:**  
The CustomerSupportAgent provides support services, including handling refunds, answering FAQs, and managing support tickets.

**Responsibilities:**

- Processes refund requests for completed transactions.
- Answers frequently asked questions using a knowledge base or AI.
- Creates and manages support tickets for user issues (technical, billing, etc.).
- Ensures user satisfaction and issue resolution.

**Typical Flow:**

- Receives user support requests (refund, FAQ, ticket).
- Processes the request and provides feedback or resolution.

---

## 6. RiskAgent

**Role:**  
The RiskAgent ensures the security and integrity of transactions by analyzing and monitoring for potential risks.

**Responsibilities:**

- Analyzes each transaction for fraud or suspicious activity.
- Provides risk levels and recommendations before payment is processed.
- Monitors agent activities (especially payment-related) for anomalies.
- Can block or flag high-risk transactions.

**Typical Flow:**

- Receives transaction data (amount, user, device info, etc.).
- Performs risk analysis and returns a risk assessment.
- Monitors ongoing payment activities for safety.

---

## MaliciousAgent

- Used to test IAM rejection for agents without identity.

## MarketAgent

- Used to test policy enforcement for agents from a different trust domain.

---

## How Agents Work Together

1. **User initiates a product search:**  
   The ResearchAgent finds and recommends products.

2. **User selects a product to buy:**  
   The OrderAgent prepares the order.

3. **Before payment:**  
   The RiskAgent analyzes the transaction for safety.  
   The PromotionsAgent checks for and applies any discounts.

4. **Payment processing:**  
   The PayPalAgent manages the payment flow, working with the RiskAgent for security.

5. **After purchase:**  
   The CustomerSupportAgent is available for refunds, FAQs, and support tickets.

- All agent-to-agent communication is subject to IAM and trust domain checks.

---

## Agent Middleware

All agents are initialized and managed through a secure middleware layer, ensuring that:

- Agents are only created when needed.
- Security checks and initializations are performed before any sensitive operation.
- Agent state is managed efficiently for the user session.

---

## Extending or Customizing Agents

ShopperAI's agent-based design allows for easy extension:

- New agents can be added for additional features (e.g., price comparison, loyalty programs).
- Existing agents can be enhanced with more sophisticated logic or integrations.
- Each agent is modular and can be tested independently.

---

## Summary Table

| Agent                | Main Responsibility             | Key Methods/Actions                                     |
| -------------------- | ------------------------------- | ------------------------------------------------------- |
| ResearchAgent        | Product search & analysis       | search_and_analyze, analyze_products                    |
| OrderAgent           | Order management                | order creation, validation                              |
| PayPalAgent          | Payment processing (PayPal)     | create_payment_order, capture_payment                   |
| PromotionsAgent      | Discounts & campaigns           | create_promotion_campaign, create_personalized_discount |
| CustomerSupportAgent | Support, refunds, FAQs, tickets | process_refund, get_faq_response, create_support_ticket |
| RiskAgent            | Transaction risk analysis       | analyze_transaction, monitor_aztp_agent                 |

---

## Developer Notes

- Each agent is implemented as a Python class in the `agents/` directory.
- Agents are initialized asynchronously and may depend on environment variables (API keys, etc.).
- The main orchestration logic is in `shopping/main.py`.
