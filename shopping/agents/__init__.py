"""
ShopperAI agents package
"""

"""
Initialize all agents for ShopperAI
"""
# from .price_comparison_agent import PriceComparisonAgent  # Temporarily disabled
from .customer_support_agent import CustomerSupportAgent
from .promotions_agent import PromotionsAgent
from .paypal_agent import PayPalAgent
from .research_agent import ResearchAgent
from .order_agent import OrderAgent

__all__ = [
    'ResearchAgent',
    # 'PriceComparisonAgent',  # Temporarily disabled
    'OrderAgent',
    'PayPalAgent',
    'PromotionsAgent',
    'CustomerSupportAgent'
]
