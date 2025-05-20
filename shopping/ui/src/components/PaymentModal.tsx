import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button, Modal, Spinner, TextInput } from 'flowbite-react';
import Promotions from './Promotions';
import { ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

interface Product {
  name: string;
  price: string;
  rating: string;
  brand?: string;
  description?: string;
  material?: string;
  capacity?: string;
  original_price?: string;
  applied_promotion?: {
    name: string;
    discount_percentage: number;
    minimum_purchase: number;
    valid_until: string;
  };
}

interface PaymentModalProps {
  show: boolean;
  onClose: () => void;
  product: Product;
  onOrderComplete: (orderData: any) => void;
}

export default function PaymentModal({ show, onClose, product, onOrderComplete }: PaymentModalProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product>(product);
  const [emailConfirmed, setEmailConfirmed] = useState(false);

  useEffect(() => {
    if (show) {
      setEmail('');
      setError(null);
      setEmailConfirmed(false);
      setSelectedProduct(product);
    }
  }, [show, product]);

  const isValidEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleEmailBlur = () => {
    if (isValidEmail(email)) {
      setEmailConfirmed(true);
    }
  };

  const handleProcessOrder = async () => {
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://localhost:8000/api/process-order', {
        product_details: selectedProduct,
        customer_email: email
      });

      if (response.data.success) {
        onOrderComplete(response.data);
      } else {
        setError(response.data.error || 'Failed to process order');
      }
    } catch (err) {
      setError('Error processing order');
      console.error('Error processing order:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePromotionSelected = (updatedProduct: Product) => {
    setSelectedProduct(updatedProduct);
  };

  return (
    <Modal show={show} onClose={onClose} size="xl">
      <Modal.Header>Complete Your Purchase</Modal.Header>
      <Modal.Body>
        <div className="space-y-6 text-black/60">
          {/* Order Summary */}
          <div className="border-b pb-4">
            <h3 className="text-lg font-semibold mb-2">Order Summary</h3>
            <div className="space-y-2">
              <p className="text-gray-700">{selectedProduct.name}</p>
              <div className="flex justify-between">
                <span className="text-gray-600">Price:</span>
                <span className="font-medium">
                  {selectedProduct.original_price ? (
                    <>
                      <span className="line-through text-gray-500 mr-2">
                        ${selectedProduct.original_price}
                      </span>
                      ${selectedProduct.price}
                    </>
                  ) : (
                    `$${selectedProduct.price}`
                  )}
                </span>
              </div>
              {selectedProduct.applied_promotion && (
                <div className="text-green-600 text-sm">
                  Applied promotion: {selectedProduct.applied_promotion.name}
                </div>
              )}
            </div>
          </div>

          {/* Email Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <TextInput
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setEmailConfirmed(false);
              }}
              onBlur={handleEmailBlur}
              placeholder="Enter your email"
              required
            />
          </div>

          {/* Promotions */}
          {emailConfirmed && (
            <div className="border-t pt-4">
              <Promotions
                productDetails={selectedProduct}
                customerEmail={email}
                onPromotionSelected={handlePromotionSelected}
              />
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="text-red-600 bg-red-50 p-3 rounded-lg flex items-start">
              <ExclamationCircleIcon className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
              <div className="whitespace-pre-line">{error}</div>
            </div>
          )}

          {/* Success Message */}
          {/* {selectedProduct.applied_promotion && (
            <div className="text-green-600 bg-green-50 p-3 rounded-lg flex items-start">
              <CheckCircleIcon className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                Applied promotion: {selectedProduct.applied_promotion.name}
                <div className="text-sm text-green-700">
                  You save: {(() => {
                    const basePrice = selectedProduct.original_price
                      ? parseFloat(selectedProduct.original_price)
                      : parseFloat(selectedProduct.price);
                    return `$${(basePrice * (selectedProduct.applied_promotion.discount_percentage / 100)).toFixed(2)}`;
                  })()}
                </div>
              </div>
            </div>
          )} */}
        </div>
      </Modal.Body>
      <Modal.Footer>
        <div className="flex justify-between w-full">
          <Button color="gray" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleProcessOrder}
            disabled={loading || !email}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
          >
            {loading ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Processing...
              </>
            ) : (
              'Proceed to Payment'
            )}
          </Button>
        </div>
      </Modal.Footer>
    </Modal>
  );
} 