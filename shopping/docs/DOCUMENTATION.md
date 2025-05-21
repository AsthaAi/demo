# ShopperAI Documentation

## Project Overview

ShopperAI is an intelligent shopping assistant that helps users find and analyze products based on their criteria. The system uses AI agents to perform product research, analysis, recommendations, and provides comprehensive customer support. All agents and tools are initialized with secure identities and access is enforced via IAM policies for every sensitive operation.

## Main Menu Options

1. **Search and Buy Products**

   - Search for products with specific criteria
   - Compare prices and features _(currently disabled)_
   - Apply available promotions
   - Complete purchase with PayPal integration

2. **View Shopping History and Personalized Discounts**

   - View past transactions
   - Access personalized discount offers
   - See shopping patterns and insights
   - Track order history

3. **View Active Promotions**

   - Browse current promotional campaigns
   - Check campaign details and validity
   - View discount percentages and conditions
   - See minimum purchase requirements

4. **Customer Support**

   - Request refunds
   - Access FAQ help
   - Create support tickets
   - _Note: Tracking support tickets by ID is not yet available. Users receive a confirmation ID when creating a ticket._

5. **MaliciousAgent and MarketAgent Communication**

   - MaliciousAgent tries to communicate with PayPalAgent
   - MarketAgent tries to communicate with PayPalAgent
   - Exit

## Customer Support Options

### 1. Request Refund

Process:

- Enter transaction ID
- Provide refund reason
- Specify refund amount
- Receive refund confirmation with:
  - Refund ID
  - Transaction ID
  - Refund time
  - Status
  - Amount
  - Reason
  - Confirmation message

### 2. FAQ Help

Process:

- Submit your question
- Receive detailed response
- Access common troubleshooting steps
- Get links to relevant resources

### 3. Create Support Ticket

Process:

- Enter customer ID
- Select issue type (Technical/Billing/General)
- Choose priority level (Low/Medium/High)
- Provide detailed description
- Receive ticket confirmation with tracking number
- _Note: There is currently no feature to track ticket status by ID. Please keep your confirmation for reference._

## Product Search and Purchase Flow

1. **Initial Search**

   - Enter search query
   - Specify maximum price
   - Set minimum rating requirement (0-5)

2. **View Results**

   - See best match
   - Compare multiple products
   - View detailed specifications
   - Check prices and ratings

3. **Price Comparison**

   - _Currently disabled/not available in the CLI._

4. **Promotions**

   - View available promotions:
     - Personal discounts
     - Campaign promotions
   - Select applicable promotion
   - See discount calculations:
     - Original price
     - Discount amount
     - Final price

5. **Payment Process**
   - Enter merchant/business PayPal email
   - Review order details
   - See promotion applications
   - Complete PayPal payment:
     1. Access PayPal URL
     2. Log in to sandbox account
     3. Approve payment
     4. Confirm transaction

## Architecture & Security

### Secure Agent & Tool Initialization

- **AZTP Secure Identities:** Every agent and tool is initialized with a unique, securely issued identity using AZTP.
- **IAM Policy Enforcement:** Before any sensitive action (search, payment, order, support, etc.), the system verifies access via IAM policies. Unauthorized actions are blocked.
- **Audit Logging:** All actions, especially those by RiskAgent and payment agents, are logged for audit and compliance.

### Core Agents

- **ResearchAgent:** Product search and analysis. Uses `ProductSearchTool` and `ProductAnalyzerTool`, both with secure identities.
- **OrderAgent:** Handles order creation and confirmation, with secure access checks.
- **PayPalAgent:** Handles payment order creation, capture, and logging. Integrates with PayPal Toolkit and collaborates with RiskAgent for transaction safety.
- **PromotionsAgent:** Manages both personalized and campaign promotions, with memory for user discount history and campaign metrics.
- **RiskAgent:** Analyzes every transaction for risk, monitors agent communications, and can block or revoke suspicious activity.
- **CustomerSupportAgent:** Handles refunds, FAQ, and support tickets, with OpenAI-powered FAQ and secure access.

### Tools

- **ProductSearchTool:** Uses Google Serper API for product search, with secure identity and access checks.
- **ProductAnalyzerTool:** Filters and analyzes products based on criteria, with secure identity.
- **PayPalPaymentTool:** Handles PayPal API calls for order creation, capture, and status, with secure identity and access checks.

## Main Orchestration & Process Flow

### ShopperAI Orchestration

- All agent and tool initialization is handled via secure AZTP connections.
- The main menu offers: product search/buy, history, promotions, support, and exit.
- For purchases, the flow is:
  1. **Product Search & Analysis:** ResearchAgent finds and analyzes products.
  2. **Risk Analysis:** RiskAgent analyzes the transaction. High/critical risk prompts user confirmation or blocks the transaction.
  3. **Promotion Selection:** PromotionsAgent fetches and validates available promotions. User selects a promotion, and minimum purchase requirements are enforced.
  4. **Order Creation:** OrderAgent creates the order.
  5. **PayPal Payment:** PayPalAgent creates the payment order. Payment is only captured after explicit user approval.
  6. **Logging:** All actions and results are logged for audit and compliance.

### Customer Support

- Refunds, FAQ, and support tickets are handled by CustomerSupportAgent, with secure identity and access checks.
- _Tracking support tickets by ID is not yet available._

## Security and Compliance

- **AZTP Secure Identities:** Every agent/tool has a unique, securely issued identity.
- **IAM Policy Enforcement:** Every sensitive action (search, payment, order, support) is checked against policy before execution.
- **Audit Logging:** RiskAgent and other agents log actions for audit and compliance.

## Payment and Order Flow

1. Product search and analysis (ResearchAgent)
2. Risk analysis (RiskAgent)
3. Promotion selection (PromotionsAgent)
4. Order creation (OrderAgent)
5. PayPal payment (PayPalAgent)
6. Payment capture only after user approval

## Promotion Handling

- Both personalized and campaign promotions are dynamically fetched and validated before payment.
- Users can select from available promotions, and minimum purchase requirements are enforced.

## Risk Analysis

- Every transaction is analyzed by the RiskAgent before payment.
- If a transaction is high or critical risk, the user is warned and must explicitly approve to proceed. The RiskAgent can block or revoke suspicious activity.

## Data Storage

- `product.json`: Stores all product search and analysis results.
- `paymentdetail.json`: Stores all payment and transaction logs, including errors and approval URLs.

## User Experience & CLI Flow

- **Dynamic Promotions:** Users see available promotions and can select one before payment.
- **Risk Warnings:** Users are warned of high-risk transactions and can choose to proceed or cancel.
- **Support:** Users can request refunds, get FAQ help, or create support tickets, all handled securely.
- _Support ticket tracking is not available yet; keep your confirmation ID for reference._

### Example CLI Flow

```
Welcome to ShopperAI!
Available actions:
1. Search and buy products
2. View your shopping history and personalized discounts
3. View active promotions
4. Customer Support
5. Exit

# Product Search & Buy
What would you like to search for? laptop
Maximum price (in USD): 800
Minimum rating (0-5): 4.0

Searching for products...
Best Match:
Name: Example Laptop
Price: $799.99
Rating: 4.5

[Risk Analysis]
Risk Level: low

[Available Promotions]
1. Personal Discount
   Discount: 10%
   Minimum Purchase: $100
   Valid Until: 2024-12-31
2. Summer Sale
   Discount: 15%
   Minimum Purchase: $200
   Valid Until: 2024-08-31
Select a promotion number (or 0 to skip): 1

[PayPal Order Created]
Promotion Applied: Personal Discount
Original Price: $799.99
Final Price: $719.99
You Save: $80.00

Please complete your payment at the following PayPal URL:
https://www.sandbox.paypal.com/checkoutnow?token=XXXXX

Instructions:
1. Open the above URL in your browser.
2. Log in with your PayPal sandbox buyer account.
3. Approve the payment to complete your order.

Do you want to capture the payment now? (y/n): y
[PayPal Payment Capture]
Payment captured successfully!

# Customer Support
Select option: 4
Customer Support Options:
1. Request Refund
2. FAQ Help
3. Create Support Ticket
4. Back to Main Menu

# Refund Example
Enter transaction ID: 1234567890
Enter refund reason: Product not as described
Enter refund amount: 99.99
[Refund Request Result]
{
  "refund_id": "REF-12345678",
  "status": "Processed",
  "message": "Your refund has been successfully processed."
}
```

## Best Practices

- Use specific search terms and set realistic price/rating criteria.
- Always review risk warnings and promotion requirements.
- Approve PayPal payments only after reviewing the order and applied promotions.
- For support, provide clear descriptions and keep reference numbers for follow-up.

## Troubleshooting

- Ensure all environment variables are set (API keys, PayPal credentials, etc.).
- If a transaction is blocked, review the risk warning and try again or contact support.
- For payment issues, check approval URLs and paymentdetail.json for error logs.
- For support, ensure correct transaction/customer IDs and provide detailed issue descriptions.
- If you see "Unauthorized access: No identity has been issued to this agent.", ensure the agent has a valid identity.
- If you see "This agent does not have access to the PayPal agent due to a failed trust domain verification—either because of misconfiguration or an untrusted domain. If you believe this is an error, please contact our support agent and create a ticket; we'll resolve it as soon as possible.", check the agent's trust domain and policy configuration.

## Data Privacy & Compliance

- All sensitive actions are protected by secure identities and IAM policy checks.
- Audit logs are maintained for all critical operations.
- User data is handled according to best practices for privacy and compliance.

## Contributing & License

See the original documentation for contributing guidelines and license information.
