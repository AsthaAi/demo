import React, { useEffect, useState } from 'react';
import { Modal, Spinner } from 'flowbite-react';
import { CheckCircleIcon, XCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

interface PaymentStatusModalProps {
  show: boolean;
  onClose: () => void;
  orderId: string;
  transactionId: string;
  status: 'success' | 'cancel';
}

export default function PaymentStatusModal({ show, onClose, orderId, transactionId, status }: PaymentStatusModalProps) {
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handlePaymentCallback = async () => {
      try {
        const response = await axios.post('http://localhost:8000/api/capture-payment', {
          transaction_id: transactionId,
          order_id: orderId,
          status: status
        });

        setResult(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to process payment status');
        setLoading(false);
      }
    };

    if (show) {
      handlePaymentCallback();
    }
  }, [show, transactionId, status]);

  const getStatusContent = () => {
    if (loading) {
      return (
        <div className="flex flex-col items-center justify-center p-6">
          <Spinner size="xl" className="mb-4" />
          <p className="text-lg text-gray-600">Processing payment status...</p>
        </div>
      );
    }

    if (!orderId) {
      return (
        <div className="flex flex-col items-center justify-center p-6">
          <ExclamationCircleIcon className="w-16 h-16 text-red-500 mb-4" />
          <p className="text-lg text-red-600 mb-2">Error occurred</p>
          <p className="text-gray-600">Order ID not found</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center p-6">
          <ExclamationCircleIcon className="w-16 h-16 text-red-500 mb-4" />
          <p className="text-lg text-red-600 mb-2">Error</p>
          <p className="text-gray-600">{error}</p>
        </div>
      );
    }

    if (result?.status === 'completed') {
      return (
        <div className="flex flex-col items-center justify-center p-6">
          <CheckCircleIcon className="w-16 h-16 text-green-500 mb-4" />
          <p className="text-lg text-green-600 mb-2">Payment Successful!</p>
          <p className="text-gray-600">Your order has been confirmed.</p>
          <div className="mt-4 text-sm text-gray-500">
            <p>Transaction ID: {result.transaction_id}</p>
            {result.order_id && <p>Order ID: {result.order_id}</p>}
          </div>
        </div>
      );
    }

    if (result?.status === 'cancelled') {
      return (
        <div className="flex flex-col items-center justify-center p-6">
          <XCircleIcon className="w-16 h-16 text-yellow-500 mb-4" />
          <p className="text-lg text-yellow-600 mb-2">Payment Cancelled</p>
          <p className="text-gray-600">Your payment was cancelled.</p>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center justify-center p-6">
        <ExclamationCircleIcon className="w-16 h-16 text-red-500 mb-4" />
        <p className="text-lg text-red-600 mb-2">Payment Failed</p>
        <p className="text-gray-600">{result?.error || 'An error occurred during payment processing.'}</p>
      </div>
    );
  };

  return (
    <Modal show={show} onClose={onClose} size="md">
      <Modal.Header>
        {result?.status === 'completed' ? 'Payment Successful' :
         result?.status === 'cancelled' ? 'Payment Cancelled' :
         'Payment Status'}
      </Modal.Header>
      <Modal.Body>
        {getStatusContent()}
      </Modal.Body>
    </Modal>
  );
} 