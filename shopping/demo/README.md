# RiskAgent Security Demonstration

This demo showcases the security capabilities of the RiskAgent in the ShopperAI system. It demonstrates how the RiskAgent protects the shopping system from various security threats and suspicious activities.

## Features Demonstrated

1. **Normal Transaction Processing**

   - Shows how legitimate transactions are processed
   - Demonstrates risk level calculation for normal activities
   - Displays various risk factors and their analysis

2. **Suspicious Transaction Detection**

   - Demonstrates detection of unusual transaction patterns
   - Shows how multiple rapid transactions are flagged
   - Illustrates location-based risk analysis
   - Demonstrates amount-based risk detection

3. **Phishing Attack Prevention**

   - Shows how phishing attempts are detected
   - Demonstrates the system's response to suspicious URLs
   - Illustrates security measures against fake payment pages
   - Shows identity revocation for compromised agents

4. **Agent Communication Monitoring**

   - Demonstrates monitoring of inter-agent communications
   - Shows detection of suspicious communication patterns
   - Illustrates handling of large data transfers
   - Demonstrates blocking of malicious commands

5. **High-Risk Transaction Notification**
   - Shows the notification system for high-risk transactions
   - Demonstrates multi-agent coordination for security
   - Illustrates the escalation process for suspicious activities

## Prerequisites

1. Python 3.8 or higher
2. Required environment variables:
   - `AZTP_API_KEY`: Your AZTP API key for secure agent communication
   - `OPENAI_API_KEY`: OpenAI API key (if using AI capabilities)

## Setup

1. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export AZTP_API_KEY="your-aztp-api-key"
   export OPENAI_API_KEY="your-openai-api-key"
   ```

## Running the Demo

1. Navigate to the demo directory:

   ```bash
   cd shopping/demo
   ```

2. Run the demo script:
   ```bash
   python risk_agent_demo.py
   ```

## Demo Output

The demo will show:

1. Risk analysis results for various transactions
2. Detection of suspicious patterns
3. Phishing attempt prevention
4. Agent communication monitoring
5. High-risk notifications

Example output:

```
🔒 RiskAgent Capability Demonstration 🔒
=======================================

=== Demo 1: Normal Transaction Processing ===
Risk Level: low
Risk Factors:
- amount_risk: low
- location_risk: low
...

=== Demo 2: Suspicious Transaction Detection ===
Pattern Analysis Result:
Overall Risk Level: high
Time Patterns: {
  "risk_level": "high",
  "reason": "Unusually rapid transactions detected"
}
...
```

## Security Features Demonstrated

1. **Transaction Risk Analysis**

   - Amount-based risk assessment
   - Location-based verification
   - Device information analysis
   - User history evaluation

2. **Pattern Detection**

   - High-frequency transaction detection
   - Multiple location monitoring
   - Large amount pattern analysis
   - Suspicious timing patterns

3. **Phishing Prevention**

   - Suspicious URL detection
   - Fake payment page identification
   - SSL verification
   - Domain age checking
   - IP reputation analysis

4. **Agent Security**

   - Communication monitoring
   - Data size verification
   - Command validation
   - Identity verification
   - Suspicious activity tracking

5. **Notification System**
   - Risk level alerts
   - Agent coordination
   - Automated responses
   - Escalation procedures

## Customizing the Demo

You can modify the demo parameters in `risk_agent_demo.py`:

- Adjust transaction amounts
- Change timing patterns
- Modify location patterns
- Add custom risk factors
- Create new security scenarios

## Troubleshooting

1. **Connection Issues**

   - Verify AZTP_API_KEY is set correctly
   - Check network connectivity
   - Ensure required ports are open

2. **Authentication Errors**

   - Verify API keys
   - Check agent permissions
   - Ensure proper initialization

3. **Performance Issues**
   - Reduce number of simultaneous transactions
   - Check system resources
   - Monitor network latency

## Contributing

Feel free to contribute to this demo by:

1. Adding new security scenarios
2. Improving detection algorithms
3. Enhancing visualization of results
4. Adding more test cases
