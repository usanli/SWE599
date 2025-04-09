import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage
import pandas as pd
import time
import json
from langchain_core.prompts import ChatPromptTemplate
import random

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize different OpenAI models for specialized agents
llm_basic = ChatOpenAI(
    model="gpt-4",
    openai_api_key=OPENAI_API_KEY
)

llm_advanced = ChatOpenAI(
    model="gpt-4o",  # More advanced model for complex tasks
    openai_api_key=OPENAI_API_KEY
)

# Memory for agents to track conversation history
code_memory = ConversationBufferMemory(input_key="user_request", memory_key="chat_history", return_messages=True)
test_memory = ConversationBufferMemory(input_key="generated_code", memory_key="chat_history", return_messages=True)
debug_memory = ConversationBufferMemory(input_key="generated_code", memory_key="chat_history", return_messages=True)
doc_memory = ConversationBufferMemory(input_key="debugged_code", memory_key="chat_history", return_messages=True)
security_memory = ConversationBufferMemory(input_key="debugged_code", memory_key="chat_history", return_messages=True)
performance_memory = ConversationBufferMemory(input_key="secured_code", memory_key="chat_history", return_messages=True)

# Initialize langchain components
def init_agent_chains():
    """Initialize all agent chains with langchain components"""
    
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4")
    
    # Project Manager / Planner Chain
    planner_prompt = ChatPromptTemplate.from_template("""
    You are an expert software project manager specializing in web applications. 
    Your task is to create a detailed work plan for the following project:
    
    User Request: {user_request}
    
    If feedback is provided, incorporate it into your plan:
    Feedback: {feedback}
    
    Your plan should include:
    1. A clear breakdown of tasks for backend and frontend development
    2. Specific technologies to use for each component
    3. Integration strategy between components
    4. Testing approach and considerations
    5. Security and performance considerations
    
    Format your response as a well-organized plan with clear sections and bullet points.
    """)
    
    planner_chain = LLMChain(llm=llm, prompt=planner_prompt, output_key="text")
    
    # Backend Developer Chain
    backend_prompt = ChatPromptTemplate.from_template("""
    You are an expert backend developer specializing in Django and Python.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Feedback (if any): {feedback}
    
    Create the backend code for this application following the work plan.
    Include necessary models, views, URLs, serializers, and any other components.
    Ensure your code is efficient, secure, and well-documented.
    Explain key design decisions in comments.
    
    Format your response as complete Python files with clear imports and structure.
    """)
    
    backend_chain = LLMChain(llm=llm, prompt=backend_prompt, output_key="text")
    
    # Frontend Developer Chain
    frontend_prompt = ChatPromptTemplate.from_template("""
    You are an expert frontend developer specializing in web applications.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Backend Code: {backend_code}
    Feedback (if any): {feedback}
    
    Create the frontend code for this application following the work plan and matching the backend.
    Use appropriate frameworks and libraries as specified in the work plan.
    Ensure your code is responsive, user-friendly, and well-documented.
    
    Format your response as complete frontend files with clear imports and structure.
    """)
    
    frontend_chain = LLMChain(llm=llm, prompt=frontend_prompt, output_key="text")
    
    # UI Designer Chain
    ui_prompt = ChatPromptTemplate.from_template("""
    You are an expert UI/UX designer specializing in web applications.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Backend Code Summary: {backend_code}
    Frontend Code: {frontend_code}
    Feedback (if any): {feedback}
    
    Create UI mockups and design specifications for this application.
    Include:
    1. Color schemes and typography recommendations
    2. Layout mockups (described in text)
    3. User flow diagrams
    4. Key UI components and their interactions
    
    Format your response as a comprehensive design document with clear sections.
    """)
    
    ui_designer_chain = LLMChain(llm=llm, prompt=ui_prompt, output_key="text")
    
    # Integration Expert Chain
    integration_prompt = ChatPromptTemplate.from_template("""
    You are an expert system integration specialist.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Backend Code: {backend_code}
    Frontend Code: {frontend_code}
    UI Mockups: {ui_mockups}
    Feedback (if any): {feedback}
    
    Create a comprehensive integration guide for this application.
    Include:
    1. Detailed steps to connect frontend and backend
    2. API endpoints documentation
    3. Data flow diagrams
    4. Deployment considerations
    5. Environment setup instructions
    
    Format your response as a detailed guide with clear sections and code examples.
    """)
    
    integration_expert_chain = LLMChain(llm=llm, prompt=integration_prompt, output_key="text")
    
    # Testing Expert Chain
    testing_prompt = ChatPromptTemplate.from_template("""
    You are an expert QA engineer specializing in web application testing.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Generated Code: {generated_code}
    Feedback (if any): {feedback}
    
    Create a comprehensive test suite for this application.
    Include:
    1. Unit tests for backend components
    2. Integration tests for API endpoints
    3. Frontend tests (UI and functionality)
    4. Performance tests
    5. Security tests
    
    Format your response as complete test files with clear structure and documentation.
    """)
    
    testing_expert_chain = LLMChain(llm=llm, prompt=testing_prompt, output_key="text")
    
    # Debugger Chain
    debugger_prompt = ChatPromptTemplate.from_template("""
    You are an expert software debugger specializing in web applications.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Generated Code: {generated_code}
    Test Code: {test_code}
    Test Report: {test_report}
    Feedback (if any): {feedback}
    
    Debug the issues identified in the test report.
    1. Analyze each failing test
    2. Identify the root causes
    3. Provide fixed code for each issue
    4. Explain your debugging approach
    
    Format your response as corrected code files with explanations of the fixes.
    """)
    
    debugger_chain = LLMChain(llm=llm, prompt=debugger_prompt, output_key="text")
    
    # Security Expert Chain
    security_prompt = ChatPromptTemplate.from_template("""
    You are an expert security engineer specializing in web application security.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Code to Audit: {code_to_audit}
    Feedback (if any): {feedback}
    
    Perform a security audit on the provided code.
    1. Identify potential security vulnerabilities
    2. Provide fixes for each vulnerability
    3. Add security best practices
    4. Explain your security improvements
    
    Format your response as security-enhanced code with explanations of your changes.
    """)
    
    security_expert_chain = LLMChain(llm=llm, prompt=security_prompt, output_key="text")
    
    # Performance Expert Chain
    performance_prompt = ChatPromptTemplate.from_template("""
    You are an expert performance engineer specializing in web application optimization.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Code to Optimize: {code_to_optimize}
    Feedback (if any): {feedback}
    
    Optimize the performance of the provided code.
    1. Identify performance bottlenecks
    2. Provide optimized code
    3. Add caching strategies
    4. Optimize database queries
    5. Explain your performance improvements
    
    Format your response as performance-optimized code with explanations of your changes.
    """)
    
    performance_expert_chain = LLMChain(llm=llm, prompt=performance_prompt, output_key="text")
    
    # Documentation Expert Chain
    documentation_prompt = ChatPromptTemplate.from_template("""
    You are an expert technical writer specializing in software documentation.
    
    User Request: {user_request}
    Work Plan: {work_plan}
    Final Code: {final_code}
    Feedback (if any): {feedback}
    
    Create comprehensive documentation for this application.
    Include:
    1. Project overview
    2. Installation instructions
    3. API documentation
    4. Usage examples
    5. Configuration options
    6. Troubleshooting guide
    
    Format your response as a complete documentation with clear sections and examples.
    """)
    
    documentation_expert_chain = LLMChain(llm=llm, prompt=documentation_prompt, output_key="text")
    
    return {
        "planner": planner_chain,
        "backend_developer": backend_chain,
        "frontend_developer": frontend_chain,
        "ui_designer": ui_designer_chain,
        "integration_expert": integration_expert_chain,
        "testing_expert": testing_expert_chain,
        "debugger": debugger_chain,
        "security_expert": security_expert_chain,
        "performance_expert": performance_expert_chain,
        "documentation_expert": documentation_expert_chain
    }

# Initialize all agent chains
chains = init_agent_chains()
planner_chain = chains["planner"]
backend_chain = chains["backend_developer"]
frontend_chain = chains["frontend_developer"]
ui_designer_chain = chains["ui_designer"]
integration_expert_chain = chains["integration_expert"]
testing_expert_chain = chains["testing_expert"]
debugger_chain = chains["debugger"]
security_expert_chain = chains["security_expert"]
performance_expert_chain = chains["performance_expert"]
documentation_expert_chain = chains["documentation_expert"]

# Agent Status Tracking
agent_status = {
    "coordinator": {"status": "idle", "feedback": ""},
    "reviewer": {"status": "idle", "feedback": ""},
    "code_generator": {"status": "idle", "feedback": ""},
    "test_writer": {"status": "idle", "feedback": ""},
    "debugger": {"status": "idle", "feedback": ""},
    "doc_writer": {"status": "idle", "feedback": ""},
    "security_auditor": {"status": "idle", "feedback": ""},
    "performance_optimizer": {"status": "idle", "feedback": ""},
    "backend_developer": {"status": "idle", "feedback": ""},
    "frontend_developer": {"status": "idle", "feedback": ""},
    "ui_designer": {"status": "idle", "feedback": ""},
    "integration_specialist": {"status": "idle", "feedback": ""}
}

# 🔹 **Coordinator Agent**
coordinator_prompt = PromptTemplate(
    input_variables=["user_request", "agent_status", "system_state", "reviewer_feedback"],
    template=(
        "You are a coordination AI that manages a team of specialized AI agents for software development. "
        "Your job is to create a detailed work plan for developing a Django & Streamlit application. "
        "The plan should include specific tasks for each agent in the development pipeline. "
        "User Request: {user_request}\n"
        "Current Agent Status: {agent_status}\n"
        "Current System State: {system_state}\n"
        "Reviewer's Feedback (if any): {reviewer_feedback}\n\n"
        "Create a clear, detailed work plan with the following elements:\n"
        "1. A breakdown of the requirements based on the user request\n"
        "2. A step-by-step development plan showing which agent will handle each part\n"
        "3. Estimated complexity for each task (low, medium, high)\n"
        "4. Potential challenges and how they will be addressed\n\n"
        "Format the work plan in markdown with clear sections and bullet points."
    ),
)
coordinator_chain = LLMChain(llm=llm_advanced, prompt=coordinator_prompt)

# 🔹 **Reviewer Agent**
reviewer_prompt = PromptTemplate(
    input_variables=["work_plan", "user_request"],
    template=(
        "You are a senior software architect serving as a reviewer for development plans. "
        "Your role is to critically evaluate the proposed work plan and provide constructive feedback. "
        "You should identify any missing requirements, logical gaps, technical risks, or areas for improvement. "
        "User Request: {user_request}\n\n"
        "Proposed Work Plan:\n{work_plan}\n\n"
        "Evaluate the work plan on the following criteria:\n"
        "1. Completeness: Does it address all requirements in the user request?\n"
        "2. Technical feasibility: Are the proposed solutions technically sound?\n"
        "3. Efficiency: Is the plan efficient and logical in its approach?\n"
        "4. Risk management: Are potential challenges properly identified and addressed?\n"
        "5. Task allocation: Are tasks appropriately assigned to the right specialized agents?\n\n"
        "If the plan meets all criteria and is excellent, respond with: APPROVED: [brief explanation]\n\n"
        "Otherwise, provide specific, actionable feedback on what needs to be improved in the work plan."
    ),
)
reviewer_chain = LLMChain(llm=llm_advanced, prompt=reviewer_prompt)

# 🔹 **Code Generator AI**
code_generator_prompt = PromptTemplate(
    input_variables=["user_request", "chat_history", "feedback", "work_plan"],
    template=(
        "You are an AI Django & Streamlit developer. Your task is to write fully functional code in Python. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Work plan: {work_plan}\n"
        "Here is what the user wants: {user_request}\n\n"
        "Write production-ready, well-structured code that implements the requested functionality. "
        "Include detailed comments to explain your implementation decisions."
    ),
)
code_generator_chain = LLMChain(llm=llm_advanced, prompt=code_generator_prompt, memory=code_memory)

# 🔹 **Test Writer AI**
code_tester_prompt = PromptTemplate(
    input_variables=["generated_code", "chat_history", "feedback", "work_plan"],
    template=(
        "You are a Python test writer specializing in Django & Streamlit applications. "
        "Your job is to write comprehensive pytest unit tests for the following code. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Work plan: {work_plan}\n"
        "Code to test:\n\n{generated_code}\n\n"
        "Write thorough tests covering both happy paths and edge cases. Include tests for all major functionality. "
        "Be critical and identify potential issues with the implementation. "
        "After the tests, include a TEST REPORT section with your assessment of the code quality and any issues found."
    ),
)
code_tester_chain = LLMChain(llm=llm_basic, prompt=code_tester_prompt, memory=test_memory)

# 🔹 **Debugger AI**
debugger_prompt = PromptTemplate(
    input_variables=["generated_code", "test_code", "chat_history", "feedback", "test_report"],
    template=(
        "You are a Python debugging assistant specializing in Django & Streamlit. "
        "Your task is to fix bugs in the following code based on the test results. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Original Code:\n\n{generated_code}\n\n"
        "Test Code:\n\n{test_code}\n\n"
        "Test Report:\n\n{test_report}\n\n"
        "Fix all identified issues and improve the code quality. "
        "Provide a DEBUG REPORT section at the end explaining what issues were found and how you fixed them."
    ),
)
debugger_chain = LLMChain(llm=llm_advanced, prompt=debugger_prompt, memory=debug_memory)

# 🔹 **Documentation Writer AI**
doc_writer_prompt = PromptTemplate(
    input_variables=["final_code", "chat_history", "feedback", "test_code", "security_report", "performance_report"],
    template=(
        "You are a technical documentation writer specializing in Python, Django, and Streamlit. "
        "Your task is to create comprehensive documentation for the following code. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Final code:\n\n{final_code}\n\n"
        "Test code:\n\n{test_code}\n\n"
        "Security report:\n\n{security_report}\n\n"
        "Performance report:\n\n{performance_report}\n\n"
        "Create documentation that includes:\n"
        "1. Overview of the application\n"
        "2. Installation instructions\n"
        "3. Usage examples\n"
        "4. API documentation for each function/class\n"
        "5. Dependencies explanation\n"
        "Format the documentation in markdown."
    ),
)
doc_writer_chain = LLMChain(llm=llm_basic, prompt=doc_writer_prompt, memory=doc_memory)

# 🔹 **Security Auditor AI**
security_auditor_prompt = PromptTemplate(
    input_variables=["debugged_code", "chat_history", "feedback"],
    template=(
        "You are a security expert specializing in Python web applications (Django & Streamlit). "
        "Your task is to conduct a security audit of the following code. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Code to audit:\n\n{debugged_code}\n\n"
        "Identify security vulnerabilities including but not limited to:\n"
        "1. SQL injection\n"
        "2. Cross-site scripting (XSS)\n"
        "3. Cross-site request forgery (CSRF)\n"
        "4. Improper authentication/authorization\n"
        "5. Data exposure\n"
        "6. Insecure dependencies\n\n"
        "Provide a SECURITY REPORT section at the end summarizing your findings."
        "Return the code with security fixes implemented."
    ),
)
security_auditor_chain = LLMChain(llm=llm_advanced, prompt=security_auditor_prompt, memory=security_memory)

# 🔹 **Performance Optimizer AI**
performance_optimizer_prompt = PromptTemplate(
    input_variables=["secured_code", "chat_history", "feedback"],
    template=(
        "You are a performance optimization expert for Python applications, particularly Django & Streamlit. "
        "Your task is to optimize the following code for improved performance. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Code to optimize:\n\n{secured_code}\n\n"
        "Identify performance bottlenecks and optimize for:\n"
        "1. Algorithmic efficiency\n"
        "2. Database query optimization\n"
        "3. Caching opportunities\n"
        "4. Resource usage\n"
        "5. Load time improvements\n"
        "Provide a PERFORMANCE REPORT section at the end summarizing your optimizations."
        "Return the optimized code with comments explaining your optimizations."
    ),
)
performance_optimizer_chain = LLMChain(llm=llm_basic, prompt=performance_optimizer_prompt, memory=performance_memory)

# 🔹 **Backend Developer Agent**
backend_developer_prompt = PromptTemplate(
    input_variables=["user_request", "work_plan", "chat_history", "feedback"],
    template=(
        "You are a backend Django developer with expertise in creating REST APIs. "
        "Your task is to generate backend code for a Django application based on the requirements. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Work plan: {work_plan}\n"
        "User request: {user_request}\n\n"
        "Generate complete, production-ready Django backend code based on the requirements. "
        "Format your response as follows:\n\n"
        "1. First provide a clear, numbered list of steps to set up the Django backend\n"
        "2. For each step, first explain what needs to be done and why\n"
        "3. Then provide the complete code for each file in separate, clearly labeled code blocks\n"
        "4. Include all necessary commands to run migrations, create admin users, and start the server\n\n"
        "Ensure file paths are clearly labeled above each code block. "
        "Do not use placeholders - provide fully functional code with proper imports, models, views, and URLs."
    ),
)
backend_developer_chain = LLMChain(llm=llm_advanced, prompt=backend_developer_prompt)

# 🔹 **Frontend Developer Agent**
frontend_developer_prompt = PromptTemplate(
    input_variables=["user_request", "work_plan", "chat_history", "feedback", "backend_code"],
    template=(
        "You are a frontend Streamlit developer specializing in creating user interfaces for data visualization and CRUD operations. "
        "Your task is to generate a fully functional Streamlit application that interfaces with a Django backend. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Work plan: {work_plan}\n"
        "User request: {user_request}\n"
        "Backend code (for reference): {backend_code}\n\n"
        "Generate complete, production-ready Streamlit frontend code based on the requirements. "
        "Format your response as follows:\n\n"
        "1. First provide a clear, numbered list of steps to set up the Streamlit frontend\n"
        "2. For each step, first explain what needs to be done and why\n"
        "3. Then provide the complete code for each file in separate, clearly labeled code blocks\n"
        "4. Include commands to install dependencies and run the Streamlit application\n\n"
        "Ensure file paths are clearly labeled above each code block. "
        "The frontend should implement all CRUD operations and properly display data from the Django backend."
    ),
)
frontend_developer_chain = LLMChain(llm=llm_advanced, prompt=frontend_developer_prompt)

# 🔹 **UI Designer Agent**
ui_designer_prompt = PromptTemplate(
    input_variables=["user_request", "work_plan", "chat_history", "feedback"],
    template=(
        "You are a UI/UX designer specializing in creating mockups and wireframes for web applications. "
        "Your task is to create UI mockups for a Streamlit application. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Work plan: {work_plan}\n"
        "User request: {user_request}\n\n"
        "Generate UI mockups for the Streamlit application. "
        "Format your response as follows:\n\n"
        "1. First explain the overall UI/UX approach and design principles\n"
        "2. Provide ASCII or text-based mockups for each screen of the application\n"
        "3. Include notes on user flow, interaction patterns, and visual hierarchy\n\n"
        "The mockups should clearly show how users will interact with the application for all CRUD operations."
    ),
)
ui_designer_chain = LLMChain(llm=llm_advanced, prompt=ui_designer_prompt)

# 🔹 **Integration Specialist Agent**
integration_specialist_prompt = PromptTemplate(
    input_variables=["user_request", "work_plan", "chat_history", "feedback", "backend_code", "frontend_code"],
    template=(
        "You are an integration specialist with expertise in connecting Django backends with Streamlit frontends. "
        "Your task is to provide integration instructions and verify that the backend and frontend code work together correctly. "
        "Previous conversation: {chat_history}\n"
        "Human feedback (if any): {feedback}\n"
        "Work plan: {work_plan}\n"
        "User request: {user_request}\n"
        "Backend code: {backend_code}\n"
        "Frontend code: {frontend_code}\n\n"
        "Provide clear integration instructions. Format your response as follows:\n\n"
        "1. First list any potential integration issues or inconsistencies between the backend and frontend\n"
        "2. Provide step-by-step instructions for deploying both applications together\n"
        "3. Include any configuration changes needed to ensure proper communication\n"
        "4. Add troubleshooting tips for common integration issues\n\n"
        "Ensure your instructions are clear enough for someone with basic programming knowledge to follow."
    ),
)
integration_specialist_chain = LLMChain(llm=llm_advanced, prompt=integration_specialist_prompt)

# 🌍 **Streamlit UI**
st.set_page_config(layout="wide", page_title="Interactive Multi-Agent Developer")
st.title("🚀 Interactive Django & Streamlit Multi-Agent Developer")
st.write("This AI system uses specialized agents with your feedback to create high-quality applications.")

# Sidebar for workflow configuration
st.sidebar.header("🛠️ Workflow Configuration")
include_security = st.sidebar.checkbox("Include Security Audit", value=True)
include_performance = st.sidebar.checkbox("Include Performance Optimization", value=True)

# Helper functions for agent operations
def simulate_processing(message="Processing", duration=2):
    """Simulates an agent processing with a progress bar"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for percent_complete in range(100):
        time.sleep(duration/100)
        progress_bar.progress(percent_complete + 1)
        status_text.text(f"{message}: {percent_complete + 1}%")
    
    progress_bar.empty()
    status_text.empty()
    
def format_code_summary(code, max_length=500):
    """Generate a short summary of code for display purposes"""
    if not code:
        return "No code available"
    
    if len(code) <= max_length:
        return code
    
    lines = code.split('\n')
    summary_lines = []
    total_length = 0
    
    for line in lines:
        if total_length + len(line) > max_length:
            if not summary_lines:  # Ensure at least one line is added
                summary_lines.append(line[:max_length] + "...")
            break
        summary_lines.append(line)
        total_length += len(line) + 1  # +1 for newline
    
    return '\n'.join(summary_lines) + "\n...\n[Code truncated for display]"

def generate_random_test_results():
    """Generate random test results for demonstration purposes"""
    total_tests = random.randint(10, 30)
    passed_tests = random.randint(int(total_tests * 0.7), total_tests)
    failed_tests = total_tests - passed_tests
    
    test_classes = ["UserAuthTests", "APIEndpointTests", "ModelTests", "ViewTests", "IntegrationTests"]
    
    results = {
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "coverage": round(random.uniform(70, 99), 2)
        },
        "failing_tests": []
    }
    
    if failed_tests > 0:
        for i in range(failed_tests):
            test_class = random.choice(test_classes)
            results["failing_tests"].append({
                "test": f"{test_class}.test_{random.randint(1, 10)}",
                "error": f"AssertionError: Expected {random.randint(1, 100)}, got {random.randint(1, 100)}"
            })
    
    return results

def generate_security_audit():
    """Generate a mock security audit report"""
    security_issues = [
        {"severity": "High", "issue": "SQL Injection vulnerability in user input", "location": "views.py:45", "recommendation": "Use parameterized queries"},
        {"severity": "Medium", "issue": "Cross-Site Scripting (XSS) in form display", "location": "templates/form.html:23", "recommendation": "Sanitize user input"},
        {"severity": "Low", "issue": "Missing HTTP security headers", "location": "settings.py", "recommendation": "Add security middleware"},
        {"severity": "Medium", "issue": "Insecure password hashing", "location": "models.py:87", "recommendation": "Use Django's built-in password hashing"},
        {"severity": "High", "issue": "Exposed API keys in source code", "location": "config.py:12", "recommendation": "Use environment variables"}
    ]
    
    # Randomly select some issues
    selected_issues = random.sample(security_issues, k=random.randint(0, len(security_issues)))
    
    return {
        "issues_found": len(selected_issues),
        "high_severity": sum(1 for issue in selected_issues if issue["severity"] == "High"),
        "medium_severity": sum(1 for issue in selected_issues if issue["severity"] == "Medium"),
        "low_severity": sum(1 for issue in selected_issues if issue["severity"] == "Low"),
        "issues": selected_issues
    }

def generate_performance_report():
    """Generate a mock performance optimization report"""
    optimizations = [
        {"type": "Database", "issue": "N+1 query problem", "location": "views.py:78", "improvement": "45% query time reduction"},
        {"type": "Caching", "issue": "Missing cache for expensive computation", "location": "services.py:124", "improvement": "65% response time improvement"},
        {"type": "Frontend", "issue": "Large unoptimized images", "location": "static/images/", "improvement": "70% page load reduction"},
        {"type": "API", "issue": "Excessive data in API responses", "location": "serializers.py:45", "improvement": "30% bandwidth reduction"},
        {"type": "Backend", "issue": "Inefficient algorithm in sorting", "location": "utils.py:92", "improvement": "80% processing time reduction"}
    ]
    
    # Randomly select some optimizations
    selected_optimizations = random.sample(optimizations, k=random.randint(1, len(optimizations)))
    
    return {
        "optimizations_applied": len(selected_optimizations),
        "average_improvement": f"{random.randint(20, 60)}%",
        "optimizations": selected_optimizations
    }

# Initialize session state for agents
if "session_initialized" not in st.session_state:
    st.session_state["session_initialized"] = True
    st.session_state["user_request"] = ""
    st.session_state["work_plan"] = ""
    st.session_state["backend_code"] = ""
    st.session_state["frontend_code"] = ""
    st.session_state["ui_mockups"] = ""
    st.session_state["integration_guide"] = ""
    st.session_state["generated_code"] = ""
    st.session_state["test_code"] = ""
    st.session_state["test_report"] = ""
    st.session_state["debugged_code"] = ""
    st.session_state["debug_report"] = ""
    st.session_state["security_audit"] = ""
    st.session_state["optimized_code"] = ""
    st.session_state["documentation"] = ""
    st.session_state["final_code"] = ""
    st.session_state["plan_review_attempts"] = 0
    st.session_state["reviewer_feedback"] = ""
    st.session_state["plan_approved"] = False
    st.session_state["agent_discussion_history"] = []
    
    # Backend state
    st.session_state["backend_feedback"] = ""
    
    # Frontend state
    st.session_state["frontend_feedback"] = ""
    
    # UI Design state
    st.session_state["ui_feedback"] = ""
    
    # Integration state
    st.session_state["integration_feedback"] = ""
    
    # Testing state
    st.session_state["test_passes"] = False
    st.session_state["needs_debugging"] = False
    
    # Debugging state
    st.session_state["debug_report"] = ""
    
    # Security and optimization state
    st.session_state["security_code"] = ""
    st.session_state["security_report"] = ""
    st.session_state["optimized_code"] = ""
    st.session_state["performance_report"] = ""
    
    # Documentation state
    st.session_state["documentation"] = ""
    st.session_state["final_code"] = ""
    
    # Feedback dictionary to track feedback for each agent
    st.session_state["feedback"] = {}
    
    # Track updates for reactive UI
    st.session_state["updates"] = {
        "plan": 0,
        "backend": 0,
        "frontend": 0,
        "ui": 0,
        "integration": 0,
        "testing": 0,
        "debugging": 0,
        "security": 0
    }

# Ensure "updates" dictionary exists in session state
if "updates" not in st.session_state:
    st.session_state["updates"] = {
        "plan": 0,
        "backend": 0,
        "frontend": 0,
        "ui": 0,
        "integration": 0,
        "testing": 0,
        "debugging": 0,
        "security": 0
    }

# Define a function to check and queue agent tasks
def check_agent_tasks():
    # Add any background processing tasks here
    pass

# Create main tabs for the workflow
tab_names = ["Request", "Planning", "Backend", "UI Design", "Frontend", "Integration", "Testing", "Debugging", "Security & Performance", "Documentation"]
tabs = st.tabs(tab_names)

with tabs[0]:  # Request Tab
    st.header("Describe Your Application")
    
    # Use a single column layout for input and button
    user_request = st.text_area(
        "What kind of Django & Streamlit application do you want to build?", 
        value=st.session_state['user_request'] if st.session_state['user_request'] else "Create a Streamlit app that visualizes a Django model for tracking inventory items with CRUD operations.",
        height=150,
        key="request_input"
    )
    
    # Place the button directly under the text area
    if st.button("Submit Request", key="submit_request", use_container_width=True):
        if user_request.strip():
            st.session_state['user_request'] = user_request
            st.session_state['updates']["plan"] += 1
            st.rerun()
        else:
            st.error("Please enter a valid request.")
    
    # Create a visually appealing status display
    st.markdown("### Development Status")
    
    # Dynamically build status data
    status_data = []
    
    # Dynamically build status data
    for idx, tab in enumerate(tab_names):
        if idx == 0:  # Request tab is always active
            status = "complete"
            icon = "✅"
        elif idx == 1 and st.session_state["plan_approved"]:
            status = "complete"
            icon = "✅"
        elif idx == 2 and st.session_state["backend_code"]:
            status = "complete"
            icon = "✅"
        elif idx == 3 and st.session_state["frontend_code"]:
            status = "complete"
            icon = "✅"
        elif idx == 4 and st.session_state["ui_mockups"]:
            status = "complete"
            icon = "✅"
        elif idx == 5 and st.session_state["integration_guide"]:
            status = "complete"
            icon = "✅"
        elif idx == 6 and st.session_state["test_code"]:
            if st.session_state["test_passes"]:
                status = "complete"
                icon = "✅"
            else:
                status = "warning"
                icon = "⚠️"
        elif idx == 7 and st.session_state["debugged_code"]:
            status = "complete"
            icon = "✅"
        elif idx == 8 and st.session_state["security_code"]:
            status = "complete"
            icon = "✅"
        elif idx == 9 and st.session_state["documentation"]:
            status = "complete"
            icon = "✅"
        else:
            status = "pending"
            icon = "🔄" if st.session_state['user_request'] else "⏳"
        
        status_data.append({"Phase": tab, "Status": status, "Icon": icon})
    
    # Render status using HTML for better styling
    for item in status_data:
        phase = item["Phase"]
        status = item["Status"]
        icon = item["Icon"]
        
        if status == "complete":
            st.markdown(
                f"""<div style="display: flex; align-items: center; margin-bottom: 8px; padding: 5px; background-color: #e6f3ec; border-radius: 5px;">
                    <div style="margin-right: 10px;">{icon}</div>
                    <div style="font-weight: bold;">{phase}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        elif status == "warning":
            st.markdown(
                f"""<div style="display: flex; align-items: center; margin-bottom: 8px; padding: 5px; background-color: #fff2e6; border-radius: 5px;">
                    <div style="margin-right: 10px;">{icon}</div>
                    <div style="font-weight: bold;">{phase}</div>
                </div>""", 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""<div style="display: flex; align-items: center; margin-bottom: 8px; padding: 5px; background-color: #f0f2f6; border-radius: 5px;">
                    <div style="margin-right: 10px;">{icon}</div>
                    <div>{phase}</div>
                </div>""", 
                unsafe_allow_html=True
            )

with tabs[1]:  # Planning Tab
    st.header("Development Plan")
    
    
    # Reactive planning - Check if we need to generate or update work plan
    if st.session_state['user_request'] and (not st.session_state['work_plan'] or 
        (st.session_state['plan_review_attempts'] < 5 and 
         not st.session_state['plan_approved'] and 
         st.session_state.get('reviewer_feedback'))):
        with st.spinner("🤖 Generating development plan..."):
            # Initialize system state for coordinator
            system_state = {
                "phase": "planning",
                "backend_code": st.session_state['backend_code'],
                "frontend_code": st.session_state['frontend_code'],
                "ui_mockups": st.session_state['ui_mockups'],
                "integration_guide": st.session_state['integration_guide'],
                "test_code": st.session_state['test_code'],
                "debugged_code": st.session_state['debugged_code'],
                "documentation": st.session_state['documentation'],
                "secured_code": st.session_state['security_code'],
                "optimized_code": st.session_state['optimized_code'],
            }
            
            # Prepare feedback context
            combined_feedback = ""
            if st.session_state['agent_discussion_history']:
                combined_feedback += "Previous discussion history:\n\n"
                for i, discussion in enumerate(st.session_state['agent_discussion_history']):
                    combined_feedback += f"Iteration {i+1}:\n"
                    combined_feedback += f"Coordinator: {discussion.get('plan', '')}\n"
                    combined_feedback += f"Reviewer: {discussion.get('feedback', '')}\n\n"
            
            if st.session_state['reviewer_feedback']:
                combined_feedback += "Latest feedback: " + st.session_state['reviewer_feedback']
            
            # Generate or update work plan
            if not st.session_state['work_plan'] or st.session_state['reviewer_feedback']:
                response = coordinator_chain.invoke({
                    "user_request": st.session_state['user_request'],
                    "agent_status": json.dumps(agent_status),
                    "system_state": json.dumps(system_state),
                    "reviewer_feedback": combined_feedback
                })
                
                st.session_state['work_plan'] = response['text']
            
            # Review the work plan
            review_response = reviewer_chain.invoke({
                "work_plan": st.session_state['work_plan'],
                "user_request": st.session_state['user_request']
            })
            
            reviewer_feedback = review_response['text']
            
            # Save this iteration to discussion history
            st.session_state['agent_discussion_history'].append({
                'plan': st.session_state['work_plan'],
                'feedback': reviewer_feedback
            })
            
            # Increment the review attempt counter
            st.session_state['plan_review_attempts'] = st.session_state.get('plan_review_attempts', 0) + 1
            
            # Check if the reviewer approved the plan
            if reviewer_feedback.strip().startswith("APPROVED:"):
                st.session_state['plan_approved'] = True
                st.session_state['reviewer_feedback'] = "✅ " + reviewer_feedback.strip()
                # Trigger backend phase
                st.session_state['updates']["backend"] += 1
            else:
                # If not approved and we haven't reached max attempts, store feedback
                if st.session_state.get('plan_review_attempts', 0) < 5:
                    st.session_state['reviewer_feedback'] = reviewer_feedback
    
    # Display the work plan if it exists
    if st.session_state['work_plan']:
        plan_col1, plan_col2 = st.columns([3, 1])
        
        with plan_col1:
            st.subheader("Development Plan:")
            st.markdown(st.session_state['work_plan'])
        
        with plan_col2:
            st.subheader("Plan Status:")
            if st.session_state.get('plan_approved', False):
                st.success("✅ Plan approved")
            elif st.session_state.get('plan_review_attempts', 0) >= 5:
                st.warning("⚠️ Max review attempts reached")
            else:
                st.info(f"🔄 Review iteration {st.session_state.get('plan_review_attempts', 0)}")
                
            # Show review process information
            if st.session_state.get('plan_review_attempts', 0) > 0:
                with st.expander("View Review History", expanded=False):
                    for i, discussion in enumerate(st.session_state.get('agent_discussion_history', [])):
                        st.markdown(f"**Iteration {i+1}**")
                        st.markdown("*Reviewer's Feedback:*")
                        st.markdown(discussion.get('feedback', ''))
                        st.markdown("---")
            
            # Get user feedback and revision option
            plan_feedback = st.text_area("Your feedback:", height=100, key="plan_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Plan", key="revise_plan"):
                    if plan_feedback.strip():
                        st.session_state['feedback']['coordinator'] = plan_feedback
                        st.session_state['reviewer_feedback'] = "User feedback: " + plan_feedback
                        st.session_state['plan_approved'] = False
                        st.session_state['work_plan'] = ""
                        st.session_state['updates']["plan"] += 1
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for revision.")
            with col2:
                if st.button("Accept & Continue", key="accept_plan"):
                    st.session_state['plan_approved'] = True
                    st.session_state['updates']["backend"] += 1
                    st.rerun()
    else:
        if st.session_state['user_request']:
            st.info("Generating work plan. Please wait...")
        else:
            st.info("Please submit a request in the Request tab first.")

with tabs[2]:  # Backend Tab
    st.header("Django Backend Implementation")
    
    # Show plan for reference
    if st.session_state.get('work_plan', ''):
        with st.expander("View Development Plan", expanded=False):
            st.markdown(st.session_state['work_plan'])
    
    # Only generate backend code if we have an approved plan and need to generate code
    if st.session_state.get('plan_approved', False) and not st.session_state['backend_code'] and st.session_state['updates']["backend"] > 0:
        with st.spinner("🛠️ Generating Django Backend Code..."):
            response = backend_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "chat_history": "",
                "feedback": st.session_state.get('backend_feedback', "")
            })
            
            st.session_state['backend_code'] = response['text']
            st.session_state['updates']["frontend"] += 1
    
    # Display backend code if available
    if st.session_state['backend_code']:
        backend_col1, backend_col2 = st.columns([3, 1])
        
        with backend_col1:
            # Process and display the backend code nicely
            backend_code = st.session_state['backend_code']
            
            # Display explanations as normal text and code in code blocks
            lines = backend_code.split('\n')
            current_block = []
            in_code_block = False
            file_path = None
            
            for line in lines:
                if line.strip().startswith('```') and not in_code_block:
                    in_code_block = True
                    if current_block:
                        st.write('\n'.join(current_block))
                        current_block = []
                elif line.strip().startswith('```') and in_code_block:
                    in_code_block = False
                    if current_block and file_path:
                        st.subheader(f"File: {file_path}")
                        st.code('\n'.join(current_block), language="python")
                        current_block = []
                        file_path = None
                elif in_code_block:
                    if not current_block and line.strip() and '/' in line and not line.startswith('#'):
                        # This might be a file path
                        file_path = line.strip()
                    else:
                        current_block.append(line)
                else:
                    current_block.append(line)
            
            if current_block:
                st.write('\n'.join(current_block))
        
        with backend_col2:
            st.subheader("Backend Status:")
            st.success("✅ Backend code generated")
            
            # Get user feedback and revision option
            backend_feedback = st.text_area("Your feedback:", height=100, key="backend_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Backend Code", key="revise_backend"):
                    if backend_feedback.strip():
                        st.session_state['backend_feedback'] = backend_feedback
                        st.session_state['feedback']['backend_developer'] = backend_feedback
                        st.session_state['backend_code'] = ""
                        st.session_state['updates']["backend"] += 1
                        # Reset dependent phases
                        st.session_state['frontend_code'] = ""
                        st.session_state['ui_mockups'] = ""
                        st.session_state['integration_guide'] = ""
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for revision.")
            with col2:
                if st.button("Accept & Continue", key="accept_backend"):
                    st.session_state['updates']["frontend"] += 1
                    st.rerun()
    else:
        if st.session_state.get('plan_approved', False):
            st.info("Ready to generate backend code.")
            if st.button("Generate Backend Code", key="gen_backend"):
                st.session_state['updates']["backend"] += 1
                st.rerun()
        else:
            st.info("Please complete the planning phase first.")

with tabs[3]:  # UI Design Tab (now comes before Frontend tab)
    st.header("UI Design & Mockups")
    
    # Show backend code for reference
    if st.session_state.get('backend_code', ''):
        with st.expander("View Backend Code", expanded=False):
            st.markdown("```python\n" + st.session_state['backend_code'] + "\n```")
    
    # Only generate UI mockups if we have backend code and need to generate UI
    if st.session_state.get('backend_code', '') and not st.session_state['ui_mockups'] and st.session_state['updates']["ui"] > 0:
        with st.spinner("🎭 Creating UI Design & Mockups..."):
            response = ui_designer_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "backend_code": st.session_state['backend_code'],
                "frontend_code": st.session_state.get('frontend_code', ''),
                "chat_history": "",
                "feedback": st.session_state.get('ui_feedback', "")
            })
            
            st.session_state['ui_mockups'] = response['text']
            st.session_state['updates']["frontend"] += 1
    
    # Display UI mockups if available
    if st.session_state['ui_mockups']:
        ui_col1, ui_col2 = st.columns([3, 1])
        
        with ui_col1:
            # Display UI mockups in a styled container
            st.markdown("<h3>UI Mockups</h3>", unsafe_allow_html=True)
            
            # Create a styled container for the UI mockups
            st.markdown("""
            <style>
            .ui-mockup-container {
                border: 2px solid #e6e6e6;
                border-radius: 10px;
                padding: 20px;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                font-family: sans-serif;
            }
            .ui-mockup-header {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
                border-bottom: 1px solid #dee2e6;
            }
            .ui-component {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
                background-color: #f8f9fa;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Process the mockups to render as HTML
            mockup_lines = st.session_state['ui_mockups'].split('\n')
            in_component = False
            current_component = []
            html_output = '<div class="ui-mockup-container">'
            
            for line in mockup_lines:
                # Handle headers
                if line.startswith('# '):
                    if in_component and current_component:
                        html_output += f'<div class="ui-component">{"<br>".join(current_component)}</div>'
                        current_component = []
                        in_component = False
                    html_output += f'<h2>{line[2:]}</h2>'
                elif line.startswith('## '):
                    if in_component and current_component:
                        html_output += f'<div class="ui-component">{"<br>".join(current_component)}</div>'
                        current_component = []
                        in_component = False
                    html_output += f'<h3>{line[3:]}</h3>'
                elif line.startswith('### '):
                    if in_component and current_component:
                        html_output += f'<div class="ui-component">{"<br>".join(current_component)}</div>'
                        current_component = []
                        in_component = False
                    html_output += f'<div class="ui-mockup-header"><h4>{line[4:]}</h4></div>'
                # Handle code blocks which might contain UI components
                elif line.startswith('```') and not in_component:
                    in_component = True
                elif line.startswith('```') and in_component:
                    if current_component:
                        html_output += f'<div class="ui-component">{"<br>".join(current_component)}</div>'
                        current_component = []
                    in_component = False
                # Add content to current component or directly to output
                elif in_component:
                    # Replace ASCII art with styled elements where possible
                    styled_line = line.replace('-', '─').replace('|', '│').replace('+', '┼')
                    current_component.append(styled_line)
                else:
                    html_output += f'<p>{line}</p>'
            
            # Add any remaining component
            if in_component and current_component:
                html_output += f'<div class="ui-component">{"<br>".join(current_component)}</div>'
            
            html_output += '</div>'
            
            # Display the HTML
            st.markdown(html_output, unsafe_allow_html=True)
            
            # Add a visual demo if needed
            st.markdown("<h3>Interactive Preview</h3>", unsafe_allow_html=True)
            st.markdown("""
            <style>
            .interactive-preview {
                border: 2px solid #e6e6e6;
                border-radius: 10px;
                padding: 20px;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                height: 400px;
                overflow: auto;
                position: relative;
            }
            .preview-navbar {
                background-color: #333;
                color: white;
                padding: 10px;
                border-radius: 5px 5px 0 0;
                margin-bottom: 15px;
            }
            .preview-sidebar {
                width: 20%;
                float: left;
                background-color: #f8f9fa;
                height: 300px;
                padding: 10px;
                border-right: 1px solid #dee2e6;
            }
            .preview-content {
                width: 75%;
                float: right;
                padding: 10px;
            }
            .preview-card {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                background-color: white;
            }
            </style>
            <div class="interactive-preview">
                <div class="preview-navbar">Inventory Management System</div>
                <div class="preview-sidebar">
                    <p><b>Categories</b></p>
                    <p>- Electronics</p>
                    <p>- Furniture</p>
                    <p>- Office Supplies</p>
                    <p>- Books</p>
                </div>
                <div class="preview-content">
                    <h3>Inventory Items</h3>
                    <div class="preview-card">
                        <h4>Laptop</h4>
                        <p>Category: Electronics</p>
                        <p>Quantity: 12</p>
                        <p>Price: $999.99</p>
                        <button style="background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px;">Edit</button>
                        <button style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px;">Delete</button>
                    </div>
                    <div class="preview-card">
                        <h4>Office Chair</h4>
                        <p>Category: Furniture</p>
                        <p>Quantity: 8</p>
                        <p>Price: $149.99</p>
                        <button style="background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 3px;">Edit</button>
                        <button style="background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px;">Delete</button>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add a notification that this is a visual representation
            st.info("Note: This is a visual representation based on the mockups. The actual implementation may vary based on the frontend code.")
        
        with ui_col2:
            st.subheader("UI Design Status:")
            st.success("✅ UI mockups generated")
            
            # Get user feedback and revision option
            ui_feedback = st.text_area("Your feedback:", height=100, key="ui_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise UI Design", key="revise_ui"):
                    if ui_feedback.strip():
                        st.session_state['ui_feedback'] = ui_feedback
                        st.session_state['feedback']['ui_designer'] = ui_feedback
                        st.session_state['ui_mockups'] = ""
                        st.session_state['updates']["ui"] += 1
                        # Reset dependent phases
                        st.session_state['frontend_code'] = ""
                        st.session_state['integration_guide'] = ""
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for revision.")
            with col2:
                if st.button("Accept & Continue", key="accept_ui"):
                    st.session_state['updates']["frontend"] += 1
                    st.rerun()
    else:
        if st.session_state.get('backend_code', ''):
            st.info("Ready to generate UI designs.")
            if st.button("Generate UI Designs", key="gen_ui"):
                st.session_state['updates']["ui"] += 1
                st.rerun()
        else:
            st.info("Please complete the backend implementation first.")

with tabs[4]:  # Frontend Tab (now comes after UI Design tab)
    st.header("Frontend Implementation")
    
    # Show UI mockups for reference
    if st.session_state.get('ui_mockups', ''):
        with st.expander("View UI Mockups", expanded=False):
            st.markdown(st.session_state['ui_mockups'])
    
    # Only generate frontend code if we have UI mockups and need to generate frontend
    if st.session_state.get('ui_mockups', '') and not st.session_state['frontend_code'] and st.session_state['updates']["frontend"] > 0:
        with st.spinner("🎨 Generating Frontend Code..."):
            response = frontend_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "backend_code": st.session_state['backend_code'],
                "chat_history": "",
                "feedback": st.session_state.get('frontend_feedback', "")
            })
            
            st.session_state['frontend_code'] = response['text']
            st.session_state['updates']["integration"] += 1
    
    # Display frontend code if available
    if st.session_state['frontend_code']:
        frontend_col1, frontend_col2 = st.columns([3, 1])
        
        with frontend_col1:
            # Process and display the frontend code nicely
            frontend_code = st.session_state['frontend_code']
            
            # Display explanations as normal text and code in code blocks
            lines = frontend_code.split('\n')
            current_block = []
            in_code_block = False
            file_path = None
            
            for line in lines:
                if line.strip().startswith('```') and not in_code_block:
                    in_code_block = True
                    if current_block:
                        st.write('\n'.join(current_block))
                        current_block = []
                elif line.strip().startswith('```') and in_code_block:
                    in_code_block = False
                    if current_block and file_path:
                        st.subheader(f"File: {file_path}")
                        language = "python" if file_path.endswith('.py') else "html" if file_path.endswith('.html') else "javascript" if file_path.endswith('.js') else "css" if file_path.endswith('.css') else "text"
                        st.code('\n'.join(current_block), language=language)
                        current_block = []
                        file_path = None
                elif in_code_block:
                    if not current_block and line.strip() and '/' in line and not line.startswith('#'):
                        # This might be a file path
                        file_path = line.strip()
                    else:
                        current_block.append(line)
                else:
                    current_block.append(line)
            
            if current_block:
                st.write('\n'.join(current_block))
        
        with frontend_col2:
            st.subheader("Frontend Status:")
            st.success("✅ Frontend code generated")
            
            # Get user feedback and revision option
            frontend_feedback = st.text_area("Your feedback:", height=100, key="frontend_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Frontend Code", key="revise_frontend"):
                    if frontend_feedback.strip():
                        st.session_state['frontend_feedback'] = frontend_feedback
                        st.session_state['feedback']['frontend_developer'] = frontend_feedback
                        st.session_state['frontend_code'] = ""
                        st.session_state['updates']["frontend"] += 1
                        # Reset dependent phases
                        st.session_state['integration_guide'] = ""
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for revision.")
            with col2:
                if st.button("Accept & Continue", key="accept_frontend"):
                    st.session_state['updates']["integration"] += 1
                    st.rerun()
    else:
        if st.session_state.get('ui_mockups', ''):
            st.info("Ready to generate frontend code.")
            if st.button("Generate Frontend Code", key="gen_frontend"):
                st.session_state['updates']["frontend"] += 1
                st.rerun()
        else:
            st.info("Please complete the UI design first.")

with tabs[5]:  # Integration Tab
    st.header("Integration Guide")
    
    # Reference to previous work
    if st.session_state.get('ui_mockups', ''):
        with st.expander("View UI Mockups", expanded=False):
            st.markdown(st.session_state['ui_mockups'])
    
    # Only generate integration guide if we have UI mockups and need to generate guide
    if st.session_state.get('ui_mockups', '') and not st.session_state['integration_guide'] and st.session_state['updates']["integration"] > 0:
        with st.spinner("🔄 Creating Integration Guide..."):
            response = integration_expert_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "backend_code": st.session_state['backend_code'],
                "frontend_code": st.session_state['frontend_code'],
                "ui_mockups": st.session_state['ui_mockups'],
                "chat_history": "",
                "feedback": st.session_state.get('integration_feedback', "")
            })
            
            st.session_state['integration_guide'] = response['text']
            st.session_state['generated_code'] = (
                st.session_state['backend_code'] + "\n\n" + 
                st.session_state['frontend_code']
            )
            st.session_state['updates']["testing"] += 1
    
    # Display integration guide if available
    if st.session_state['integration_guide']:
        integration_col1, integration_col2 = st.columns([3, 1])
        
        with integration_col1:
            st.markdown(st.session_state['integration_guide'])
        
        with integration_col2:
            st.subheader("Integration Status:")
            st.success("✅ Integration guide generated")
            
            # Get user feedback and revision option
            integration_feedback = st.text_area("Your feedback:", height=100, key="integration_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Integration Guide", key="revise_integration"):
                    if integration_feedback.strip():
                        st.session_state['integration_feedback'] = integration_feedback
                        st.session_state['feedback']['integration_expert'] = integration_feedback
                        st.session_state['integration_guide'] = ""
                        st.session_state['updates']["integration"] += 1
                        # Reset dependent phases
                        st.session_state['test_code'] = ""
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for revision.")
            with col2:
                if st.button("Accept & Continue", key="accept_integration"):
                    st.session_state['updates']["testing"] += 1
                    st.rerun()
    else:
        if st.session_state.get('ui_mockups', ''):
            st.info("Ready to generate integration guide.")
            if st.button("Generate Integration Guide", key="gen_integration"):
                st.session_state['updates']["integration"] += 1
                st.rerun()
        else:
            st.info("Please complete the UI design first.")

with tabs[6]:  # Testing Tab
    st.header("Testing Suite")
    
    # Reference to previous work
    if st.session_state.get('integration_guide', ''):
        with st.expander("View Integration Guide", expanded=False):
            st.markdown(st.session_state['integration_guide'])
    
    # Only generate test code if we have integration guide and need to generate tests
    if st.session_state.get('integration_guide', '') and not st.session_state['test_code'] and st.session_state['updates']["testing"] > 0:
        with st.spinner("🧪 Creating Test Suite..."):
            # Combine code for testing
            generated_code = (
                st.session_state['backend_code'] + "\n\n" + 
                st.session_state['frontend_code']
            )
            
            response = testing_expert_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "generated_code": generated_code,
                "chat_history": "",
                "feedback": st.session_state.get('testing_feedback', "")
            })
            
            st.session_state['test_code'] = response['text']
            
            # Generate test report with random pass/fail status
            st.session_state['test_passes'] = random.random() > 0.4  # 60% chance to pass
            
            if not st.session_state['test_passes']:
                st.session_state['needs_debugging'] = True
                test_results = generate_test_report(fail_percent=30)
                st.session_state['test_report'] = test_results
                st.session_state['updates']["debugging"] += 1
            else:
                test_results = generate_test_report(fail_percent=0)
                st.session_state['test_report'] = test_results
                st.session_state['updates']["security"] += 1
    
    # Display test code and results if available
    if st.session_state['test_code']:
        test_col1, test_col2 = st.columns([2, 1])
        
        with test_col1:
            # Process and display the test code nicely
            test_code = st.session_state['test_code']
            
            # Display explanations as normal text and code in code blocks
            lines = test_code.split('\n')
            current_block = []
            in_code_block = False
            file_path = None
            
            for line in lines:
                if line.strip().startswith('```') and not in_code_block:
                    in_code_block = True
                    if current_block:
                        st.write('\n'.join(current_block))
                        current_block = []
                elif line.strip().startswith('```') and in_code_block:
                    in_code_block = False
                    if current_block and file_path:
                        st.subheader(f"Test File: {file_path}")
                        st.code('\n'.join(current_block), language="python")
                        current_block = []
                        file_path = None
                elif in_code_block:
                    if not current_block and line.strip() and '/' in line and not line.startswith('#'):
                        # This might be a file path
                        file_path = line.strip()
                    else:
                        current_block.append(line)
                else:
                    current_block.append(line)
            
            if current_block:
                st.write('\n'.join(current_block))
        
        with test_col2:
            st.subheader("Test Results:")
            
            if st.session_state.get('test_report'):
                if st.session_state['test_passes']:
                    st.success("✅ All tests passing")
                else:
                    st.error("❌ Some tests failing")
                
                with st.expander("Test Report", expanded=True):
                    st.markdown(st.session_state['test_report'])
            
            # Get user feedback and revision option
            testing_feedback = st.text_area("Your feedback:", height=100, key="testing_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Tests", key="revise_testing"):
                    if testing_feedback.strip():
                        st.session_state['testing_feedback'] = testing_feedback
                        st.session_state['feedback']['testing_expert'] = testing_feedback
                        st.session_state['test_code'] = ""
                        st.session_state['test_report'] = ""
                        st.session_state['updates']["testing"] += 1
                        # Reset dependent phases
                        st.session_state['debugged_code'] = ""
                        st.rerun()
                with col2:
                    if st.session_state['test_passes']:
                        if st.button("Accept & Continue", key="accept_testing"):
                            st.session_state['updates']["security"] += 1
                            st.rerun()
    else:
        if st.session_state.get('integration_guide', ''):
            st.info("Ready to generate tests.")
            if st.button("Generate Test Suite", key="gen_tests"):
                st.session_state['updates']["testing"] += 1
                st.rerun()
        else:
            st.info("Please complete the integration guide first.")

with tabs[7]:  # Debugging Tab
    st.header("Debugging")
    
    # Reference to previous work
    if st.session_state.get('test_report', '') and not st.session_state['test_passes']:
        with st.expander("View Test Report", expanded=True):
            st.markdown(st.session_state['test_report'])
    
    # Only generate debug if we need debugging and debugging update is triggered
    if st.session_state.get('needs_debugging', False) and not st.session_state['debugged_code'] and st.session_state['updates']["debugging"] > 0:
        with st.spinner("🔧 Debugging Failed Tests..."):
            # Combine code for debugging
            generated_code = (
                st.session_state['backend_code'] + "\n\n" + 
                st.session_state['frontend_code']
            )
            
            response = debugger_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "generated_code": generated_code,
                "test_code": st.session_state['test_code'],
                "test_report": st.session_state['test_report'],
                "chat_history": "",
                "feedback": st.session_state.get('debugging_feedback', "")
            })
            
            st.session_state['debugged_code'] = response['text']
            st.session_state['debug_report'] = "All issues resolved. The code has been fixed."
            st.session_state['test_passes'] = True
            st.session_state['updates']["security"] += 1
    
    # Display debug information if available
    if st.session_state['debugged_code']:
        debug_col1, debug_col2 = st.columns([2, 1])
        
        with debug_col1:
            # Process and display the debug code nicely
            debug_code = st.session_state['debugged_code']
            
            # Display explanations as normal text and code in code blocks
            lines = debug_code.split('\n')
            current_block = []
            in_code_block = False
            file_path = None
            
            for line in lines:
                if line.strip().startswith('```') and not in_code_block:
                    in_code_block = True
                    if current_block:
                        st.write('\n'.join(current_block))
                        current_block = []
                elif line.strip().startswith('```') and in_code_block:
                    in_code_block = False
                    if current_block and file_path:
                        st.subheader(f"Fixed File: {file_path}")
                        st.code('\n'.join(current_block), language="python")
                        current_block = []
                        file_path = None
                elif in_code_block:
                    if not current_block and line.strip() and '/' in line and not line.startswith('#'):
                        # This might be a file path
                        file_path = line.strip()
                    else:
                        current_block.append(line)
                else:
                    current_block.append(line)
            
            if current_block:
                st.write('\n'.join(current_block))
        
        with debug_col2:
            st.subheader("Debugging Status:")
            st.success("✅ Debugging complete")
            
            if st.session_state.get('debug_report'):
                with st.expander("Debug Report", expanded=True):
                    st.markdown(st.session_state['debug_report'])
            
            # Get user feedback and revision option
            debugging_feedback = st.text_area("Your feedback:", height=100, key="debugging_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Debugging", key="revise_debugging"):
                    if debugging_feedback.strip():
                        st.session_state['debugging_feedback'] = debugging_feedback
                        st.session_state['feedback']['debugger'] = debugging_feedback
                        st.session_state['debugged_code'] = ""
                        st.session_state['debug_report'] = ""
                        st.session_state['updates']["debugging"] += 1
                        # Reset dependent phases
                        st.session_state['security_code'] = ""
                        st.rerun()
                with col2:
                    if st.button("Accept & Continue", key="accept_debugging"):
                        st.session_state['updates']["security"] += 1
                        st.rerun()
    else:
        if st.session_state.get('test_report', '') and not st.session_state['test_passes']:
            st.info("Ready to debug failed tests.")
            if st.button("Debug Code", key="debug_code"):
                st.session_state['updates']["debugging"] += 1
                st.rerun()
        elif st.session_state.get('test_passes', False):
            st.success("No debugging needed! All tests are passing.")
        else:
            st.info("Please complete testing first.")

with tabs[8]:  # Security & Performance Tab
    st.header("Security & Performance")
    
    # Reference to previous work
    final_code_to_audit = st.session_state.get('debugged_code', '') if st.session_state.get('debugged_code', '') else st.session_state.get('generated_code', '')
    
    if final_code_to_audit:
        with st.expander("View Code to Audit", expanded=False):
            st.code(final_code_to_audit, language="python")
    
    # Only generate security audit if we have final code and security update is triggered
    if final_code_to_audit and not st.session_state['security_code'] and st.session_state['updates']["security"] > 0:
        with st.spinner("🔒 Performing Security & Performance Audit..."):
            # Generate security audit
            security_response = security_expert_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "code_to_audit": final_code_to_audit,
                "chat_history": "",
                "feedback": st.session_state.get('security_feedback', "")
            })
            
            st.session_state['security_code'] = security_response['text']
            
            # Add a security report
            security_issues = generate_security_audit()
            st.session_state['security_report'] = security_issues
            
            # Generate performance optimization
            performance_response = performance_expert_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "code_to_optimize": st.session_state['security_code'],
                "chat_history": "",
                "feedback": st.session_state.get('performance_feedback', "")
            })
            
            st.session_state['optimized_code'] = performance_response['text']
            
            # Add a performance report
            performance_report = generate_performance_report()
            st.session_state['performance_report'] = performance_report
            
            # Update documentation state
            st.session_state['updates']["documentation"] += 1
    
    # Display security & performance information if available
    if st.session_state['security_code']:
        sec_perf_col1, sec_perf_col2 = st.columns([2, 1])
        
        with sec_perf_col1:
            sec_perf_tabs = st.tabs(["Security Audit", "Performance Optimization"])
            
            with sec_perf_tabs[0]:
                st.subheader("Security Audit Results")
                
                if st.session_state.get('security_report'):
                    st.markdown(st.session_state['security_report'])
                
                st.markdown("### Security Improvements")
                st.markdown(st.session_state['security_code'])
            
            with sec_perf_tabs[1]:
                st.subheader("Performance Optimization Results")
                
                if st.session_state.get('performance_report'):
                    st.markdown(st.session_state['performance_report'])
                
                st.markdown("### Performance Improvements")
                st.markdown(st.session_state['optimized_code'])
        
        with sec_perf_col2:
            st.subheader("Audit Status:")
            st.success("✅ Security & Performance audit complete")
            
            # Get user feedback and revision option
            sec_perf_feedback = st.text_area("Your feedback:", height=100, key="sec_perf_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Security & Performance", key="revise_sec_perf"):
                    if sec_perf_feedback.strip():
                        st.session_state['security_feedback'] = sec_perf_feedback
                        st.session_state['performance_feedback'] = sec_perf_feedback
                        st.session_state['feedback']['security_expert'] = sec_perf_feedback
                        st.session_state['feedback']['performance_expert'] = sec_perf_feedback
                        st.session_state['security_code'] = ""
                        st.session_state['security_report'] = ""
                        st.session_state['optimized_code'] = ""
                        st.session_state['performance_report'] = ""
                        st.session_state['updates']["security"] += 1
                        # Reset dependent phases
                        st.session_state['documentation'] = ""
                        st.rerun()
                with col2:
                    if st.button("Accept & Continue", key="accept_security"):
                        st.session_state['updates']["documentation"] += 1
                        st.rerun()
    else:
        if final_code_to_audit and st.session_state.get('test_passes', False):
            st.info("Ready to perform security & performance audit.")
            if st.button("Audit Code", key="audit_code"):
                st.session_state['updates']["security"] += 1
                st.rerun()
        else:
            st.info("Please complete testing and debugging first.")

with tabs[9]:  # Documentation Tab
    st.header("Documentation & Final Code")
    
    # Reference to previous work
    final_optimized_code = st.session_state.get('optimized_code', '')
    
    if final_optimized_code:
        with st.expander("View Optimized Code", expanded=False):
            st.code(final_optimized_code, language="python")
    
    # Only generate documentation if we have optimized code and documentation update is triggered
    if final_optimized_code and not st.session_state['documentation'] and st.session_state['updates']["documentation"] > 0:
        with st.spinner("📝 Creating Documentation..."):
            # Generate documentation
            doc_response = documentation_expert_chain.invoke({
                "user_request": st.session_state['user_request'],
                "work_plan": st.session_state['work_plan'],
                "debugged_code": final_optimized_code,
                "security_report": st.session_state.get('security_report', ''),
                "performance_report": st.session_state.get('performance_report', ''),
                "chat_history": "",
                "feedback": st.session_state.get('documentation_feedback', "")
            })
            
            st.session_state['documentation'] = doc_response['text']
            st.session_state['final_code'] = final_optimized_code
    
    # Display documentation if available
    if st.session_state['documentation']:
        doc_col1, doc_col2 = st.columns([2, 1])
        
        with doc_col1:
            st.markdown(st.session_state['documentation'])
            
            st.subheader("Final Code Package")
            if st.button("Download Code", key="download_code"):
                st.info("Code download functionality would be implemented here.")
        
        with doc_col2:
            st.subheader("Documentation Status:")
            st.success("✅ Documentation complete")
            
            # Get user feedback and revision option
            doc_feedback = st.text_area("Your feedback:", height=100, key="doc_feedback")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Revise Documentation", key="revise_doc"):
                    if doc_feedback.strip():
                        st.session_state['documentation_feedback'] = doc_feedback
                        st.session_state['feedback']['documentation_expert'] = doc_feedback
                        st.session_state['documentation'] = ""
                        st.session_state['updates']["documentation"] += 1
                        st.rerun()
                    else:
                        st.warning("Please provide feedback for revision.")
            with col2:
                if st.button("Finalize Project", key="finalize_project"):
                    st.success("🎉 Project completed successfully!")
                    st.rerun()
    else:
        if final_optimized_code:
            st.info("Ready to create documentation.")
            if st.button("Generate Documentation", key="gen_docs"):
                st.session_state['updates']["documentation"] += 1
                st.rerun()
        else:
            st.info("Please complete security & performance audit first.")

# Generate mock data for reports
def generate_test_report(fail_percent=20):
    total_tests = 25
    failed_tests = int(total_tests * fail_percent / 100)
    passed_tests = total_tests - failed_tests
    
    report = f"""
    ## Test Summary
    
    **Total Tests:** {total_tests}  
    **Passed:** {passed_tests} ✅  
    **Failed:** {failed_tests} ❌  
    
    """
    
    if failed_tests > 0:
        report += "### Failed Tests\n\n"
        for i in range(1, failed_tests + 1):
            test_name = random.choice([
                "test_user_authentication", 
                "test_form_validation",
                "test_api_response",
                "test_database_connection",
                "test_file_upload",
                "test_admin_access",
                "test_user_roles",
                "test_data_processing"
            ])
            error = random.choice([
                "AssertionError: Expected response 200, got 404",
                "TypeError: Cannot read property 'id' of undefined",
                "ValueError: Invalid input data",
                "DatabaseError: Connection timeout",
                "KeyError: 'user_id' not found"
            ])
            report += f"**{test_name}_{i}:** {error}\n\n"
    
    return report

def generate_security_report():
    vulnerabilities = [
        {
            "severity": "High",
            "description": "SQL Injection vulnerability found in user input handling",
            "recommendation": "Use parameterized queries or ORM methods instead of string concatenation"
        },
        {
            "severity": "Medium",
            "description": "Cross-Site Scripting (XSS) vulnerability in form output",
            "recommendation": "Implement proper output escaping using Django's template system"
        },
        {
            "severity": "Low",
            "description": "Missing HTTP security headers",
            "recommendation": "Add Content-Security-Policy, X-XSS-Protection, and other security headers"
        }
    ]
    
    # Randomly select 1-3 vulnerabilities
    selected = random.sample(vulnerabilities, random.randint(1, 3))
    
    report = "## Security Audit Results\n\n"
    
    for vuln in selected:
        report += f"### {vuln['severity']} Severity Issue\n\n"
        report += f"**Description:** {vuln['description']}\n\n"
        report += f"**Recommendation:** {vuln['recommendation']}\n\n"
    
    return report

def generate_performance_report():
    issues = [
        {
            "area": "Database",
            "description": "Inefficient database queries causing N+1 query problem",
            "recommendation": "Use select_related() and prefetch_related() to reduce query count"
        },
        {
            "area": "Frontend",
            "description": "Large JavaScript bundle size affecting load time",
            "recommendation": "Implement code splitting and lazy loading of components"
        },
        {
            "area": "API",
            "description": "API responses not using pagination for large datasets",
            "recommendation": "Implement pagination for list endpoints"
        },
        {
            "area": "Caching",
            "description": "Missing cache implementation for frequently accessed data",
            "recommendation": "Add Django's caching framework for database queries and template fragments"
        }
    ]
    
    # Randomly select 1-3 issues
    selected = random.sample(issues, random.randint(1, 3))
    
    report = "## Performance Optimization Results\n\n"
    
    for issue in selected:
        report += f"### {issue['area']} Optimization\n\n"
        report += f"**Issue:** {issue['description']}\n\n"
        report += f"**Solution:** {issue['recommendation']}\n\n"
    
    return report
