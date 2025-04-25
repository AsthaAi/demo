import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import paypal from "@paypal/checkout-server-sdk";
import cors from "cors";
import dotenv from "dotenv";
import { EventEmitter } from "events";
import type {
  Response as ExpressResponse,
  Router as ExpressRouter,
  Request,
  Response,
} from "express";
import express from "express";
import { dirname } from "path";
import { fileURLToPath } from "url";
import { z } from "zod";

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const router: ExpressRouter = express.Router();
const PORT = 5500;

// PayPal environment setup
function environment() {
  const clientId = process.env.PAYPAL_CLIENT_ID;
  const clientSecret = process.env.PAYPAL_CLIENT_SECRET;

  if (!clientId || !clientSecret) {
    throw new Error("PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are required");
  }

  const environment =
    process.env.PAYPAL_ENVIRONMENT === "live"
      ? new paypal.core.LiveEnvironment(clientId, clientSecret)
      : new paypal.core.SandboxEnvironment(clientId, clientSecret);

  return new paypal.core.PayPalHttpClient(environment);
}

// Initialize PayPal client
const paypalClient = environment();

// Define tool types
type ToolResponse = {
  content: Array<{ type: string; text: string }>;
  isError?: boolean;
};

type ToolRequest = {
  params: {
    name: string;
    arguments?: Record<string, any>;
  };
};

type Tool = {
  name: string;
  description: string;
  schema: z.ZodType<any, any>;
};

// PayPal Tool Schemas using Zod
const CREATE_ORDER_TOOL: Tool = {
  name: "create_paypal_order",
  description: "Create a PayPal order for processing payments",
  schema: z.object({
    intent: z.enum(["CAPTURE", "AUTHORIZE"]),
    purchase_units: z.array(
      z.object({
        amount: z.object({
          currency_code: z.string(),
          value: z.string(),
        }),
        description: z.string().optional(),
      })
    ),
    merchant_id: z.string(),
  }),
};

const CAPTURE_ORDER_TOOL: Tool = {
  name: "capture_paypal_order",
  description: "Capture an authorized payment",
  schema: z.object({
    order_id: z.string(),
    merchant_id: z.string(),
  }),
};

const GET_ORDER_DETAILS_TOOL: Tool = {
  name: "get_order_details",
  description: "Get details of a specific order",
  schema: z.object({
    order_id: z.string(),
    merchant_id: z.string(),
  }),
};

const CREATE_SUBSCRIPTION_TOOL: Tool = {
  name: "create_paypal_subscription",
  description: "Create a PayPal subscription plan",
  schema: z.object({
    product_id: z.string(),
    billing_cycles: z.array(
      z.object({
        frequency: z.object({
          interval_unit: z.enum(["DAY", "WEEK", "MONTH", "YEAR"]),
          interval_count: z.number(),
        }),
        tenure_type: z.enum(["REGULAR", "TRIAL"]),
        sequence: z.number(),
        total_cycles: z.number(),
        pricing_scheme: z.object({
          fixed_price: z.object({
            value: z.string(),
            currency_code: z.string(),
          }),
        }),
      })
    ),
    merchant_id: z.string(),
  }),
};

const CANCEL_SUBSCRIPTION_TOOL: Tool = {
  name: "cancel_subscription",
  description: "Cancel a subscription",
  schema: z.object({
    subscription_id: z.string(),
    reason: z.string().optional(),
    merchant_id: z.string(),
  }),
};

const CREATE_REFUND_TOOL: Tool = {
  name: "create_refund",
  description: "Create a refund for a captured payment",
  schema: z.object({
    capture_id: z.string(),
    amount: z
      .object({
        value: z.string(),
        currency_code: z.string(),
      })
      .optional(),
    merchant_id: z.string(),
  }),
};

const CREATE_PAYOUT_TOOL: Tool = {
  name: "create_paypal_payout",
  description: "Create a payout to transfer funds",
  schema: z.object({
    sender_batch_id: z.string(),
    items: z.array(
      z.object({
        recipient_type: z.enum(["EMAIL", "PHONE", "PAYPAL_ID"]),
        amount: z.object({
          value: z.string(),
          currency: z.string(),
        }),
        receiver: z.string(),
        note: z.string().optional(),
      })
    ),
    merchant_id: z.string(),
  }),
};

// Request schemas
const ListToolsSchema = z.object({
  method: z.literal("list_tools"),
});

const CallToolSchema = z.object({
  method: z.literal("call_tool"),
  params: z.object({
    name: z.string(),
    arguments: z.record(z.unknown()).optional(),
  }),
});

// Initialize the MCP Server
const server = new Server(
  {
    name: "paypal-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {
        create_paypal_order: CREATE_ORDER_TOOL,
        capture_paypal_order: CAPTURE_ORDER_TOOL,
        get_order_details: GET_ORDER_DETAILS_TOOL,
        create_paypal_subscription: CREATE_SUBSCRIPTION_TOOL,
        cancel_subscription: CANCEL_SUBSCRIPTION_TOOL,
        create_refund: CREATE_REFUND_TOOL,
        create_paypal_payout: CREATE_PAYOUT_TOOL,
      },
    },
  }
);

// Enable CORS with specific options
app.use(
  cors({
    origin: "*",
    methods: ["GET", "POST"],
    credentials: true,
    optionsSuccessStatus: 204,
  })
);

app.use(express.json());

// Store active SSE connections
const activeConnections = new Map<string, SSEServerTransport>();

// Extend SSEServerTransport type
declare module "@modelcontextprotocol/sdk/server/sse.js" {
  interface SSEServerTransport {
    response: ExpressResponse;
    emit(event: string, ...args: any[]): boolean;
    on(event: string, listener: (...args: any[]) => void): this;
  }
}

// Extend SSEServerTransport with EventEmitter
Object.setPrototypeOf(SSEServerTransport.prototype, EventEmitter.prototype);

// Custom error type
interface TransportError extends Error {
  code?: string;
  details?: unknown;
}

// MCP SSE Handler
const mpcStreamHandler = async (req: Request, res: Response) => {
  try {
    const connectionId = Date.now().toString();

    // Create transport first
    const transport = new SSEServerTransport("/messages", res);

    // Set up error handler before connecting
    transport.on("error", (error: TransportError) => {
      console.error("Transport error:", error);
      if (!res.writableEnded) {
        res.write(
          `data: ${JSON.stringify({
            jsonrpc: "2.0",
            error: {
              code: error.code || -32000,
              message: "Transport error",
              data: error.message || error.details || "Unknown error",
            },
          })}\n\n`
        );
      }
    });

    // Store the connection
    activeConnections.set(connectionId, transport);

    // Connect transport to server - this will set up headers
    await server.connect(transport);

    // Send initial connection message after transport is connected
    if (!res.writableEnded) {
      const connectionMessage = {
        jsonrpc: "2.0",
        method: "CONNECTION_STATUS",
        params: {
          status: "connected",
          connectionId,
          timestamp: new Date().toISOString(),
        },
      };
      res.write(`data: ${JSON.stringify(connectionMessage)}\n\n`);
    }

    // Keep the connection alive with a ping every 30 seconds
    const keepAliveInterval = setInterval(() => {
      if (!res.writableEnded) {
        res.write(": ping\n\n");
      } else {
        clearInterval(keepAliveInterval);
      }
    }, 30000);

    // Handle client disconnect
    req.on("close", () => {
      clearInterval(keepAliveInterval);
      activeConnections.delete(connectionId);
      transport.emit("close");
    });
  } catch (error) {
    console.error("Error in SSE handler:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: {
          code: -32000,
          message: "Internal Server Error",
          data: error instanceof Error ? error.message : "Unknown error",
        },
      });
    }
  }
};

// Helper function to check if transport is active
function isTransportActive(transport: SSEServerTransport): boolean {
  return transport.response && !transport.response.writableEnded;
}

// Handle POST messages
const messageHandler = async (req: Request, res: Response) => {
  try {
    const { connectionId } = req.query;

    if (!connectionId) {
      return res.status(400).json({
        jsonrpc: "2.0",
        error: {
          code: -32602,
          message: "Invalid params",
          data: "Missing connectionId parameter",
        },
      });
    }

    const transport = activeConnections.get(connectionId as string);

    if (!transport) {
      return res.status(404).json({
        jsonrpc: "2.0",
        error: {
          code: -32001,
          message: "Connection not found",
          data: "The specified connection ID does not exist",
        },
      });
    }

    // Check if transport is still active
    if (!isTransportActive(transport)) {
      activeConnections.delete(connectionId as string);
      return res.status(410).json({
        jsonrpc: "2.0",
        error: {
          code: -32001,
          message: "Connection closed",
          data: "The SSE connection is no longer active",
        },
      });
    }

    await transport.handlePostMessage(req, res);
  } catch (error) {
    console.error("Error handling message:", error);
    res.status(500).json({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Internal server error",
        data: error instanceof Error ? error.message : "Unknown error",
      },
    });
  }
};

// Broadcast message to all connected clients
async function broadcastMessage(method: string, params: any) {
  const message = {
    jsonrpc: "2.0" as const,
    method,
    params,
  };

  for (const transport of activeConnections.values()) {
    try {
      await transport.send(message);
    } catch (error) {
      console.error("Error broadcasting message:", error);
    }
  }
}

// PayPal Response Types
interface PayPalOrderResponse {
  id: string;
  status: string;
  links: Array<{
    href: string;
    rel: string;
    method: string;
  }>;
  purchase_units?: Array<{
    payments?: {
      captures?: Array<{
        id: string;
      }>;
    };
  }>;
}

interface PayPalPlanResponse {
  id: string;
  status: string;
  links: Array<{
    href: string;
    rel: string;
    method: string;
  }>;
}

interface PayPalSubscriptionResponse {
  id: string;
  status: string;
}

interface PayPalRefundResponse {
  id: string;
  status: string;
  amount: {
    value: string;
    currency_code: string;
  };
}

interface PayPalPayoutResponse {
  batch_header: {
    payout_batch_id: string;
    batch_status: string;
  };
  links: Array<{
    href: string;
    rel: string;
    method: string;
  }>;
}

// PayPal Tool Implementation Functions

// Create PayPal Order
async function createOrder(args: {
  intent: "CAPTURE" | "AUTHORIZE";
  purchase_units: Array<{
    amount: {
      currency_code: string;
      value: string;
    };
    description?: string;
  }>;
  merchant_id: string;
}) {
  try {
    // Validate PayPal environment
    if (!process.env.PAYPAL_CLIENT_ID || !process.env.PAYPAL_CLIENT_SECRET) {
      throw new Error("PayPal credentials are not configured");
    }

    const request = new paypal.orders.OrdersCreateRequest();
    request.prefer("return=representation");
    request.requestBody({
      intent: args.intent,
      purchase_units: args.purchase_units,
      application_context: {
        return_url:
          process.env.PAYPAL_RETURN_URL || "https://example.com/return",
        cancel_url:
          process.env.PAYPAL_CANCEL_URL || "https://example.com/cancel",
      },
    });

    const response = await paypalClient.execute(request);
    const result = response.result as PayPalOrderResponse;

    return {
      orderId: result.id,
      status: result.status,
      links: result.links,
    };
  } catch (error: any) {
    console.error("PayPal order creation failed:", error);

    // Format the error response
    const errorResponse = {
      error: error.message || "PayPal order creation failed",
      details: error.details || [],
      httpStatusCode: error.statusCode || 500,
    };

    if (error.response) {
      try {
        const paypalError = error.response.error || error.response.details?.[0];
        errorResponse.details = [
          {
            issue: paypalError?.issue || paypalError?.message || error.message,
            description:
              paypalError?.description || "No additional details available",
          },
        ];
      } catch (parseError) {
        console.error("Error parsing PayPal error response:", parseError);
      }
    }

    throw errorResponse;
  }
}

// Capture PayPal Order
async function captureOrder(args: { order_id: string; merchant_id: string }) {
  try {
    const request = new paypal.orders.OrdersCaptureRequest(args.order_id);
    request.prefer("return=representation");

    const response = await paypalClient.execute(request);
    const result = response.result as PayPalOrderResponse;

    return {
      orderId: result.id,
      status: result.status,
      captureId:
        result.purchase_units?.[0]?.payments?.captures?.[0]?.id || null,
    };
  } catch (error: any) {
    console.error("PayPal order capture failed:", error);
    throw new Error(`PayPal order capture failed: ${error.message}`);
  }
}

// Get Order Details
async function getOrderDetails(args: {
  order_id: string;
  merchant_id: string;
}) {
  try {
    const request = new paypal.orders.OrdersGetRequest(args.order_id);
    const response = await paypalClient.execute(request);
    return response.result as PayPalOrderResponse;
  } catch (error: any) {
    console.error("PayPal get order details failed:", error);
    throw new Error(`PayPal get order details failed: ${error.message}`);
  }
}

// Create Subscription
async function createSubscription(args: {
  product_id: string;
  billing_cycles: Array<{
    frequency: {
      interval_unit: "DAY" | "WEEK" | "MONTH" | "YEAR";
      interval_count: number;
    };
    tenure_type: "REGULAR" | "TRIAL";
    sequence: number;
    total_cycles: number;
    pricing_scheme: {
      fixed_price: {
        value: string;
        currency_code: string;
      };
    };
  }>;
  merchant_id: string;
}) {
  try {
    const planCreateRequest = new paypal.subscriptions.PlansCreateRequest();
    planCreateRequest.requestBody({
      product_id: args.product_id,
      name: "Subscription Plan",
      description: "Subscription plan created via MCP server",
      billing_cycles: args.billing_cycles,
      payment_preferences: {
        auto_bill_outstanding: true,
        setup_fee_failure_action: "CONTINUE",
        payment_failure_threshold: 3,
      },
    });

    const planResponse = await paypalClient.execute(planCreateRequest);
    const result = planResponse.result as PayPalPlanResponse;

    return {
      planId: result.id,
      status: "CREATED",
      links: result.links,
    };
  } catch (error: any) {
    console.error("PayPal subscription creation failed:", error);
    throw new Error(`PayPal subscription creation failed: ${error.message}`);
  }
}

// Cancel Subscription
async function cancelSubscription(args: {
  subscription_id: string;
  reason?: string;
  merchant_id: string;
}) {
  try {
    const request = new paypal.subscriptions.SubscriptionsCancelRequest(
      args.subscription_id
    );
    request.requestBody({
      reason: args.reason || "Merchant initiated cancellation",
    });

    await paypalClient.execute(request);

    // Verify the subscription status
    const getRequest = new paypal.subscriptions.SubscriptionsGetRequest(
      args.subscription_id
    );
    const response = await paypalClient.execute(getRequest);
    const result = response.result as PayPalSubscriptionResponse;

    return {
      subscriptionId: args.subscription_id,
      status: result.status,
      message: "Subscription cancelled successfully",
    };
  } catch (error: any) {
    console.error("PayPal subscription cancellation failed:", error);
    throw new Error(
      `PayPal subscription cancellation failed: ${error.message}`
    );
  }
}

// Create Refund
async function createRefund(args: {
  capture_id: string;
  amount?: {
    value: string;
    currency_code: string;
  };
  merchant_id: string;
}) {
  try {
    const request = new paypal.payments.CapturesRefundRequest(args.capture_id);

    if (args.amount) {
      request.requestBody({
        amount: args.amount,
        note_to_payer: "Refund from merchant",
      });
    }

    const response = await paypalClient.execute(request);
    const result = response.result as PayPalRefundResponse;

    return {
      refundId: result.id,
      captureId: args.capture_id,
      status: result.status,
      amount: result.amount,
    };
  } catch (error: any) {
    console.error("PayPal refund creation failed:", error);
    throw new Error(`PayPal refund creation failed: ${error.message}`);
  }
}

// Create Payout
async function createPayout(args: {
  sender_batch_id: string;
  items: Array<{
    recipient_type: "EMAIL" | "PHONE" | "PAYPAL_ID";
    amount: {
      value: string;
      currency: string;
    };
    receiver: string;
    note?: string;
  }>;
  merchant_id: string;
}) {
  try {
    const request = new paypal.payouts.PayoutsPostRequest();
    request.requestBody({
      sender_batch_header: {
        sender_batch_id: args.sender_batch_id,
        email_subject: "You have received a payout",
        email_message: "You have received a payout from a merchant",
      },
      items: args.items,
    });

    const response = await paypalClient.execute(request);
    const result = response.result as PayPalPayoutResponse;

    return {
      batchId: result.batch_header.payout_batch_id,
      status: result.batch_header.batch_status,
      links: result.links,
    };
  } catch (error: any) {
    console.error("PayPal payout creation failed:", error);
    throw new Error(`PayPal payout creation failed: ${error.message}`);
  }
}

// Handle list tools request
server.setRequestHandler(ListToolsSchema, async () => {
  return {
    tools: [
      CREATE_ORDER_TOOL,
      CAPTURE_ORDER_TOOL,
      GET_ORDER_DETAILS_TOOL,
      CREATE_SUBSCRIPTION_TOOL,
      CANCEL_SUBSCRIPTION_TOOL,
      CREATE_REFUND_TOOL,
      CREATE_PAYOUT_TOOL,
    ],
  };
});

// Handle tool calls
server.setRequestHandler(
  CallToolSchema,
  async (request: ToolRequest): Promise<ToolResponse> => {
    const { name, arguments: args = {} } = request.params;

    try {
      switch (name) {
        case "create_paypal_order": {
          // Validate input against schema
          const validatedArgs = CREATE_ORDER_TOOL.schema.parse(args);
          const orderResult = await createOrder(validatedArgs);
          return {
            content: [{ type: "text", text: JSON.stringify(orderResult) }],
          };
        }

        case "capture_paypal_order": {
          const typedArgs = args as { order_id: string; merchant_id: string };
          const captureResult = await captureOrder(typedArgs);
          return {
            content: [{ type: "text", text: JSON.stringify(captureResult) }],
          };
        }

        case "get_order_details": {
          const typedArgs = args as { order_id: string; merchant_id: string };
          const orderDetails = await getOrderDetails(typedArgs);
          return {
            content: [{ type: "text", text: JSON.stringify(orderDetails) }],
          };
        }

        case "create_paypal_subscription": {
          const typedArgs = args as {
            product_id: string;
            billing_cycles: Array<{
              frequency: {
                interval_unit: "DAY" | "WEEK" | "MONTH" | "YEAR";
                interval_count: number;
              };
              tenure_type: "REGULAR" | "TRIAL";
              sequence: number;
              total_cycles: number;
              pricing_scheme: {
                fixed_price: {
                  value: string;
                  currency_code: string;
                };
              };
            }>;
            merchant_id: string;
          };
          const subscriptionResult = await createSubscription(typedArgs);
          return {
            content: [
              { type: "text", text: JSON.stringify(subscriptionResult) },
            ],
          };
        }

        case "cancel_subscription": {
          const typedArgs = args as {
            subscription_id: string;
            reason?: string;
            merchant_id: string;
          };
          const cancelResult = await cancelSubscription(typedArgs);
          return {
            content: [{ type: "text", text: JSON.stringify(cancelResult) }],
          };
        }

        case "create_refund": {
          const typedArgs = args as {
            capture_id: string;
            amount?: {
              value: string;
              currency_code: string;
            };
            merchant_id: string;
          };
          const refundResult = await createRefund(typedArgs);
          return {
            content: [{ type: "text", text: JSON.stringify(refundResult) }],
          };
        }

        case "create_paypal_payout": {
          const typedArgs = args as {
            sender_batch_id: string;
            items: Array<{
              recipient_type: "EMAIL" | "PHONE" | "PAYPAL_ID";
              amount: {
                value: string;
                currency: string;
              };
              receiver: string;
              note?: string;
            }>;
            merchant_id: string;
          };
          const payoutResult = await createPayout(typedArgs);
          return {
            content: [{ type: "text", text: JSON.stringify(payoutResult) }],
          };
        }

        default:
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  error: `Unknown tool: ${name}`,
                  details: [],
                  httpStatusCode: 400,
                }),
              },
            ],
            isError: true,
          };
      }
    } catch (error: any) {
      console.error(`Error executing tool ${name}:`, error);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error:
                error.error || error.message || `Error executing tool ${name}`,
              details: error.details || [],
              httpStatusCode: error.httpStatusCode || 500,
            }),
          },
        ],
        isError: true,
      };
    }
  }
);

// Example endpoint to demonstrate SSE functionality
const sendMessageHandler = async (req: Request, res: Response) => {
  try {
    const { message, type = "INFO" } = req.body;

    if (!message) {
      res.status(400).json({
        success: false,
        error: "Message is required",
      });
      return;
    }

    // Create message response
    const messageResponse = {
      type,
      content: message,
      timestamp: new Date().toISOString(),
    };

    // Broadcast message event
    await broadcastMessage("MESSAGE_RECEIVED", messageResponse);

    // Send success response
    res.status(200).json({
      success: true,
      message: "Message broadcasted successfully",
      data: messageResponse,
    });
  } catch (error) {
    // Broadcast error event
    await broadcastMessage("MESSAGE_ERROR", {
      error: "Message broadcasting failed",
      details: error instanceof Error ? error.message : "Unknown error",
      timestamp: new Date().toISOString(),
    });

    res.status(500).json({
      success: false,
      error: "Message broadcasting failed",
      details: error instanceof Error ? error.message : "Unknown error",
    });
  }
};

// Register routes
app.get("/stream", mpcStreamHandler);
app.post("/messages", messageHandler);
router.post("/send-message", sendMessageHandler);

// Mount all routes under /mcp
app.use("/mcp", router);

// Serve static files
app.use(express.static(__dirname));

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("Shutting down server...");
  for (const transport of activeConnections.values()) {
    transport.close();
  }
  process.exit(0);
});

app.listen(PORT, () => {
  console.log(`PayPal MCP SSE Server listening on http://localhost:${PORT}`);
});
