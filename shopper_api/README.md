# ShopperAI API

A FastAPI implementation of the ShopperAI shopping assistant.

## Features

- Product search and research
- Price comparison
- Payment processing via PayPal
- Promotions and discounts
- Customer support including FAQ and refunds

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

Create a `.env` file in the root directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_api_key
PORT=8000
```

## Running the API

```bash
cd shopper_api
python run.py
```

The API will be available at http://localhost:8000 and the Swagger documentation at http://localhost:8000/docs

## API Endpoints

### Research

- **POST /research/** - Search for products based on query and criteria
- **POST /research/price-comparison** - Compare prices for products

### Orders

- **POST /orders/** - Process an order with payment
- **GET /orders/latest-payment** - Get the latest payment details

### Promotions

- **POST /promotions/campaigns** - Create a promotion campaign
- **POST /promotions/shopping-history** - Analyze shopping history

### Support

- **POST /support/refund** - Process a refund
- **POST /support/faq** - Get FAQ answers
- **POST /support/ticket** - Create a support ticket

## Example Usage

### Search for products

```bash
curl -X 'POST' \
  'http://localhost:8000/research/' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "water bottle",
  "max_price": 50,
  "min_rating": 4
}'
```

## License

MIT 