"""Setup script for the AI Code Review Tool."""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from __init__.py
with open(os.path.join("code_review_tool", "__init__.py"), "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

setup(
    name="code-review-tool",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered code review tool that analyzes Git diffs and provides feedback",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/code-review-tool",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "gitpython>=3.1.30",
        "typer>=0.9.0",
        "rich>=13.3.5",
        "openai>=1.1.0",
        "anthropic>=0.5.0",
        "pydantic>=2.0.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "code-review=code_review_tool.cli:main",
        ],
    },
)
