'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Card, Modal, TextInput, Button, Alert } from 'flowbite-react';
import { ShoppingBagIcon, SparklesIcon, PaperAirplaneIcon, MagnifyingGlassIcon, ArrowPathIcon, TagIcon } from '@heroicons/react/24/outline';
import ChatMessage from '../components/ChatMessage';
import LoadingSkeleton from '../components/LoadingSkeleton';
import axios from 'axios';
import SearchForm from '../components/SearchForm';
import SearchResults from '../components/SearchResults';
import Promotions from '../components/Promotions';
import PaymentModal from '../components/PaymentModal';
import Link from 'next/link';

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
  comparisonResults?: ComparisonResult;
  products?: Product[];
  campaign?: Promotion;
  historyResult?: any;
  supportResult?: any;
}

interface PromotionSummary {
  originalPrice: number;
  discountPercentage: number;
  discountAmount: number;
  finalPrice: number;
  promotionName: string;
}

interface ComparisonResult {
  products: Product[];
  best_deal: Product | null;
  price_range: {
    lowest: number;
    highest: number;
  };
}

interface SearchCriteria {
  query: string;
  maxPrice: number;
  minRating: number;
}

type ActionStep =
  | 'menu'
  | 'search_product'
  | 'search_max_price'
  | 'search_min_rating'
  | 'searching'
  | 'show_results'
  | 'history_email'
  | 'history_result'
  | 'promotions_list'
  | 'support_menu'
  | 'support_refund_tid'
  | 'support_refund_reason'
  | 'support_refund_amount'
  | 'support_faq_question'
  | 'support_ticket_cid'
  | 'support_ticket_type'
  | 'support_ticket_priority'
  | 'support_ticket_desc'
  | 'support_result'
  | 'exit';

const SUPPORT_OPTIONS = [
  { key: 'refund', label: 'Request Refund' },
  { key: 'faq', label: 'FAQ Help' },
  { key: 'ticket', label: 'Create Support Ticket' },
  { key: 'back', label: 'Back to Main Menu' },
];

const MENU_OPTIONS = [
  { key: 'search', label: 'Research Agent: Search and buy products' },
  { key: 'history', label: 'History Agent: View your shopping history and personalized discounts' },
  { key: 'promotions', label: 'Promotions Agent: View active promotions' },
  { key: 'support', label: 'Customer Support Agent' },
  { key: 'fake_agent', label: 'Malicious Agent' },
  { key: 'market_agent', label: 'Agent with Unauthorized Policy' },
  { key: 'exit', label: 'Exit' },
];

function calculatePromotionSummary(product: Product, promotion: Promotion): PromotionSummary | null {
  if (!promotion || !product) return null;
  const originalPrice = typeof product.price === 'string' 
    ? parseFloat(product.price.replace('$', ''))
    : product.price;
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [step, setStep] = useState<ActionStep>('menu');
  const [pendingAction, setPendingAction] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [maxPrice, setMaxPrice] = useState<number | null>(null);
  const [minRating, setMinRating] = useState<number | null>(null);
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
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [historyEmail, setHistoryEmail] = useState('');
  const [supportStep, setSupportStep] = useState<string>('');
  const [refundDetails, setRefundDetails] = useState({ tid: '', reason: '', amount: '' });
  const [faqQuestion, setFaqQuestion] = useState('');
  const [ticketDetails, setTicketDetails] = useState({ cid: '', type: '', priority: '', desc: '' });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          type: 'assistant',
          content: `Welcome to ShopperAI!`
          // \nAvailable actions:\n`
          // ${MENU_OPTIONS.map((opt, i) => `${i + 1}. ${opt.label}`).join('\n')}`
        }
      ]);
    }
  }, []);

  const handleMenuSelect = (optionKey: string) => {
    setPendingAction(optionKey);
    if (optionKey === 'search') {
      setStep('search_product');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'What would you like to search for?' }
      ]);
    } else if (optionKey === 'history') {
      setStep('history_email');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Please enter your email address to view your shopping history and personalized discounts.' }
      ]);
    } else if (optionKey === 'promotions') {
      setStep('promotions_list');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Fetching active promotions...' }
      ]);
      fetchPromotions();
    } else if (optionKey === 'support') {
      setStep('support_menu');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Customer Support Options:\n' + SUPPORT_OPTIONS.map((opt, i) => `${i + 1}. ${opt.label}`).join('\n') }
      ]);
    } else if (optionKey === 'fake_agent') {
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Malicious Agent communication...' }
      ]);
      testAgent('fake');
    } else if (optionKey === 'market_agent') {
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Agent with Unauthorized Policy communication...' }
      ]);
      testAgent('market');
    } else if (optionKey === 'exit') {
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Thank you for using ShopperAI!' }
      ]);
      setStep('exit');
    }
  };

  const fetchPromotions = async () => {
    try {
      // Use the same campaign_data as in main.py CLI option 3
      const campaign_data = {
        name: 'Summer Sale',
        description: 'Special discounts on summer items',
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        discount_type: 'percentage',
        discount_value: 15,
        conditions: {
          minimum_purchase: 100,
          categories: ['summer', 'outdoor']
        }
      };
      const response = await axios.post('http://localhost:8000/api/create-promotion-campaign', campaign_data);
      if (response.data && response.data.success && response.data.campaign) {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', campaign: response.data.campaign, content: '' }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'No active promotions at this time.' }
        ]);
      }
    } catch {
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Error fetching promotions.' }
      ]);
    }
    setStep('menu');
  };

  const testAgent = async (agentType: 'fake' | 'market') => {
    setIsLoading(true);
    try {
      const response = await axios.post(`http://localhost:8000/api/test-${agentType}-agent`);
      if (response.data.success) {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: `${agentType === 'fake' ? 'Malicious' : 'Unauthorized Policy'} Agent: ${agentType === 'fake' ? JSON.stringify(response.data.result, null, 2) : "This agent does not have access to the PayPal agent due to a failed trust domain verification—either because of misconfiguration or an untrusted domain. If you believe this is an error, please contact our support team and create a ticket; we’ll resolve it as soon as possible."}` }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: `Error testing ${agentType} agent: ${response.data.error}` }
        ]);
      }
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: `Error testing ${agentType} agent: ${error instanceof Error ? error.message : 'Unknown error'}` }
      ]);
    } finally {
      setIsLoading(false);
      setStep('menu');
    }
  };

  const handleStepInput = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages(prev => [...prev, { type: 'user', content: input.trim() }]);
    const value = input.trim();
    setInput('');

    if (step === 'search_product') {
      setSearchQuery(value);
      setStep('search_max_price');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Maximum price (in USD):' }
      ]);
    } else if (step === 'search_max_price') {
      const price = parseFloat(value);
      if (isNaN(price) || price <= 0) {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Please enter a valid number for the maximum price.' }
        ]);
        return;
      }
      setMaxPrice(price);
      setStep('search_min_rating');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Minimum rating (0-5):' }
      ]);
    } else if (step === 'search_min_rating') {
      const rating = parseFloat(value);
      if (isNaN(rating) || rating < 0 || rating > 5) {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Please enter a valid rating between 0 and 5.' }
        ]);
        return;
      }
      setMinRating(rating);
      setStep('searching');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Searching for products...' }
      ]);
      setIsLoading(true);
      try {
        const response = await axios.post('http://localhost:8000/api/search', {
          query: searchQuery,
          max_price: maxPrice ?? 1000,
          min_rating: rating
        });
        setIsLoading(false);
        if (response.data.success) {
          const { best_match, products } = response.data;
          if (best_match) {
            setMessages(prev => [
              ...prev,
              {
                type: 'assistant',
                content: `I found a great match for "${searchQuery}":`,
                product: best_match
              }
            ]);
          }
          if (products && products.length > 0) {
            const otherProducts = best_match ? products.filter((p: Product) => p.name !== best_match.name) : products;
            if (otherProducts.length > 0) {
              setMessages(prev => [
                ...prev,
                {
                  type: 'assistant',
                  content: `Here are other matching products:`,
                  products: otherProducts
                }
              ]);
            }
          }
          setStep('menu');
        } else {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: 'No products found. Please try again.' }
          ]);
          setStep('menu');
        }
      } catch (error) {
        setIsLoading(false);
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Error searching for products. Please try again.' }
        ]);
        setStep('menu');
      }
    } else if (step === 'history_email') {
      setHistoryEmail(value);
      setStep('history_result');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Analyzing your shopping history...' }
      ]);
      try {
        const response = await axios.post('http://localhost:8000/api/history', { email: value });
        if (response.data.success) {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: '', historyResult: response.data.result }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: response.data.result }
          ]);
        }
      } catch {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Error fetching history.' }
        ]);
      }
      setStep('menu');
    } else if (step === 'support_menu') {
      const idx = parseInt(value) - 1;
      const opt = SUPPORT_OPTIONS[idx]?.key;
      if (opt === 'refund') {
        setSupportStep('refund');
        setStep('support_refund_tid');
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Enter transaction ID:' }
        ]);
      } else if (opt === 'faq') {
        setSupportStep('faq');
        setStep('support_faq_question');
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'What is your question?' }
        ]);
      } else if (opt === 'ticket') {
        setSupportStep('ticket');
        setStep('support_ticket_cid');
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Enter your customer ID:' }
        ]);
      } else {
        setStep('menu');
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: `Welcome to ShopperAI!\nAvailable actions:\n${MENU_OPTIONS.map((opt, i) => `${i + 1}. ${opt.label}`).join('\n')}` }
        ]);
      }
    } else if (step === 'support_refund_tid') {
      setRefundDetails(prev => ({ ...prev, tid: value }));
      setStep('support_refund_reason');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Enter refund reason:' }
      ]);
    } else if (step === 'support_refund_reason') {
      setRefundDetails(prev => ({ ...prev, reason: value }));
      setStep('support_refund_amount');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Enter refund amount:' }
      ]);
    } else if (step === 'support_refund_amount') {
      setRefundDetails(prev => ({ ...prev, amount: value }));
      setStep('support_result');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Processing refund request...' }
      ]);
      // Call refund API
      try {
        const response = await axios.post('http://localhost:8000/api/refund', {
          transaction_id: refundDetails.tid,
          reason: refundDetails.reason,
          amount: parseFloat(value)
        });
        if (response.data.success) {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: 'Refund request submitted.', supportResult: response.data.result }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: response.data.result }
          ]);
        }
      } catch {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Error submitting refund request.' }
        ]);
      }
      setStep('menu');
    } else if (step === 'support_faq_question') {
      setFaqQuestion(value);
      setStep('support_result');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Fetching FAQ answer...' }
      ]);
      // Call FAQ API
      try {
        const response = await axios.post('http://localhost:8000/api/faq', {
          question: value
        });
        if (response.data.success) {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: 'FAQ Answer:', supportResult: response.data.result }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: response.data.result }
          ]);
        }
      } catch {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Error fetching FAQ answer.' }
        ]);
      }
      setStep('menu');
    } else if (step === 'support_ticket_cid') {
      setTicketDetails(prev => ({ ...prev, cid: value }));
      setStep('support_ticket_type');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Enter issue type (Technical/Billing/General):' }
      ]);
    } else if (step === 'support_ticket_type') {
      setTicketDetails(prev => ({ ...prev, type: value }));
      setStep('support_ticket_priority');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Enter priority (Low/Medium/High):' }
      ]);
    } else if (step === 'support_ticket_priority') {
      setTicketDetails(prev => ({ ...prev, priority: value }));
      setStep('support_ticket_desc');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Enter issue description:' }
      ]);
    } else if (step === 'support_ticket_desc') {
      setTicketDetails(prev => ({ ...prev, desc: value }));
      setStep('support_result');
      setMessages(prev => [
        ...prev,
        { type: 'assistant', content: 'Submitting support ticket...' }
      ]);
      // Call support ticket API
      try {
        const response = await axios.post('http://localhost:8000/api/support-ticket', {
          customer_id: ticketDetails.cid,
          issue_type: ticketDetails.type,
          priority: ticketDetails.priority,
          description: value
        });
        if (response.data.success) {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: 'Support ticket created.', supportResult: response.data.result }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            { type: 'assistant', content: response.data.result }
          ]);
        }
      } catch {
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: 'Error submitting support ticket.' }
        ]);
      }
      setStep('menu');
    }
  };

  const handleProcessOrder = async () => {
    if (!selectedProduct || !customerEmail) return;
    setIsProcessingPayment(true);
    try {
      // Process the order
      const response = await axios.post('http://localhost:8000/api/process-order', {
        product_details: selectedProduct,
        customer_email: customerEmail,
      });
      
      if (!response.data.success) {
        throw new Error(response.data.error || 'Failed to process order');
      }
      
      // Store order data and approval URL
      setOrderId(response.data.order_data.id);
      setApprovalUrl(response.data.approval_url);
      setPromotionStep('ready');

      // If a promotion was applied, update the product details
      if (response.data.promotion_applied) {
        const updatedProduct = {
          ...selectedProduct,
          original_price: response.data.original_price,
          price: response.data.final_price,
          applied_promotion: response.data.promotion_details
        };
        setSelectedProduct(updatedProduct);
      }
    } catch (error) {
      console.error('Error processing order:', error);
      alert('Failed to process order. Please try again.');
      setShowPaymentModal(false);
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const handleBuyNow = (product: Product) => {
    setSelectedProduct(product);
    setShowPaymentModal(true);
  };

  const handleOrderComplete = (orderData: any) => {
    if (orderData.success && orderData.approval_url) {
      // Redirect to PayPal approval URL
      window.location.href = orderData.approval_url;
    }
  };

  const handleComparePrices = async (products: Product[]) => {
    if (products.length < 2) {
      alert('Need at least 2 products to compare prices');
      return;
    }

    setIsComparing(true);
    try {
      const response = await axios.post('http://localhost:8000/api/compare-prices', {
        products: products
      });

      if (response.data.success) {
        setComparisonResults(response.data.results);
        setMessages(prev => [
          ...prev,
          {
            type: 'assistant',
            content: 'Here are the price comparison results:',
            comparisonResults: response.data.results
          }
        ]);
      }
    } catch (error) {
      console.error('Error comparing prices:', error);
      alert('Failed to compare prices. Please try again.');
    } finally {
      setIsComparing(false);
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
              <span>Powered by <Link href="https://astha.ai" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">astha.ai</Link></span>
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
                products={message.products}
                onBuyNow={handleBuyNow}
                onComparePrices={handleComparePrices}
                comparisonResults={message.comparisonResults}
                campaign={message.campaign}
                historyResult={message.historyResult}
                supportResult={message.supportResult}
              />
            ))}
            {isLoading && <LoadingSkeleton type="message" />}
            <div ref={messagesEndRef} />
          </div>

          {/* Step-based Input */}
          {step === 'menu' && (
            <div className="flex flex-col gap-2">
              {MENU_OPTIONS.map((opt, i) => (
                <Button
                  key={opt.key}
                  onClick={() => handleMenuSelect(opt.key)}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                >
                  {i + 1}. {opt.label}
                </Button>
              ))}
            </div>
          )}
          {step !== 'exit' && (
            <form onSubmit={handleStepInput} className="flex gap-2 mt-2">
              <TextInput
                type={step === 'search_max_price' ? 'number' : 'text'}
                placeholder={
                  step === 'search_product'
                    ? 'e.g. iPhone 14'
                    : step === 'search_max_price'
                    ? 'Maximum price (USD)'
                    : step === 'search_min_rating'
                    ? 'Minimum rating (0-5)'
                    : step === 'history_email'
                    ? 'Enter your email address'
                    : step === 'support_refund_tid'
                    ? 'Transaction ID'
                    : step === 'support_refund_reason'
                    ? 'Refund reason'
                    : step === 'support_refund_amount'
                    ? 'Refund amount'
                    : step === 'support_faq_question'
                    ? 'Your question'
                    : step === 'support_ticket_cid'
                    ? 'Customer ID'
                    : step === 'support_ticket_type'
                    ? 'Issue type (Technical/Billing/General)'
                    : step === 'support_ticket_priority'
                    ? 'Priority (Low/Medium/High)'
                    : step === 'support_ticket_desc'
                    ? 'Issue description'
                    : 'Type your message...'
                }
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
          )}

          {/* Product Details */}
          {false && selectedProduct && (
            <div className="mt-8">
              <h2 className="text-2xl font-bold mb-4">Product Details</h2>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold">{selectedProduct?.name}</h3>
                <p className="text-gray-600 mt-2">{selectedProduct?.description}</p>
                <div className="mt-4">
                  <span className="text-2xl font-bold text-green-600">
                    {selectedProduct?.price}
                  </span>
                  {selectedProduct?.rating && (
                    <span className="ml-4 text-yellow-500">
                      ★ {selectedProduct?.rating}
                    </span>
                  )}
                </div>
                
                {/* Add Promotions component */}
                {selectedProduct && (
                  <div className="mt-6">
                    <Promotions
                      productDetails={selectedProduct as Product}
                      customerEmail={customerEmail}
                      onPromotionSelected={(updatedDetails: Product) => {
                        // Ensure price and rating are strings
                        const updatedProduct: Product = {
                          ...updatedDetails,
                          price: typeof updatedDetails.price === 'number' 
                            ? `$${(updatedDetails.price as number).toFixed(2)}`
                            : String(updatedDetails.price || '0'),
                          rating: typeof updatedDetails.rating === 'number'
                            ? String(updatedDetails.rating)
                            : String(updatedDetails.rating || '0')
                        };
                        setSelectedProduct(updatedProduct);
                      }}
                    />
                  </div>
                )}

                <button
                  onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                    e.preventDefault();
                    if (selectedProduct) {
                      handleBuyNow(selectedProduct);
                    }
                  }}
                  className="mt-6 w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
                >
                  Buy Now
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Payment Modal */}
      {selectedProduct && (
        <PaymentModal
          show={showPaymentModal}
          onClose={() => setShowPaymentModal(false)}
          product={selectedProduct}
          onOrderComplete={handleOrderComplete}
        />
      )}
    </div>
  );
}
