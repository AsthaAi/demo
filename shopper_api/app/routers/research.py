from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models import SearchRequest
from ..mock_data import search_products, compare_prices

router = APIRouter(
    prefix="/research",
    tags=["research"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def search_products_api(search_request: SearchRequest) -> Dict[str, Any]:
    """
    Search for products based on the query and criteria
    """
    try:
        # Create criteria dictionary from the request
        criteria = {
            "max_price": search_request.max_price,
            "min_rating": search_request.min_rating
        }
        
        # Use mock function to search products
        research_results = await search_products(search_request.query, criteria)
        
        return research_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")


@router.post("/price-comparison")
async def compare_prices_api(products: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare prices for products
    """
    try:
        # Extract products list from the request
        product_list = []
        if "top_products" in products:
            product_list = products["top_products"]
        elif "filtered_products" in products:
            product_list = products["filtered_products"]
        elif "raw_products" in products:
            product_list = products["raw_products"]
        elif "products" in products:
            product_list = products["products"]
        
        # Use mock function to compare prices
        price_results = await compare_prices(product_list)
        
        return price_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare prices: {str(e)}") 