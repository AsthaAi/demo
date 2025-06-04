import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Import aztp-client on server side where Node.js modules are available
    const aztp = require('aztp-client');
    
    const apiKey = process.env.AZTP_API_KEY || process.env.NEXT_PUBLIC_AZTP_API_KEY || "";
    
    if (!apiKey || apiKey === '1a9e69661a0356a2e71fafb4098ce29cf515ac4ac7f97e75c181f0f8c190a8f6') {
      return NextResponse.json(
        { success: false, error: 'AZTP API key not configured. Please set AZTP_API_KEY in .env.local' },
        { status: 400 }
      );
    }

    // Initialize AZTP client
    const aztpClient = aztp.initialize({
      apiKey: apiKey,
    });

    // Get the token from the request
    const body = await request.json();
    const token = body.token;

    if (!token) {
      return NextResponse.json(
        { success: false, error: 'Token is required' },
        { status: 400 }
      );
    }

    // Validate the token
    const validationResult = await aztpClient.oidc.validateToken(token);

    return NextResponse.json(validationResult);
  } catch (error) {
    console.error('Token validation API error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to validate token: ' + (error as Error).message },
      { status: 500 }
    );https://meet.google.com/zxh-gbrv-qih
  }
} 