import { useState } from 'react';
import { Card, TextInput, Button, Label } from 'flowbite-react';
import { MagnifyingGlassIcon, CurrencyDollarIcon, StarIcon } from '@heroicons/react/24/outline';

interface SearchFormProps {
  onSearch: (query: string, maxPrice: number, minRating: number) => void;
  isLoading: boolean;
}

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [minRating, setMinRating] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const price = parseFloat(maxPrice);
    const rating = parseFloat(minRating);
    
    if (isNaN(price) || isNaN(rating)) {
      alert('Please enter valid numbers for price and rating');
      return;
    }
    
    if (rating < 0 || rating > 5) {
      alert('Rating must be between 0 and 5');
      return;
    }
    
    onSearch(query, price, rating);
  };

  return (
    <div className="relative">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl -z-10" />
      
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-32 h-32 bg-blue-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob" />
      <div className="absolute top-0 right-0 w-32 h-32 bg-purple-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000" />
      <div className="absolute -bottom-8 left-20 w-32 h-32 bg-pink-100 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000" />

      <Card className="w-full max-w-md mx-auto border-none shadow-xl bg-white/80 backdrop-blur-sm">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Find Your Perfect Product</h2>
          <p className="text-gray-600">Enter your search criteria below</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <div className="space-y-2">
            <Label htmlFor="query" className="text-gray-700 font-medium">
              What would you like to search for?
            </Label>
            <div className="relative">
              <TextInput
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter product name..."
                required
                className="pl-10 bg-white/50 focus:bg-white transition-colors duration-200"
              />
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="maxPrice" className="text-gray-700 font-medium">
              Maximum price (in USD)
            </Label>
            <div className="relative">
              <TextInput
                id="maxPrice"
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="Enter maximum price..."
                required
                className="pl-10 bg-white/50 focus:bg-white transition-colors duration-200"
              />
              <CurrencyDollarIcon className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="minRating" className="text-gray-700 font-medium">
              Minimum rating (0-5)
            </Label>
            <div className="relative">
              <TextInput
                id="minRating"
                type="number"
                value={minRating}
                onChange={(e) => setMinRating(e.target.value)}
                placeholder="Enter minimum rating..."
                min="0"
                max="5"
                step="0.1"
                required
                className="pl-10 bg-white/50 focus:bg-white transition-colors duration-200"
              />
              <StarIcon className="h-5 w-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            </div>
          </div>
          
          <Button
            type="submit"
            disabled={isLoading}
            className="mt-4 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 focus:ring-4 focus:ring-purple-200 transition-all duration-200 transform hover:scale-[1.02]"
          >
            {isLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Searching...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <MagnifyingGlassIcon className="h-5 w-5" />
                <span>Search Products</span>
              </div>
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
} 