import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI  # Using ChatOpenAI for chat models
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI Chat Model
llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # Change to "gpt-4" if needed
    openai_api_key=OPENAI_API_KEY
)

# 🔹 **Code Generator AI**
code_generator_prompt = PromptTemplate(
    input_variables=["user_request"],
    template=(
        "You are an AI Django & Streamlit developer. Your task is to write fully functional code in Python. "
        "Do not add explanations, only return the code. "
        "Here is what the user wants: {user_request}"
    ),
)
code_generator_chain = LLMChain(llm=llm, prompt=code_generator_prompt)

# 🔹 **Test Writer AI**
code_tester_prompt = PromptTemplate(
    input_variables=["generated_code"],
    template=(
        "You are a Python test writer. Your job is to write pytest unit tests for the following Django & Streamlit code. "
        "Ensure that the tests check functionality properly. "
        "Return only the test code. "
        "Code to test:\n\n{generated_code}"
    ),
)
code_tester_chain = LLMChain(llm=llm, prompt=code_tester_prompt)

# 🔹 **Debugger AI**
debugger_prompt = PromptTemplate(
    input_variables=["generated_code", "test_code"],
    template=(
        "You are a Python debugging assistant. Your task is to find bugs in the following Django & Streamlit code "
        "by analyzing the generated test cases. If you find issues, fix them. Return only the fixed version of the code. "
        "Original Code:\n\n{generated_code}\n\nTest Code:\n\n{test_code}"
    ),
)
debugger_chain = LLMChain(llm=llm, prompt=debugger_prompt)

# 🌍 **Streamlit UI**
st.title("🐍 Django & Streamlit Multi-Agent Developer")
st.write("This AI system generates, tests, and debugs Django + Streamlit applications.")

user_prompt = st.text_area("Describe your app:", "Create a Streamlit app that visualizes a Django model.")

if st.button("Generate Code"):
    if user_prompt.strip():
        with st.spinner("Generating Code..."):
            generated_code = code_generator_chain.run(user_request=user_prompt)
        
        with st.spinner("Writing Tests..."):
            test_code = code_tester_chain.run(generated_code=generated_code)
        
        with st.spinner("Debugging Code..."):
            debugged_code = debugger_chain.run(generated_code=generated_code, test_code=test_code)

        st.subheader("Generated Code:")
        st.code(generated_code.replace("```python", "").replace("```", "").strip(), language="python")

        st.subheader("Generated Test Code:")
        st.code(test_code.replace("```python", "").replace("```", "").strip(), language="python")

        st.subheader("Debugged Code:")
        st.code(debugged_code.replace("```python", "").replace("```", "").strip(), language="python")

    else:
        st.warning("Please enter a valid request.")
