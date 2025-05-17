import { StarIcon, ShoppingCartIcon } from '@heroicons/react/24/solid';
import { Button } from 'flowbite-react';

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

interface ChatMessageProps {
  type: 'user' | 'assistant';
  content: string;
  product?: Product;
  onBuyNow?: (product: Product) => void;
}

export default function ChatMessage({ type, content, product, onBuyNow }: ChatMessageProps) {
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
              <p className="text-xl font-bold text-gray-800">{product.price}</p>
              <Button
                size="sm"
                onClick={() => onBuyNow?.(product)}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                <ShoppingCartIcon className="w-4 h-4 mr-2" />
                Buy Now
              </Button>
            </div>
          </div>
        ) : (
          <p className={`whitespace-pre-wrap ${type === 'user' ? 'text-white' : 'text-gray-800'}`}>
            {content}
          </p>
        )}
      </div>
    </div>
  );
} 