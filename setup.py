from setuptools import setup, find_packages

setup(
    name="fastapi_access_control",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "asyncpg",
        "python-jose",
        "passlib",
        "python-multipart",
        "asyncio-mqtt"
    ]
) 