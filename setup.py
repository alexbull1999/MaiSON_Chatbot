from setuptools import setup, find_packages

setup(
    name="maison-chatbot",
    version="0.1.0",
    packages=find_packages(include=['app', 'app.*']),
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
    ],
    python_requires=">=3.11",
)
