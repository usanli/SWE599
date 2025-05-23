import streamlit as st
import os
from dotenv import load_dotenv
import time
import json
import zipfile # For packaging
from io import BytesIO # For packaging
# Removed old Langchain imports, will be in agent modules
# from langchain_openai import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain.schema import SystemMessage
# import pandas as pd # No longer used
# from langchain_core.prompts import ChatPromptTemplate # No longer used
# import random # No longer used for mock data generation here

# Import the agents
from webgen.agents.requirements_agent import RequirementsAgent as OriginalRequirementsAgent # Import with an alias
from webgen.agents.ui_design_agent import UIDesignAgent
from webgen.agents.web_code_agent import WebCodeAgent # New unified agent
# Removed individual coding agents
# from webgen.agents.html_agent import HTMLAgent # Removed
# from webgen.agents.css_agent import CSSAgent # Removed
# from webgen.agents.js_agent import JSAgent # Removed

# Add imports needed for our standalone function
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# --- Force reload of the RequirementsAgent module ---
import importlib
import webgen.agents.requirements_agent # 1. Import the module path
importlib.reload(webgen.agents.requirements_agent) # 2. Reload the module object
# 3. Explicitly get the RequirementsAgent class from the reloaded module object
ReloadedRequirementsAgent = webgen.agents.requirements_agent.RequirementsAgent
# --- End force reload ---

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Output directory for generated site files
OUTPUT_DIR = "output/site"

# Removed old LLM initializations (llm_basic, llm_advanced)
# Removed old agent memory initializations (code_memory, test_memory, etc.)

# Removed old init_agent_chains() function and all old agent chain definitions/initializations
# (planner_chain, backend_chain, frontend_chain, ui_designer_chain (old), 
# integration_expert_chain, testing_expert_chain, debugger_chain, security_expert_chain, 
# performance_expert_chain, documentation_expert_chain, coordinator_chain, reviewer_chain, etc.)

# Removed old agent_status dictionary

# 🌍 Streamlit UI Configuration
st.set_page_config(page_title="AI Website Builder", page_icon="✨", layout="wide")

st.title("AI Website Builder")
st.subheader("Let's build your HTML/CSS/JavaScript website step-by-step!")

if not OPENAI_API_KEY:
    st.error("🚨 OPENAI_API_KEY not found. Please set it in your .env file or environment variables.")
    st.stop()

# Initialize Agents using the reloaded class for RequirementsAgent
try:
    requirements_agent = ReloadedRequirementsAgent(openai_api_key=OPENAI_API_KEY) # Use the reloaded class
    ui_design_agent = UIDesignAgent(openai_api_key=OPENAI_API_KEY)
    web_code_agent = WebCodeAgent(openai_api_key=OPENAI_API_KEY) # Initialize unified code agent
    # Remove individual agents
    # html_agent = HTMLAgent(openai_api_key=OPENAI_API_KEY) # Removed
    # css_agent = CSSAgent(openai_api_key=OPENAI_API_KEY) # Removed
    # js_agent = JSAgent(openai_api_key=OPENAI_API_KEY) # Removed
except Exception as e:
    st.error(f"🚨 Failed to initialize an AI Agent: {e}")
    st.stop()

# --- Session State Initialization ---
# Chat and Conversation Flow
if 'conversation_stage' not in st.session_state:
    st.session_state.conversation_stage = "initial"  # initial, verification, feature_selection, design, refinement, final
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []  # List of {role, content} dictionaries
if 'current_user_input' not in st.session_state:
    st.session_state.current_user_input = ""

# User Inputs
if 'user_website_idea' not in st.session_state:
    st.session_state.user_website_idea = ""
if 'idea_verification' not in st.session_state:
    st.session_state.idea_verification = ""
if 'verified_idea' not in st.session_state:
    st.session_state.verified_idea = False
if 'selected_color_theme' not in st.session_state:
    st.session_state.selected_color_theme = "modern-blue" # Default theme

# Features and Selection
if 'generated_feature_suggestions' not in st.session_state:
    st.session_state.generated_feature_suggestions = []
if 'selected_features' not in st.session_state:
    st.session_state.selected_features = []
if 'editable_requirements_document' not in st.session_state:
    st.session_state.editable_requirements_document = ""

# Design and Mockups
if 'ui_design_spec' not in st.session_state:
    st.session_state.ui_design_spec = ""
if 'ui_page_designs' not in st.session_state:
    st.session_state.ui_page_designs = {}
if 'ui_page_mockups' not in st.session_state:
    st.session_state.ui_page_mockups = {}
if 'current_preview_page' not in st.session_state:
    st.session_state.current_preview_page = None
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = {}  # Dictionary to store uploaded images with their descriptions

# Code Generation
if 'generated_code_files' not in st.session_state:
    st.session_state.generated_code_files = {}
if 'code_generated' not in st.session_state:
    st.session_state.code_generated = False
if 'zip_buffer' not in st.session_state:
    st.session_state.zip_buffer = None
if 'site_report' not in st.session_state:
    st.session_state.site_report = None

# Triggers and Flags
if 'trigger_feature_suggestion' not in st.session_state:
    st.session_state.trigger_feature_suggestion = False
if 'trigger_design_generation' not in st.session_state:
    st.session_state.trigger_design_generation = False
if 'trigger_code_generation' not in st.session_state:
    st.session_state.trigger_code_generation = False
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
if 'generation_progress' not in st.session_state:
    st.session_state.generation_progress = 0
if 'generation_status' not in st.session_state:
    st.session_state.generation_status = ""

# --- Helper functions for the new interface ---
def add_message(role, content):
    """Add a message to the chat history"""
    st.session_state.chat_history.append({"role": role, "content": content})

def set_stage(stage):
    """Set the current conversation stage"""
    st.session_state.conversation_stage = stage

def verify_idea(idea):
    """Generate a verification response for the user's idea"""
    try:
        # Create a simple verification prompt
        llm = ChatOpenAI(
            model_name="gpt-4", 
            openai_api_key=OPENAI_API_KEY,
            temperature=0.3
        )
        
        verification_template = """
        As an AI website builder assistant, analyze the user's website request and provide a clear, concise verification.
        Summarize what type of website they want to build and include any specific details they've mentioned (company name, purpose, etc.).
        Format your response as: "You want to build a [type] website for [purpose/company name]."
        
        User's website request: {idea}
        
        Your verification:
        """
        
        prompt = PromptTemplate(
            input_variables=["idea"],
            template=verification_template
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        
        response = chain.invoke({"idea": idea})
        if response and 'text' in response:
            return response['text'].strip()
        return "I'm not sure I understand what kind of website you want to build. Could you provide more details?"
    except Exception as e:
        print(f"Error in idea verification: {str(e)}")
        return f"Error verifying your idea: {str(e)}"

def generate_all_code():
    """Generate a single-page website using the WebCodeAgent"""
    if not st.session_state.selected_features or not st.session_state.ui_design_spec:
        return False
    
    # Set generating flag and reset progress
    st.session_state.is_generating = True
    st.session_state.generation_progress = 10
    st.session_state.generation_status = "Starting website generation..."
    
    with st.spinner("Generating your modern single-page website..."):
        try:
            # Pass the selected color theme to the code generation
            selected_theme = "modern-blue"  # Default theme
            if hasattr(st.session_state, 'selected_color_theme') and st.session_state.selected_color_theme:
                selected_theme = st.session_state.selected_color_theme
            
            # Update progress
            st.session_state.generation_progress = 25
            st.session_state.generation_status = "Applying color theme and design patterns..."
            
            # Get theme colors to pass to the agent
            color_themes = {
                "modern-blue": {
                    "primary": "#4361ee",
                    "secondary": "#3a0ca3",
                    "accent": "#f72585",
                    "text": "#2b2d42",
                    "bg": "#ffffff"
                },
                "eco-green": {
                    "primary": "#2d6a4f",
                    "secondary": "#1b4332",
                    "accent": "#d8f3dc",
                    "text": "#081c15",
                    "bg": "#f8f9fa"
                },
                "warm-sunset": {
                    "primary": "#e85d04",
                    "secondary": "#dc2f02",
                    "accent": "#ffba08",
                    "text": "#370617",
                    "bg": "#faf0e6"
                },
                "tech-dark": {
                    "primary": "#7209b7",
                    "secondary": "#3a0ca3",
                    "accent": "#4cc9f0",
                    "text": "#f8f9fa",
                    "bg": "#121212"
                },
                "minimal-gray": {
                    "primary": "#6c757d",
                    "secondary": "#495057",
                    "accent": "#adb5bd",
                    "text": "#212529",
                    "bg": "#f8f9fa"
                }
            }
            
            theme_colors = color_themes.get(selected_theme, color_themes["modern-blue"])
            
            # Update progress
            st.session_state.generation_progress = 40
            st.session_state.generation_status = "Generating HTML structure and content..."
            
            # Generate all code files at once with the unified WebCodeAgent
            generated_files = web_code_agent.generate_website_code(
                st.session_state.editable_requirements_document,
                st.session_state.ui_design_spec,
                st.session_state.selected_features,
                st.session_state.uploaded_images,  # Pass uploaded images
                selected_theme,  # Pass theme name
                theme_colors  # Pass theme colors
            )
            
            # Update progress
            st.session_state.generation_progress = 75
            st.session_state.generation_status = "Processing generated code..."
            
            # Store all generated code
            if "error.txt" not in generated_files:
                st.session_state.generated_code_files = generated_files
                
                # Update progress
                st.session_state.generation_progress = 85
                st.session_state.generation_status = "Processing uploaded images..."
                
                # Also store any uploaded images in the generated code files
                for image_key, image_data in st.session_state.uploaded_images.items():
                    if 'image' in image_data and image_data['image'] is not None:
                        image_filename = f"images/{image_key}"
                        st.session_state.generated_code_files[image_filename] = image_data['image']
                
                # Update progress
                st.session_state.generation_progress = 100
                st.session_state.generation_status = "Website generated successfully!"
                
                st.session_state.code_generated = True
                
                # Reset generating flag after a brief delay
                time.sleep(1)
                st.session_state.is_generating = False
                return True
            else:
                st.error(f"Error in code generation: {generated_files.get('error.txt')}")
                st.session_state.is_generating = False
                return False
        except Exception as e:
            st.error(f"Error generating code: {e}")
            st.session_state.is_generating = False
            return False

def generate_site_report():
    """Generate a simple performance and quality report for the website"""
    try:
        # Initialize report sections
        report = {}
        
        # Check if code has been generated
        if not st.session_state.code_generated or not st.session_state.generated_code_files:
            return {"error": "No website code has been generated yet."}
            
        # 1. File size analysis
        total_size = 0
        file_sizes = {}
        
        for filename, content in st.session_state.generated_code_files.items():
            if isinstance(content, str):
                # Text files (HTML, CSS, JS)
                size_bytes = len(content.encode('utf-8'))
                file_sizes[filename] = size_bytes
                total_size += size_bytes
            elif isinstance(content, bytes):
                # Binary files (images)
                size_bytes = len(content)
                file_sizes[filename] = size_bytes
                total_size += size_bytes
        
        # Convert to KB for easier reading
        file_sizes = {k: f"{v / 1024:.2f} KB" for k, v in file_sizes.items()}
        report["total_size"] = f"{total_size / 1024:.2f} KB"
        report["file_sizes"] = file_sizes
        
        # 2. Code structure analysis
        html_file = next((content for filename, content in st.session_state.generated_code_files.items() 
                         if filename.endswith('.html')), None)
        css_file = next((content for filename, content in st.session_state.generated_code_files.items() 
                        if filename.endswith('.css')), None)
        js_file = next((content for filename, content in st.session_state.generated_code_files.items() 
                       if filename.endswith('.js')), None)
        
        # HTML analysis
        if html_file and isinstance(html_file, str):
            # Count sections
            section_count = html_file.lower().count('<section')
            # Count images
            img_count = html_file.lower().count('<img')
            # Count links
            link_count = html_file.lower().count('<a ')
            # Count form elements
            form_count = html_file.lower().count('<form')
            
            # Check for basic SEO elements
            has_title = '<title>' in html_file.lower()
            has_meta_desc = 'meta name="description"' in html_file.lower() or 'meta property="og:description"' in html_file.lower()
            has_og_tags = 'property="og:' in html_file.lower()
            has_twitter_tags = 'name="twitter:' in html_file.lower()
            
            # Calculate estimated load time (very rough approximation)
            estimated_load_time = total_size / 1024 / 100  # Assume ~100KB/s as very conservative load speed
            
            report["structure"] = {
                "sections": section_count,
                "images": img_count,
                "links": link_count,
                "forms": form_count,
                "has_seo_title": has_title,
                "has_meta_description": has_meta_desc,
                "has_open_graph": has_og_tags,
                "has_twitter_cards": has_twitter_tags,
                "estimated_load_time": f"{estimated_load_time:.2f} seconds"
            }
        
        # 3. Feature completeness check
        report["features"] = {
            "responsive_design": css_file and '@media' in css_file,
            "navigation": html_file and ('<nav' in html_file or 'class="nav' in html_file),
            "images": img_count > 0 if 'img_count' in locals() else False,
            "interactive_elements": js_file and ('addEventListener' in js_file or 'onclick' in js_file),
            "forms": form_count > 0 if 'form_count' in locals() else False
        }
        
        # 4. Overall rating
        # A very simple scoring system
        score = 0
        max_score = 10
        
        # Size score (smaller is better)
        if total_size < 500 * 1024:  # Less than 500KB
            score += 2
        elif total_size < 1000 * 1024:  # Less than 1MB
            score += 1
        
        # SEO score
        if 'structure' in report:
            seo_elements = [report["structure"].get("has_seo_title", False),
                          report["structure"].get("has_meta_description", False),
                          report["structure"].get("has_open_graph", False),
                          report["structure"].get("has_twitter_cards", False)]
            seo_score = sum(1 for element in seo_elements if element)
            score += min(seo_score, 3)  # Max 3 points for SEO
        
        # Features score
        if 'features' in report:
            feature_score = sum(1 for feature, present in report["features"].items() if present)
            score += min(feature_score, 3)  # Max 3 points for features
        
        # Structure score
        if 'structure' in report and report["structure"].get("sections", 0) > 2:
            score += 2  # Good structure with multiple sections
        
        report["overall_score"] = f"{score}/{max_score}"
        
        return report
    except Exception as e:
        return {"error": f"Error generating report: {str(e)}"}

def create_download_package():
    """Create a downloadable ZIP package of the website"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Create images directory inside the output directory if needed
        images_dir = os.path.join(OUTPUT_DIR, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_f:
            for filename, content in st.session_state.generated_code_files.items():
                if filename.startswith("images/"):
                    # Handle image files
                    zip_f.writestr(filename, content)
                else:
                    # Handle text-based files (HTML, CSS, JS)
                    zip_f.writestr(filename, content)
        
        st.session_state.zip_buffer = zip_buffer.getvalue()
        return True
    except Exception as e:
        st.error(f"Error creating ZIP file: {e}")
        return False

def direct_generate_initial_document(requirements_agent, user_idea, selected_features):
    """
    A direct wrapper function to generate the initial document.
    This avoids any potential module import/reload issues.
    """
    if not user_idea or not selected_features:
        return "Error: User idea and selected features are required to generate the document."
    
    # Create a completely standalone implementation that doesn't rely on the agent object at all
    llm = ChatOpenAI(
        model_name="gpt-4", 
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3
    )
    
    initial_document_template = """
    You are a requirements analyst. Based on the user's initial website idea and a list of selected pages/features,
    generate a well-structured and detailed "Consolidated Requirements Document". This document should elaborate
    on the purpose of the website, describe each selected page/feature in a paragraph or two, and outline any key functionalities or
    user interactions implied by the selections. Structure it with clear headings for each section (e.g., Overall Purpose, Page: Homepage, Page: About Us, Feature: Contact Form).
    Be comprehensive but concise.

    User's Initial Website Idea:
    {user_idea}

    Selected Pages/Features:
    {selected_features}

    Consolidated Requirements Document:
    """
    
    prompt = PromptTemplate(
        input_variables=["user_idea", "selected_features"],
        template=initial_document_template
    )
    
    chain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    
    features_str = "\n- " + "\n- ".join(selected_features)
    try:
        response = chain.invoke({
            "user_idea": user_idea,
            "selected_features": features_str
        })
        if response and 'text' in response:
            return response['text'].strip()
        return "Error: Could not generate the initial requirements document."
    except Exception as e:
        print(f"Error in standalone document generation: {str(e)}")
        return f"Error generating initial document: {str(e)}"

# Function to parse UI design specs
def parse_ui_design_spec(design_spec):
    """
    Parses the UI design specification to extract individual page designs.
    Expects a markdown-formatted string with ## Page headings.
    Returns a dictionary with page names as keys and their design specs as values.
    """
    page_designs = {}
    current_page = None
    current_content = []
    
    # Split by lines and process
    lines = design_spec.split('\n')
    for line in lines:
        # Check if this is a page header (## Page Name)
        if line.strip().startswith('## '):
            # If we were already collecting a page, save it
            if current_page:
                page_designs[current_page] = '\n'.join(current_content)
                current_content = []
            
            # Start a new page
            current_page = line.strip()[3:].strip()  # Remove '## ' prefix
            current_content.append(line)  # Include the header in the content
        elif current_page:
            # Add to current page content
            current_content.append(line)
    
    # Add the last page if there is one
    if current_page and current_content:
        page_designs[current_page] = '\n'.join(current_content)
    
    return page_designs

# Function to create a modern HTML mockup from a design spec
def generate_html_mockup(page_name, design_spec, all_features=None):
    """
    Creates a modern HTML mockup visualization with all features as sections on a single page.
    
    Args:
        page_name: The name of the current section/feature
        design_spec: The UI design spec for this section
        all_features: A list of all features to include as sections
    """
    # If all_features is None, initialize it to just contain the current feature
    if all_features is None:
        all_features = [page_name]
    
    # Check for common UI components in the spec
    has_header = "header" in design_spec.lower()
    has_footer = "footer" in design_spec.lower()
    has_hero = "hero" in design_spec.lower()
    has_sidebar = "sidebar" in design_spec.lower()
    has_gallery = any(term in design_spec.lower() for term in ["gallery", "portfolio", "images"])
    has_form = any(term in design_spec.lower() for term in ["form", "contact form", "input"])
    
    # Determine layout structure 
    columns = 1
    if any(term in design_spec.lower() for term in ["two-column", "2-column", "2 column", "two column"]):
        columns = 2
    elif any(term in design_spec.lower() for term in ["three-column", "3-column", "3 column", "three column"]):
        columns = 3
    
    # Get selected color theme or use default
    selected_theme = "modern-blue"
    if hasattr(st.session_state, 'selected_color_theme') and st.session_state.selected_color_theme:
        selected_theme = st.session_state.selected_color_theme
    
    # Define color themes
    color_themes = {
        "modern-blue": {
            "primary_color": "#4361ee",    # Modern blue
            "secondary_color": "#3a0ca3",  # Deep purple
            "text_color": "#2b2d42",       # Dark blue-gray
            "light_text": "#f8f9fa",       # Off-white
            "bg_color": "#ffffff",         # White
            "accent_color": "#f72585",     # Bright pink accent
            "section_bg": "#f8f9fa"        # Light gray for sections
        },
        "eco-green": {
            "primary_color": "#2d6a4f",    # Forest green
            "secondary_color": "#1b4332",  # Dark green
            "text_color": "#081c15",       # Very dark green
            "light_text": "#f8f9fa",       # Off-white
            "bg_color": "#f8f9fa",         # Light background
            "accent_color": "#d8f3dc",     # Light mint
            "section_bg": "#f0f7f4"        # Pale green
        },
        "warm-sunset": {
            "primary_color": "#e85d04",    # Orange
            "secondary_color": "#dc2f02",  # Red-orange
            "text_color": "#370617",       # Deep red-brown
            "light_text": "#f8f9fa",       # Off-white
            "bg_color": "#faf0e6",         # Light beige
            "accent_color": "#ffba08",     # Yellow
            "section_bg": "#fef9ef"        # Very light yellow
        },
        "tech-dark": {
            "primary_color": "#7209b7",    # Purple
            "secondary_color": "#3a0ca3",  # Deep blue
            "text_color": "#f8f9fa",       # White
            "light_text": "#f8f9fa",       # White
            "bg_color": "#121212",         # Almost black
            "accent_color": "#4cc9f0",     # Bright blue
            "section_bg": "#1a1a1a"        # Dark gray
        },
        "minimal-gray": {
            "primary_color": "#6c757d",    # Medium gray
            "secondary_color": "#495057",  # Dark gray
            "text_color": "#212529",       # Almost black
            "light_text": "#f8f9fa",       # Off-white
            "bg_color": "#f8f9fa",         # Very light gray
            "accent_color": "#adb5bd",     # Light gray
            "section_bg": "#e9ecef"        # Pale gray
        }
    }
    
    # Use the selected theme colors or fall back to default
    theme = color_themes.get(selected_theme, color_themes["modern-blue"])
    primary_color = theme["primary_color"]
    secondary_color = theme["secondary_color"]
    text_color = theme["text_color"]
    light_text = theme["light_text"]
    bg_color = theme["bg_color"]
    accent_color = theme["accent_color"]
    section_bg = theme["section_bg"]
    
    # Custom CSS for modern design elements
    custom_css = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
      
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        scroll-behavior: smooth;
      }}
      
      body {{
        font-family: 'Poppins', sans-serif;
        color: {text_color};
        line-height: 1.6;
      }}
      
      .container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 20px;
      }}
      
      /* Modern header */
      .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0;
        position: sticky;
        top: 0;
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(0,0,0,0.05);
        z-index: 1000;
      }}
      
      .logo {{
        font-weight: 700;
        font-size: 24px;
        color: {primary_color};
      }}
      
      .nav-links {{
        display: flex;
        gap: 30px;
      }}
      
      .nav-links a {{
        text-decoration: none;
        color: {text_color};
        font-weight: 500;
        transition: color 0.3s ease;
        position: relative;
        cursor: pointer;
      }}
      
      .nav-links a:hover {{
        color: {primary_color};
      }}
      
      .nav-links a::after {{
        content: '';
        position: absolute;
        width: 0;
        height: 2px;
        bottom: -5px;
        left: 0;
        background-color: {primary_color};
        transition: width 0.3s ease;
      }}
      
      .nav-links a:hover::after {{
        width: 100%;
      }}
      
      .nav-links a.active {{
        color: {primary_color};
      }}
      
      .nav-links a.active::after {{
        width: 100%;
      }}
      
      /* Modern hero section */
      .hero {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 100px 20px;
        background-size: cover;
        background-position: center;
        color: {light_text};
        position: relative;
        min-height: 80vh;
      }}
      
      .hero::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.6));
      }}
      
      .hero-content {{
        position: relative;
        z-index: 1;
        max-width: 800px;
      }}
      
      .hero h1 {{
        font-size: 48px;
        margin-bottom: 20px;
        font-weight: 700;
      }}
      
      .hero p {{
        font-size: 20px;
        margin-bottom: 30px;
        max-width: 600px;
      }}
      
      .btn {{
        display: inline-block;
        padding: 12px 30px;
        background-color: {accent_color};
        color: white;
        text-decoration: none;
        border-radius: 50px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
      }}
      
      .btn:hover {{
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
      }}
      
      /* Content sections */
      .section {{
        padding: 80px 0;
        scroll-margin-top: 80px;  /* Offset for sticky header */
      }}
      
      .section:nth-child(even) {{
        background-color: {section_bg};
      }}
      
      .section-title {{
        font-size: 32px;
        text-align: center;
        margin-bottom: 60px;
        position: relative;
      }}
      
      .section-title::after {{
        content: '';
        position: absolute;
        width: 70px;
        height: 3px;
        background-color: {primary_color};
        bottom: -15px;
        left: 50%;
        transform: translateX(-50%);
      }}
      
      .cards {{
        display: flex;
        gap: 30px;
        flex-wrap: wrap;
      }}
      
      .card {{
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        flex: 1;
        min-width: 300px;
      }}
      
      .card:hover {{
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
      }}
      
      .card-img {{
        height: 200px;
        background-size: cover;
        background-position: center;
      }}
      
      .card-content {{
        padding: 30px;
      }}
      
      .card h3 {{
        margin-bottom: 15px;
        font-weight: 600;
      }}
      
      /* Gallery section */
      .gallery {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 20px;
      }}
      
      .gallery-item {{
        height: 250px;
        background-size: cover;
        background-position: center;
        border-radius: 10px;
        overflow: hidden;
        position: relative;
      }}
      
      .gallery-item::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(rgba(0,0,0,0.1), rgba(0,0,0,0.4));
        opacity: 0;
        transition: opacity 0.3s ease;
      }}
      
      .gallery-item:hover::after {{
        opacity: 1;
      }}
      
      /* Forms */
      .form-group {{
        margin-bottom: 20px;
      }}
      
      .form-group label {{
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
      }}
      
      .form-control {{
        width: 100%;
        padding: 15px;
        border: 1px solid #ddd;
        border-radius: 8px;
        font-size: 16px;
        transition: border-color 0.3s ease;
      }}
      
      .form-control:focus {{
        outline: none;
        border-color: {primary_color};
      }}
      
      textarea.form-control {{
        min-height: 150px;
        resize: vertical;
      }}
      
      /* Footer */
      .footer {{
        background-color: {section_bg};
        padding: 60px 0 30px;
        text-align: center;
      }}
      
      .footer-links {{
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 30px;
      }}
      
      .footer-links a {{
        color: {text_color};
        text-decoration: none;
        transition: color 0.3s ease;
        cursor: pointer;
      }}
      
      .footer-links a:hover {{
        color: {primary_color};
      }}
      
      .copyright {{
        color: #777;
        font-size: 14px;
      }}
    </style>
    """
    
    # JavaScript for smooth scrolling
    navigation_js = """
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
          anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
              // Highlight the active nav link
              document.querySelectorAll('.nav-links a').forEach(link => {
                link.classList.remove('active');
              });
              this.classList.add('active');
              
              // Smooth scroll to the section
              targetElement.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
              });
            }
          });
        });
      });
    </script>
    """
    
    # Start building the HTML with the custom CSS and JavaScript
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Website Preview</title>
      {custom_css}
      {navigation_js}
    </head>
    <body>
    """
    
    # Add a header if specified
    if has_header:
        html += f"""
        <header class="header container">
            <div class="logo">Company Name</div>
            <nav class="nav-links">
        """
        
        # Add navigation links for all features as anchor links
        for feature in all_features:
            feature_id = feature.lower().replace(' ', '-').replace('(', '').replace(')', '')
            is_active = feature == page_name
            active_class = "active" if is_active else ""
            html += f"""
                <a href="#{feature_id}" class="{active_class}">{feature.replace('_', ' ')}</a>
            """
            
        html += """
            </nav>
        </header>
        """
    
    # Create content sections for each feature
    for feature in all_features:
        feature_id = feature.lower().replace(' ', '-').replace('(', '').replace(')', '')
        
        # For the first feature (homepage), add a hero section
        if feature == all_features[0] and has_hero:
            hero_bg = "url('https://images.unsplash.com/photo-1506748686214-e9df14d4d9d0?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80')"
            
            # Check if we have a hero image in the uploaded images
            hero_img = None
            for img_key, img_data in st.session_state.uploaded_images.items():
                if 'description' in img_data and 'hero' in img_data['description'].lower():
                    hero_img = img_key
                    break
            
            if hero_img:
                # Use the uploaded hero image as background
                hero_bg = f"url('images/{hero_img}')"
                
            html += f"""
            <section class="hero" style="background-image: {hero_bg};">
                <div class="hero-content">
                    <h1>Welcome to Our Website</h1>
                    <p>This is a compelling subheadline that briefly describes your value proposition and captures attention.</p>
                    <a href="#{all_features[1].lower().replace(' ', '-').replace('(', '').replace(')', '')}" class="btn">Explore</a>
                </div>
            </section>
            """
        
        # Start the section for this feature
        html += f'<section id="{feature_id}" class="section">'
        html += f'<div class="container">'
        html += f'<h2 class="section-title">{feature}</h2>'
        
        # Content section - customize based on feature type
        if "about" in feature.lower():
            # About section with two columns
            html += f"""
            <div class="cards">
                <div class="card">
                    <div class="card-content">
                        <h3>Our Story</h3>
                        <p>This section tells the story of your company or organization. It should provide enough information to build trust with your audience and share your mission, vision and values.</p>
                    </div>
                </div>
                <div class="card">
                    <div class="card-img" style="background-image: url('https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80');"></div>
                    <div class="card-content">
                        <h3>Our Team</h3>
                        <p>Introduce the key team members or leadership that makes your organization special. Highlight their expertise and what they bring to the table.</p>
                    </div>
                </div>
            </div>
            """
        elif "service" in feature.lower() or "product" in feature.lower():
            # Services/Products section with cards
            html += '<div class="cards">'
            for i in range(3):  # 3 service cards
                service_img = None
                for img_key, img_data in st.session_state.uploaded_images.items():
                    if 'description' in img_data and f'service {i+1}' in img_data['description'].lower():
                        service_img = img_key
                        break
                
                card_img_style = "background-image: url('https://images.unsplash.com/photo-1558655146-d09347e92766?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80');"
                if service_img:
                    card_img_style = f"background-image: url('images/{service_img}');"
                    
                html += f"""
                <div class="card">
                    <div class="card-img" style="{card_img_style}"></div>
                    <div class="card-content">
                        <h3>Service/Product {i+1}</h3>
                        <p>This describes one of your key services or products. Highlight its benefits and what makes it special.</p>
                        <a href="#" style="color: {primary_color}; text-decoration: none; font-weight: 500; display: inline-block; margin-top: 15px;">Learn more →</a>
                    </div>
                </div>
                """
            html += '</div>'
        elif "gallery" in feature.lower() or "portfolio" in feature.lower():
            # Gallery/Portfolio section
            html += '<div class="gallery">'
            # Find all gallery images
            gallery_images = []
            for img_key, img_data in st.session_state.uploaded_images.items():
                if 'description' in img_data and 'gallery' in img_data['description'].lower():
                    gallery_images.append(img_key)
            
            # If we have gallery images, use them, otherwise use placeholders
            if gallery_images:
                for i, img_key in enumerate(gallery_images[:6]):  # Show up to 6 images
                    html += f"""
                    <div class="gallery-item" style="background-image: url('images/{img_key}');"></div>
                    """
            else:
                # Fallback to placeholders
                placeholder_urls = [
                    "https://images.unsplash.com/photo-1558981806-ec527fa84c39?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1558981420-87aa9dad1c89?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1558981001-792f6c0d5068?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1558981852-426c6c22a060?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1558981333-0ddb4b5fde79?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1558980394-dbb977039a2e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                ]
                for i, url in enumerate(placeholder_urls):
                    html += f"""
                    <div class="gallery-item" style="background-image: url('{url}');"></div>
                    """
            html += '</div>'
        elif "contact" in feature.lower():
            # Contact section with form
            html += f"""
            <div style="max-width: 600px; margin: 0 auto;">
                <div class="form-group">
                    <label for="name">Name</label>
                    <input type="text" class="form-control" id="name">
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" class="form-control" id="email">
                </div>
                <div class="form-group">
                    <label for="message">Message</label>
                    <textarea class="form-control" id="message"></textarea>
                </div>
                <button class="btn" style="background-color: {primary_color};">Send Message</button>
            </div>
            """
        else:
            # Generic content section
            html += f"""
            <div style="max-width: 800px; margin: 0 auto;">
                <p style="text-align: center; margin-bottom: 30px;">This is the content area for {feature}. It would contain information relevant to this section's purpose.</p>
                
                <div style="text-align: center; margin: 40px 0;">
                    <a href="#{all_features[(all_features.index(feature) + 1) % len(all_features)].lower().replace(' ', '-').replace('(', '').replace(')', '')}" class="btn">Next Section</a>
                </div>
            </div>
            """
        
        html += '</div></section>'
    
    # Footer
    if has_footer:
        html += f"""
        <footer class="footer">
            <div class="container">
                <div class="footer-links">
        """
        
        # Add navigation links in footer as well
        for feature in all_features:
            feature_id = feature.lower().replace(' ', '-').replace('(', '').replace(')', '')
            html += f"""
                <a href="#{feature_id}">{feature.replace('_', ' ')}</a>
            """
            
        html += f"""
                </div>
                <div class="copyright">© 2024 Company Name. All rights reserved.</div>
            </div>
        </footer>
        """
    
    # Close the HTML document
    html += '</body></html>'
    
    return html

# --- Main Layout: Two-Column Design ---
st.title("AI Website Builder")

# Create two columns for the main layout
left_col, right_col = st.columns([2, 3])

# === LEFT COLUMN: Conversation Interface ===
with left_col:
    st.markdown("### Website Builder Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Initial Idea Input (only shown in initial stage)
    if st.session_state.conversation_stage == "initial":
        st.markdown("#### Describe Your Website")
        user_idea = st.text_area(
            "Tell me about the website you want to build:",
            placeholder="For example: I want to build a website for my SAP consultancy company named Orvon...",
            key="idea_input_area",
            height=100
        )
        
        if st.button("Build My Website", key="build_btn", type="primary", disabled=not user_idea.strip()):
            st.session_state.user_website_idea = user_idea
            
            # Add user message to chat
            add_message("user", user_idea)
            
            # Skip verification and directly generate feature suggestions
            with st.spinner("Analyzing your requirements..."):
                suggestions = requirements_agent.suggest_features(user_idea)
                if suggestions:
                    st.session_state.generated_feature_suggestions = suggestions
                    
                    # Auto-select all suggested features
                    st.session_state.selected_features = suggestions
                    
                    # Generate requirements document
                    doc = direct_generate_initial_document(
                        requirements_agent,
                        user_idea,
                        suggestions
                    )
                    
                    if not doc.startswith("Error:"):
                        st.session_state.editable_requirements_document = doc
                        
                        # Generate UI design
                        design_spec = ui_design_agent.generate_design_spec(
                            st.session_state.editable_requirements_document,
                            st.session_state.selected_features
                        )
                        
                        if design_spec:
                            st.session_state.ui_design_spec = design_spec
                            
                            # Parse the design spec
                            page_designs = parse_ui_design_spec(design_spec)
                            st.session_state.ui_page_designs = page_designs
                            
                            # Generate HTML mockup for single-page website with all features
                            mockup_html = generate_html_mockup(
                                st.session_state.selected_features[0], # Use first feature as the main one
                                design_spec,
                                all_features=st.session_state.selected_features
                            )
                            
                            # Store the single mockup in the session state
                            st.session_state.ui_page_mockups = {"single_page": mockup_html}
                            st.session_state.current_preview_page = "single_page"
                            
                            # Generate all code
                            generate_all_code()
                            
                            # Add confirmation message
                            feature_count = len(st.session_state.selected_features)
                            add_message("assistant", f"✅ I've built your website with {feature_count} sections based on your requirements. You can now view and download it below.")
                            
                            # Move to refinement stage
                            set_stage("refinement")
                        else:
                            add_message("assistant", "I had trouble generating the UI design. Please try again with more details.")
                    else:
                        add_message("assistant", f"Error generating requirements: {doc}")
                else:
                    add_message("assistant", "I couldn't understand your requirements. Please provide more details about what you want on the website.")
            
            st.rerun()
    
    # Verification Stage
    elif st.session_state.conversation_stage == "verification":
        user_feedback = st.chat_input("Provide feedback or confirm...")
        
        if user_feedback:
            # Add user response to chat
            add_message("user", user_feedback)
            
            # Check if it's a confirmation
            if any(word in user_feedback.lower() for word in ["yes", "correct", "right", "good", "perfect", "confirm"]):
                st.session_state.verified_idea = True
                
                # Generate feature suggestions
                with st.spinner("Generating feature suggestions..."):
                    suggestions = requirements_agent.suggest_features(st.session_state.user_website_idea)
                    if suggestions:
                        st.session_state.generated_feature_suggestions = suggestions
                        feature_list = "\n".join([f"- {feature}" for feature in suggestions])
                        add_message("assistant", f"Great! Based on your requirements, here are the suggested pages/features I recommend:\n\n{feature_list}\n\nPlease select the features you want to include.")
                        set_stage("feature_selection")
            else:
                        add_message("assistant", "I had trouble suggesting features based on your idea. Could you provide more details about what you want on the website?")
                
            # Update stage
            set_stage("verification")
            st.rerun()
    
    # Feature Selection Stage
    elif st.session_state.conversation_stage == "feature_selection":
        st.markdown("#### Select Pages/Features")
        
        # Add image upload capability
        st.markdown("#### Upload Images for Your Website")
        st.info("Upload images to include in your website. Provide a descriptive name to help us place it correctly.")
        
        # Add guidance for image placement
        with st.expander("Image Placement Guide"):
            st.markdown("""
            **Tips for effective image placement:**
            - **Hero/Banner**: Main banner image at the top of your site (name it 'hero' or 'banner')
            - **Logo**: Your company/brand logo (name it 'logo')
            - **Gallery**: Images for a gallery section (name them 'gallery1', 'gallery2', etc.)
            - **About**: Team photos or about section images (name them 'team', 'about', etc.)
            - **Products/Services**: Images of your products or services (name them 'product1', 'service1', etc.)
            
            The more descriptive your image name, the better we can place it in the right section of your website.
            """)
        
        with st.form("image_upload_form"):
            uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "gif"])
            image_description = st.text_input("Image name/description (e.g., 'hero', 'logo', 'team', 'product1')")
            
            submit_button = st.form_submit_button("Upload Image")
            
            if submit_button and uploaded_file is not None and image_description:
                # Create a unique key for this image
                import hashlib
                import datetime
                
                # Generate a unique key using the file name, size, and timestamp
                unique_id = hashlib.md5(f"{uploaded_file.name}-{datetime.datetime.now().isoformat()}".encode()).hexdigest()[:8]
                image_key = f"{uploaded_file.name.split('.')[0]}_{unique_id}.{uploaded_file.name.split('.')[-1]}"
                
                # Store the uploaded file in the session state
                st.session_state.uploaded_images[image_key] = {
                    'description': image_description,
                    'image': uploaded_file.getvalue(),
                    'type': uploaded_file.type,
                    'name': uploaded_file.name
                }
                
                st.success(f"Image '{uploaded_file.name}' uploaded successfully!")
                st.rerun()
        
        # Display uploaded images in a gallery
        if st.session_state.uploaded_images:
            st.markdown("#### Your Uploaded Images")
            
            # Create a container with horizontal scrolling for the gallery
            gallery_container = st.container()
            with gallery_container:
                # Calculate how many columns we need (3 per row)
                num_images = len(st.session_state.uploaded_images)
                num_rows = (num_images + 2) // 3  # Ceiling division to get number of rows
                
                for row in range(num_rows):
                    cols = st.columns(3)
                    
                    # Get slices for this row
                    start_idx = row * 3
                    end_idx = min(start_idx + 3, num_images)
                    row_images = list(st.session_state.uploaded_images.items())[start_idx:end_idx]
                    
                    for i, (image_key, image_data) in enumerate(row_images):
                        with cols[i]:
                            # Safely display image with error handling
                            try:
                                st.image(image_data['image'], caption=image_data['description'], width=150)
                                
                                # Add a remove button for each image
                                if st.button(f"Remove", key=f"remove_{image_key}"):
                                    del st.session_state.uploaded_images[image_key]
                                    st.rerun()
                            except Exception as e:
                                st.warning(f"Cannot display image: {image_key}")
                                # Show a placeholder and error details in an expander
                                st.image("https://via.placeholder.com/150?text=Image+Error", width=150)
                                with st.expander("Error details"):
                                    st.error(f"Error: {str(e)}")
                                    
                                # Still provide remove button
                                if st.button(f"Remove Error Image", key=f"remove_error_{image_key}"):
                                    del st.session_state.uploaded_images[image_key]
                                    st.rerun()
            
            # Add a clear all button if there are many images
            if num_images > 3:
                if st.button("Clear All Images"):
                    st.session_state.uploaded_images = {}
                    st.rerun()
        
        # Rest of the feature selection UI
        selected = st.multiselect(
            "Choose the pages and features you want for your website:",
            options=st.session_state.generated_feature_suggestions,
            default=st.session_state.selected_features
        )
        
        # Update selected features if changed
        if selected != st.session_state.selected_features:
            st.session_state.selected_features = selected
        
        # Add color theme selection
        st.markdown("#### Choose a Color Theme")
        
        # Define some modern color themes
        color_themes = {
            "modern-blue": {
                "name": "Modern Blue",
                "primary": "#4361ee",
                "secondary": "#3a0ca3",
                "accent": "#f72585",
                "text": "#2b2d42",
                "bg": "#ffffff"
            },
            "eco-green": {
                "name": "Eco Green",
                "primary": "#2d6a4f",
                "secondary": "#1b4332",
                "accent": "#d8f3dc",
                "text": "#081c15",
                "bg": "#f8f9fa"
            },
            "warm-sunset": {
                "name": "Warm Sunset",
                "primary": "#e85d04",
                "secondary": "#dc2f02",
                "accent": "#ffba08",
                "text": "#370617",
                "bg": "#faf0e6"
            },
            "tech-dark": {
                "name": "Tech Dark",
                "primary": "#7209b7",
                "secondary": "#3a0ca3",
                "accent": "#4cc9f0",
                "text": "#f8f9fa",
                "bg": "#121212"
            },
            "minimal-gray": {
                "name": "Minimal Gray",
                "primary": "#6c757d",
                "secondary": "#495057",
                "accent": "#adb5bd",
                "text": "#212529",
                "bg": "#f8f9fa"
            }
        }
        
        # Create theme preview boxes
        cols = st.columns(len(color_themes))
        for i, (theme_id, theme) in enumerate(color_themes.items()):
            with cols[i]:
                # Create HTML for theme preview
                preview_html = f"""
                <div style="
                    background-color: {theme['bg']}; 
                    border: 2px solid {theme['primary']}; 
                    border-radius: 10px; 
                    padding: 10px;
                    color: {theme['text']};
                    height: 150px;
                    text-align: center;
                    margin-bottom: 10px;
                    position: relative;
                ">
                    <h4 style="color: {theme['primary']};">{theme['name']}</h4>
                    <div style="display: flex; justify-content: center; gap: 5px; margin: 10px 0;">
                        <div style="height: 30px; width: 30px; border-radius: 50%; background-color: {theme['primary']}"></div>
                        <div style="height: 30px; width: 30px; border-radius: 50%; background-color: {theme['secondary']}"></div>
                        <div style="height: 30px; width: 30px; border-radius: 50%; background-color: {theme['accent']}"></div>
                    </div>
                    <div style="position: absolute; bottom: 10px; left: 0; right: 0;">
                        <button style="
                            background-color: {theme['primary']}; 
                            color: white;
                            border: none;
                            padding: 5px 10px;
                            border-radius: 5px;
                            cursor: pointer;
                        ">Button</button>
                    </div>
                </div>
                """
                
                # Display the preview
                st.components.v1.html(preview_html, height=170)
                
                # Add a radio button for selection
                is_selected = st.session_state.selected_color_theme == theme_id
                if st.checkbox("Select", key=f"theme_{theme_id}", value=is_selected):
                    # Uncheck other theme options and set the selected theme
                    st.session_state.selected_color_theme = theme_id
                    # Rerun to update other checkboxes
                    st.rerun()
        
        # Button to proceed with selected features
        if st.button("Generate Website with Selected Features", key="generate_site_btn", 
                    type="primary", disabled=len(selected) == 0):
            # Set generating flag and reset progress
            st.session_state.is_generating = True
            st.session_state.generation_progress = 5
            st.session_state.generation_status = "Starting website generation..."
            
            with st.spinner("Generating website..."):
                # First generate requirements document
                st.session_state.generation_progress = 15
                st.session_state.generation_status = "Analyzing requirements..."
                
                doc = direct_generate_initial_document(
                    requirements_agent,
                    st.session_state.user_website_idea,
                    st.session_state.selected_features
                )
                
                if not doc.startswith("Error:"):
                    st.session_state.editable_requirements_document = doc
                    
                    # Update progress
                    st.session_state.generation_progress = 30
                    st.session_state.generation_status = "Designing UI layout..."
                    
                    # Generate UI design
                    design_spec = ui_design_agent.generate_design_spec(
                        st.session_state.editable_requirements_document,
                        st.session_state.selected_features
                    )
                    
                    if design_spec:
                        st.session_state.ui_design_spec = design_spec
                        
                        # Update progress
                        st.session_state.generation_progress = 50
                        st.session_state.generation_status = "Creating visual mockups..."
                        
                        # Parse the design spec
                        page_designs = parse_ui_design_spec(design_spec)
                        st.session_state.ui_page_designs = page_designs
                        
                        # Generate HTML mockup for single-page website with all features
                        mockup_html = generate_html_mockup(
                            st.session_state.selected_features[0], # Use first feature as the main one
                            design_spec,
                            all_features=st.session_state.selected_features
                        )
                        
                        # Store the single mockup in the session state
                        st.session_state.ui_page_mockups = {"single_page": mockup_html}
                        st.session_state.current_preview_page = "single_page"
                        
                        # Generate all code (this function will continue updating progress)
                        generate_all_code()
                        
                        # Add confirmation message
                        feature_count = len(st.session_state.selected_features)
                        image_count = len(st.session_state.uploaded_images)
                        add_message("assistant", f"✅ Your website with {feature_count} sections and {image_count} uploaded images has been generated! You can now view and refine it. If you want to download the code, click the button below.")
                        
                        # Move to refinement stage
                        set_stage("refinement")
                    else:
                        add_message("assistant", "I had trouble generating the UI design. Could you try again with different feature selections?")
                        st.session_state.is_generating = False
                else:
                    add_message("assistant", f"Error generating requirements: {doc}")
                    st.session_state.is_generating = False
            
            st.rerun()
    
    # Refinement Stage
    elif st.session_state.conversation_stage == "refinement":
        # If code is generated, show refinement options
        if st.session_state.code_generated:
            # Create prominent download button in main conversation area
            if not st.session_state.zip_buffer:
                if st.button("📦 Create Download Package", key="package_main_btn", type="primary"):
                    with st.spinner("Creating download package..."):
                        if create_download_package():
                            st.success("Package created successfully!")
                        else:
                            st.error("Error creating package.")
                        st.rerun()
            else:
                st.download_button(
                    label="📥 Download Website.zip",
                    data=st.session_state.zip_buffer,
                    file_name="website.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            
            # Create download package section in sidebar
            st.sidebar.markdown("### Download Your Website")
            
            if st.sidebar.button("📦 Package Website", key="package_btn"):
                with st.sidebar.spinner("Creating download package..."):
                    if create_download_package():
                        st.sidebar.success("Package created successfully!")
                    else:
                        st.sidebar.error("Error creating package.")
                    st.rerun()
            
            if st.session_state.zip_buffer:
                st.sidebar.download_button(
                    label="📥 Download Website.zip",
                    data=st.session_state.zip_buffer,
                    file_name="website.zip",
                    mime="application/zip"
                )
            
            # Add website performance report option
            st.sidebar.markdown("### Website Report")
            
            if st.sidebar.button("📊 Generate Performance Report", key="report_btn"):
                with st.sidebar.spinner("Analyzing website..."):
                    report = generate_site_report()
                    if "error" not in report:
                        st.session_state.site_report = report
                        st.sidebar.success("Report generated!")
                    else:
                        st.sidebar.error(report["error"])
                    st.rerun()
            
            # Display report if available
            if 'site_report' in st.session_state and st.session_state.site_report:
                with st.sidebar.expander("View Website Report", expanded=True):
                    report = st.session_state.site_report
                    
                    # Overall score
                    st.markdown(f"### Overall Score: {report['overall_score']}")
                    
                    # Size information
                    st.markdown("#### Size Analysis")
                    st.markdown(f"Total size: **{report['total_size']}**")
                    
                    # Structure analysis
                    if 'structure' in report:
                        st.markdown("#### Structure Analysis")
                        structure = report['structure']
                        st.markdown(f"- Sections: {structure.get('sections', 'N/A')}")
                        st.markdown(f"- Images: {structure.get('images', 'N/A')}")
                        st.markdown(f"- Links: {structure.get('links', 'N/A')}")
                        st.markdown(f"- Forms: {structure.get('forms', 'N/A')}")
                        st.markdown(f"- Est. Load Time: {structure.get('estimated_load_time', 'N/A')}")
                    
                    # SEO status
                    if 'structure' in report:
                        st.markdown("#### SEO Status")
                        structure = report['structure']
                        st.markdown(f"- Title Tag: {'✅' if structure.get('has_seo_title', False) else '❌'}")
                        st.markdown(f"- Meta Description: {'✅' if structure.get('has_meta_description', False) else '❌'}")
                        st.markdown(f"- Open Graph Tags: {'✅' if structure.get('has_open_graph', False) else '❌'}")
                        st.markdown(f"- Twitter Cards: {'✅' if structure.get('has_twitter_cards', False) else '❌'}")
                    
                    # Features check
                    if 'features' in report:
                        st.markdown("#### Features")
                        features = report['features']
                        for feature, present in features.items():
                            st.markdown(f"- {feature.replace('_', ' ').title()}: {'✅' if present else '❌'}")
                    
                    # Display detailed file sizes in a table (optional)
                    with st.expander("File Size Details"):
                        if 'file_sizes' in report:
                            for filename, size in report['file_sizes'].items():
                                st.markdown(f"- {filename}: {size}")
            
            # Add the feedback option in chat
            user_feedback = st.chat_input("How would you like to refine the website?")
            
            if user_feedback:
                add_message("user", user_feedback)
                add_message("assistant", "I'll update the design based on your feedback...")
                
                # Re-run design generation with feedback
                with st.spinner("Updating website based on feedback..."):
                    try:
                        # Regenerate design with feedback
                        updated_design = ui_design_agent.generate_design_spec_with_feedback(
                            st.session_state.editable_requirements_document,
                            st.session_state.selected_features,
                            st.session_state.ui_design_spec,
                            user_feedback
                        )
                        
                        if updated_design:
                            st.session_state.ui_design_spec = updated_design
                            
                            # Generate updated mockup for single-page website
                            mockup_html = generate_html_mockup(
                                st.session_state.selected_features[0],
                                updated_design,
                                all_features=st.session_state.selected_features
                            )
                            
                            # Store the updated mockup
                            st.session_state.ui_page_mockups = {"single_page": mockup_html}
                            
                            # Regenerate code
                            generate_all_code()
                            
                            # Add confirmation
                            add_message("assistant", "✅ Website updated based on your feedback! Check the preview.")
                    except Exception as e:
                        add_message("assistant", f"Error updating the design: {str(e)}")
                
                st.rerun()

# === RIGHT COLUMN: Preview Area ===
with right_col:
    # Show different content based on conversation stage
    if st.session_state.conversation_stage in ["initial", "verification"]:
        st.markdown("### Website Preview")
        st.info("Describe your website on the left and click 'Build My Website'")
        # Show sample placeholder
        st.image("https://via.placeholder.com/800x500?text=Your+Website+Preview+Will+Appear+Here", use_container_width=True)
    
    elif st.session_state.conversation_stage == "feature_selection":
        st.markdown("### Website Preview")
        st.info("Select features for your website on the left.")
        # Show sample placeholder with selected features
        if st.session_state.selected_features:
            features_text = "\n".join([f"- {feature}" for feature in st.session_state.selected_features])
            st.text_area("Selected Features:", value=features_text, height=200, disabled=True)
            # Add a placeholder image for aesthetics
            st.image("https://via.placeholder.com/800x300?text=Features+Selected", use_container_width=True)
        else:
            st.image("https://via.placeholder.com/800x450?text=Select+Features+to+Preview+Website", use_container_width=True)
    
    elif st.session_state.conversation_stage in ["refinement"]:
        st.markdown("### Your Website")
        # Single-page website preview
        if st.session_state.ui_page_mockups:
            # Display the single-page website mockup
            with st.container():
                try:
                    # Use st.components.v1.html to render the mockup
                    st.components.v1.html(
                        st.session_state.ui_page_mockups["single_page"], 
                        height=600,
                        scrolling=True
                    )
                except Exception as e:
                    st.error(f"Error displaying preview: {str(e)}")
                    st.info("Generating a new preview...")
                    # Fallback to a simple placeholder
                    st.image("https://via.placeholder.com/800x500?text=Website+Preview", use_container_width=True)
            
            # Display download instructions
            st.info("👈 Use the sidebar to download your website code")
            
        else:
            st.warning("No website preview available yet.")
            st.image("https://via.placeholder.com/800x450?text=Website+Generation+in+Progress", use_container_width=True)
    
    else:
        # Show loading animation during generation
        if st.session_state.is_generating:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            # Display progress bar
            progress_placeholder.progress(st.session_state.generation_progress / 100)
            status_placeholder.info(st.session_state.generation_status)
            
            # Add a visual animation
            cols = st.columns(5)
            for i, col in enumerate(cols):
                if (int(time.time() * 2) % 5) == i:
                    col.markdown("🔄")
                else:
                    col.markdown("⚪")
                    
            # Show a placeholder image
            st.image("https://via.placeholder.com/800x450?text=Building+Your+Website...", use_container_width=True)
        else:
            st.info("Complete the steps on the left to see your website preview here.")
            st.image("https://via.placeholder.com/800x450?text=Website+Preview+Coming+Soon", use_container_width=True)

# Clear conversation button (always available)
if st.sidebar.button("Start Over", key="clear_btn"):
    # Reset all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
