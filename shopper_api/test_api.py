import requests
import json
from typing import Dict, Any


def test_health():
    """Test the health check endpoint"""
    response = requests.get("http://localhost:8000/health")
    print(f"Health check response: {response.status_code}")
    print(response.json())
    print()


def test_search(query: str, max_price: float, min_rating: float):
    """Test the search endpoint"""
    url = "http://localhost:8000/research/"
    payload = {
        "query": query,
        "max_price": max_price,
        "min_rating": min_rating
    }
    
    print(f"Searching for: {query}")
    response = requests.post(url, json=payload)
    print(f"Search response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Search results:")
        print_product_info(data)
        return data
    else:
        print(response.text)
        return None


def test_price_comparison(products: Dict[str, Any]):
    """Test the price comparison endpoint"""
    url = "http://localhost:8000/research/price-comparison"
    
    print("\nComparing prices...")
    response = requests.post(url, json=products)
    print(f"Price comparison response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Best deal:")
        if data.get("product"):
            product = data["product"]
            print(f"Name: {product.get('name', 'Unknown')}")
            print(f"Price: {product.get('price', 'N/A')}")
            print(f"Rating: {product.get('rating', 'N/A')}")
        if data.get("summary"):
            print(f"Summary: {data['summary']}")
        return data
    else:
        print(response.text)
        return None


def print_product_info(data: Dict[str, Any]):
    """Print product information from research results"""
    if not isinstance(data, dict):
        print("No product data available")
        return
    
    # Try to get the best match first
    if data.get("best_match") and data["best_match"]:
        best = data["best_match"]
        print("\nBest Match:")
        print(f"Name: {best.get('name', best.get('title', ''))}")
        print(f"Price: {best.get('price', '')}")
        print(f"Rating: {best.get('rating', '')}")
    
    # Print top products if available
    products = []
    if data.get("top_products") and data["top_products"]:
        products = data["top_products"]
        print("\nTop Products:")
    elif data.get("filtered_products") and data["filtered_products"]:
        products = data["filtered_products"]
        print("\nFiltered Products:")
    elif data.get("raw_products") and data["raw_products"]:
        products = data["raw_products"]
        print("\nRaw Products:")
    
    if products:
        print("\n{:<40} {:<10} {:<10}".format("Product", "Price", "Rating"))
        print("-" * 60)
        for product in products:
            name = product.get("name", product.get("title", "Unknown"))
            price = product.get("price", "N/A")
            rating = product.get("rating", "N/A")
            print("{:<40} {:<10} {:<10}".format(
                name[:37] + "..." if len(name) > 37 else name,
                price,
                rating
            ))


def main():
    """Main test function"""
    print("Testing ShopperAI API")
    print("=====================\n")
    
    # Test health check
    test_health()
    
    # Test product search
    search_results = test_search("water bottle", 50.0, 4.0)
    
    # Test price comparison if search was successful
    if search_results:
        test_price_comparison(search_results)
    
    print("\nAPI Tests completed!")


if __name__ == "__main__":
    main() 