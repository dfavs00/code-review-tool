# AI Code Review Tool

An automated tool that analyzes code changes between Git branches and provides feedback using Large Language Models.

## Overview

This tool helps developers improve code quality by providing automated reviews of code changes. It analyzes the differences between Git branches, sends the relevant code to a language model, and presents structured feedback.

## Features

- Git integration to analyze diffs between branches
- Intelligent code analysis using LLMs
- Structured feedback with actionable suggestions
- Command-line interface for easy integration into workflows
- Support for multiple LLM providers (OpenAI, Anthropic)
- Multiple output formats (text, markdown, JSON)

## Installation

```bash
# Clone the repository
git clone https://github.com/dfavs00/code-review-tool.git
cd code-review-tool

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install the package in development mode
pip install -e .
```

## Configuration

Create a `.env` file based on the provided `.env.example` template:

```bash
cp .env.example .env
```

Then edit the `.env` file to add your API keys:

```
# API Keys for LLM providers
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Usage

### Command Line Interface

```bash
# Basic usage
python -m code_review_tool review --target-branch main

# Specify the LLM provider
python -m code_review_tool review --target-branch main --provider anthropic

# Output in different formats
python -m code_review_tool review --target-branch main --format markdown
python -m code_review_tool review --target-branch main --format json

# Save output to a file
python -m code_review_tool review --target-branch main --output review.md

# For more options
python -m code_review_tool --help
```

### Example Script

You can also use the provided example script:

```bash
python example_usage.py [target_branch]
```

## Components

- **Git Client**: Interfaces with Git repositories to fetch diffs between branches
- **Diff Parser**: Extracts and processes code changes from Git diffs
- **LLM Integration**: Connects to language model APIs to generate code reviews
- **Feedback Processor**: Structures and formats the LLM-generated feedback
- **CLI**: Provides a user-friendly command-line interface

## Requirements

- Python 3.8+
- Git
- Access to an LLM API (OpenAI, Anthropic, or local model)

## Future Enhancements

- CI/CD pipeline integration
- Fine-tuning prompts based on user feedback
- Additional output formats
- GUI interface
