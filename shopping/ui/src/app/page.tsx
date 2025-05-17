'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, Modal, TextInput, Button } from 'flowbite-react';
import { ShoppingBagIcon, SparklesIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import ChatMessage from '@/components/ChatMessage';
import axios from 'axios';

interface Product {
  name: string;
  price: string;
  rating: string;
  brand?: string;
  description?: string;
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  product?: Product;
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
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [customerEmail, setCustomerEmail] = useState('');
  const [approvalUrl, setApprovalUrl] = useState<string | null>(null);
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

  const handleProceedToPayment = (product: Product) => {
    setSelectedProduct(product);
    setShowPaymentModal(true);
  };

  const handlePayment = async () => {
    if (!selectedProduct || !customerEmail) return;

    setIsLoading(true);
    setApprovalUrl(null);
    try {
      const response = await axios.post('http://localhost:8000/api/process-order', {
        product_details: {
          name: selectedProduct.name,
          price: selectedProduct.price,
          quantity: 1,
          description: selectedProduct.description || ''
        },
        customer_email: customerEmail
      });

      if (response.data.success) {
        const { approval_url } = response.data.result;
        if (approval_url) {
          setApprovalUrl(approval_url);
        }
        setMessages(prev => [
          ...prev,
          {
            type: 'assistant',
            content: 'A payment link is ready. Please click the button in the modal to complete your purchase.'
          }
        ]);
      }
    } catch (error) {
      console.error('Error processing payment:', error);
      setMessages(prev => [
        ...prev,
        {
          type: 'assistant',
          content: 'I apologize, but there was an error processing your payment. Please try again.'
        }
      ]);
    } finally {
      setIsLoading(false);
    }
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
                onProceedToPayment={handleProceedToPayment}
              />
            ))}
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
              <PaperAirplaneIcon className="w-5 h-5" />
            </Button>
          </form>
        </div>
      </main>

      {/* Payment Modal */}
      <Modal show={showPaymentModal} onClose={() => { setShowPaymentModal(false); setApprovalUrl(null); }}>
        <Modal.Header className="text-gray-900">Complete Your Purchase</Modal.Header>
        <Modal.Body>
          <div className="space-y-4">
            {approvalUrl ? (
              <div className="flex flex-col items-center space-y-4">
                <p className="text-green-700 font-semibold">
                  Your order is ready! Click below to proceed to PayPal:
                </p>
                <Button
                  onClick={() => window.open(approvalUrl, '_blank')}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold shadow hover:from-blue-700 hover:to-purple-700 transition"
                >
                  Open PayPal Checkout
                </Button>
                <div className="text-center">
                  <span className="block text-gray-500 text-xs mt-2">Or copy the link below:</span>
                  <a
                    href={approvalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="break-all text-blue-700 underline text-xs"
                  >
                    {approvalUrl}
                  </a>
                </div>
              </div>
            ) : (
              <>
                <p className="text-gray-700">Please enter your email to proceed with payment:</p>
                <TextInput
                  type="email"
                  placeholder="Enter your email"
                  value={customerEmail}
                  onChange={(e) => setCustomerEmail(e.target.value)}
                  required
                  className="bg-white text-gray-900 placeholder-gray-500"
                  disabled={isLoading}
                />
                {selectedProduct && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900">Order Summary</h3>
                    <div className="mt-2 space-y-2 text-sm text-gray-700">
                      <p><span className="font-medium">Product:</span> {selectedProduct.name}</p>
                      <p><span className="font-medium">Price:</span> {selectedProduct.price}</p>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </Modal.Body>
        <Modal.Footer>
          {approvalUrl ? (
            <Button color="gray" onClick={() => { setShowPaymentModal(false); setApprovalUrl(null); setCustomerEmail(''); setSelectedProduct(null); }}>
              Close
            </Button>
          ) : (
            <>
              <Button
                onClick={handlePayment}
                disabled={isLoading || !customerEmail}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Processing...</span>
                  </div>
                ) : (
                  'Proceed to Payment'
                )}
              </Button>
              <Button color="gray" onClick={() => setShowPaymentModal(false)}>
                Cancel
              </Button>
            </>
          )}
        </Modal.Footer>
      </Modal>
    </div>
  );
}
