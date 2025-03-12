## **📖 SWE599 - Multi-Agent LLM Pipeline for Software Development**
### **An AI-powered system for automating Django & Streamlit application development**

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.12-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-🔗-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT-orange.svg)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-AI-yellow.svg)

---

## **📌 About This Repository**
This repository is part of my **SWE599 capstone project**, which explores the use of **Multi-Agent LLM Pipelines** for software development.

Currently, it contains a **single AI-powered pipeline:**
### `multiagent_django_streamlit.py`
💡 **An AI system that generates, tests, and debugs Django & Streamlit applications** using OpenAI's GPT models and LangChain.

In the future, additional pipelines may be added to expand the system's capabilities.

---

## **🚀 Current Working Pipeline: Django & Streamlit Multi-Agent Developer**
### **📌 Overview**
This pipeline helps developers **automate Django & Streamlit application creation** using AI.  
It consists of **three AI agents**, each handling a different task:

1️⃣ **Code Generator** → Generates Django & Streamlit applications based on user input  
2️⃣ **Test Writer** → Writes pytest unit tests for the generated code  
3️⃣ **Debugger** → Finds and fixes issues based on test results  

---

## **🛠 Tech Stack**
- **Programming Language:** Python 🐍
- **Frameworks:** Django, Streamlit
- **AI Models:** OpenAI GPT (via LangChain)
- **Libraries:** LangChain, OpenAI API, pytest, dotenv

---

## **📌 Installation**
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/SWE599-Multi-Agent-LLM-Pipeline.git
cd SWE599-Multi-Agent-LLM-Pipeline
```

### 2️⃣ Set Up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows, use: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Add Your OpenAI API Key
Create a `.env` file and add:
```bash
OPENAI_API_KEY=your-api-key-here
```

### 5️⃣ Run the Application
```bash
streamlit run multiagent_django_streamlit.py
```

---

## **📌 How It Works**
💬 **User Input:**  
> `"Create a Streamlit app that visualizes a Django model."`

📌 **AI Output (Generated Code):**
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

📌 **AI Output (Generated Test Code):**
```python
import pytest
from unittest.mock import MagicMock, patch
from myapp.models import Book

def test_book_model():
    book = Book(title="Sample Book", author="John Doe", publication_date="2024-01-01")
    assert book.title == "Sample Book"
    assert book.author == "John Doe"
```

📌 **AI Output (Debugged Code):**  
The AI reviews the generated code and tests, then fixes any issues before finalizing the output.

---

## 🤝 **Contributing**
Pull requests are welcome!  
1. Fork the repo 🍴  
2. Create a new branch (`git checkout -b feature-branch`)  
3. Commit your changes (`git commit -m "Added new feature"`)  
4. Push to the branch (`git push origin feature-branch`)  
5. Open a PR 🚀  

---

## 📜 **License**
MIT License © 2025 **Umut Şanlı**