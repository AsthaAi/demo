from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from ..models import PromotionCampaignRequest, ShoppingHistoryRequest
from ..mock_data import create_promotion_campaign, analyze_shopping_history

router = APIRouter(
    prefix="/promotions",
    tags=["promotions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/campaigns")
async def create_campaign(campaign_request: PromotionCampaignRequest) -> Dict[str, Any]:
    """
    Create a new promotional campaign
    """
    try:
        # Create the campaign using mock function
        campaign_result = await create_promotion_campaign(campaign_request.dict())
        
        if not campaign_result:
            raise HTTPException(status_code=400, detail="Failed to create promotion campaign")
        
        return campaign_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create promotion campaign: {str(e)}")


@router.post("/shopping-history")
async def analyze_shopping_history_api(history_request: ShoppingHistoryRequest) -> Dict[str, Any]:
    """
    Analyze a user's shopping history for insights and personalized recommendations
    """
    try:
        # Analyze shopping history using mock function
        analysis_result = await analyze_shopping_history(
            history_request.user_id,
            history_request.history
        )
        
        if not analysis_result:
            raise HTTPException(status_code=400, detail="Failed to analyze shopping history")
        
        return analysis_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze shopping history: {str(e)}") 