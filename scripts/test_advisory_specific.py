import asyncio
from app.modules.advisory import AdvisoryModule


async def test():
    module = AdvisoryModule()
    response = await module.handle_general_inquiry(
        "I need to be within a 30 minute commute of Peckham for work. Then my other key factors are looking for an area with a low crime-rate," 
        " and which has properties available for ~£500,000. I am looking for a 2-bed flat for that money"
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(test())
