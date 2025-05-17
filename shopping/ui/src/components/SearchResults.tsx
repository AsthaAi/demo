import { Card, Button, Table } from 'flowbite-react';
import { StarIcon, ArrowPathIcon, ShoppingCartIcon } from '@heroicons/react/24/solid';

interface Product {
  name: string;
  price: string;
  rating: string;
  brand?: string;
  description?: string;
}

interface SearchResultsProps {
  bestMatch: Product | null;
  products: Product[];
  onComparePrices: () => void;
  onProceedToPayment: (product: Product) => void;
  isLoading: boolean;
}

export default function SearchResults({
  bestMatch,
  products,
  onComparePrices,
  onProceedToPayment,
  isLoading
}: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Searching for the best products...</p>
        </div>
      </div>
    );
  }

  if (!bestMatch && products.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShoppingCartIcon className="w-12 h-12 text-gray-400" />
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No Products Found</h3>
        <p className="text-gray-600">Try adjusting your search criteria</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {bestMatch && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Best Match</h2>
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              Recommended
            </span>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{bestMatch.name}</h3>
                {bestMatch.brand && (
                  <p className="text-sm text-gray-600">by {bestMatch.brand}</p>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <StarIcon
                      key={i}
                      className={`w-5 h-5 ${
                        i < Math.floor(parseFloat(bestMatch.rating))
                          ? 'text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
                <span className="text-sm text-gray-600">({bestMatch.rating})</span>
              </div>
              {bestMatch.description && (
                <p className="text-gray-600">{bestMatch.description}</p>
              )}
            </div>
            <div className="flex flex-col items-end justify-between">
              <div className="text-right">
                <p className="text-3xl font-bold text-gray-900">{bestMatch.price}</p>
              </div>
              <Button
                onClick={() => onProceedToPayment(bestMatch)}
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
              >
                <ShoppingCartIcon className="w-5 h-5 mr-2" />
                Buy Now
              </Button>
            </div>
          </div>
        </div>
      )}

      {products.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">All Products</h2>
            <Button
              onClick={onComparePrices}
              disabled={isLoading}
              className="bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
            >
              <ArrowPathIcon className="w-5 h-5 mr-2" />
              Compare Prices
            </Button>
          </div>
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <Table hoverable>
              <Table.Head>
                <Table.HeadCell>Product</Table.HeadCell>
                <Table.HeadCell>Price</Table.HeadCell>
                <Table.HeadCell>Rating</Table.HeadCell>
                <Table.HeadCell>Actions</Table.HeadCell>
              </Table.Head>
              <Table.Body>
                {products.map((product, index) => (
                  <Table.Row key={index} className="hover:bg-gray-50">
                    <Table.Cell className="whitespace-nowrap font-medium">
                      <div>
                        <p className="text-gray-900">{product.name}</p>
                        {product.brand && (
                          <p className="text-sm text-gray-500">{product.brand}</p>
                        )}
                      </div>
                    </Table.Cell>
                    <Table.Cell className="font-semibold text-gray-900">
                      {product.price}
                    </Table.Cell>
                    <Table.Cell>
                      <div className="flex items-center">
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
                        <span className="ml-2 text-sm text-gray-600">
                          ({product.rating})
                        </span>
                      </div>
                    </Table.Cell>
                    <Table.Cell>
                      <Button
                        size="sm"
                        onClick={() => onProceedToPayment(product)}
                        className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                      >
                        <ShoppingCartIcon className="w-4 h-4 mr-2" />
                        Buy
                      </Button>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
} 