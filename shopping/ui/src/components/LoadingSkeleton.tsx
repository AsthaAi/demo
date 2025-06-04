import { Card } from 'flowbite-react';

interface LoadingSkeletonProps {
  type: 'message' | 'product';
}

export default function LoadingSkeleton({ type }: LoadingSkeletonProps) {
  // if (type === 'message') {
    return (
      <div className="flex items-start space-x-3 animate-pulse">
        {/* <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
        </div> */}
        <div className="flex-1 space-y-2">
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  // }

  // return (
  //   <Card className="animate-pulse">
  //     <div className="space-y-4">
  //       <div className="flex items-center space-x-4">
  //         <div className="w-16 h-16 bg-gray-200 rounded"></div>
  //         <div className="flex-1 space-y-2">
  //           <div className="h-4 bg-gray-200 rounded w-3/4"></div>
  //           <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  //         </div>
  //       </div>
  //       <div className="space-y-2">
  //         <div className="h-4 bg-gray-200 rounded"></div>
  //         <div className="h-4 bg-gray-200 rounded w-5/6"></div>
  //       </div>
  //       <div className="flex justify-between items-center">
  //         <div className="h-4 bg-gray-200 rounded w-1/4"></div>
  //         <div className="h-8 bg-gray-200 rounded w-1/4"></div>
  //       </div>
  //     </div>
  //   </Card>
  // );
} 