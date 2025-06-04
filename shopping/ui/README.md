This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/learn/basics/create-nextjs-app).

## ShopperAI - AI-Powered Shopping Assistant

A modern shopping interface with secure authentication powered by AZTP and Google OAuth.

### Features

- 🔐 Secure authentication with Google OAuth via AZTP
- 🛍️ AI-powered product search and recommendations
- 💳 Integrated payment processing
- 📊 Shopping history and analytics
- 🎯 Personalized promotions
- 🤖 Multiple AI agents for different shopping tasks

### Authentication Setup

This application uses AZTP (AI Agent Transport Protocol) for secure authentication. You'll need to:

1. **Get AZTP API Key**: Obtain your AZTP API key from your AZTP dashboard
2. **Configure Environment**: Create a `.env.local` file in the root of the `ui` directory with:
   ```
   NEXT_PUBLIC_AZTP_API_KEY=your_actual_aztp_api_key_here
   ```
3. **AZTP Agent ID**: The app is configured to use the agent ID: `aztp://aiagentscommunity.ai/workload/production/node/research-agent`

### Getting Started

First, install the dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Authentication Flow

1. **Login**: Users click "Continue with Google" to initiate OAuth flow
2. **AZTP Integration**: The app uses aztp-client to handle secure authentication
3. **Token Validation**: Tokens are validated using AZTP's validation endpoint
4. **Protected Routes**: All shopping features require authentication
5. **Logout**: Users can securely logout, clearing all session data

### Project Structure

```
src/
├── app/
│   ├── auth/
│   │   └── callback/          # OAuth callback handler
│   ├── layout.tsx             # Root layout with AuthProvider
│   └── page.tsx              # Main page with auth routing
├── components/
│   ├── LoginButton.tsx        # Google OAuth login component
│   ├── Header.tsx            # App header with user info
│   └── [other components]     # Shopping interface components
└── context/
    └── AuthContext.tsx        # Authentication state management
```

### Environment Variables

Required environment variables:

- `NEXT_PUBLIC_AZTP_API_KEY`: Your AZTP API key for authentication

### Learn More

To learn more about the technologies used:

- [Next.js Documentation](https://nextjs.org/docs)
- [AZTP Documentation](https://aztp.ai/docs)
- [React Authentication Patterns](https://reactjs.org/docs/context.html)

### Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
