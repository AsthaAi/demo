declare module "@paypal/checkout-server-sdk" {
  export namespace core {
    class SandboxEnvironment {
      constructor(clientId: string, clientSecret: string);
    }

    class LiveEnvironment {
      constructor(clientId: string, clientSecret: string);
    }

    class PayPalHttpClient {
      constructor(environment: SandboxEnvironment | LiveEnvironment);
      execute<T>(request: any): Promise<{ result: T }>;
    }
  }

  export namespace orders {
    class OrdersCreateRequest {
      prefer(preference: string): void;
      requestBody(body: any): void;
    }

    class OrdersCaptureRequest {
      constructor(orderId: string);
      prefer(preference: string): void;
    }

    class OrdersGetRequest {
      constructor(orderId: string);
    }

    interface OrderResponse {
      id: string;
      status: string;
      links: Array<{
        href: string;
        rel: string;
        method: string;
      }>;
      purchase_units: Array<{
        payments?: {
          captures?: Array<{
            id: string;
            status: string;
            amount: {
              currency_code: string;
              value: string;
            };
          }>;
        };
      }>;
    }
  }

  export namespace subscriptions {
    class PlansCreateRequest {
      requestBody(body: any): void;
    }

    class SubscriptionsCreateRequest {
      requestBody(body: any): void;
    }

    class SubscriptionsCancelRequest {
      constructor(subscriptionId: string);
      requestBody(body: any): void;
    }

    class SubscriptionsGetRequest {
      constructor(subscriptionId: string);
    }

    interface PlanResponse {
      id: string;
      status: string;
      name: string;
      description: string;
    }

    interface SubscriptionResponse {
      id: string;
      status: string;
      links: Array<{
        href: string;
        rel: string;
        method: string;
      }>;
    }
  }

  export namespace payments {
    class CapturesRefundRequest {
      constructor(captureId: string);
      requestBody(body: any): void;
    }

    interface RefundResponse {
      id: string;
      status: string;
      amount: {
        currency_code: string;
        value: string;
      };
    }
  }

  export namespace payouts {
    class PayoutsPostRequest {
      requestBody(body: any): void;
    }

    interface PayoutResponse {
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
  }

  const core: typeof core;
  const orders: typeof orders;
  const subscriptions: typeof subscriptions;
  const payments: typeof payments;
  const payouts: typeof payouts;

  export { core, orders, payments, payouts, subscriptions };
}
