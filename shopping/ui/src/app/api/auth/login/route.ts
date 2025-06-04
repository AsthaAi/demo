import { NextResponse } from 'next/server';
import aztp from 'aztp-client';

export async function POST(request: Request) {
    console.log('Login route called');

    // Check if API key is configured
    const apiKey = process.env.AZTP_API_KEY;
    const aztpId = process.env.AZTP_ID || "";
    if (!apiKey) {
      console.error('AZTP_API_KEY is not configured');
      return NextResponse.json(
        { error: 'Authentication service is not properly configured' },
        { status: 500 }
      );
    }

    try {
      console.log('Initializing aztp client...');
      const client = aztp.initialize({
        apiKey,
      });
      const provider = (await request.json()).provider;

      console.log('Initiating OIDC login...');
      const response = await client.oidc.login(provider, aztpId, {
        callbackUrl: "http://localhost:3000/api/auth/callback"
      });

      console.log('Response:', response);

      if (!response) {
        console.error('No response from OIDC login');
        return NextResponse.json(
          { error: 'Authentication failed - no response from provider' },
          { status: 401 }
        );
      }

      if (!response.redirectUrl) {
        console.error('No redirectUrl in OIDC response');
        return NextResponse.json(
          { error: 'Authentication failed - no redirectUrl received' },
          { status: 401 }
        );
      }

      // Return the redirect URL to the client
      return NextResponse.json({ redirectUrl: response.redirectUrl });
    } catch (error) {
      console.error('Login error:', error);
      return NextResponse.json(
        { error: 'Authentication failed' },
        { status: 500 }
      );
    }
} 