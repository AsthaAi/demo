import { NextResponse } from 'next/server';
import aztp from 'aztp-client';

export async function GET(request: Request) {
  try {
    console.log('Callback route called');
    const { searchParams } = new URL(request.url);
    const token = searchParams.get('token');
    const agent = searchParams.get('agent');
    const provider = searchParams.get('provider');

    console.log('URL parameters:', { token: !!token, agent, provider });

    if (!token || !agent || !provider) {
      console.error('Missing required parameters:', { token: !!token, agent: !!agent, provider: !!provider });
      const redirectUrl = new URL('/', request.url);
      redirectUrl.searchParams.set('error', 'invalid_callback');
      console.log('Redirecting to:', redirectUrl.toString());
      return NextResponse.redirect(redirectUrl);
    }

    const apiKey = process.env.AZTP_API_KEY;
    if (!apiKey) {
      console.error('AZTP_API_KEY is not configured');
      const redirectUrl = new URL('/', request.url);
      redirectUrl.searchParams.set('error', 'configuration_error');
      console.log('Redirecting to:', redirectUrl.toString());
      return NextResponse.redirect(redirectUrl);
    }

    console.log('Initializing aztp client...');
    let client;
    try {
      client = aztp.initialize({
        apiKey,
      });
      console.log('AZTP client initialized successfully');
    } catch (initError) {
      console.error('Failed to initialize AZTP client:', initError);
      const redirectUrl = new URL('/', request.url);
      redirectUrl.searchParams.set('error', 'client_initialization_failed');
      console.log('Redirecting to:', redirectUrl.toString());
      return NextResponse.redirect(redirectUrl);
    }

    console.log('Validating token...');
    try {
      const tokenResponse = await client.oidc.validateToken(token);
      console.log('Token validation response:', JSON.stringify(tokenResponse, null, 2));
      
      if (!tokenResponse?.user) {
        console.error('Token validation failed - no user in response');
        const redirectUrl = new URL('/', request.url);
        redirectUrl.searchParams.set('error', 'token_validation_failed');
        console.log('Redirecting to:', redirectUrl.toString());
        return NextResponse.redirect(redirectUrl);
      }

      // Create user info object
      const userInfo = {
        name: tokenResponse.user.name || tokenResponse.user.email,
        email: tokenResponse.user.email,
        picture: `https://ui-avatars.com/api/?name=${encodeURIComponent(tokenResponse.user.name || tokenResponse.user.email)}&background=random`
      };

      console.log('Setting user info cookie...');
      // Store user info in a cookie
      const redirectUrl = new URL('/', request.url);
      console.log('Redirecting to:', redirectUrl.toString());
      const response = NextResponse.redirect(redirectUrl);
      
      response.cookies.set('userInfo', JSON.stringify(userInfo), {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7 // 1 week
      });

      console.log('Cookie set successfully, returning response');
      return response;
    } catch (tokenError) {
      console.error('Token validation error:', tokenError);
      if (tokenError instanceof Error) {
        console.error('Token validation error details:', {
          message: tokenError.message,
          stack: tokenError.stack,
          name: tokenError.name
        });
      }
      const redirectUrl = new URL('/', request.url);
      redirectUrl.searchParams.set('error', 'token_validation_error');
      console.log('Redirecting to:', redirectUrl.toString());
      return NextResponse.redirect(redirectUrl);
    }
  } catch (error) {
    console.error('Callback error:', error);
    if (error instanceof Error) {
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
    }
    const redirectUrl = new URL('/', request.url);
    redirectUrl.searchParams.set('error', 'authentication_failed');
    console.log('Redirecting to:', redirectUrl.toString());
    return NextResponse.redirect(redirectUrl);
  }
} 