import asyncio
from routers.openrouter import OpenRouterClient

async def test_chat_completion():
    client = OpenRouterClient()
    try:
        response = await client.chat_completion(
            model="openai/gpt-4.1-nano",#"google/gemma-3-27b-it:free",
            messages=[
                {
                    "role": "user",
                    "content": "What's the capital of France?"
                }
            ],
            max_tokens=10,
            temperature=0.7
        )
        print("Response:\n", response)
        # extract final assistant message from response
        assistant_message = response['choices'][0]['message']['content']
        print("Assistant message:\n", assistant_message)

        # get cost of the request
        id = response['id']
        await asyncio.sleep(2) # wait for the cost to be available
        details = await client.get_generation_details(id)
        print("Details:\n", details)
        stats = details['data']
        total_tokens = int(stats['native_tokens_prompt'] + stats['native_tokens_completion'])
        cost = float(stats['total_cost'])
        print("Total tokens: ", total_tokens)
        print("Cost: ", cost)

    except Exception as e:
        print("Error:", e)
    finally:
        await client.client.aclose() # close AsyncClient

if __name__ == "__main__":
    asyncio.run(test_chat_completion())