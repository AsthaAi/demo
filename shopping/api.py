from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
import asyncio
from main import ShopperAI

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    max_price: float = 1000.0
    min_rating: float = 0.0

class OrderRequest(BaseModel):
    product_details: Dict[str, Any]
    customer_email: str

@app.post("/api/search")
async def search_products(request: SearchRequest):
    try:
        # Initialize ShopperAI with the search criteria
        shopper = ShopperAI(
            query=request.query,
            criteria={
                "max_price": request.max_price,
                "min_rating": request.min_rating
            }
        )

        # Run the research phase - properly await the async function
        research_results = await shopper.run_research()
        print(f"Research results: {json.dumps(research_results, indent=2)}")  # Debug log

        # Extract products and best match
        products = []
        best_match = None

        if isinstance(research_results, dict):
            if research_results.get("best_match"):
                best_match = research_results["best_match"]
                products = [best_match]
            elif research_results.get("top_products"):
                products = research_results["top_products"]
            elif research_results.get("filtered_products"):
                products = research_results["filtered_products"]
            elif research_results.get("raw_products"):
                products = research_results["raw_products"]

        # If no products found, try to load from product.json
        if not products and not best_match:
            try:
                product_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'product.json')
                if os.path.exists(product_json_path):
                    with open(product_json_path, 'r') as f:
                        saved_results = json.load(f)
                        if saved_results.get("best_match"):
                            best_match = saved_results["best_match"]
                            products = [best_match]
                        elif saved_results.get("top_products"):
                            products = saved_results["top_products"]
                        elif saved_results.get("filtered_products"):
                            products = saved_results["filtered_products"]
                        elif saved_results.get("raw_products"):
                            products = saved_results["raw_products"]
            except Exception as e:
                print(f"Error loading from product.json: {str(e)}")

        return {
            "success": True,
            "best_match": best_match,
            "products": products
        }

    except Exception as e:
        print(f"Error in search_products: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching products: {str(e)}"
        )

@app.post("/api/compare-prices")
async def compare_prices(request: SearchRequest):
    try:
        # Initialize ShopperAI
        shopper = ShopperAI(
            query=request.query,
            criteria={
                "max_price": request.max_price,
                "min_rating": request.min_rating
            }
        )

        # Run price comparison - properly await the async function
        price_results = await shopper.run_price_comparison()
        print(f"Price comparison results: {json.dumps(price_results, indent=2)}")  # Debug log

        return {
            "success": True,
            "results": price_results
        }

    except Exception as e:
        print(f"Error in compare_prices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing prices: {str(e)}"
        )

@app.post("/api/process-order")
async def process_order(request: OrderRequest):
    try:
        # Initialize ShopperAI with minimal criteria
        shopper = ShopperAI(
            query=request.product_details.get("name", ""),
            criteria={"max_price": 1000, "min_rating": 0}
        )

        # Process the order with payment - properly await the async function
        result = await shopper.process_order_with_payment(
            product_details=request.product_details,
            customer_email=request.customer_email
        )
        print(f"Order processing results: {json.dumps(result, indent=2)}")  # Debug log

        return {
            "success": True,
            "result": result
        }

    except Exception as e:
        print(f"Error in process_order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing order: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 