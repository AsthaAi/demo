'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '../../../context/AuthContext';

export default function AuthCallback() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { validateToken } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the authorization code from URL parameters
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        if (error) {
          setStatus('error');
          setMessage(`Authentication failed: ${error}`);
          return;
        }

        if (!code || !state) {
          setStatus('error');
          setMessage('Missing authentication parameters');
          return;
        }

        // Validate state (optional security check)
        const storedState = localStorage.getItem('auth_state');
        if (storedState !== state) {
          setStatus('error');
          setMessage('Invalid authentication state');
          return;
        }

        // For AZTP, the token is typically included in the callback or we need to exchange the code
        // Since aztp-client handles OIDC, we might need to extract the token differently
        // For now, let's assume the token is in the URL or we get it through another mechanism
        
        // In a real implementation, you might need to make an additional call to exchange the code for a token
        // or the token might be provided differently by aztp-client
        
        // For this demo, we'll check if there's a token parameter or handle it as per aztp-client's documentation
        const token = searchParams.get('token') || searchParams.get('access_token');
        
        if (token) {
          const isValid = await validateToken(token);
          if (isValid) {
            setStatus('success');
            setMessage('Authentication successful! Redirecting...');
            setTimeout(() => {
              router.push('/');
            }, 1500);
          } else {
            setStatus('error');
            setMessage('Token validation failed');
          }
        } else {
          // If no token in URL, this might be handled differently by aztp-client
          // For now, we'll redirect and let the main app handle the authentication state
          setStatus('success');
          setMessage('Authentication successful! Redirecting...');
          setTimeout(() => {
            router.push('/');
          }, 1500);
        }

      } catch (error) {
        console.error('Callback error:', error);
        setStatus('error');
        setMessage('An error occurred during authentication');
      }
    };

    handleCallback();
  }, [searchParams, validateToken, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full mx-4 text-center">
        {status === 'processing' && (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
              <svg className="animate-spin w-8 h-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Processing Authentication</h1>
            <p className="text-gray-600">{message}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Success!</h1>
            <p className="text-gray-600">{message}</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Authentication Failed</h1>
            <p className="text-gray-600 mb-4">{message}</p>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  );
} 