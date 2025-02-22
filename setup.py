from setuptools import setup, find_packages

setup(
    name="maison-chatbot",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2-binary",
        "pydantic",
        "pydantic-settings",
        "python-dotenv",
        "openai",
        "anthropic",
        "google-generativeai",
        "tenacity",
        "aiohttp>=3.8.0",
        "apscheduler",
        "cachetools>=5.5.1",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "httpx",
        ],
    },
    python_requires=">=3.11",
)
