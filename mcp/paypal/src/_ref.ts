#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import paypal from "@paypal/checkout-server-sdk";
import dotenv from "dotenv";

// Load environment variables
dotenv.config();

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

// Define the tools
const CREATE_ORDER_TOOL: Tool = {
  name: "create_paypal_order",
  description: "Create a PayPal order for processing payments",
  inputSchema: {
    type: "object",
    properties: {
      intent: {
        type: "string",
        enum: ["CAPTURE", "AUTHORIZE"],
        description: "Payment intent (CAPTURE or AUTHORIZE)",
      },
      purchase_units: {
        type: "array",
        items: {
          type: "object",
          properties: {
            amount: {
              type: "object",
              properties: {
                currency_code: { type: "string" },
                value: { type: "string" },
              },
              required: ["currency_code", "value"],
            },
            description: { type: "string" },
          },
          required: ["amount"],
        },
      },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["intent", "purchase_units", "merchant_id"],
  },
};

const CAPTURE_ORDER_TOOL: Tool = {
  name: "capture_paypal_order",
  description: "Capture an authorized payment",
  inputSchema: {
    type: "object",
    properties: {
      order_id: { type: "string", description: "PayPal order ID to capture" },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["order_id", "merchant_id"],
  },
};

const GET_ORDER_DETAILS_TOOL: Tool = {
  name: "get_order_details",
  description: "Get details of a specific order",
  inputSchema: {
    type: "object",
    properties: {
      order_id: { type: "string", description: "PayPal order ID" },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["order_id", "merchant_id"],
  },
};

const CREATE_SUBSCRIPTION_TOOL: Tool = {
  name: "create_paypal_subscription",
  description: "Create a PayPal subscription plan",
  inputSchema: {
    type: "object",
    properties: {
      product_id: { type: "string", description: "PayPal product ID" },
      billing_cycles: {
        type: "array",
        items: {
          type: "object",
          properties: {
            frequency: {
              type: "object",
              properties: {
                interval_unit: {
                  type: "string",
                  enum: ["DAY", "WEEK", "MONTH", "YEAR"],
                },
                interval_count: { type: "number" },
              },
              required: ["interval_unit", "interval_count"],
            },
            tenure_type: {
              type: "string",
              enum: ["REGULAR", "TRIAL"],
            },
            sequence: { type: "number" },
            total_cycles: { type: "number" },
            pricing_scheme: {
              type: "object",
              properties: {
                fixed_price: {
                  type: "object",
                  properties: {
                    value: { type: "string" },
                    currency_code: { type: "string" },
                  },
                  required: ["value", "currency_code"],
                },
              },
              required: ["fixed_price"],
            },
          },
          required: ["frequency", "tenure_type", "sequence", "pricing_scheme"],
        },
      },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["product_id", "billing_cycles", "merchant_id"],
  },
};

const CANCEL_SUBSCRIPTION_TOOL: Tool = {
  name: "cancel_subscription",
  description: "Cancel a subscription",
  inputSchema: {
    type: "object",
    properties: {
      subscription_id: {
        type: "string",
        description: "PayPal subscription ID",
      },
      reason: { type: "string", description: "Cancellation reason" },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["subscription_id", "merchant_id"],
  },
};

const CREATE_REFUND_TOOL: Tool = {
  name: "create_refund",
  description: "Create a refund for a captured payment",
  inputSchema: {
    type: "object",
    properties: {
      capture_id: { type: "string", description: "PayPal capture ID" },
      amount: {
        type: "object",
        properties: {
          value: { type: "string" },
          currency_code: { type: "string" },
        },
        required: ["value", "currency_code"],
      },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["capture_id", "merchant_id"],
  },
};

const CREATE_PAYOUT_TOOL: Tool = {
  name: "create_paypal_payout",
  description: "Create a payout to transfer funds",
  inputSchema: {
    type: "object",
    properties: {
      sender_batch_id: {
        type: "string",
        description: "Unique identifier for the payout",
      },
      items: {
        type: "array",
        items: {
          type: "object",
          properties: {
            recipient_type: {
              type: "string",
              enum: ["EMAIL", "PHONE", "PAYPAL_ID"],
            },
            amount: {
              type: "object",
              properties: {
                value: { type: "string" },
                currency: { type: "string" },
              },
              required: ["value", "currency"],
            },
            receiver: { type: "string" },
            note: { type: "string" },
          },
          required: ["recipient_type", "amount", "receiver"],
        },
      },
      merchant_id: {
        type: "string",
        description: "Merchant's PayPal account ID",
      },
    },
    required: ["sender_batch_id", "items", "merchant_id"],
  },
};

// Server setup
const server = new Server(
  {
    name: "paypal-mcp-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool implementation functions

// Create PayPal Order
async function createOrder(args: any) {
  try {
    const request = new paypal.orders.OrdersCreateRequest();
    request.prefer("return=representation");
    request.requestBody({
      intent: args.intent,
      purchase_units: args.purchase_units,
      application_context: {
        return_url: process.env.PAYPAL_RETURN_URL,
        cancel_url: process.env.PAYPAL_CANCEL_URL,
      },
    });

    const response = await paypalClient.execute(request);
    return {
      orderId: response.result.id,
      status: response.result.status,
      links: response.result.links,
    };
  } catch (error: any) {
    console.error("PayPal order creation failed:", error);
    throw new Error(`PayPal order creation failed: ${error.message}`);
  }
}

// Capture PayPal Order
async function captureOrder(args: any) {
  try {
    const request = new paypal.orders.OrdersCaptureRequest(args.order_id);
    request.prefer("return=representation");

    const response = await paypalClient.execute(request);
    return {
      orderId: response.result.id,
      status: response.result.status,
      captureId:
        response.result.purchase_units[0]?.payments?.captures[0]?.id || null,
    };
  } catch (error: any) {
    console.error("PayPal order capture failed:", error);
    throw new Error(`PayPal order capture failed: ${error.message}`);
  }
}

// Get Order Details
async function getOrderDetails(args: any) {
  try {
    const request = new paypal.orders.OrdersGetRequest(args.order_id);

    const response = await paypalClient.execute(request);
    return response.result;
  } catch (error: any) {
    console.error("PayPal get order details failed:", error);
    throw new Error(`PayPal get order details failed: ${error.message}`);
  }
}

// Create Subscription
async function createSubscription(args: any) {
  try {
    // First, create a subscription plan
    const planRequest = {
      product_id: args.product_id,
      name: args.name || "Subscription Plan",
      description:
        args.description || "Subscription plan created via MCP server",
      billing_cycles: args.billing_cycles,
      payment_preferences: {
        auto_bill_outstanding: true,
        setup_fee: args.setup_fee,
        setup_fee_failure_action: "CONTINUE",
        payment_failure_threshold: 3,
      },
    };

    // Create plan
    const planCreateRequest = new paypal.subscriptions.PlansCreateRequest();
    planCreateRequest.requestBody(planRequest);

    const planResponse = await paypalClient.execute(planCreateRequest);
    const planId = planResponse.result.id;

    // Now create a subscription using this plan
    const subscriptionRequest = {
      plan_id: planId,
      start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Start tomorrow
      subscriber: {
        name: {
          given_name: args.subscriber_first_name || "Subscriber",
          surname: args.subscriber_last_name || "User",
        },
        email_address: args.subscriber_email,
      },
      application_context: {
        brand_name: args.brand_name || "Merchant",
        shipping_preference: "NO_SHIPPING",
        user_action: "SUBSCRIBE_NOW",
        payment_method: {
          payer_selected: "PAYPAL",
          payee_preferred: "IMMEDIATE_PAYMENT_REQUIRED",
        },
        return_url: process.env.PAYPAL_RETURN_URL,
        cancel_url: process.env.PAYPAL_CANCEL_URL,
      },
    };

    const subscriptionCreateRequest =
      new paypal.subscriptions.SubscriptionsCreateRequest();
    subscriptionCreateRequest.requestBody(subscriptionRequest);

    const subscriptionResponse = await paypalClient.execute(
      subscriptionCreateRequest
    );

    return {
      subscriptionId: subscriptionResponse.result.id,
      planId: planId,
      status: subscriptionResponse.result.status,
      links: subscriptionResponse.result.links,
    };
  } catch (error: any) {
    console.error("PayPal subscription creation failed:", error);
    throw new Error(`PayPal subscription creation failed: ${error.message}`);
  }
}

// Cancel Subscription
async function cancelSubscription(args: any) {
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

    return {
      subscriptionId: args.subscription_id,
      status: response.result.status,
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
async function createRefund(args: any) {
  try {
    const request = new paypal.payments.CapturesRefundRequest(args.capture_id);

    if (args.amount) {
      request.requestBody({
        amount: {
          value: args.amount.value,
          currency_code: args.amount.currency_code,
        },
        note_to_payer: args.note || "Refund from merchant",
      });
    }

    const response = await paypalClient.execute(request);

    return {
      refundId: response.result.id,
      captureId: args.capture_id,
      status: response.result.status,
      amount: response.result.amount,
    };
  } catch (error: any) {
    console.error("PayPal refund creation failed:", error);
    throw new Error(`PayPal refund creation failed: ${error.message}`);
  }
}

// Create Payout
async function createPayout(args: any) {
  try {
    const request = new paypal.payouts.PayoutsPostRequest();
    request.requestBody({
      sender_batch_header: {
        sender_batch_id: args.sender_batch_id,
        email_subject: args.email_subject || "You have received a payout",
        email_message:
          args.email_message || "You have received a payout from a merchant",
      },
      items: args.items,
    });

    const response = await paypalClient.execute(request);

    return {
      batchId: response.result.batch_header.payout_batch_id,
      status: response.result.batch_header.batch_status,
      links: response.result.links,
    };
  } catch (error: any) {
    console.error("PayPal payout creation failed:", error);
    throw new Error(`PayPal payout creation failed: ${error.message}`);
  }
}

// Request handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    CREATE_ORDER_TOOL,
    CAPTURE_ORDER_TOOL,
    GET_ORDER_DETAILS_TOOL,
    CREATE_SUBSCRIPTION_TOOL,
    CANCEL_SUBSCRIPTION_TOOL,
    CREATE_REFUND_TOOL,
    CREATE_PAYOUT_TOOL,
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "create_paypal_order":
        const orderResult = await createOrder(args);
        return {
          content: [{ type: "text", text: JSON.stringify(orderResult) }],
        };

      case "capture_paypal_order":
        const captureResult = await captureOrder(args);
        return {
          content: [{ type: "text", text: JSON.stringify(captureResult) }],
        };

      case "get_order_details":
        const orderDetails = await getOrderDetails(args);
        return {
          content: [{ type: "text", text: JSON.stringify(orderDetails) }],
        };

      case "create_paypal_subscription":
        const subscriptionResult = await createSubscription(args);
        return {
          content: [{ type: "text", text: JSON.stringify(subscriptionResult) }],
        };

      case "cancel_subscription":
        const cancelResult = await cancelSubscription(args);
        return {
          content: [{ type: "text", text: JSON.stringify(cancelResult) }],
        };

      case "create_refund":
        const refundResult = await createRefund(args);
        return {
          content: [{ type: "text", text: JSON.stringify(refundResult) }],
        };

      case "create_paypal_payout":
        const payoutResult = await createPayout(args);
        return {
          content: [{ type: "text", text: JSON.stringify(payoutResult) }],
        };

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (error: any) {
    console.error(`Error executing tool ${name}:`, error);
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

// Server startup
async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("PayPal MCP Server running on stdio");
}

// Run the server
runServer().catch((error) => {
  console.error("Fatal error running server:", error);
  process.exit(1);
});
