from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="freeseek-sdk",
    version="0.0.1",
    description="Python SDK for Freeseek's AI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/freeseek-sdk",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.26.0",
        "python-dotenv>=0.19.0",
        "typing-extensions>=4.0.0",
        "sseclient-py>=1.7.0",
        "httpx>=0.23.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=22.3.0",
            "mypy>=0.910",
        ]
    },
)