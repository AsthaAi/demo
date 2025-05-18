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

class PromotionRequest(BaseModel):
    product_details: Dict[str, Any]
    customer_email: str

class CapturePaymentRequest(BaseModel):
    order_id: str

class PriceComparisonRequest(BaseModel):
    products: List[Dict[str, Any]]

class CampaignData(BaseModel):
    name: str
    description: str
    start_date: str
    end_date: str
    discount_type: str
    discount_value: float
    conditions: dict

class HistoryRequest(BaseModel):
    email: str

class RefundRequest(BaseModel):
    transaction_id: str
    reason: str
    amount: float

class FAQRequest(BaseModel):
    question: str

class SupportTicketRequest(BaseModel):
    customer_id: str
    issue_type: str
    priority: str
    description: str

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
            # Get all products first
            if research_results.get("top_products"):
                products = research_results["top_products"]
            elif research_results.get("filtered_products"):
                products = research_results["filtered_products"]
            elif research_results.get("raw_products"):
                products = research_results["raw_products"]
            
            # Then get best match
            if research_results.get("best_match"):
                best_match = research_results["best_match"]
                # Add best match to products if not already included
                if best_match and not any(p.get('name') == best_match.get('name') for p in products):
                    products.insert(0, best_match)

        # If no products found, try to load from product.json
        if not products and not best_match:
            try:
                product_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'product.json')
                if os.path.exists(product_json_path):
                    with open(product_json_path, 'r') as f:
                        saved_results = json.load(f)
                        if saved_results.get("top_products"):
                            products = saved_results["top_products"]
                        elif saved_results.get("filtered_products"):
                            products = saved_results["filtered_products"]
                        elif saved_results.get("raw_products"):
                            products = saved_results["raw_products"]
                        
                        if saved_results.get("best_match"):
                            best_match = saved_results["best_match"]
                            # Add best match to products if not already included
                            if best_match and not any(p.get('name') == best_match.get('name') for p in products):
                                products.insert(0, best_match)
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
async def compare_prices(request: PriceComparisonRequest):
    try:
        shopper = ShopperAI("", {"max_price": 1000, "min_rating": 0})
        comparison_results = await shopper.run_price_comparison(request.products)
        return {"success": True, "results": comparison_results}
    except Exception as e:
        print(f"Error comparing prices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error comparing prices: {str(e)}")

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

@app.post("/api/get-promotions")
async def get_promotions(request: PromotionRequest):
    # Skipping promotions for now
    # try:
    #     shopper = ShopperAI(
    #         query=request.product_details.get("name", ""),
    #         criteria={"max_price": 1000, "min_rating": 0}
    #     )
    #     promotions = await shopper.get_available_promotions(
    #         product_details=request.product_details,
    #         customer_email=request.customer_email
    #     )
    #     return {"success": True, "promotions": promotions}
    # except Exception as e:
    #     print(f"Error getting promotions: {str(e)}")
    #     raise HTTPException(status_code=500, detail=f"Error getting promotions: {str(e)}")
    return {"success": True, "promotions": []}

@app.post("/api/capture-payment")
async def capture_payment(request: CapturePaymentRequest):
    # Skipping real capture for now
    # try:
    #     shopper = ShopperAI("", {"max_price": 1000, "min_rating": 0})
    #     result = await shopper.capture_payment(request.order_id)
    #     return {"success": True, "result": result}
    # except Exception as e:
    #     print(f"Error capturing payment: {str(e)}")
    #     raise HTTPException(status_code=500, detail=f"Error capturing payment: {str(e)}")
    return {"success": True, "result": {"approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=DUMMY"}}

@app.post("/api/create-promotion-campaign")
async def create_promotion_campaign(campaign_data: CampaignData):
    try:
        shopper = ShopperAI("", {})
        campaign = await shopper.create_promotion_campaign(campaign_data.dict())
        return {"success": True, "campaign": campaign}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/history")
async def get_history(request: HistoryRequest):
    try:
        shopper = ShopperAI("", {})
        analysis = await shopper.analyze_user_shopping_history(request.email)
        if analysis:
            return {"success": True, "result": analysis}
        else:
            return {"success": False, "result": "No history found for this email."}
    except Exception as e:
        return {"success": False, "result": f"Error: {str(e)}"}

@app.post("/api/refund")
async def refund(request: RefundRequest):
    try:
        shopper = ShopperAI("", {})
        refund_details = {
            "transaction_id": request.transaction_id,
            "reason": request.reason,
            "amount": request.amount
        }
        result = await shopper.process_refund_request(refund_details)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "result": f"Error: {str(e)}"}

@app.post("/api/faq")
async def faq(request: FAQRequest):
    try:
        shopper = ShopperAI("", {})
        result = await shopper.get_faq_answer(request.question)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "result": f"Error: {str(e)}"}

@app.post("/api/support-ticket")
async def support_ticket(request: SupportTicketRequest):
    try:
        shopper = ShopperAI("", {})
        ticket_details = {
            "customer_id": request.customer_id,
            "issue_type": request.issue_type,
            "priority": request.priority,
            "description": request.description
        }
        result = await shopper.create_support_ticket(ticket_details)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "result": f"Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 