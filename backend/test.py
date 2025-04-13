import asyncio
from routers.openrouter import OpenRouterClient

async def test_chat_completion():
    client = OpenRouterClient()
    try:
        response = await client.chat_completion(
            model="openrouter/optimus-alpha",
            messages=[
                {
                "role": "user",
                "content": "What's the capital of France?"
                }
            ],
            max_tokens=50,
            temperature=0.7
        )
        print("Response:\n", response)

    except Exception as e:
        print("Error:", e)
    finally:
        await client.client.aclose() # close AsyncClient

if __name__ == "__main__":
    asyncio.run(test_chat_completion())