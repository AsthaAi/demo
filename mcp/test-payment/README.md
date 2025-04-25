# MCP Payment Test Implementation

This directory contains a test implementation of a payment system using Server-Sent Events (SSE) with the Model Context Protocol (MCP).

## Structure

```
test-payment/
├── index.ts        # Server implementation
├── client.html     # Client interface
└── README.md       # Documentation
```

## Server Implementation (index.ts)

The server is built using Express.js and implements the MCP SSE transport for real-time communication.

### Features

- SSE server implementation using MCP SDK
- Payment processing endpoints
- Real-time event broadcasting
- Connection management
- Error handling
- Graceful shutdown

### Endpoints

- `GET /stream` - SSE connection endpoint
- `POST /mcp/payment` - Process payment
- `GET /mcp/payment/:transactionCode` - Check payment status
- `POST /mcp/messages` - Handle SSE messages

### Event Types

1. `CONNECTION_STATUS`

   - Sent when client connects/disconnects
   - Contains connection status and timestamp

2. `PAYMENT_RECEIVED`

   - Sent when payment is processed successfully
   - Contains transaction details, amount, currency, etc.

3. `PAYMENT_ERROR`

   - Sent when payment processing fails
   - Contains error details and timestamp

4. `PAYMENT_STATUS`
   - Sent when payment status is checked
   - Contains transaction status and details

## Client Implementation (client.html)

A modern, responsive single-page web interface for interacting with the payment system.

### Features

- Real-time SSE connection
- Persistent connection status header
- Responsive payment form
- Live event streaming
- Transaction tracking
- Automatic reconnection
- Error handling

### UI Components

1. Connection Status Bar

   - Fixed position at top of window
   - Color-coded status indicators
   - Always visible while scrolling
   - Smooth status transitions

2. Payment Form

   - Clean, aligned form fields
   - Proper input validation
   - Interactive focus states
   - Responsive button design
   - Currency selection dropdown
   - Description field

3. Latest Transaction Panel

   - Prominent transaction display
   - Highlighted transaction code
   - Formatted timestamp
   - Transaction status
   - Payment details

4. Events Panel
   - Real-time event log
   - Color-coded event types
   - Formatted JSON data
   - Scrollable history
   - Hover effects

### UI/UX Features

1. Responsive Design

   - Adapts to different screen sizes
   - Mobile-friendly layout
   - Minimum width constraints
   - Proper spacing and padding

2. Visual Feedback

   - Interactive hover states
   - Focus indicators
   - Loading states
   - Error notifications
   - Success confirmations

3. Typography

   - Clear hierarchy
   - Consistent font sizes
   - Proper line heights
   - Monospace for codes

4. Layout
   - Two-column grid design
   - Fixed header
   - Proper content spacing
   - Consistent margins
   - Box shadows for depth

## Running the Application

1. Start the server:

   ```bash
   ts-node --esm index.ts
   ```

2. Access the client:

   - Open `client.html` in a web browser
   - Or serve it using a local server:
     ```bash
     python -m http.server
     # or
     npx serve
     ```

3. Server will be available at:
   - Main URL: `http://localhost:5500`
   - SSE endpoint: `http://localhost:5500/stream`
   - Payment endpoint: `http://localhost:5500/mcp/payment`

## Technical Details

### Server Dependencies

- `@modelcontextprotocol/sdk`: MCP SDK for SSE transport
- `express`: Web server framework
- `cors`: Cross-origin resource sharing middleware

### Message Format

Uses JSON-RPC 2.0 format:

```typescript
{
  jsonrpc: "2.0",
  method: string,
  params: {
    // Event specific data
    timestamp: string,
    // ... other fields
  }
}
```

### Error Handling

1. Server-side:

   - Connection errors
   - Payment validation
   - Message broadcasting
   - Header conflicts
   - Graceful shutdown

2. Client-side:
   - Connection drops
   - Payment submission errors
   - Message parsing
   - Automatic reconnection
   - Form validation

## Security Considerations

1. CORS is enabled with specific options
2. Headers are properly set for SSE
3. Input validation for payment data
4. Error messages are sanitized
5. Proper connection cleanup
6. Secure form submission

## Development

### Adding New Events

1. Add event type to server broadcast function
2. Update client event handling
3. Add UI components if needed

### Modifying Payment Process

1. Update payment handler in server
2. Modify form handling in client
3. Update event types as needed

### UI Customization

1. Colors and Themes

   - Update CSS variables
   - Modify color schemes
   - Adjust animations

2. Layout Changes

   - Modify grid system
   - Adjust responsive breakpoints
   - Update component spacing

3. Component Styling
   - Customize form elements
   - Modify card designs
   - Update typography

## Future Improvements

1. Authentication system
2. Payment validation logic
3. Database integration
4. More payment methods
5. Enhanced error handling
6. Transaction history
7. Admin interface
8. Dark mode support
9. More currency options
10. Payment analytics
