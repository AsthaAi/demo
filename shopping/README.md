# ShopperAI - The Agentic Shopping Assistant

ShopperAI is an intelligent shopping assistant that automates the product research, comparison, and purchasing process. It uses a team of specialized AI agents to help users find and purchase products efficiently.

## Features

- Product Research: Find and compare products based on user criteria
- Cart Management: Add items to cart and manage quantities
- Checkout Process: Streamlined checkout experience
- Agent Coordination: Multiple specialized agents working together

## Architecture

The project uses CrewAI to orchestrate multiple AI agents:

- Research Agent: Searches and compares products
- Cart Agent: Manages shopping cart operations
- Checkout Agent: Handles the checkout process

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   SERPAPI_API_KEY=your_serpapi_key
   ```

## Usage

Run the example script:

```bash
python examples/shopper_example.py
```

This will:

1. Initialize the shopping agents
2. Search for a laptop under $800
3. Add the best match to cart
4. Process checkout

## Customization

- Modify search criteria in `shopper_example.py`
- Add new agent roles in `agents/`
- Extend available tools in `tools/`

## License

MIT License
