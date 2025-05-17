import { NextResponse } from 'next/server';
import axios from 'axios';

interface ProductData {
  name: string;
  price: number;
  rating: number;
  description: string;
}

interface ChatResponse {
  message: string;
  type: 'text' | 'product';
  data: ProductData | null;
}

export async function POST(request: Request) {
  try {
    const { message } = await request.json();

    // TODO: Replace with actual backend API call
    // For now, we'll simulate a response
    const response: ChatResponse = {
      message: "I understand you're looking for products. Let me help you with that.",
      type: "text",
      data: null
    };

    // If the message contains product-related keywords, return a sample product
    if (message.toLowerCase().includes('product') || message.toLowerCase().includes('search')) {
      response.type = 'product';
      response.data = {
        name: 'Sample Product',
        price: 99.99,
        rating: 4.5,
        description: 'This is a sample product description.'
      };
    }

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 