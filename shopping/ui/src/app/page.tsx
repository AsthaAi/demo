'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, Modal, TextInput, Button, Alert } from 'flowbite-react';
import { ShoppingBagIcon, SparklesIcon, PaperAirplaneIcon, MagnifyingGlassIcon, ArrowPathIcon, TagIcon } from '@heroicons/react/24/outline';
import ChatMessage from '@/components/ChatMessage';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import axios from 'axios';
import SearchForm from '@/components/SearchForm';
import SearchResults from '@/components/SearchResults';

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

interface Promotion {
  id: string;
  name: string;
  discount_percentage: number;
  minimum_purchase: number;
  valid_until: string;
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  product?: Product;
}

interface PromotionSummary {
  originalPrice: number;
  discountPercentage: number;
  discountAmount: number;
  finalPrice: number;
  promotionName: string;
}

function calculatePromotionSummary(product: Product, promotion: Promotion): PromotionSummary | null {
  if (!promotion || !product) return null;
  const originalPrice = parseFloat(product.price.replace('$', ''));
  const discountAmount = originalPrice * (promotion.discount_percentage / 100);
  const finalPrice = originalPrice - discountAmount;
  return {
    originalPrice,
    discountPercentage: promotion.discount_percentage,
    discountAmount,
    finalPrice,
    promotionName: promotion.name,
  };
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      type: 'assistant',
      content: 'Welcome to ShopperAI! I can help you find and compare products. What would you like to search for?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [customerEmail, setCustomerEmail] = useState('');
  const [paymentUrl, setPaymentUrl] = useState('');
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [promotionStep, setPromotionStep] = useState<'none' | 'select' | 'capturing' | 'ready'>('none');
  const [selectedPromotion, setSelectedPromotion] = useState<Promotion | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [approvalUrl, setApprovalUrl] = useState<string>('');
  const [promotionSummary, setPromotionSummary] = useState<PromotionSummary | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Extract price and rating from user message if present
      const priceMatch = userMessage.match(/\$(\d+)/);
      const ratingMatch = userMessage.match(/(\d+(?:\.\d+)?)\s*stars?/i);
      
      const maxPrice = priceMatch ? parseFloat(priceMatch[1]) : 1000;
      const minRating = ratingMatch ? parseFloat(ratingMatch[1]) : 0;

      const response = await axios.post('http://localhost:8000/api/search', {
        query: userMessage,
        max_price: maxPrice,
        min_rating: minRating
      });

      if (response.data.success) {
        const { best_match, products } = response.data;
        
        // Add assistant message with best match
        if (best_match) {
          setMessages(prev => [
            ...prev,
            {
              type: 'assistant',
              content: `I found a great match for "${userMessage}":`,
              product: best_match
            }
          ]);
        }

        // Add message about other products if available
        if (products && products.length > 0) {
          setMessages(prev => [
            ...prev,
            {
              type: 'assistant',
              content: `I found ${products.length} other products that match your criteria. Would you like to compare prices or proceed with the best match?`
            }
          ]);
        }
      }
    } catch (error) {
      console.error('Error searching products:', error);
      setMessages(prev => [
        ...prev,
        {
          type: 'assistant',
          content: 'I apologize, but I encountered an error while searching for products. Please try again.'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProcessOrder = async () => {
    if (!selectedProduct || !customerEmail) return;
    setIsProcessingPayment(true);
    setPromotionStep('none');
    try {
      // Process the order
      const response = await axios.post('http://localhost:8000/api/process-order', {
        product_details: selectedProduct,
        customer_email: customerEmail,
      });
      if (!response.data.success) throw new Error('Failed to process order');
      setOrderId(response.data.result.id);
      // Get available promotions
      const promoRes = await axios.post('http://localhost:8000/api/get-promotions', {
        product_details: selectedProduct,
        customer_email: customerEmail,
      });
      if (!promoRes.data.success) throw new Error('Failed to get promotions');
      setPromotions(promoRes.data.promotions);
      setPromotionStep('select');
    } catch (error) {
      alert('Failed to process order or get promotions.');
      setShowPaymentModal(false);
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const handlePromotionSelect = async (promotion: Promotion | null) => {
    setSelectedPromotion(promotion);
    // Calculate summary if promotion is selected
    if (promotion && selectedProduct) {
      const summary = calculatePromotionSummary(selectedProduct, promotion);
      setPromotionSummary(summary);
    } else {
      setPromotionSummary(null);
    }
    setPromotionStep('capturing');
    try {
      const response = await axios.post('http://localhost:8000/api/capture-payment', {
        order_id: orderId,
        promotion: promotion, // send full promotion object or null
      });
      if (!response.data.success) throw new Error('Failed to capture payment');
      setApprovalUrl(response.data.result.approval_url);
      setPromotionStep('ready');
    } catch (error) {
      alert('Failed to capture payment.');
      setShowPaymentModal(false);
    }
  };

  const handleBuyNow = (product: Product) => {
    setSelectedProduct(product);
    setShowPaymentModal(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <ShoppingBagIcon className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">ShopperAI</h1>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-700">
              <SparklesIcon className="h-5 w-5 text-yellow-400" />
              <span>Powered by AI</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 min-h-[600px] flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto mb-4 space-y-4">
            {messages.map((message, index) => (
              <ChatMessage
                key={index}
                type={message.type}
                content={message.content}
                product={message.product}
                onBuyNow={handleBuyNow}
              />
            ))}
            {isLoading && (
              <>
                <LoadingSkeleton type="message" />
                {/* <LoadingSkeleton type="product" /> */}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <TextInput
              type="text"
              placeholder="What would you like to search for? (e.g., 'Find me a laptop under $1000 with 4 stars')"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              className="flex-1 bg-white text-gray-900 placeholder-gray-500"
            />
            <Button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              {isLoading ? (
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
            </Button>
          </form>
        </div>
      </main>

      {/* Payment Modal */}
      <Modal show={showPaymentModal} onClose={() => { 
        setShowPaymentModal(false); 
        setPaymentUrl(''); 
        setCustomerEmail(''); 
        setSelectedProduct(null);
        setSelectedPromotion(null);
        setOrderId(null);
        setPromotionStep('none');
        setPromotionSummary(null);
      }}>
        <Modal.Header className="text-gray-900">Complete Your Purchase</Modal.Header>
        <Modal.Body>
          <div className="space-y-4">
            {selectedProduct && promotionStep === 'none' && (
              <div>
                <h3 className="text-xl font-semibold mb-4">Order Summary</h3>
                <div className="bg-gray-50 p-4 rounded-lg w-full mb-4">
                  <div className="space-y-2">
                    <p className="font-medium">Product: {selectedProduct.name}</p>
                    <p className="font-medium">Price: {selectedProduct.price}</p>
                    {selectedProduct.brand && (
                      <p className="text-sm text-gray-600">Brand: {selectedProduct.brand}</p>
                    )}
                  </div>
                </div>
                <div className="w-full">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <TextInput
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    required
                    className="w-full"
                  />
                </div>
              </div>
            )}
            {promotionStep === 'select' && (
              <div>
                <h3 className="text-xl font-semibold mb-4">Available Promotions</h3>
                <div className="space-y-4 mb-6">
                  {promotions.map((promotion, idx) => (
                    <div
                      key={promotion.id || idx}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${selectedPromotion?.id === promotion.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'}`}
                      onClick={() => handlePromotionSelect(promotion)}
                    >
                      <div className="font-medium">{promotion.name}</div>
                      <div className="text-sm text-gray-600">Discount: {promotion.discount_percentage}%</div>
                      <div className="text-sm text-gray-600">Minimum Purchase: ${promotion.minimum_purchase}</div>
                      <div className="text-sm text-gray-600">Valid Until: {promotion.valid_until}</div>
                    </div>
                  ))}
                  <button
                    className="w-full mt-2 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300"
                    onClick={() => handlePromotionSelect(null)}
                  >
                    Skip Promotions
                  </button>
                </div>
              </div>
            )}
            {promotionStep === 'capturing' && (
              <div className="text-center">
                <h3 className="text-xl font-semibold mb-4">Processing Payment</h3>
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Please wait while we process your payment...</p>
              </div>
            )}
            {promotionStep === 'ready' && (
              <div>
                <h3 className="text-xl font-semibold mb-4">Your Order is Ready!</h3>
                {/* Promotion summary */}
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  {promotionSummary ? (
                    <>
                      <div className="font-medium mb-2">Promotion Applied: {promotionSummary.promotionName}</div>
                      <div className="text-sm text-gray-700">Original Price: ${promotionSummary.originalPrice.toFixed(2)}</div>
                      <div className="text-sm text-gray-700">Discount: {promotionSummary.discountPercentage}% (-${promotionSummary.discountAmount.toFixed(2)})</div>
                      <div className="text-lg font-bold text-green-700 mt-2">Final Price: ${promotionSummary.finalPrice.toFixed(2)}</div>
                    </>
                  ) : (
                    <div className="text-sm text-gray-700">No promotion applied. Price: {selectedProduct?.price}</div>
                  )}
                </div>
                <p className="text-gray-600 mb-4">Click below to proceed to PayPal</p>
                {approvalUrl && (
                  <a
                    href={approvalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-blue-500 text-white text-center py-2 px-4 rounded-lg hover:bg-blue-600"
                  >
                    Proceed to PayPal
                  </a>
                )}
                <div className="mt-2 text-xs text-gray-500 break-all">{approvalUrl}</div>
                <div className="mt-4 text-gray-700">
                  <ol className="list-decimal ml-5">
                    <li>Open the above URL in your browser.</li>
                    <li>Log in with your PayPal sandbox buyer account.</li>
                    <li>Approve the payment to complete your order.</li>
                  </ol>
                </div>
              </div>
            )}
          </div>
        </Modal.Body>
        <Modal.Footer>
          {selectedProduct && promotionStep === 'none' && (
            <Button
              onClick={handleProcessOrder}
              disabled={!customerEmail}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              Proceed to Payment
            </Button>
          )}
          <Button 
            color="gray" 
            onClick={() => { 
              setShowPaymentModal(false); 
              setPaymentUrl(''); 
              setCustomerEmail(''); 
              setSelectedProduct(null);
              setSelectedPromotion(null);
              setOrderId(null);
              setPromotionStep('none');
              setPromotionSummary(null);
            }}
          >
            {approvalUrl ? 'Close' : 'Cancel'}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}
