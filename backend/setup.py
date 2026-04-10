from setuptools import find_packages, setup


setup(
    name="uyqur-ai-backend",
    version="0.1.0",
    description="Telegram support analytics bot backend with admin API.",
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["app", "app.*"]),
    py_modules=["bot"],
    install_requires=[
        "eval_type_backport>=0.2.2,<1.0.0",
        "fastapi>=0.116.1,<1.0.0",
        "httpx>=0.28.1,<1.0.0",
        "python-multipart>=0.0.20,<1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.5,<9.0.0",
            "pytest-asyncio>=0.26.0,<1.0.0",
            "uvicorn>=0.34.2,<1.0.0",
        ],
    },
)
