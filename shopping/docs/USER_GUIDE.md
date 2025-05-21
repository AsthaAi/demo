# ShopperAI User Guide

**ShopperAI** is an intelligent shopping assistant that helps you search for products, compare options, make purchases securely via PayPal, and access customer support—all from a single, interactive command-line interface.

---

## Getting Started

1. **Run the Application**
   - Open your terminal.
   - Navigate to the project directory.
   - Run:
     ```bash
     python shopping/main.py
     ```
   - You'll see a welcome message and a menu of actions.

---

## Main Menu Options

You'll be presented with these options:

1. **Search and buy products**
2. **View your shopping history and personalized discounts**
3. **View active promotions**
4. **Customer Support**
5. MaliciousAgent tries to communicate with PayPalAgent
6. MarketAgent tries to communicate with PayPalAgent
7. Exit

---

### 1. Search and Buy Products

- **How it works:**
  - Enter what you want to search for (e.g., "wireless headphones").
  - Specify your maximum price and minimum rating.
  - ShopperAI will search for products matching your criteria.
  - You'll see the best match or a list of products.
  - You can choose a product to purchase.
  - Enter the merchant's PayPal email to proceed.
  - ShopperAI will process your order, apply any available promotions, and guide you through PayPal payment and capture.

---

### 2. View Your Shopping History and Personalized Discounts

- **How it works:**
  - Enter your email address.
  - ShopperAI analyzes your past purchases and spending.
  - If eligible, you'll see personalized discount offers based on your history.

---

### 3. View Active Promotions

- **How it works:**
  - ShopperAI displays current promotional campaigns (e.g., "Summer Sale").
  - You'll see details like discount percentage, minimum purchase, and valid categories.

---

### 4. Customer Support

- **Options:**
  1. **Request Refund:**
     - Enter your transaction ID, reason, and amount to request a refund.
  2. **FAQ Help:**
     - Type your question to get instant answers to common queries.
  3. **Create Support Ticket:**
     - Submit an issue (technical, billing, etc.) for personalized support.
  4. **Back to Main Menu**
  - **Tip:** You can also type a product search query directly here (e.g., "buy headphones under $100 rating 4.5") and ShopperAI will help you find products.

---

## Payment and Security

- Payments are processed securely via PayPal.
- ShopperAI performs risk analysis on each transaction.
- You may be offered promotions or discounts before payment.
- After payment, you'll see transaction details and can view your latest payment record.

---

## After Purchase

- ShopperAI records your payment details for history and future discounts.
- You can always view your latest payment or request support/refunds.

---

## FAQ

**Q: What if I don't see any products?**  
A: ShopperAI will always try to find products matching your criteria. If none are found, it will show sample products.

**Q: How do I get a refund?**  
A: Go to Customer Support > Request Refund and provide your transaction details.

**Q: How are discounts applied?**  
A: ShopperAI checks for personalized and campaign promotions before you pay. If eligible, you can select and apply them.

---

## Tips

- Use clear product names and set realistic price/rating criteria for best results.
- Always use your correct email for history and discounts.
- For PayPal payments, use a sandbox (test) buyer account for testing.

---

## Troubleshooting

- If you encounter errors, check your internet connection and ensure your environment variables (like PayPal and OpenAI API keys) are set.
- For technical issues, use the Customer Support > Create Support Ticket option.

### Agent Communication Security

- Only agents with a valid, issued identity can communicate with PayPalAgent.
- If an agent without identity (e.g., MaliciousAgent) tries to connect, you'll see:
  "Unauthorized access: No identity has been issued to this agent."
- If an agent from a different trust domain (e.g., MarketAgent) tries to connect, you'll see:
  "This agent does not have access to the PayPal agent due to a failed trust domain verification—either because of misconfiguration or an untrusted domain. If you believe this is an error, please contact our support agent and create a ticket; we'll resolve it as soon as possible."
