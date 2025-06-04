import { StarIcon, ShoppingCartIcon, ArrowsRightLeftIcon } from '@heroicons/react/24/solid';
import { Button } from 'flowbite-react';
import TypeIt from 'typeit-react';
import { UserAuth } from './UserAuth';
import React, { useState } from 'react';

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

interface ComparisonResult {
  products: Product[];
  best_deal: Product | null;
  price_range: {
    lowest: number;
    highest: number;
  };
}

interface HistoryResult {
  total_transactions?: number;
  date_range?: {
    first_transaction?: string;
    last_transaction?: string;
  };
  payment_history_source?: string;
  personalized_discount?: {
    discount_percentage: number;
    minimum_purchase: number;
    valid_from: string;
    valid_until: string;
  };
  user_id?: string;
  total_purchases?: number;
  total_spent?: number;
  average_purchase?: number;
  favorite_category?: string;
  category_distribution?: { [category: string]: number };
  analyzed_at?: string;
  [key: string]: any;
}

interface ChatMessageProps {
  type: 'user' | 'assistant' | 'login_prompt';
  content: string;
  product?: Product;
  products?: Product[];
  onBuyNow: (product: Product) => void;
  onComparePrices?: (products: Product[]) => void;
  comparisonResults?: ComparisonResult;
  campaign?: any;
  historyResult?: HistoryResult;
  supportResult?: any;
}

export default function ChatMessage({ 
  type, 
  content, 
  product,
  products,
  onBuyNow,
  onComparePrices,
  comparisonResults,
  campaign,
  historyResult,
  supportResult
}: ChatMessageProps) {
  const [showButtons, setShowButtons] = useState(false);
  if (type === 'assistant' && campaign) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white shadow-md border border-blue-200">
          <h3 className="text-lg font-bold text-blue-700 mb-2">{campaign.name}</h3>
          <p className="text-gray-700 mb-1">{campaign.description}</p>
          <div className="text-sm text-gray-600 mb-1">
            <span className="font-semibold">Discount:</span> {campaign.discount_value}
            {campaign.discount_type === 'percentage' ? '%' : ''}
          </div>
          <div className="text-sm text-gray-600 mb-1">
            <span className="font-semibold">Valid:</span> {new Date(campaign.start_date).toLocaleDateString()} - {new Date(campaign.end_date).toLocaleDateString()}
          </div>
          <div className="text-sm text-gray-600 mb-1">
            <span className="font-semibold">Minimum Purchase:</span> ${campaign.conditions?.minimum_purchase}
          </div>
          <div className="text-sm text-gray-600 mb-1">
            <span className="font-semibold">Categories:</span> {campaign.conditions?.categories?.join(', ')}
          </div>
          <div className="text-xs text-green-700 font-semibold mt-2">
            Status: {campaign.status}
          </div>
        </div>
      </div>
    );
  }
  if (type === 'assistant' && historyResult) {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white shadow-md border border-green-200">
          <h3 className="text-lg font-bold text-green-700 mb-2">Shopping History</h3>
          {historyResult.user_id && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">User:</span> {historyResult.user_id}
            </div>
          )}
          {historyResult.total_purchases !== undefined && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Total Purchases:</span> {historyResult.total_purchases}
            </div>
          )}
          {historyResult.total_spent !== undefined && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Total Spent:</span> ${historyResult.total_spent}
            </div>
          )}
          {historyResult.average_purchase !== undefined && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Average Purchase:</span> ${historyResult.average_purchase}
            </div>
          )}
          {historyResult.favorite_category && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Favorite Category:</span> {historyResult.favorite_category}
            </div>
          )}
          {historyResult.category_distribution && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Category Distribution:</span> {Object.entries(historyResult.category_distribution).map(([cat, count]) => `${cat}: ${count}`).join(', ')}
            </div>
          )}
          {historyResult.analyzed_at && (
            <div className="text-xs text-gray-500 mb-1">
              <span className="font-semibold">Analyzed At:</span> {new Date(historyResult.analyzed_at).toLocaleString()}
            </div>
          )}
          {historyResult.total_transactions !== undefined && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Total Transactions:</span> {historyResult.total_transactions}
            </div>
          )}
          {historyResult.date_range && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Date Range:</span> {historyResult.date_range.first_transaction} - {historyResult.date_range.last_transaction}
            </div>
          )}
          {historyResult.payment_history_source && (
            <div className="text-sm text-gray-700 mb-1">
              <span className="font-semibold">Source:</span> {historyResult.payment_history_source}
            </div>
          )}
          {historyResult.personalized_discount && (
            <div className="bg-green-50 p-3 rounded-lg mt-2">
              <div className="font-medium text-green-800 mb-1">Personalized Discount</div>
              <div className="text-sm text-green-700">Discount: {historyResult.personalized_discount.discount_percentage}%</div>
              <div className="text-sm text-green-700">Minimum Purchase: ${historyResult.personalized_discount.minimum_purchase}</div>
              <div className="text-sm text-green-700">Valid: {historyResult.personalized_discount.valid_from} - {historyResult.personalized_discount.valid_until}</div>
            </div>
          )}
        </div>
      </div>
    );
  }
  if (type === 'assistant' && supportResult) {
    // FAQ answer formatting
    if (supportResult.answer) {
      return (
        <div className="flex justify-start mb-4">
          <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white shadow-md border border-yellow-200">
            <h3 className="text-lg font-bold text-yellow-700 mb-2">FAQ Answer</h3>
            {supportResult.query && (
              <div className="text-sm text-gray-700 mb-1">
                <span className="font-semibold">Your Question:</span> {supportResult.query}
              </div>
            )}
            {supportResult.question && (
              <div className="text-sm text-gray-700 mb-1">
                <span className="font-semibold">Matched FAQ:</span> {supportResult.question}
              </div>
            )}
            {supportResult.answer && (
              <div className="text-base text-gray-900 mb-2">
                <span className="font-semibold">Answer:</span> {supportResult.answer}
              </div>
            )}
            {supportResult.category && (
              <div className="text-xs text-gray-500 mb-1">
                <span className="font-semibold">Category:</span> {supportResult.category}
              </div>
            )}
            {supportResult.confidence_score !== undefined && (
              <div className="text-xs text-gray-500 mb-1">
                <span className="font-semibold">Confidence:</span> {Math.round(supportResult.confidence_score * 100)}%
              </div>
            )}
            {supportResult.timestamp && (
              <div className="text-xs text-gray-400 mb-1">
                <span className="font-semibold">Timestamp:</span> {supportResult.timestamp}
              </div>
            )}
          </div>
        </div>
      );
    }
    // Fallback for other supportResult types
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white shadow-md border border-yellow-200">
          <h3 className="text-lg font-bold text-yellow-700 mb-2">Support Response</h3>
          <pre className="text-xs text-gray-800 whitespace-pre-wrap">{typeof supportResult === 'string' ? supportResult : JSON.stringify(supportResult, null, 2)}</pre>
        </div>
      </div>
    );
  }
  if (type === 'login_prompt') {
    return (
      <div className="flex justify-start mb-4">
        <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white shadow-md border border-blue-200 flex flex-col items-start gap-3">
          <span className="text-gray-800">
            <TypeIt
              options={{
                speed: 35,
                waitUntilVisible: true,
                cursor: false,
                lifeLike: true,
                afterComplete: () => setShowButtons(true),
              }}
            >
              You need to login to perform this action. You can log in using the <b>Google</b> or <b>Github</b> button at the top right of the page, or use the button below:
            </TypeIt>
          </span>
          {showButtons && (
            <div>
              <UserAuth />
            </div>
          )}
        </div>
      </div>
    );
  }
  return (
    <div className={`flex ${type === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          type === 'user'
            ? 'bg-blue-600 text-white'
            : 'bg-white shadow-md border border-gray-200'
        }`}
      >
        {type === 'assistant' && product ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">{product.name}</h3>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                Best Match
              </span>
            </div>
            {product.brand && (
              <p className="text-sm text-gray-700">by {product.brand}</p>
            )}
            <div className="flex items-center space-x-2">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  <StarIcon
                    key={i}
                    className={`w-4 h-4 ${
                      i < Math.floor(parseFloat(product.rating))
                        ? 'text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm text-gray-700">({product.rating})</span>
            </div>
            {product.description && (
              <p className="text-gray-700 text-sm">{product.description}</p>
            )}
            <div className="flex items-center justify-between pt-2">
              <p className="text-xl font-bold text-gray-800">${product.price}</p>
              <div className="flex space-x-2">
                {/* {onComparePrices && (
                  <Button
                    size="sm"
                    onClick={() => onComparePrices([product])}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700"
                  >
                    <ArrowsRightLeftIcon className="w-4 h-4 mr-2" />
                    Compare
                  </Button>
                )} */}
                <Button
                  size="sm"
                  onClick={() => onBuyNow(product)}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                >
                  <ShoppingCartIcon className="w-4 h-4 mr-2" />
                  Buy Now
                </Button>
              </div>
            </div>
          </div>
        ) : type === 'assistant' && products ? (
          <div className="space-y-4">
            <p className="text-gray-800">{content}</p>
            <div className="grid grid-cols-1 gap-4">
              {products.map((p, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-800">{p.name || 'Unnamed Product'}</h3>
                    {p.brand && (
                      <span className="text-sm text-gray-600">by {p.brand}</span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 mt-2">
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <StarIcon
                          key={i}
                          className={`w-4 h-4 ${
                            i < Math.floor(parseFloat(p.rating))
                              ? 'text-yellow-400'
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-sm text-gray-700">({p.rating})</span>
                  </div>
                  {p.description && (
                    <p className="text-gray-700 text-sm mt-2">{p.description}</p>
                  )}
                  <div className="flex items-center justify-between pt-2">
                    <p className="text-xl font-bold text-gray-800">${p.price}</p>
                    <div className="flex space-x-2">
                      {/* {onComparePrices && (
                        <Button
                          size="sm"
                          onClick={() => onComparePrices([p])}
                          className="bg-gray-100 hover:bg-gray-200 text-gray-700"
                        >
                          <ArrowsRightLeftIcon className="w-4 h-4 mr-2" />
                          Compare
                        </Button>
                      )} */}
                      <Button
                        size="sm"
                        onClick={() => onBuyNow(p)}
                        className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
                      >
                        <ShoppingCartIcon className="w-4 h-4 mr-2" />
                        Buy Now
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : type === 'assistant' && comparisonResults ? (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Price Comparison Results</h3>
            <div className="space-y-2">
              <p className="text-sm text-gray-700">
                Price Range: ${comparisonResults.price_range.lowest.toFixed(2)} - ${comparisonResults.price_range.highest.toFixed(2)}
              </p>
              {comparisonResults.best_deal && (
                <div className="bg-green-50 p-3 rounded-lg">
                  <p className="font-medium text-green-800">Best Deal:</p>
                  <p className="text-sm text-green-700">{comparisonResults.best_deal.name}</p>
                  <p className="text-sm text-green-700">Price: {comparisonResults.best_deal.price}</p>
                  <p className="text-sm text-green-700">Rating: {comparisonResults.best_deal.rating}</p>
                </div>
              )}
            </div>
          </div>
        ) : type === 'assistant' ? (
          <div className="whitespace-pre-wrap text-gray-800">
            <TypeIt
              options={{
                speed: 35,
                waitUntilVisible: true,
                cursor: false,
                lifeLike: true,
              }}
            >
              {content}
            </TypeIt>
          </div>
        ) : (
          <p className="whitespace-pre-wrap text-white">{content}</p>
        )}
      </div>
    </div>
  );
} 