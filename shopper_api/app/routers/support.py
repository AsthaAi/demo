from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models import RefundRequest, FaqRequest, SupportTicketRequest
from ..mock_data import process_refund, get_faq_response, create_support_ticket

router = APIRouter(
    prefix="/support",
    tags=["support"],
    responses={404: {"description": "Not found"}},
)


@router.post("/refund")
async def process_refund_api(refund_request: RefundRequest) -> Dict[str, Any]:
    """
    Process a refund request
    """
    try:
        # Process the refund using mock function
        refund_result = await process_refund(refund_request.dict())
        
        if not refund_result:
            raise HTTPException(status_code=400, detail="Failed to process refund")
        
        return refund_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process refund: {str(e)}")


@router.post("/faq")
async def get_faq_answer_api(faq_request: FaqRequest) -> Dict[str, Any]:
    """
    Get answer for a FAQ query
    """
    try:
        # Get FAQ response using mock function
        faq_result = await get_faq_response(faq_request.query)
        
        if not faq_result:
            raise HTTPException(status_code=400, detail="Failed to get FAQ response")
        
        return faq_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get FAQ response: {str(e)}")


@router.post("/ticket")
async def create_support_ticket_api(ticket_request: SupportTicketRequest) -> Dict[str, Any]:
    """
    Create a support ticket
    """
    try:
        # Create support ticket using mock function
        ticket_result = await create_support_ticket(ticket_request.dict())
        
        if not ticket_result:
            raise HTTPException(status_code=400, detail="Failed to create support ticket")
        
        return ticket_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create support ticket: {str(e)}") 