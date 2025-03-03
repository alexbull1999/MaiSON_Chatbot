import asyncio
from app.modules.advisory import AdvisoryModule


async def test():
    module = AdvisoryModule()
    response = await module.handle_general_inquiry(
        "Can you help me find a good area to live in London? I can talk to you about what I'm looking for and then want your suggestions?"
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(test())
