"""
Mock data and functionality for demonstration purposes
"""
import json
import random
from typing import Dict, Any, List

# Sample products for demonstration
SAMPLE_PRODUCTS = [
    {
        "name": "Premium Water Bottle",
        "price": "$24.99",
        "rating": 4.7,
        "brand": "HydroMax",
        "description": "Vacuum insulated stainless steel water bottle keeps drinks hot or cold for hours",
        "material": "Stainless Steel",
        "capacity": "32 oz"
    },
    {
        "name": "Sports Water Bottle",
        "price": "$15.99",
        "rating": 4.5,
        "brand": "FitFlow",
        "description": "BPA-free plastic water bottle with leak-proof lid and carrying strap",
        "material": "Tritan Plastic",
        "capacity": "24 oz"
    },
    {
        "name": "Glass Water Bottle",
        "price": "$19.99",
        "rating": 4.3,
        "brand": "PureGlass",
        "description": "Eco-friendly glass water bottle with silicone sleeve for protection",
        "material": "Borosilicate Glass",
        "capacity": "20 oz"
    },
    {
        "name": "Collapsible Water Bottle",
        "price": "$12.99",
        "rating": 4.0,
        "brand": "TravelSip",
        "description": "Space-saving collapsible silicone water bottle for travel and outdoors",
        "material": "Food-grade Silicone",
        "capacity": "17 oz"
    },
    {
        "name": "Insulated Tumbler",
        "price": "$29.99",
        "rating": 4.8,
        "brand": "ChillKeep",
        "description": "Double-wall vacuum insulated tumbler with sliding lid and straw",
        "material": "Stainless Steel",
        "capacity": "30 oz"
    }
]

# Sample payment details
SAMPLE_PAYMENT = {
    "id": "PAY-1234567890ABCDEF",
    "status": "COMPLETED",
    "amount": {
        "total": "24.99",
        "currency": "USD"
    },
    "links": [
        {
            "href": "https://example.com/payments/PAY-1234567890ABCDEF",
            "rel": "self",
            "method": "GET"
        }
    ]
}

# Sample promotions
SAMPLE_PROMOTIONS = [
    {
        "name": "Summer Sale",
        "description": "Special discounts on summer items",
        "discount_percentage": 15,
        "minimum_purchase": 50,
        "valid_until": "2024-08-31"
    },
    {
        "name": "New Customer",
        "description": "Welcome discount for new customers",
        "discount_percentage": 10,
        "minimum_purchase": 25,
        "valid_until": "2024-12-31"
    }
]

# Sample shopping history analysis
SAMPLE_HISTORY_ANALYSIS = {
    "total_spent": 149.95,
    "average_order_value": 49.98,
    "total_transactions": 3,
    "favorite_categories": ["Drinkware", "Accessories"],
    "recommended_products": [
        "Insulated Food Container",
        "Hydration Backpack",
        "Water Bottle Cleaning Kit"
    ]
}

# Sample FAQ responses
SAMPLE_FAQ_RESPONSES = {
    "return": {
        "question": "What is your return policy?",
        "answer": "We offer a 30-day return policy for unused items in original packaging."
    },
    "shipping": {
        "question": "How long does shipping take?",
        "answer": "Standard shipping takes 3-5 business days. Express shipping is 1-2 business days."
    },
    "warranty": {
        "question": "Do your products have a warranty?",
        "answer": "Yes, all of our products come with a 1-year limited warranty against manufacturer defects."
    }
}


async def search_products(query: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock function to search for products based on criteria
    """
    # Filter products based on criteria
    max_price = criteria.get('max_price', 1000)
    min_rating = criteria.get('min_rating', 0)
    
    filtered_products = []
    for product in SAMPLE_PRODUCTS:
        # Extract price as float (remove $ sign)
        price_value = float(product['price'].replace('$', ''))
        if price_value <= max_price and product['rating'] >= min_rating:
            filtered_products.append(product)
    
    # Sort by rating (descending)
    filtered_products.sort(key=lambda x: x['rating'], reverse=True)
    
    # Select top 3 products
    top_products = filtered_products[:3]
    
    # Best match is the first one
    best_match = top_products[0] if top_products else None
    
    return {
        "raw_products": SAMPLE_PRODUCTS,
        "filtered_products": filtered_products,
        "top_products": top_products,
        "best_match": best_match
    }


async def compare_prices(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Mock function to compare prices of products
    """
    if not products:
        products = SAMPLE_PRODUCTS
    
    # Find the cheapest product
    cheapest = min(products, key=lambda x: float(x['price'].replace('$', '')))
    
    return {
        "product": cheapest,
        "summary": f"Found the best deal for {cheapest['name']} at {cheapest['price']}"
    }


async def process_payment(product_details: Dict[str, Any], customer_email: str) -> Dict[str, Any]:
    """
    Mock function to process payment
    """
    # Generate a unique order ID
    order_id = f"ORDER-{random.randint(1000000, 9999999)}"
    
    # Create a payment response
    payment_response = {
        "id": order_id,
        "status": "CREATED",
        "amount": {
            "total": product_details.get('price', '0.00'),
            "currency": "USD"
        },
        "links": [
            {
                "href": f"https://example.com/pay/{order_id}",
                "rel": "approve",
                "method": "GET"
            },
            {
                "href": f"https://example.com/orders/{order_id}",
                "rel": "self",
                "method": "GET"
            }
        ],
        "customer_email": customer_email
    }
    
    return payment_response


async def create_promotion_campaign(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock function to create a promotion campaign
    """
    # Create a new promotion based on the input data
    promotion = {
        "name": campaign_data.get('name', 'Unnamed Promotion'),
        "description": campaign_data.get('description', ''),
        "discount_type": campaign_data.get('discount_type', 'percentage'),
        "discount_value": campaign_data.get('discount_value', 10),
        "start_date": campaign_data.get('start_date'),
        "end_date": campaign_data.get('end_date'),
        "conditions": campaign_data.get('conditions', {}),
        "id": f"PROMO-{random.randint(1000, 9999)}"
    }
    
    return promotion


async def analyze_shopping_history(user_id: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Mock function to analyze shopping history
    """
    # Add user_id to the analysis
    analysis = SAMPLE_HISTORY_ANALYSIS.copy()
    analysis["user_id"] = user_id
    
    if history:
        # Calculate basic stats if history is provided
        total_spent = sum(item.get('amount', 0) for item in history)
        analysis["total_spent"] = total_spent
        analysis["average_order_value"] = total_spent / len(history) if history else 0
        analysis["total_transactions"] = len(history)
    
    return analysis


async def process_refund(order_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock function to process a refund
    """
    refund_id = f"REFUND-{random.randint(1000000, 9999999)}"
    
    refund_result = {
        "id": refund_id,
        "transaction_id": order_details.get('transaction_id'),
        "amount": order_details.get('amount'),
        "reason": order_details.get('reason'),
        "status": "COMPLETED",
        "create_time": "2024-05-17T14:30:00Z"
    }
    
    return refund_result


async def get_faq_response(query: str) -> Dict[str, Any]:
    """
    Mock function to get FAQ response
    """
    # Search for keywords in the query
    keywords = ["return", "shipping", "warranty"]
    matched_keyword = None
    
    for keyword in keywords:
        if keyword in query.lower():
            matched_keyword = keyword
            break
    
    if matched_keyword and matched_keyword in SAMPLE_FAQ_RESPONSES:
        return SAMPLE_FAQ_RESPONSES[matched_keyword]
    else:
        return {
            "question": query,
            "answer": "I'm sorry, I don't have specific information about that. Please contact our customer support for assistance."
        }


async def create_support_ticket(issue_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock function to create a support ticket
    """
    ticket_id = f"TICKET-{random.randint(10000, 99999)}"
    
    ticket = {
        "id": ticket_id,
        "customer_id": issue_details.get('customer_id'),
        "issue_type": issue_details.get('issue_type'),
        "priority": issue_details.get('priority'),
        "description": issue_details.get('description'),
        "status": "OPEN",
        "created_at": "2024-05-17T15:00:00Z"
    }
    
    return ticket 