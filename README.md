# AI Code Review Tool

An automated tool that analyzes code changes between Git branches and provides feedback using Large Language Models.

## Overview

This tool helps developers improve code quality by providing automated reviews of code changes. It analyzes the differences between Git branches, sends the relevant code to a language model, and presents structured feedback.

## Features

- Git integration to analyze diffs between branches
- Intelligent code analysis using LLMs
- Structured feedback with actionable suggestions
- Command-line interface for easy integration into workflows

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd code-review-tool

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Basic usage
python -m code_review_tool review --target-branch main

# For more options
python -m code_review_tool --help
```

## Requirements

- Python 3.8+
- Git
- Access to an LLM API (OpenAI, Anthropic, or local model)
