import asyncio
import json
from main import ShopperAI


async def test_faq():
    shopper = ShopperAI('', {})

    # Test cases with different types of questions
    test_questions = [
        "How do I track my order?",  # Direct match
        "Where can I see my order status?",  # Similar question
        "What payment methods do you accept?",  # Different category
        "How do I get a refund?",  # Process question
        "Can I combine multiple discounts?"  # Complex question
    ]

    for question in test_questions:
        print(f"\n=== Testing Question: {question} ===")
        response = await shopper.get_faq_answer(question)
        print("Response:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    asyncio.run(test_faq())
