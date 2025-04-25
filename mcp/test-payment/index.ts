import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import cors from "cors";
import type { Router as ExpressRouter, Request, Response } from "express";
import express from "express";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const router: ExpressRouter = express.Router();
const PORT = 5500;

// Initialize the MCP Server
const server = new Server(
  {
    name: "payment-server",
    version: "1.0.0",
  },
  {
    capabilities: {},
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

// MCP SSE Handler
const mpcStreamHandler = async (req: Request, res: Response) => {
  try {
    // Set SSE headers
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("Access-Control-Allow-Origin", "*");

    // Create transport after headers are set
    const transport = new SSEServerTransport("/messages", res);
    const connectionId = Date.now().toString();
    activeConnections.set(connectionId, transport);

    // Connect transport to server
    await server.connect(transport);

    // Handle client disconnect
    req.on("close", () => {
      activeConnections.delete(connectionId);
      transport.close();
    });

    // Send initial connection message after everything is set up
    transport.send({
      jsonrpc: "2.0" as const,
      method: "CONNECTION_STATUS",
      params: {
        status: "connected",
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error("Error in SSE handler:", error);
    if (!res.headersSent) {
      res.status(500).end();
    }
  }
};

// Handle POST messages
const messageHandler = async (req: Request, res: Response) => {
  try {
    const { connectionId } = req.query;
    const transport = activeConnections.get(connectionId as string);

    if (transport) {
      await transport.handlePostMessage(req, res);
    } else {
      res.status(404).json({ error: "Connection not found" });
    }
  } catch (error) {
    console.error("Error handling message:", error);
    res.status(500).json({ error: "Internal server error" });
  }
};

// Generate a unique transaction code
function generateTransactionCode(): string {
  return `TXN${Date.now()}${Math.random().toString(36).substr(2, 9).toUpperCase()}`;
}

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

// Payment processing endpoint with MCP context
const paymentHandler = async (req: Request, res: Response) => {
  try {
    const { amount, currency, description } = req.body;

    // Validate payment data
    if (!amount || !currency) {
      await broadcastMessage("PAYMENT_ERROR", {
        error: "Amount and currency are required",
        timestamp: new Date().toISOString(),
      });

      res.status(400).json({
        success: false,
        error: "Amount and currency are required",
      });
      return;
    }

    // Generate transaction code
    const transactionCode = generateTransactionCode();

    // Create payment response
    const paymentResponse = {
      success: true,
      transactionCode,
      amount,
      currency,
      description,
      timestamp: new Date().toISOString(),
      status: "COMPLETED",
    };

    // Broadcast payment event
    await broadcastMessage("PAYMENT_RECEIVED", paymentResponse);

    // Send success response
    res.status(200).json(paymentResponse);
  } catch (error) {
    // Broadcast error event
    await broadcastMessage("PAYMENT_ERROR", {
      error: "Payment processing failed",
      details: error instanceof Error ? error.message : "Unknown error",
      timestamp: new Date().toISOString(),
    });

    res.status(500).json({
      success: false,
      error: "Payment processing failed",
      details: error instanceof Error ? error.message : "Unknown error",
    });
  }
};

// Payment status check endpoint
const paymentStatusHandler = async (req: Request, res: Response) => {
  const { transactionCode } = req.params;

  const statusResponse = {
    success: true,
    transactionCode,
    status: "COMPLETED",
    timestamp: new Date().toISOString(),
  };

  // Broadcast status event
  await broadcastMessage("PAYMENT_STATUS", statusResponse);

  res.status(200).json(statusResponse);
};

// Register routes
app.get("/stream", mpcStreamHandler);
app.post("/messages", messageHandler);
router.post("/payment", paymentHandler);
router.get("/payment/:transactionCode", paymentStatusHandler);

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
  console.log(`MCP SSE Server listening on http://localhost:${PORT}`);
});
