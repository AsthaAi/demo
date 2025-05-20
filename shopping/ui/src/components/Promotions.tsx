import React, { useState, useEffect } from 'react';
import { Card, Button, Spinner } from 'flowbite-react';
import { 
  TagIcon, 
  ExclamationCircleIcon, 
  CheckCircleIcon,
  CurrencyDollarIcon,
  ClockIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';

interface Promotion {
  id: string;
  name: string;
  discount_percentage: number;
  minimum_purchase: number;
  valid_until: string;
}

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

interface PromotionsProps {
  productDetails: Product;
  customerEmail: string;
  onPromotionSelected: (updatedDetails: Product) => void;
}

export default function Promotions({ productDetails, customerEmail, onPromotionSelected }: PromotionsProps) {
  const [loading, setLoading] = useState(false);
  const [applyingPromotion, setApplyingPromotion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [availablePromotions, setAvailablePromotions] = useState<Promotion[]>([]);
  const [selectedPromotion, setSelectedPromotion] = useState<Promotion | null>(null);

  useEffect(() => {
    if (productDetails && customerEmail) {
      if (selectedPromotion) {
        // Always use the original price for calculations
        const basePrice = productDetails.original_price
          ? parseFloat(productDetails.original_price)
          : parseFloat(productDetails.price);

        const discountAmount = basePrice * (selectedPromotion.discount_percentage / 100);
        const discountedPrice = basePrice - discountAmount;

        // Create updated product details
        const updatedDetails: Product = {
          ...productDetails,
          original_price: productDetails.original_price || productDetails.price,
          price: discountedPrice.toFixed(2),
          applied_promotion: {
            name: selectedPromotion.name,
            discount_percentage: selectedPromotion.discount_percentage,
            minimum_purchase: selectedPromotion.minimum_purchase,
            valid_until: selectedPromotion.valid_until
          }
        };

        onPromotionSelected(updatedDetails);
      } else {
        fetchPromotions();
      }
    }
  }, [productDetails, customerEmail, selectedPromotion, onPromotionSelected]);

  const handlePromotionSelect = async (promotion: Promotion) => {
    setLoading(true);
    setApplyingPromotion(promotion.id);
    setError(null);
    try {
      setSelectedPromotion(promotion);
    } catch (err) {
      setError('Error applying promotion');
      console.error('Error applying promotion:', err);
    } finally {
      setLoading(false);
      setApplyingPromotion(null);
    }
  };

  const fetchPromotions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/api/get-promotions', {
        product_details: productDetails,
        customer_email: customerEmail
      });

      if (response.data.success) {
        setAvailablePromotions(response.data.promotions);
      } else {
        setError(response.data.error || 'Failed to fetch promotions');
      }
    } catch (err) {
      setError('Error fetching promotions');
      console.error('Error fetching promotions:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !applyingPromotion) {
    return (
      <div className="flex items-center justify-center p-4">
        <Spinner size="sm" />
        <span className="ml-2 text-gray-600">Loading promotions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600 bg-red-50 rounded-lg flex items-start">
        <ExclamationCircleIcon className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
        <div className="whitespace-pre-line">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
        <TagIcon className="w-5 h-5 mr-2 text-blue-600" />
        Available Promotions
      </h3>
      
      {availablePromotions.length > 0 ? (
        <div className="space-y-3">
          {availablePromotions.map((promotion) => {
            const basePrice = productDetails.original_price
              ? parseFloat(productDetails.original_price)
              : parseFloat(productDetails.price);

            const discountAmount = basePrice * (promotion.discount_percentage / 100);
            const discountedPrice = basePrice - discountAmount;
            const isEligible = basePrice >= promotion.minimum_purchase;

            return (
              <Card key={promotion.id} className={`relative ${!isEligible ? 'opacity-50' : ''}`}>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">{promotion.name}</h4>
                    <div className="space-y-1 mt-2">
                      <p className="text-green-600 font-medium flex items-center">
                        <CurrencyDollarIcon className="w-4 h-4 mr-1" />
                        {promotion.discount_percentage}% off
                      </p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <CurrencyDollarIcon className="w-4 h-4 mr-1" />
                        Minimum purchase: ${promotion.minimum_purchase}
                      </p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <ClockIcon className="w-4 h-4 mr-1" />
                        Valid until: {new Date(promotion.valid_until).toLocaleDateString()}
                      </p>
                      {isEligible && (
                        <p className="text-sm text-green-600 mt-2 flex items-center">
                          <CurrencyDollarIcon className="w-4 h-4 mr-1" />
                          You save: ${discountAmount.toFixed(2)} (New price: ${discountedPrice.toFixed(2)})
                        </p>
                      )}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handlePromotionSelect(promotion)}
                    disabled={loading || selectedPromotion?.id === promotion.id || !isEligible}
                    className={`${
                      selectedPromotion?.id === promotion.id
                        ? 'bg-green-500 hover:bg-green-600'
                        : 'bg-blue-500 hover:bg-blue-600'
                    } min-w-[100px]`}
                  >
                    {applyingPromotion === promotion.id ? (
                      <>
                        <Spinner size="sm" className="mr-2" />
                        Applying...
                      </>
                    ) : selectedPromotion?.id === promotion.id ? (
                      <>
                        <CheckCircleIcon className="w-4 h-4 mr-1" />
                        Applied
                      </>
                    ) : (
                      'Apply'
                    )}
                  </Button>
                </div>
                {!isEligible && (
                  <p className="text-sm text-red-700 mt-2 flex items-center bg-red-100 rounded-lg p-2">
                    <InformationCircleIcon className="w-4 h-4 mr-1" />
                    Minimum purchase requirement not met.
                  </p>
                )}
              </Card>
            );
          })}
        </div>
      ) : (
        <p className="text-gray-600 flex items-center">
          <InformationCircleIcon className="w-5 h-5 mr-2" />
          No promotions available at this time.
        </p>
      )}

      {selectedPromotion && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-start">
          <CheckCircleIcon className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5 text-green-600" />
          <div>
            <h4 className="text-green-800 font-semibold">Applied Promotion</h4>
            <p className="text-green-700">{selectedPromotion.name}</p>
            <p className="text-green-700 flex items-center">
              <CurrencyDollarIcon className="w-4 h-4 mr-1" />
              You save: {(() => {
                const basePrice = productDetails.original_price
                  ? parseFloat(productDetails.original_price)
                  : parseFloat(productDetails.price);
                return `$${(basePrice * (selectedPromotion.discount_percentage / 100)).toFixed(2)}`;
              })()}
            </p>
          </div>
        </div>
      )}
    </div>
  );
} 