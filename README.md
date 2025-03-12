# 🤖 SWE599 - Multi-Agent LLM Pipeline for Software Development

> An AI-powered system for automating Django & Streamlit application development

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.12-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-🔗-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT-orange.svg)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-AI-yellow.svg)

## 📋 Table of Contents
- [About](#-about-this-project)
- [Current Pipeline](#-current-pipeline-django--streamlit-multi-agent-developer)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [How It Works](#-how-it-works)
- [Contributing](#-contributing)
- [License](#-license)

## 🔍 About This Project

This repository contains my **SWE599 capstone project**, which explores the use of **Multi-Agent LLM Pipelines** for automating software development tasks.

Currently, the project features a single AI-powered pipeline:

### `multiagent_django_streamlit.py`
An intelligent system that generates, tests, and debugs Django & Streamlit applications using OpenAI's GPT models and LangChain.

## 🚀 Current Pipeline: Django & Streamlit Multi-Agent Developer

This pipeline helps developers **automate Django & Streamlit application creation** using a team of specialized AI agents:

| Agent | Role |
|-------|------|
| **Code Generator** | Creates Django & Streamlit applications based on user requirements |
| **Test Writer** | Develops pytest unit tests for the generated code |
| **Debugger** | Identifies and resolves issues based on test results |

## 🛠️ Tech Stack

- **Language:** Python 3.10
- **Frameworks:** Django 4.2, Streamlit 1.12
- **AI Integration:** OpenAI GPT models via LangChain
- **Testing:** pytest
- **Environment:** dotenv for configuration

## 📥 Installation

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/SWE599-Multi-Agent-LLM-Pipeline.git
   cd SWE599-Multi-Agent-LLM-Pipeline
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**
   
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

5. **Launch the application**
   ```bash
   streamlit run multiagent_django_streamlit.py
   ```

## 💡 How It Works

### Example Workflow

**User Input:**
> "Create a Streamlit app that visualizes a Django model."

**Step 1: Code Generation**
```python
import streamlit as st
from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    publication_date = models.DateField()

def main():
    st.title('Django Model Visualization')
    books = Book.objects.all()
    st.write(f'Number of books: {len(books)}')
    for book in books:
        st.write(f'Title: {book.title}')
        st.write(f'Author: {book.author}')
        st.write(f'Publication Date: {book.publication_date}')

if __name__ == '__main__':
    main()
```

**Step 2: Test Generation**
```python
import pytest
from unittest.mock import MagicMock, patch
from myapp.models import Book

def test_book_model():
    book = Book(title="Sample Book", author="John Doe", publication_date="2024-01-01")
    assert book.title == "Sample Book"
    assert book.author == "John Doe"
```

**Step 3: Debugging & Optimization**
The system automatically identifies and fixes issues in the generated code before delivering the final solution.

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License © 2025 **Umut Şanlı**