import { openai } from "@ai-sdk/openai";
import { PayPalAgentToolkit } from "@paypal/agent-toolkit/ai-sdk";
import { generateText } from "ai";
import { NextRequest, NextResponse } from "next/server";

const paypalToolkit = new PayPalAgentToolkit({
  clientId: process.env.PAYPAL_CLIENT_ID !== undefined ? process.env.PAYPAL_CLIENT_ID : "",
  clientSecret: process.env.PAYPAL_CLIENT_SECRET!== undefined ? process.env.PAYPAL_CLIENT_SECRET : "",
  configuration: {
    actions: {
      orders: { create: true, get: true },
      invoices: { create: true, list: true },
      // Extend with other actions as needed
    },
  },
});

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();

    // Define System Prompt for controlling behavior
    const systemPrompt =
      "This is a PayPal agent. You are tasked with handling PayPal orders and providing relevant information.";

    const { text: response } = await generateText({
      model: openai("gpt-4o"),
      tools: paypalToolkit.getTools(),
      maxSteps: 10,
      prompt: message,
      system: systemPrompt,
    });

    return NextResponse.json({ response });
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "An unknown error occurred";

    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
