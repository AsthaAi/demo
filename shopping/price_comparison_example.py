"""
Example script demonstrating the usage of PriceComparisonAgent with ResearchAgent
"""
from agents.research_agent import ResearchAgent
from agents.price_comparison_agent import PriceComparisonAgent
from agents.order_agent import OrderAgent
import asyncio


async def main():
    # Initialize agents
    research_agent = ResearchAgent()
    price_agent = PriceComparisonAgent()
    order_agent = OrderAgent()

    # Example search criteria
    search_query = "gaming laptop"
    criteria = {
        "budget": 1000,
        "min_rating": 4.0
    }

    # Search for products
    print("\n🔍 Searching for products...")
    products = research_agent.search_and_analyze(search_query, criteria)

    if not products:
        print("No products found matching the criteria.")
        return

    print(f"\n✅ Found {len(products)} products")

    # Get price recommendation
    print("\n💰 Finding the best deal...")
    recommendation = price_agent.recommend_best_product(products)

    if recommendation and "recommendation" in recommendation and recommendation["recommendation"]:
        print("\n🏆 Best Deal Found:")
        product = recommendation["product"]

        print(f"Product Name: {product['name']}")
        print(f"Brand: {product['brand']}")
        print(f"Price: {product['price']}")
        print(f"Color: {product['color']}")
        print(f"Total Cost (with shipping): {product['total_cost']}")

        print(f"\n📝 Summary:")
        print(recommendation["summary"])

        # Ask if the user wants to buy the product
        print("\n🛒 Purchase Option:")
        buy_choice = input(
            "Do you want to buy this product? (Type 'yes' or 'y' to confirm): ").lower()

        if buy_choice == "yes" or buy_choice == "y":
            print("\n✅ Great choice! Processing your purchase...")

            # Process the purchase
            confirmation = order_agent.process_purchase(product)

            # Display order confirmation
            print("\n\n##############################")
            print("## Order Confirmation")
            print("##############################")
            print(f"Transaction ID: {confirmation['transaction_id']}")
            print(f"Purchase Time: {confirmation['purchase_time']}")
            print(f"Status: {confirmation['status']}")
            print(
                f"Product: {confirmation['product']['name']} ({confirmation['product']['brand']})")
            print(f"Price: {confirmation['product']['price']}")
            print(f"Color: {confirmation['product']['color']}")
            print(f"Total Cost: {confirmation['product']['total_cost']}")
            print(f"\n{confirmation['message']}")
        else:
            print("\n❌ No problem! You can continue browsing or try a different search.")
    else:
        print("No suitable product found for recommendation.")


if __name__ == "__main__":
    asyncio.run(main())
