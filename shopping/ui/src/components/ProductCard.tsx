import { Card, Button } from 'flowbite-react';
import { ShoppingCartIcon, StarIcon } from '@heroicons/react/24/outline';

interface ProductCardProps {
  name: string;
  price: number;
  rating: number;
  description: string;
  onOrder: () => void;
}

export default function ProductCard({
  name,
  price,
  rating,
  description,
  onOrder,
}: ProductCardProps) {
  return (
    <Card className="max-w-sm">
      <div className="flex flex-col gap-4">
        <h5 className="text-xl font-bold tracking-tight text-gray-900">
          {name}
        </h5>
        
        <div className="flex items-center gap-2">
          <div className="flex">
            {[...Array(5)].map((_, i) => (
              <StarIcon
                key={i}
                className={`h-5 w-5 ${
                  i < Math.floor(rating)
                    ? 'text-yellow-400 fill-current'
                    : 'text-gray-300'
                }`}
              />
            ))}
          </div>
          <span className="text-sm text-gray-500">({rating.toFixed(1)})</span>
        </div>

        <p className="font-normal text-gray-700">
          {description}
        </p>

        <div className="flex items-center justify-between">
          <span className="text-2xl font-bold text-gray-900">
            ${price.toFixed(2)}
          </span>
          <Button onClick={onOrder}>
            <ShoppingCartIcon className="h-5 w-5 mr-2" />
            Order Now
          </Button>
        </div>
      </div>
    </Card>
  );
} 