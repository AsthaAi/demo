# PayPal MCP Integration

This project implements a Model Context Protocol (MCP) server for PayPal integration, providing a set of tools for handling PayPal payments, subscriptions, and payouts through a Server-Sent Events (SSE) transport layer.

## Features

- **PayPal Tools**:

  - Create Order (`create_paypal_order`)
  - Capture Order (`capture_paypal_order`)
  - Get Order Details (`get_order_details`)
  - Create Subscription (`create_paypal_subscription`)
  - Cancel Subscription (`cancel_subscription`)
  - Create Refund (`create_refund`)
  - Create Payout (`create_paypal_payout`)

- **Transport Layer**:
  - Server-Sent Events (SSE) for real-time communication
  - Automatic reconnection handling
  - Keep-alive mechanism
  - Error handling and recovery

## Setup

1. **Install Dependencies**:

   ```bash
   npm install
   ```

2. **Environment Configuration**:
   Create a `.env` file with the following variables:

   ```env
   PAYPAL_CLIENT_ID=your_client_id
   PAYPAL_CLIENT_SECRET=your_client_secret
   PAYPAL_ENVIRONMENT=sandbox  # or 'live' for production
   PAYPAL_RETURN_URL=https://example.com/return
   PAYPAL_CANCEL_URL=https://example.com/cancel
   ```

3. **Start the Server**:
   ```bash
   npm run dev
   ```
   The server will start on `http://localhost:5500`

## Tool Schemas

### Create Order

```typescript
{
  name: "create_paypal_order",
  description: "Create a PayPal order for processing payments",
  schema: {
    intent: "CAPTURE" | "AUTHORIZE",
    purchase_units: [{
      amount: {
        currency_code: string,
        value: string
      },
      description?: string
    }],
    merchant_id: string
  }
}
```

### Capture Order

```typescript
{
  name: "capture_paypal_order",
  description: "Capture an authorized payment",
  schema: {
    order_id: string,
    merchant_id: string
  }
}
```

### Get Order Details

```typescript
{
  name: "get_order_details",
  description: "Get details of a specific order",
  schema: {
    order_id: string,
    merchant_id: string
  }
}
```

### Create Subscription

```typescript
{
  name: "create_paypal_subscription",
  description: "Create a PayPal subscription plan",
  schema: {
    product_id: string,
    billing_cycles: [{
      frequency: {
        interval_unit: "DAY" | "WEEK" | "MONTH" | "YEAR",
        interval_count: number
      },
      tenure_type: "REGULAR" | "TRIAL",
      sequence: number,
      total_cycles: number,
      pricing_scheme: {
        fixed_price: {
          value: string,
          currency_code: string
        }
      }
    }],
    merchant_id: string
  }
}
```

### Cancel Subscription

```typescript
{
  name: "cancel_subscription",
  description: "Cancel a subscription",
  schema: {
    subscription_id: string,
    reason?: string,
    merchant_id: string
  }
}
```

### Create Refund

```typescript
{
  name: "create_refund",
  description: "Create a refund for a captured payment",
  schema: {
    capture_id: string,
    amount?: {
      value: string,
      currency_code: string
    },
    merchant_id: string
  }
}
```

### Create Payout

```typescript
{
  name: "create_paypal_payout",
  description: "Create a payout to transfer funds",
  schema: {
    sender_batch_id: string,
    items: [{
      recipient_type: "EMAIL" | "PHONE" | "PAYPAL_ID",
      amount: {
        value: string,
        currency: string
      },
      receiver: string,
      note?: string
    }],
    merchant_id: string
  }
}
```

## Error Handling

The server implements comprehensive error handling with JSON-RPC 2.0 compliant error responses:

```typescript
{
  jsonrpc: "2.0",
  error: {
    code: number,      // Error code (e.g., -32000 for server error)
    message: string,   // Human-readable error message
    data?: any        // Additional error details
  }
}
```

Common error codes:

- `-32000`: Internal Server Error
- `-32001`: Connection Error
- `-32602`: Invalid Parameters

## Connection Management

The server implements several features for robust connection handling:

1. **Connection Lifecycle**:

   - Automatic connection ID assignment
   - Connection status tracking
   - Proper cleanup on disconnection

2. **Keep-alive Mechanism**:

   - 30-second ping intervals
   - Automatic connection cleanup
   - Connection state monitoring

3. **Transport Safety**:
   - Header handling
   - Write state checking
   - Error recovery

## Development

The project uses TypeScript and implements:

- Zod for runtime type validation
- Express for HTTP server
- PayPal SDK for payment processing
- Model Context Protocol for tool management

### Key Files:

- `src/index.ts`: Main server implementation
- `src/paypal-client.html`: Client interface for testing

### Running Tests

```bash
npm test
```

### Development Mode

```bash
npm run dev
```

## Client Usage

Connect to the server using the provided client interface or implement your own using the following steps:

1. **Connect to SSE Stream**:

   ```javascript
   const eventSource = new EventSource("http://localhost:5500/stream");
   ```

2. **Listen for Messages**:

   ```javascript
   eventSource.onmessage = (event) => {
     const data = JSON.parse(event.data);
     // Handle message
   };
   ```

3. **Call Tools**:
   ```javascript
   fetch("http://localhost:5500/messages?connectionId=YOUR_CONNECTION_ID", {
     method: "POST",
     headers: {
       "Content-Type": "application/json",
     },
     body: JSON.stringify({
       jsonrpc: "2.0",
       method: "call_tool",
       params: {
         name: "create_paypal_order",
         arguments: {
           // Tool arguments
         },
       },
     }),
   });
   ```

## Security Considerations

1. **Environment Variables**:

   - Never commit `.env` files
   - Use secure secrets management in production

2. **API Keys**:

   - Rotate PayPal credentials regularly
   - Use environment-specific credentials

3. **Error Handling**:
   - Sanitize error messages
   - Don't expose internal details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

ISC License
