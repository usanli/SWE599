import streamlit as st
import os
import json
import tempfile
import shutil
import zipfile
import threading
import time
import re
import subprocess
import socket
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import webbrowser

# LLM imports for multiagent AI system
from dotenv import load_dotenv
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "your_unsplash_key_here")

# Debug: Check if API keys are loaded (without exposing them)
if OPENAI_API_KEY:
    print(f"OpenAI API key loaded: {OPENAI_API_KEY[:8]}...")
if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_key_here":
    print(f"Unsplash API key loaded: {UNSPLASH_ACCESS_KEY[:8]}...")

# Configure Streamlit page
st.set_page_config(
    page_title="WebWeaver",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize LLM models for multiagent system
def get_available_llm():
    """Get the best available LLM model"""
    try:
        if OPENAI_API_KEY and OPENAI_AVAILABLE and ChatOpenAI:
            try:
                llm = ChatOpenAI(
                    model="gpt-4o",
                    api_key=OPENAI_API_KEY,
                    temperature=0.7
                )
                # Just create the model, don't test it during startup for speed
                return llm, "OpenAI GPT-4o"
            except Exception as e:
                print(f"OpenAI initialization failed: {e}")
                return None, "OpenAI Failed"
                
    except Exception as e:
        print(f"LLM initialization error: {e}")
    
    return None, "No LLM Available"

# Global LLM variables (initialized on first use)
LLM_MODEL = None
LLM_NAME = "No LLM Available"
_llm_initialized = False

def log_agent_communication(source, target, message, details=None):
    """Log agent-to-agent communication to console"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Log to console instead of UI
    print(f"[{timestamp}] {source} → {target}: {message}")
    if details:
        print(f"  Details: {details}")
    
    # Still keep a minimal log for debugging if needed
    if 'agent_log' not in st.session_state:
        st.session_state.agent_log = []
    
    log_entry = {
        'timestamp': timestamp,
        'source': source,
        'target': target,
        'message': f"{source} → {target}: {message}",
        'details': details
    }
    
    st.session_state.agent_log.append(log_entry)
    
    # Keep only last 10 entries
    if len(st.session_state.agent_log) > 10:
        st.session_state.agent_log.pop(0)

class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events for auto-reload"""
    def __init__(self, callback):
        self.callback = callback
        
    def on_modified(self, event):
        if not event.is_directory and (event.src_path.endswith('.html') or event.src_path.endswith('.css')):
            self.callback()

class PreviewAgent:
    """Manages live preview server and auto-reload"""
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.server_port = self.find_free_port()
        self.server_process = None
        self.observer = None
        self.reload_trigger = 0
        
    def find_free_port(self):
        """Find an available port for the HTTP server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def start_server(self):
        """Start HTTP server in workspace directory"""
        if self.server_process is None:
            try:
                self.server_process = subprocess.Popen(
                    ['python', '-m', 'http.server', str(self.server_port)],
                    cwd=self.workspace_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(1)  # Give server time to start
            except Exception as e:
                st.error(f"Failed to start server: {e}")
    
    def start_file_watcher(self):
        """Start watching for file changes"""
        if self.observer is None:
            event_handler = FileChangeHandler(self.trigger_reload)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.workspace_path, recursive=True)
            self.observer.start()
    
    def trigger_reload(self):
        """Trigger iframe reload by incrementing counter"""
        self.reload_trigger += 1
        if 'reload_trigger' in st.session_state:
            st.session_state.reload_trigger = self.reload_trigger
    
    def stop(self):
        """Stop server and file watcher"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

class SpecAgent:
    """Enhanced requirement gathering for truly custom websites"""
    @staticmethod
    def collect_specs():
        """Collect detailed user specifications through comprehensive wizard"""
        st.sidebar.header("🧙‍♂️ Website Builder")
        
        # Step 1: Business/Purpose
        st.sidebar.subheader("1️⃣ What's Your Purpose?")
        purpose = st.sidebar.selectbox(
            "Website purpose:",
            ["Personal Portfolio", "Business/Corporate", "E-commerce Store", "Restaurant/Food", 
             "Medical/Healthcare", "Legal Services", "Technology/Software", "Consulting", 
             "Real Estate", "Education", "Non-profit", "Creative/Agency", "Other"],
            key='purpose'
        )
        
        if purpose == "Other":
            custom_purpose = st.sidebar.text_input("Describe your purpose:", key='custom_purpose')
            purpose = custom_purpose if custom_purpose else "General Business"
        
        # Step 2: Detailed Business Info
        st.sidebar.subheader("2️⃣ Business Details")
        business_name = st.sidebar.text_input(
            "Business/Site name:", 
            value=st.session_state.get('business_name', ''),
            key='business_name'
        )
        
        industry_focus = st.sidebar.text_area(
            "What do you do? (be specific):",
            placeholder="e.g., 'SAP implementation consulting for Fortune 500 companies' or 'Italian fine dining restaurant with wood-fired pizza'",
            height=80,
            key='industry_focus'
        )
        
        target_audience = st.sidebar.text_input(
            "Who are your customers?",
            placeholder="e.g., 'Enterprise CTOs', 'Young professionals', 'Local families'",
            key='target_audience'
        )
        
        # Step 3: Style & Design Preferences
        st.sidebar.subheader("3️⃣ Design Style")
        design_style = st.sidebar.selectbox(
            "Design style preference:",
            ["Modern & Minimalist", "Professional Corporate", "Creative & Artistic", 
             "Traditional & Classic", "Tech/Futuristic", "Warm & Friendly", 
             "Luxury & Premium", "Playful & Colorful"],
            key='design_style'
        )
        
        color_scheme = st.sidebar.selectbox(
            "Color preference:",
            ["Brand Colors (specify below)", "Blue Professional", "Elegant Dark", 
             "Warm & Welcoming", "Fresh & Green", "Creative & Colorful", "Monochrome", "Custom"],
            key='color_scheme'
        )
        
        if color_scheme in ["Brand Colors (specify below)", "Custom"]:
            primary_color = st.sidebar.color_picker("Primary color:", value='#3498db', key='primary_color')
        else:
            # Set predefined colors based on selection
            color_map = {
                "Blue Professional": "#2c3e50",
                "Elegant Dark": "#1a1a1a", 
                "Warm & Welcoming": "#e67e22",
                "Fresh & Green": "#27ae60",
                "Creative & Colorful": "#9b59b6",
                "Monochrome": "#34495e"
            }
            primary_color = color_map.get(color_scheme, "#3498db")
        
        # Step 4: Content & Features
        st.sidebar.subheader("4️⃣ Required Features")
        
        # Core sections
        core_sections = st.sidebar.multiselect(
            "Core sections needed:",
            ["Hero/Welcome", "About Us", "Services/Products", "Portfolio/Gallery", 
             "Team", "Testimonials", "Pricing", "Blog/News", "Contact"],
            default=["Hero/Welcome", "About Us", "Services/Products", "Contact"],
            key='core_sections'
        )
        
        # Special features
        special_features = st.sidebar.multiselect(
            "Special features:",
            ["Contact Form", "Newsletter Signup", "Social Media Links", "Live Chat", 
             "Appointment Booking", "E-commerce Cart", "Search Function", "Multi-language",
             "Download Section", "FAQ Section"],
            key='special_features'
        )
        
        # Step 5: Content Specifics
        st.sidebar.subheader("5️⃣ Content Details")
        key_messages = st.sidebar.text_area(
            "Key messages to highlight:",
            placeholder="e.g., '20+ years experience', 'Award-winning service', 'Available 24/7'",
            height=80,
            key='key_messages'
        )
        
        unique_selling_points = st.sidebar.text_area(
            "What makes you unique?:",
            placeholder="e.g., 'Only certified SAP partner in the region', 'Family recipes from Italy'",
            height=80,
            key='unique_selling_points'
        )
        
        # Create comprehensive specification object
        spec = {
            'purpose': purpose,
            'business_name': business_name,
            'industry_focus': industry_focus,
            'target_audience': target_audience,
            'design_style': design_style,
            'color_scheme': color_scheme,
            'primary_color': primary_color,
            'core_sections': core_sections,
            'special_features': special_features,
            'key_messages': key_messages,
            'unique_selling_points': unique_selling_points,
            
            # Legacy compatibility
            'site_title': business_name if business_name else "My Website",
            'needs_nav': True,
            'sections': core_sections if core_sections else ['hero', 'about', 'contact']
        }
        
        # Simple validation
        if not business_name:
            st.sidebar.warning("⚠️ Enter business name")
        elif not industry_focus:
            st.sidebar.warning("⚠️ Describe what you do")
        else:
            st.sidebar.success("✅ Ready to build")
        
        return spec

class CodeAgent:
    """Generates single HTML file with embedded CSS and JavaScript"""
    @staticmethod
    def generate_files(spec, workspace_path):
        """Generate single index.html file with embedded CSS and JS"""
        
        if LLM_MODEL:
            # Step 1: ProductManager refines requirements
            with st.spinner("Analyzing requirements..."):
                log_agent_communication("SpecAgent", "ProductManager", "Sending user specifications", 
                                       f"Business: {spec.get('business_name')}, Style: {spec.get('design_style')}")
                
                refined_specs = ProductManagerAgent.refine_initial_requirements(spec)
                
                log_agent_communication("ProductManager", "CodeAgent", "Sending refined specifications",
                                       f"Risk assessment completed, brand strategy defined")
            
            # Step 2: Use refined specs for intelligent generation
            with st.spinner("Creating website..."):
                log_agent_communication("CodeAgent", "LLM", "Generating HTML with specifications",
                                       f"Prompt length: {len(str(refined_specs)) if refined_specs else 0} chars")
                html_content = CodeAgent.generate_single_file_with_llm(spec, refined_specs)
                log_agent_communication("CodeAgent", "System", "Website generation completed",
                                       f"HTML length: {len(html_content)} chars")
        else:
            # Only use templates when NO LLM is available
            st.warning("⚠️ No LLM available - using basic templates. Add API keys for AI generation!")
            html_content = CodeAgent.generate_single_file_template(spec)
        
        # Write single file
        with open(os.path.join(workspace_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Create a placeholder styles.css for backward compatibility (empty file)
        with open(os.path.join(workspace_path, 'styles.css'), 'w', encoding='utf-8') as f:
            f.write('/* All styles are embedded in index.html for better cohesion */')
    
    @staticmethod
    def generate_single_file_with_llm(spec, refined_specs=None, retry_count=0):
        """Generate Fortune 500-quality single HTML file with embedded CSS and JS"""
        if not LLM_MODEL:
            st.error("❌ No LLM available for HTML generation")
            return CodeAgent.generate_single_file_template(spec)
        
        # Use refined specifications if available
        if refined_specs:
            brand_strategy = refined_specs.get('brand_strategy', {})
            design_system = refined_specs.get('design_system', {})
            content_strategy = refined_specs.get('content_strategy', {})
            technical_specs = refined_specs.get('technical_specs', {})
            
            # Create enhanced prompt using ProductManager specifications
            prompt = f"""You are a world-class web designer implementing detailed product specifications from a Senior Product Manager. Create a complete, professional website in a SINGLE HTML file with embedded CSS and JavaScript.

PRODUCT MANAGER SPECIFICATIONS:

**BRAND STRATEGY:**
• Positioning: {brand_strategy.get('positioning', 'Professional services')}
• Tone of Voice: {brand_strategy.get('tone_of_voice', 'Professional')}
• Value Proposition: {brand_strategy.get('value_proposition', 'Expert solutions')}
• Target Persona: {brand_strategy.get('target_persona', 'Business decision makers')}

**DESIGN SYSTEM:**
• Primary Color: {design_system.get('primary_color', '#3498db')}
• Secondary Color: {design_system.get('secondary_color', '#2c3e50')}
• Accent Color: {design_system.get('accent_color', '#e74c3c')}
• Typography: {design_system.get('typography', 'Modern, professional fonts')}
• Visual Style: {design_system.get('visual_style', 'Clean and professional')}

**CONTENT STRATEGY:**
• Hero Headline: {content_strategy.get('hero_headline', spec.get('business_name', 'Professional Services'))}
• Hero Subline: {content_strategy.get('hero_subline', spec.get('industry_focus', 'Expert solutions'))}

**SECTION SPECIFICATIONS:**"""

            # Add detailed section specifications
            for section in content_strategy.get('key_sections', []):
                prompt += f"""
• {section.get('name', 'Section')}: {section.get('purpose', 'Professional content')}
  Content: {section.get('content_outline', 'Industry expertise and solutions')}
  Design: {section.get('design_notes', 'Clean, professional layout')}"""

            prompt += f"""

**TECHNICAL IMPLEMENTATION:**
• Layout System: {technical_specs.get('layout_type', 'CSS Grid and Flexbox')}
• Responsive Design: {technical_specs.get('responsive_breakpoints', 'Mobile-first approach')}
• Interactions: {', '.join(technical_specs.get('interactive_elements', ['Smooth scrolling']))}
• Performance: {technical_specs.get('performance_requirements', 'Fast loading, optimized')}

**SINGLE-FILE ARCHITECTURE REQUIREMENTS:**
• All CSS embedded in <style> tags in the <head>
• Optional JavaScript embedded in <script> tags
• No external dependencies except Google Fonts (optional)
• Self-contained, deployable anywhere

**QUALITY STANDARDS:**
• Fortune 500-level visual quality and professionalism
• Modern design patterns and best practices
• Responsive across all devices
• Accessibility compliance (WCAG 2.1 AA)
• Fast loading and optimized performance

**CONVERSION OPTIMIZATION:**
• Clear value propositions throughout
• Strategic placement of contact information
• Professional credibility indicators
• Mobile-optimized user experience

CRITICAL OUTPUT INSTRUCTIONS:
- Return ONLY the complete HTML document
- Start with <!DOCTYPE html> and end with </html>
- Do NOT include any explanatory text before or after the HTML
- Do NOT include markdown code blocks or formatting
- The response should be pure, clean HTML code that can be used directly

Generate the complete HTML document implementing these detailed specifications:"""

        else:
            # Fallback to original prompt if no refined specs
            sections_list = ', '.join(spec.get('core_sections', ['Hero/Welcome', 'About Us', 'Contact']))
            features_list = ', '.join(spec.get('special_features', []))
            
            prompt = f"""You are a world-class web designer and developer creating a complete, professional website in a SINGLE HTML file. This will include embedded CSS and JavaScript for a cohesive, high-quality result.

CLIENT BRIEF - PREMIUM {spec.get('business_name', 'Business')} WEBSITE:

BUSINESS CONTEXT:
• Industry: {spec.get('purpose', 'Business')} 
• Company: {spec.get('business_name', 'Business')}
• Services: {spec.get('industry_focus', 'Professional services')}
• Target Audience: {spec.get('target_audience', 'Enterprise decision makers')}
• Design Style: {spec.get('design_style', 'Modern & Minimalist')}
• Brand Colors: {spec.get('color_scheme', 'Professional')} palette
• Primary Color: {spec.get('primary_color', '#3498db')}

CONTENT REQUIREMENTS:
• Key Messages: {spec.get('key_messages', 'Excellence and expertise')}
• Unique Value: {spec.get('unique_selling_points', 'Industry-leading solutions')}
• Required Sections: {sections_list}
• Special Features: {features_list if features_list else 'Professional essentials'}

SINGLE-FILE ARCHITECTURE REQUIREMENTS:

**1. COMPLETE EMBEDDED DESIGN:**
• All CSS embedded in <style> tags in the <head>
• Optional JavaScript embedded in <script> tags
• No external dependencies except Google Fonts (optional)
• Self-contained, deployable anywhere

**2. PROFESSIONAL VISUAL DESIGN:**
• Professional color palette with sophisticated gradients
• Modern typography (Inter, SF Pro, or web-safe alternatives)  
• Perfect spacing and visual hierarchy
• Subtle shadows, rounded corners, and premium effects
• Responsive grid layouts using CSS Grid and Flexbox

CRITICAL OUTPUT INSTRUCTIONS:
- Return ONLY the complete HTML document
- Start with <!DOCTYPE html> and end with </html>
- Do NOT include any explanatory text before or after the HTML
- Do NOT include markdown code blocks or formatting
- The response should be pure, clean HTML code that can be used directly

Generate the complete HTML document now:"""

        try:
            # Log prompt to console for debugging
            print(f"\n[CodeAgent] Sending prompt to LLM ({len(prompt)} chars)")
            print(f"[CodeAgent] Prompt preview: {prompt[:200]}...")
            
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            print(f"[CodeAgent] LLM response received ({len(content)} chars)")
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'html')
            
            if FeedbackAgent._validate_html(content):
                if refined_specs:
                    return content
                else:
                    return content
            else:
                if retry_count < 2:
                    st.warning(f"🔄 HTML validation failed, retrying with enhanced requirements... ({retry_count + 1}/3)")
                    return CodeAgent.generate_single_file_with_llm(spec, refined_specs, retry_count + 1)
                else:
                    st.error("❌ LLM failed to generate valid HTML after 3 attempts")
                    return CodeAgent.generate_single_file_template(spec)
                    
        except Exception as e:
            if retry_count < 2:
                st.warning(f"🔄 LLM error in generation, retrying... ({retry_count + 1}/3): {str(e)[:100]}")
                return CodeAgent.generate_single_file_with_llm(spec, refined_specs, retry_count + 1)
            else:
                st.error(f"❌ LLM generation failed after 3 attempts: {str(e)}")
                return CodeAgent.generate_single_file_template(spec)
    
    @staticmethod
    def generate_single_file_template(spec):
        """Generate single HTML file template (fallback)"""
        nav_items = ['Home', 'About', 'Services', 'Contact']
        nav_links = ''.join([f'<a href="#{item.lower()}" class="nav-link">{item}</a>' for item in nav_items])
        
        sections_html = ""
        for section in spec.get('core_sections', ['Hero/Welcome', 'About Us', 'Contact']):
            section_id = section.replace(' ', '-').replace('/', '-').lower()
            sections_html += f"""
        <section id="{section_id}" class="section">
            <div class="container">
                <h2>{section}</h2>
                <p>This is the {section} section. Professional content will be added here.</p>
                {CodeAgent.get_section_content_template(section)}
            </div>
        </section>"""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec.get('business_name', 'My Business')} | Professional Services</title>
    <style>
        /* Modern CSS Variables */
        :root {{
            --primary-color: {spec.get('primary_color', '#3498db')};
            --primary-dark: #2980b9;
            --secondary-color: #2c3e50;
            --accent-color: #e74c3c;
            --text-color: #2c3e50;
            --text-light: #7f8c8d;
            --background: #ffffff;
            --surface: #f8fafc;
            --border: #e1e8ed;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
            --border-radius: 8px;
            --spacing: 2rem;
        }}
        
        /* Modern Reset */
        *, *::before, *::after {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background: var(--background);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 var(--spacing);
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            color: white;
            padding: var(--spacing) 0;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        /* Navigation */
        .navbar {{
            background: var(--secondary-color);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .nav-link {{
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            margin: 0 0.5rem;
            border-radius: var(--border-radius);
            transition: background 0.3s ease;
        }}
        
        .nav-link:hover {{
            background: rgba(255,255,255,0.1);
        }}
        
        /* Sections */
        .section {{
            padding: var(--spacing) 0;
        }}
        
        .section:nth-child(even) {{
            background: var(--surface);
        }}
        
        .section h2 {{
            font-size: 2.5rem;
            margin-bottom: 1rem;
            text-align: center;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 2rem; }}
            .section h2 {{ font-size: 2rem; }}
            .container {{ padding: 0 1rem; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>{spec.get('business_name', 'My Business')}</h1>
            <p>Professional {spec.get('purpose', 'Business')} Services</p>
        </div>
    </header>
    
    <nav class="navbar">
        <div class="container">
            {nav_links}
        </div>
    </nav>
    
    <main>
        {sections_html}
    </main>
    
    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('.nav-link').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    @staticmethod
    def get_section_content_template(section):
        """Generate specific content for different sections"""
        if 'contact' in section.lower():
            return """
                <div style="max-width: 600px; margin: 2rem auto;">
                    <form style="background: white; padding: 2rem; border-radius: 8px; box-shadow: var(--shadow);">
                        <input type="text" placeholder="Your Name" style="width: 100%; padding: 1rem; margin-bottom: 1rem; border: 2px solid var(--border); border-radius: 4px;" required>
                        <input type="email" placeholder="Your Email" style="width: 100%; padding: 1rem; margin-bottom: 1rem; border: 2px solid var(--border); border-radius: 4px;" required>
                        <textarea placeholder="Your Message" rows="4" style="width: 100%; padding: 1rem; margin-bottom: 1rem; border: 2px solid var(--border); border-radius: 4px;" required></textarea>
                        <button type="submit" style="background: var(--primary-color); color: white; padding: 1rem 2rem; border: none; border-radius: 4px; cursor: pointer;">Send Message</button>
                    </form>
                </div>"""
        elif 'services' in section.lower() or 'products' in section.lower():
            return """
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem;">
                    <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: var(--shadow);">
                        <h3>Professional Service 1</h3>
                        <p>Comprehensive solutions tailored to your business needs.</p>
                    </div>
                    <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: var(--shadow);">
                        <h3>Expert Consultation</h3>
                        <p>Strategic guidance from industry professionals.</p>
                    </div>
                    <div style="background: white; padding: 2rem; border-radius: 8px; box-shadow: var(--shadow);">
                        <h3>Ongoing Support</h3>
                        <p>Dedicated support to ensure your continued success.</p>
                    </div>
                </div>"""
        else:
            return ""

class FeedbackAgent:
    """Handles stateful, incremental website updates with memory and context awareness"""
    @staticmethod
    def parse_and_apply_feedback(feedback, workspace_path):
        """Parse user feedback and apply changes to the single HTML file"""
        try:
            if not LLM_MODEL:
                return FeedbackAgent._fallback_single_file_parsing(feedback, workspace_path)
            
            # Step 1: ProductManager analyzes and refines the user feedback
            with st.spinner("Analyzing feedback..."):
                log_agent_communication("User", "FeedbackAgent", f"Feedback: {feedback[:50]}...", 
                                       f"Full feedback: {feedback}")
                
                context = st.session_state.website_context
                website_state = {"architecture": "single_file", "responsive": True}
                
                log_agent_communication("FeedbackAgent", "ProductManager", "Requesting feedback analysis",
                                       f"Context: {context.get('business_type')}")
                
                feedback_analysis = ProductManagerAgent.refine_user_feedback(feedback, context, website_state)
                
                log_agent_communication("ProductManager", "FeedbackAgent", "Analysis complete",
                                       f"Risk: {feedback_analysis.get('change_analysis', {}).get('risk_level', 'unknown')}")
            
            # Step 2: Update conversation memory with refined analysis
            FeedbackAgent._update_conversation_memory(feedback, feedback_analysis)
            
            # Step 3: Read current single HTML file
            html_path = os.path.join(workspace_path, 'index.html')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                current_html = f.read()
            
            # Step 4: Apply changes using ProductManager's refined specifications
            with st.spinner("Applying changes..."):
                log_agent_communication("FeedbackAgent", "CodeAgent", "Requesting implementation",
                                       f"Risk level: {feedback_analysis.get('change_analysis', {}).get('risk_level', 'medium')}")
                
                new_html = FeedbackAgent._apply_single_file_changes_with_pm(
                    feedback, current_html, feedback_analysis
                )
                
                if new_html:
                    log_agent_communication("CodeAgent", "FeedbackAgent", "Implementation successful",
                                           f"Changes applied successfully")
                else:
                    log_agent_communication("CodeAgent", "FeedbackAgent", "Implementation failed",
                                           f"No changes made or failed validation")
            
            if not new_html:
                new_html = current_html
            
            # Step 5: Write updated file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            
            # Step 6: Update website context with ProductManager insights
            FeedbackAgent._update_website_context_with_pm(feedback, feedback_analysis)
            
            # Step 7: Log the change with risk assessment
            FeedbackAgent._log_pm_guided_change(feedback, feedback_analysis)
            
            if new_html != current_html:
                risk_level = feedback_analysis.get('change_analysis', {}).get('risk_level', 'medium')
                return True, f"✅ Update complete (Risk: {risk_level})"
            else:
                return False, f"ℹ️ No changes needed - current state optimal"
            
        except Exception as e:
            st.error(f"❌ Agent communication error: {str(e)}")
            return False, f"❌ Update failed: {str(e)}"
    
    @staticmethod
    def _apply_single_file_changes_with_pm(feedback, current_html, pm_analysis):
        """Apply changes using ProductManager's refined specifications"""
        if not LLM_MODEL:
            return None
        
        # Use ProductManager's refined prompt
        refined_prompt = pm_analysis.get('refined_prompt', f"Apply this change safely: {feedback}")
        
        # Get technical requirements from ProductManager
        tech_requirements = pm_analysis.get('technical_requirements', {})
        target_elements = tech_requirements.get('target_elements', [])
        preserve_elements = tech_requirements.get('preserve_elements', [])
        
        # Create enhanced prompt with ProductManager specifications
        enhanced_prompt = f"""You are a professional web developer implementing changes specified by a Senior Product Manager. Apply the requested modifications while maintaining all existing functionality and quality.

PRODUCT MANAGER'S REFINED SPECIFICATIONS:
{refined_prompt}

TECHNICAL REQUIREMENTS FROM PRODUCT MANAGER:
• Target Elements: {', '.join(target_elements) if target_elements else 'As specified in prompt'}
• Elements to Preserve: {', '.join(preserve_elements) if preserve_elements else 'All existing functionality'}
• Risk Level: {pm_analysis.get('change_analysis', {}).get('risk_level', 'medium')}
• Scope: {pm_analysis.get('change_analysis', {}).get('scope', 'targeted')}

IMPLEMENTATION STRATEGY:
• Approach: {pm_analysis.get('implementation_strategy', {}).get('approach', 'Make targeted changes')}
• Success Criteria: {pm_analysis.get('implementation_strategy', {}).get('success_criteria', 'User request fulfilled')}

CURRENT SINGLE HTML FILE:
{current_html}

CRITICAL SAFETY REQUIREMENTS:
• Make ONLY the changes specified by the Product Manager
• Preserve all existing navigation, styling, and functionality
• Maintain the single-file architecture with embedded CSS/JS
• Ensure responsive design remains intact
• Keep professional visual quality and consistency
• Test that all existing features continue to work

CRITICAL OUTPUT INSTRUCTIONS:
- Return ONLY the complete, updated HTML document
- Start with <!DOCTYPE html> and end with </html>
- Do NOT include any explanatory text before or after the HTML
- Do NOT include markdown code blocks or formatting
- The response should be pure, clean HTML code that can be used directly

Apply the ProductManager's specifications now:"""

        try:
            # Log feedback prompt to console
            print(f"\n[FeedbackAgent] Sending feedback prompt to LLM ({len(enhanced_prompt)} chars)")
            print(f"[FeedbackAgent] Prompt preview: {enhanced_prompt[:200]}...")
            
            response = LLM_MODEL.invoke(enhanced_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            print(f"[FeedbackAgent] LLM response received ({len(content)} chars)")
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'html')
            
            if FeedbackAgent._validate_html(content):
                change_ratio = FeedbackAgent._calculate_change_ratio(current_html, content)
                
                # Use ProductManager's risk assessment for validation
                risk_level = pm_analysis.get('change_analysis', {}).get('risk_level', 'medium')
                max_change_ratio = {'low': 0.95, 'medium': 0.85, 'high': 0.60}.get(risk_level, 0.85)
                
                if change_ratio > max_change_ratio:
                    print(f"Warning: Change too extensive ({change_ratio:.1%}) for {risk_level} risk, preserving stability")
                    return None
                elif change_ratio > 0:
                    return content
                else:
                    return None
            else:
                print("Warning: HTML validation failed, keeping current version for stability")
                return None
                
        except Exception as e:
            st.error(f"❌ ProductManager-guided implementation error: {str(e)[:100]}")
            return None
    
    @staticmethod
    def _update_conversation_memory(feedback, pm_analysis=None):
        """Update conversation memory with new user input and ProductManager analysis"""
        memory_entry = {
            'timestamp': time.time(),
            'type': 'user_feedback',
            'content': feedback,
            'context_snapshot': st.session_state.website_context.copy()
        }
        
        if pm_analysis:
            memory_entry.update({
                'pm_analysis': {
                    'risk_level': pm_analysis.get('change_analysis', {}).get('risk_level', 'medium'),
                    'scope': pm_analysis.get('change_analysis', {}).get('scope', 'targeted'),
                    'user_intent': pm_analysis.get('change_analysis', {}).get('user_intent', feedback)
                }
            })
        
        st.session_state.conversation_memory.append(memory_entry)
        
        # Keep only last 10 interactions to manage memory
        if len(st.session_state.conversation_memory) > 10:
            st.session_state.conversation_memory.pop(0)
    
    @staticmethod
    def _update_website_context_with_pm(feedback, pm_analysis):
        """Update website context using ProductManager insights"""
        context = st.session_state.website_context
        
        # Update based on ProductManager's analysis
        user_intent = pm_analysis.get('change_analysis', {}).get('user_intent', feedback)
        business_impact = pm_analysis.get('change_analysis', {}).get('business_impact', 'Improve user experience')
        
        # Standard context updates
        FeedbackAgent._update_website_context(feedback, {'intent': user_intent})
        
        # Add ProductManager-specific insights
        if 'pm_insights' not in context:
            context['pm_insights'] = []
        
        context['pm_insights'].append({
            'feedback': feedback,
            'intent': user_intent,
            'business_impact': business_impact,
            'risk_level': pm_analysis.get('change_analysis', {}).get('risk_level', 'medium'),
            'timestamp': time.time()
        })
        
        # Keep only last 5 PM insights
        if len(context['pm_insights']) > 5:
            context['pm_insights'].pop(0)
    
    @staticmethod
    def _log_pm_guided_change(feedback, pm_analysis):
        """Log ProductManager-guided changes for future reference"""
        change_log = {
            'feedback': feedback,
            'timestamp': time.time(),
            'pm_guided': True,
            'risk_level': pm_analysis.get('change_analysis', {}).get('risk_level', 'medium'),
            'scope': pm_analysis.get('change_analysis', {}).get('scope', 'targeted'),
            'user_intent': pm_analysis.get('change_analysis', {}).get('user_intent', feedback),
            'business_impact': pm_analysis.get('change_analysis', {}).get('business_impact', 'UX improvement'),
            'implementation_approach': pm_analysis.get('implementation_strategy', {}).get('approach', 'Targeted changes')
        }
        
        st.session_state.incremental_changes.append(change_log)
        
        # Keep only last 15 changes
        if len(st.session_state.incremental_changes) > 15:
            st.session_state.incremental_changes.pop(0)
    
    @staticmethod
    def _clean_code_response(content, file_type):
        """Clean LLM response to extract pure code"""
        if not content:
            return ""
        
        # Remove markdown code blocks
        content = content.strip()
        if content.startswith("```"):
            lines = content.split('\n')
            # Remove first line (```html or similar)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        return content.strip()
    
    @staticmethod
    def _validate_html(content):
        """Basic HTML validation"""
        if not content:
            return False
        
        content = content.strip()
        return (content.startswith('<!DOCTYPE html') or content.startswith('<html')) and content.endswith('</html>')
    
    @staticmethod
    def _calculate_change_ratio(old_content, new_content):
        """Calculate how much content has changed"""
        if not old_content or not new_content:
            return 1.0
        
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        # Simple line-based comparison
        total_lines = max(len(old_lines), len(new_lines))
        if total_lines == 0:
            return 0.0
        
        # Count different lines
        different_lines = 0
        for i in range(max(len(old_lines), len(new_lines))):
            old_line = old_lines[i] if i < len(old_lines) else ""
            new_line = new_lines[i] if i < len(new_lines) else ""
            if old_line.strip() != new_line.strip():
                different_lines += 1
        
        return different_lines / total_lines
    
    @staticmethod
    def _update_website_context(feedback, analysis):
        """Update website context with feedback"""
        context = st.session_state.website_context
        
        # Add to evolution log
        if 'evolution_log' not in context:
            context['evolution_log'] = []
        
        context['evolution_log'].append({
            'feedback': feedback,
            'intent': analysis.get('intent', feedback),
            'timestamp': time.time()
        })
        
        # Keep only last 10 entries
        if len(context['evolution_log']) > 10:
            context['evolution_log'].pop(0)
    
    @staticmethod
    def _fallback_single_file_parsing(feedback, workspace_path):
        """Fallback feedback processing without LLM"""
        try:
            html_path = os.path.join(workspace_path, 'index.html')
            if not os.path.exists(html_path):
                return False, "No website file found"
            
            # Simple text replacements for common requests
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Basic text replacements
            if 'dark' in feedback.lower() and 'header' in feedback.lower():
                content = content.replace('background: linear-gradient(135deg, var(--primary-color), var(--primary-dark))', 
                                        'background: linear-gradient(135deg, #1a1a1a, #000000)')
            
            if content != original_content:
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, "✅ Basic changes applied"
            else:
                return False, "No matching patterns found"
                
        except Exception as e:
            return False, f"Error: {str(e)}"

class PackageAgent:
    """Handles project packaging and download"""
    @staticmethod
    def create_zip(workspace_path):
        """Create a ZIP file of the workspace"""
        zip_path = os.path.join(workspace_path, 'site.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    if file != 'site.zip':  # Don't include the zip itself
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, workspace_path)
                        zipf.write(file_path, arc_name)
        
        return zip_path

class ImageService:
    """Handles professional image integration from free sources"""
    
    @staticmethod
    def get_business_images(business_type, sections, count=4):
        """Get relevant professional images for the business"""
        # Always use placeholder images for now to avoid broken image issues
        return ImageService._get_placeholder_images(business_type, count)
    
    @staticmethod
    def _get_unsplash_images(business_type, sections, count=4):
        """Fetch professional images from Unsplash API (disabled for now)"""
        # Temporarily disabled to fix broken image issues
        return ImageService._get_placeholder_images(business_type, count)
    
    @staticmethod
    def _get_placeholder_images(business_type, count=4):
        """Generate working placeholder images as fallback"""
        # Use reliable placeholder services
        images = []
        
        # Business-themed placeholder images with working URLs
        for i in range(count):
            # Use different sizes to create variety
            width = 800 + (i * 100)
            height = 400 + (i * 50)
            
            images.append({
                'url': f"https://via.placeholder.com/{width}x{height}/2c3e50/ffffff?text=Professional+{business_type.replace(' ', '+')}",
                'url_small': f"https://via.placeholder.com/400x200/2c3e50/ffffff?text=Business+Image",
                'alt': f'Professional {business_type} placeholder',
                'photographer': 'Placeholder Service',
                'photographer_url': '#'
            })
        
        return images
    
    @staticmethod
    def create_image_html(images, business_type):
        """Create HTML code for embedding images - DISABLED for now"""
        # Disable image integration until properly working
        return ""

class ProductManagerAgent:
    """Intelligent product management layer that refines user requirements and feedback into safe technical specifications"""
    
    @staticmethod
    def refine_initial_requirements(spec):
        """Take user specs and create detailed technical requirements for CodeAgent"""
        if not LLM_MODEL:
            return ProductManagerAgent._create_basic_requirements(spec)
        
        # Create comprehensive product specification
        raw_requirements = {
            'business_name': spec.get('business_name', ''),
            'industry': spec.get('purpose', ''),
            'focus': spec.get('industry_focus', ''),
            'audience': spec.get('target_audience', ''),
            'style': spec.get('design_style', ''),
            'sections': spec.get('core_sections', []),
            'features': spec.get('special_features', []),
            'messages': spec.get('key_messages', ''),
            'unique_value': spec.get('unique_selling_points', '')
        }
        
        prompt = f"""You are a Senior Product Manager working with a development team to create a professional business website. Your job is to take raw user requirements and convert them into detailed, technical specifications that will produce a cohesive, high-quality result.

RAW USER REQUIREMENTS:
• Business: {raw_requirements['business_name']}
• Industry: {raw_requirements['industry']} 
• Focus: {raw_requirements['focus']}
• Target Audience: {raw_requirements['audience']}
• Design Style: {raw_requirements['style']}
• Required Sections: {', '.join(raw_requirements['sections'])}
• Special Features: {', '.join(raw_requirements['features'])}
• Key Messages: {raw_requirements['messages']}
• Unique Value Proposition: {raw_requirements['unique_value']}

PRODUCT MANAGER TASKS:

1. **ANALYZE BUSINESS CONTEXT**
   - Determine the appropriate industry positioning and competitive landscape
   - Identify the target audience's primary pain points and expectations
   - Define the conversion goals and success metrics

2. **DEFINE TECHNICAL REQUIREMENTS**
   - Specify exact color palette and typography choices
   - Detail the information architecture and user flow
   - Define responsive behavior and accessibility requirements
   - Specify content strategy and messaging hierarchy

3. **CREATE DEVELOPMENT SPECIFICATIONS**
   - Break down each section with specific content and functionality
   - Define the visual hierarchy and design system
   - Specify interactions and micro-animations
   - Ensure brand consistency and professional quality

4. **QUALITY ASSURANCE CRITERIA**
   - Define what "done" looks like for each section
   - Specify testing criteria and edge cases
   - Ensure scalability and maintainability

OUTPUT REFINED TECHNICAL SPECIFICATIONS:

Return a JSON object with the following structure:
{{
  "brand_strategy": {{
    "positioning": "Brief positioning statement",
    "tone_of_voice": "Professional, authoritative, etc.",
    "value_proposition": "Clear value prop",
    "target_persona": "Detailed audience description"
  }},
  "design_system": {{
    "primary_color": "Hex color",
    "secondary_color": "Hex color", 
    "accent_color": "Hex color",
    "typography": "Font system specification",
    "spacing": "Spacing system",
    "visual_style": "Detailed style guide"
  }},
  "content_strategy": {{
    "hero_headline": "Specific headline text",
    "hero_subline": "Supporting text",
    "key_sections": [
      {{
        "name": "Section name",
        "purpose": "What this section accomplishes",
        "content_outline": "Specific content to include",
        "design_notes": "How it should look and feel"
      }}
    ]
  }},
  "technical_specs": {{
    "layout_type": "Grid system to use",
    "responsive_breakpoints": "Mobile, tablet, desktop specs",
    "interactive_elements": "List of interactions needed",
    "performance_requirements": "Loading and optimization notes"
  }},
  "success_criteria": {{
    "primary_goals": ["Goal 1", "Goal 2"],
    "conversion_points": ["CTA 1", "CTA 2"],
    "quality_standards": ["Standard 1", "Standard 2"]
  }}
}}

Focus on creating specifications that will result in a cohesive, professional website that effectively serves the business goals."""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON response
            try:
                import json
                # Clean the response to extract JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_content = content[json_start:json_end]
                    refined_specs = json.loads(json_content)
                    return refined_specs
            except:
                pass
            
            # Fallback to basic requirements if JSON parsing fails
            return ProductManagerAgent._create_basic_requirements(spec)
            
        except Exception as e:
            st.error(f"❌ ProductManager error: {str(e)[:50]}...")
            return ProductManagerAgent._create_basic_requirements(spec)
    
    @staticmethod
    def _create_basic_requirements(spec):
        """Create basic requirements structure as fallback"""
        return {
            "brand_strategy": {
                "positioning": f"Professional {spec.get('purpose', 'business')} services",
                "tone_of_voice": "Professional and trustworthy",
                "value_proposition": spec.get('unique_selling_points', 'Expert solutions'),
                "target_persona": spec.get('target_audience', 'Business decision makers')
            },
            "design_system": {
                "primary_color": spec.get('primary_color', '#3498db'),
                "secondary_color": "#2c3e50",
                "accent_color": "#e74c3c",
                "typography": "Modern, professional fonts",
                "spacing": "Consistent spacing system",
                "visual_style": "Clean and professional"
            },
            "content_strategy": {
                "hero_headline": f"Professional {spec.get('purpose', 'Business')} Services",
                "hero_subline": spec.get('industry_focus', 'Expert solutions for your business'),
                "key_sections": [
                    {
                        "name": section,
                        "purpose": f"Communicate {section.lower()} information",
                        "content_outline": f"Professional {section.lower()} content",
                        "design_notes": "Clean and professional layout"
                    } for section in spec.get('core_sections', ['About', 'Services', 'Contact'])
                ]
            },
            "technical_specs": {
                "layout_type": "CSS Grid and Flexbox",
                "responsive_breakpoints": "Mobile-first design",
                "interactive_elements": ["Smooth scrolling", "Contact forms"],
                "performance_requirements": "Fast loading, optimized"
            },
            "success_criteria": {
                "primary_goals": ["Generate leads", "Build credibility"],
                "conversion_points": ["Contact form", "Phone number"],
                "quality_standards": ["Professional appearance", "Mobile responsive"]
            }
        }
    
    @staticmethod
    def refine_user_feedback(feedback, current_context, website_state):
        """Refine user feedback into safe, incremental technical changes"""
        if not LLM_MODEL:
            return ProductManagerAgent._create_basic_feedback_refinement(feedback)
        
        prompt = f"""You are a Senior Product Manager working with a development team. A user has provided feedback on their website, and you need to refine this into safe, specific technical instructions that won't break existing functionality.

USER FEEDBACK: "{feedback}"

CURRENT WEBSITE CONTEXT:
• Business Type: {current_context.get('business_type', 'general')}
• Current Theme: {current_context.get('current_theme', 'basic')}
• Key Features: {', '.join(current_context.get('key_features', []))}
• Style Preferences: {current_context.get('style_preferences', {})}

WEBSITE TECHNICAL STATE:
• Architecture: Single HTML file with embedded CSS/JS
• Current Sections: Multiple sections with navigation
• Responsive: Mobile and desktop optimized
• Interactive Elements: Smooth scrolling, contact forms

PRODUCT MANAGER ANALYSIS REQUIRED:

1. **INTERPRET USER INTENT**
   - What is the user really trying to achieve?
   - What business goal does this serve?
   - Are there any unstated requirements?

2. **RISK ASSESSMENT**
   - Could this change break existing functionality?
   - Will this conflict with other design elements?
   - Are there any technical limitations to consider?

3. **SCOPE DEFINITION**
   - What exactly needs to be changed?
   - What should NOT be changed to maintain quality?
   - How can we implement this safely?

4. **TECHNICAL TRANSLATION**
   - Convert business language into specific technical requirements
   - Define exact CSS/HTML changes needed
   - Specify testing criteria

OUTPUT REFINED CHANGE SPECIFICATION:

Return a JSON object with this structure:
{{
  "change_analysis": {{
    "user_intent": "What the user really wants to accomplish",
    "business_impact": "How this serves business goals",
    "risk_level": "low/medium/high",
    "scope": "specific/targeted/broad"
  }},
  "technical_requirements": {{
    "target_elements": ["Specific elements to modify"],
    "preserve_elements": ["Elements that must NOT change"],
    "css_changes": ["Specific CSS modifications needed"],
    "html_changes": ["Any HTML structure changes"],
    "testing_points": ["What to verify after changes"]
  }},
  "implementation_strategy": {{
    "approach": "How to implement safely",
    "fallback_plan": "What to do if it breaks",
    "validation_steps": ["Steps to ensure quality"],
    "success_criteria": "How to know it worked"
  }},
  "refined_prompt": "Detailed technical prompt for the coding agent that will produce safe, high-quality results"
}}

Focus on creating specifications that will result in targeted improvements without breaking existing functionality."""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON response
            try:
                import json
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_content = content[json_start:json_end]
                    feedback_analysis = json.loads(json_content)
                    
                    risk_level = feedback_analysis.get('change_analysis', {}).get('risk_level', 'medium')
                    if risk_level == 'high':
                        st.warning(f"⚠️ ProductManager: High-risk change detected - {feedback}")
                    
                    return feedback_analysis
            except:
                pass
            
            # Fallback to basic refinement
            return ProductManagerAgent._create_basic_feedback_refinement(feedback)
            
        except Exception as e:
            st.error(f"❌ ProductManager error: {str(e)[:50]}...")
            return ProductManagerAgent._create_basic_feedback_refinement(feedback)
    
    @staticmethod
    def _create_basic_feedback_refinement(feedback):
        """Create basic feedback refinement as fallback"""
        return {
            "change_analysis": {
                "user_intent": feedback,
                "business_impact": "Improve user experience",
                "risk_level": "medium",
                "scope": "targeted"
            },
            "technical_requirements": {
                "target_elements": ["Elements mentioned in feedback"],
                "preserve_elements": ["All existing functionality"],
                "css_changes": ["Style modifications as requested"],
                "html_changes": ["Minimal structure changes"],
                "testing_points": ["Verify change works", "Check nothing broke"]
            },
            "implementation_strategy": {
                "approach": "Make minimal, targeted changes",
                "fallback_plan": "Revert if issues occur",
                "validation_steps": ["Test on mobile and desktop"],
                "success_criteria": "User request fulfilled without breaking site"
            },
            "refined_prompt": f"Apply the following change safely: {feedback}. Make minimal modifications and preserve all existing functionality."
        }

def initialize_session():
    """Initialize session state variables"""
    if 'workspace_path' not in st.session_state:
        # Create unique workspace for this session
        st.session_state.workspace_path = tempfile.mkdtemp(prefix='webweaver_')
        st.session_state.preview_agent = None
        st.session_state.development_started = False
        st.session_state.reload_trigger = 0
    if 'feedback_history' not in st.session_state:
        st.session_state.feedback_history = []
    
    # Add memory/state management for incremental development
    if 'website_context' not in st.session_state:
        st.session_state.website_context = {
            'current_theme': 'generic website',
            'business_type': 'general',
            'key_features': [],
            'style_preferences': {},
            'content_focus': 'basic',
            'evolution_log': [],
            'user_intent_history': []
        }
    if 'conversation_memory' not in st.session_state:
        st.session_state.conversation_memory = []
    if 'incremental_changes' not in st.session_state:
        st.session_state.incremental_changes = []

def cleanup_old_workspaces():
    """Clean up old temporary workspaces"""
    try:
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith('webweaver_'):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path):
                    # Check if older than 1 hour
                    if time.time() - os.path.getctime(item_path) > 3600:
                        shutil.rmtree(item_path, ignore_errors=True)
    except:
        pass  # Ignore cleanup errors

def main():
    """Main Streamlit application"""
    global LLM_MODEL, LLM_NAME, _llm_initialized
    
    # Initialize
    initialize_session()
    cleanup_old_workspaces()
    
    # Initialize LLM on first run
    if not _llm_initialized:
        try:
            LLM_MODEL, LLM_NAME = get_available_llm()
            _llm_initialized = True
        except Exception as e:
            LLM_MODEL, LLM_NAME = None, "LLM Failed"
            _llm_initialized = True
    
    # Title
    st.title("🕸️ WebWeaver")
    st.markdown("*AI website builder*")
    
    # Simple API key setup for non-AI mode
    if not LLM_MODEL:
        with st.expander("Add API Key"):
            st.code("OPENAI_API_KEY=your_key_here")
    
    # Sidebar - SpecAgent
    with st.sidebar:
        spec = SpecAgent.collect_specs()
        
        # Start Development Button
        if st.button("🚀 Start Development", type="primary", use_container_width=True):
            if not spec.get('business_name') or not spec.get('industry_focus'):
                st.error("⚠️ Please complete the required fields: Business Name and Industry Focus")
            else:
                with st.spinner("Creating website..."):
                    # Store the comprehensive spec in session state
                    st.session_state.website_context.update({
                        'current_theme': f"{spec.get('purpose', 'business')} website",
                        'business_type': spec.get('purpose', 'business'),
                        'content_focus': spec.get('industry_focus', 'professional services'),
                        'key_features': spec.get('special_features', []),
                        'style_preferences': {
                            'design_style': spec.get('design_style', 'Modern'),
                            'color_scheme': spec.get('color_scheme', 'Professional'),
                            'primary_color': spec.get('primary_color', '#3498db')
                        }
                    })
                    
                    # Generate files
                    CodeAgent.generate_files(spec, st.session_state.workspace_path)
                    
                    # Start preview
                    if st.session_state.preview_agent:
                        st.session_state.preview_agent.stop()
                    
                    st.session_state.preview_agent = PreviewAgent(st.session_state.workspace_path)
                    st.session_state.preview_agent.start_server()
                    st.session_state.preview_agent.start_file_watcher()
                    st.session_state.development_started = True
                    
                    st.success("✅ Website created!")
                    st.rerun()
        
        # PackageAgent - Download ZIP
        if st.session_state.development_started:
            st.markdown("---")
            
            if st.button("📥 Download ZIP", use_container_width=True):
                zip_path = PackageAgent.create_zip(st.session_state.workspace_path)
                
                with open(zip_path, 'rb') as f:
                    st.download_button(
                        label="💾 Download site.zip",
                        data=f.read(),
                        file_name="site.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
    
    # Main content area
    if st.session_state.development_started and st.session_state.preview_agent:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("🔍 Live Preview")
            
            # Live preview iframe
            preview_url = f"http://localhost:{st.session_state.preview_agent.server_port}"
            
            # Use a unique key based on reload trigger to force refresh
            iframe_html = f"""
            <iframe 
                src="{preview_url}?t={st.session_state.reload_trigger}" 
                width="100%" 
                height="600" 
                style="border: 1px solid #ddd; border-radius: 8px;"
            ></iframe>
            """
            st.components.v1.html(iframe_html, height=600)
        
        with col2:
            st.subheader("🎨 FeedbackAgent")
            
            # Feedback input
            feedback_key = f"feedback_input_{st.session_state.get('feedback_counter', 0)}"
            feedback = st.text_area(
                "Describe changes:",
                placeholder="• Add a pricing section\n• Make header darker\n• Include testimonials",
                height=100,
                key=feedback_key
            )
            
            if st.button("🚀 Apply Changes", type="primary", use_container_width=True):
                if feedback.strip():
                    with st.spinner("Applying changes..."):
                        success, message = FeedbackAgent.parse_and_apply_feedback(
                            feedback, st.session_state.workspace_path
                        )
                    
                    if success:
                        st.success("✅ Updated")
                        st.session_state.feedback_history.append(feedback)
                        st.session_state.reload_trigger += 1
                        st.session_state.feedback_counter = st.session_state.get('feedback_counter', 0) + 1
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Describe what to change")
            
            # Simple history
            if st.session_state.get('incremental_changes'):
                with st.expander("Recent Changes"):
                    recent_changes = st.session_state.incremental_changes[-3:]
                    for change in reversed(recent_changes):
                        risk = change.get('risk_level', 'medium')
                        icon = {"low": "✅", "medium": "⚠️", "high": "🚨"}.get(risk, "⚠️")
                        feedback_text = change.get('user_intent', change.get('feedback', ''))[:30]
                        st.text(f"{icon} {feedback_text}...")
    
    else:
        # Simple welcome
        st.markdown("## Configure your website in the sidebar to get started")
        if not LLM_MODEL:
            st.info("💡 Add `OPENAI_API_KEY=your_key` to .env file for AI features")

if __name__ == "__main__":
    main() 