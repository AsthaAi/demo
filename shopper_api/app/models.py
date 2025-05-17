from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class SearchRequest(BaseModel):
    query: str
    max_price: float = Field(..., gt=0)
    min_rating: float = Field(..., ge=0, le=5)
    
    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "query": self.query,
            "max_price": self.max_price,
            "min_rating": self.min_rating
        }


class ProductDetail(BaseModel):
    name: str
    price: float
    quantity: int = 1
    description: str = ""
    payee_email: str

    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
            "description": self.description,
            "payee_email": self.payee_email
        }


class OrderRequest(BaseModel):
    product_details: ProductDetail
    customer_email: str
    
    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "product_details": self.product_details.dict(),
            "customer_email": self.customer_email
        }


class RefundRequest(BaseModel):
    transaction_id: str
    reason: str
    amount: float
    
    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "transaction_id": self.transaction_id,
            "reason": self.reason,
            "amount": self.amount
        }


class FaqRequest(BaseModel):
    query: str
    
    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "query": self.query
        }


class SupportTicketRequest(BaseModel):
    customer_id: str
    issue_type: str
    priority: str
    description: str
    
    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "customer_id": self.customer_id,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "description": self.description
        }


class PromotionCampaignRequest(BaseModel):
    name: str
    description: str
    start_date: str
    end_date: str
    discount_type: str
    discount_value: float
    conditions: Dict[str, Any]

    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "discount_type": self.discount_type,
            "discount_value": self.discount_value,
            "conditions": self.conditions
        }


class ShoppingHistoryRequest(BaseModel):
    user_id: str
    history: Optional[List[Dict[str, Any]]] = None
    
    def dict(self):
        """
        Backwards compatibility with older versions of Pydantic
        """
        return {
            "user_id": self.user_id,
            "history": self.history
        } 