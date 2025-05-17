from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models import OrderRequest
from ..mock_data import process_payment, SAMPLE_PAYMENT

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "Not found"}},
)


@router.post("/")
async def process_order(order_request: OrderRequest) -> Dict[str, Any]:
    """
    Process an order with payment via PayPal
    """
    try:
        # Process the order with payment using mock function
        order_result = await process_payment(
            order_request.product_details.dict(),
            order_request.customer_email
        )
        
        if not order_result:
            raise HTTPException(status_code=400, detail="Failed to process order")
        
        return order_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process order: {str(e)}")
        
        
@router.get("/latest-payment")
async def get_latest_payment() -> Dict[str, Any]:
    """
    Get the latest payment details
    """
    try:
        # Return sample payment data
        return SAMPLE_PAYMENT
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get latest payment: {str(e)}") 