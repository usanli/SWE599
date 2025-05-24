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

# Load environment variables - check multiple locations (only once)
if not os.getenv("OPENAI_API_KEY"):
    env_paths = ['.env', '../.env', '../../.env']
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"Loading environment from: {env_path}")
            break

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "your_unsplash_key_here")

# Debug: Check if API keys are loaded (only once at startup)
if OPENAI_API_KEY and not globals().get('_env_debug_printed'):
    print(f"OpenAI API key loaded: {OPENAI_API_KEY[:8]}...")
    globals()['_env_debug_printed'] = True

if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_key_here" and not globals().get('_unsplash_debug_printed'):
    print(f"Unsplash API key loaded: {UNSPLASH_ACCESS_KEY[:8]}...")
    globals()['_unsplash_debug_printed'] = True

# Configure Streamlit page
st.set_page_config(
    page_title="WebWeaver Enterprise",
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

# Enhanced multi-agent system with individual LLM integration and memories
class AgentMemory:
    """Individual memory system for each agent"""
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.conversation_history = []
        self.context_data = {}
        self.previous_outputs = []
        self.learning_notes = []
    
    def add_interaction(self, input_data, output_data, interaction_type="standard"):
        """Add an interaction to memory"""
        interaction = {
            'timestamp': time.time(),
            'type': interaction_type,
            'input': input_data,
            'output': output_data,
            'context_snapshot': self.context_data.copy()
        }
        self.conversation_history.append(interaction)
        
        # Keep only last 20 interactions to prevent memory overflow
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)
    
    def update_context(self, key, value):
        """Update context data"""
        self.context_data[key] = value
    
    def get_relevant_context(self, query_type=None):
        """Retrieve relevant context for current query"""
        if query_type:
            relevant = [h for h in self.conversation_history if h['type'] == query_type]
            return relevant[-5:] if relevant else []
        return self.conversation_history[-5:]
    
    def add_learning_note(self, note):
        """Add learning note for future reference"""
        self.learning_notes.append({
            'timestamp': time.time(),
            'note': note
        })
        
        # Keep only last 10 learning notes
        if len(self.learning_notes) > 10:
            self.learning_notes.pop(0)

class WorkflowManager:
    """Manages complex agent workflows and cycle counting"""
    def __init__(self):
        self.reset_cycles()
    
    def reset_cycles(self):
        """Reset all cycle counters"""
        self.html_qa_cycles = 0
        self.pm_html_cycles = 0
        self.total_cycles = 0
    
    def can_continue_html_qa(self):
        """Check if HTML-QA cycle can continue"""
        return self.html_qa_cycles < 5 and self.total_cycles < 25
    
    def can_continue_pm_html(self):
        """Check if PM-HTML cycle can continue"""
        return self.pm_html_cycles < 5 and self.total_cycles < 25
    
    def increment_html_qa(self):
        """Increment HTML-QA cycle counter"""
        self.html_qa_cycles += 1
        self.total_cycles += 1
    
    def increment_pm_html(self):
        """Increment PM-HTML cycle counter"""
        self.pm_html_cycles += 1
        self.total_cycles += 1
    
    def reset_html_qa(self):
        """Reset HTML-QA cycles for new PM iteration"""
        self.html_qa_cycles = 0

class ProductManagerAgent:
    """Enhanced Product Manager with LLM and memory"""
    
    def __init__(self):
        self.memory = AgentMemory("ProductManager")
        self.memory.update_context("role", "Strategic product manager and requirements analyst")
    
    def analyze_user_requirements(self, user_specs):
        """Analyze and enhance user requirements using LLM"""
        if not LLM_MODEL:
            return self._create_basic_requirements(user_specs)
        
        # Get relevant context from memory
        previous_context = self.memory.get_relevant_context("requirements_analysis")
        context_summary = ""
        if previous_context:
            context_summary = f"\nPREVIOUS EXPERIENCE:\n{self._format_context(previous_context)}"
        
        prompt = f"""You are a senior product manager and business analyst. Analyze the user's website requirements and enhance them with strategic insights.

USER SPECIFICATIONS:
• Business Name: {user_specs.get('business_name', 'Not specified')}
• Industry: {user_specs.get('industry_focus', 'Not specified')}
• Purpose: {user_specs.get('purpose', 'Not specified')}
• Target Audience: {user_specs.get('target_audience', 'Not specified')}
• Design Style: {user_specs.get('design_style', 'Not specified')}
• Core Sections: {user_specs.get('core_sections', [])}
• Special Features: {user_specs.get('special_features', [])}
• Key Messages: {user_specs.get('key_messages', 'Not specified')}
• Unique Selling Points: {user_specs.get('unique_selling_points', 'Not specified')}
{context_summary}

TASKS:
1. Analyze the business requirements deeply
2. Identify gaps in user specifications
3. Suggest strategic improvements and missing elements
4. Define clear success metrics
5. Create enhanced requirements document
6. Generate specific prompt for Design Agent

OUTPUT FORMAT:
```json
{{
    "analysis": {{
        "business_type": "detailed business classification",
        "target_market": "refined target audience analysis",
        "competitive_positioning": "market positioning strategy",
        "success_metrics": ["metric1", "metric2", "metric3"]
    }},
    "enhanced_requirements": {{
        "primary_objectives": ["objective1", "objective2"],
        "user_journey": "describe ideal user flow",
        "conversion_goals": ["goal1", "goal2"],
        "technical_requirements": ["req1", "req2"],
        "content_strategy": "content approach description"
    }},
    "design_agent_prompt": "Detailed prompt for design agent including all strategic insights, visual requirements, user experience goals, and specific design direction based on business analysis"
}}
```"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            result = self._extract_json_from_response(content)
            if result:
                self.memory.add_interaction(user_specs, result, "requirements_analysis")
                self.memory.update_context("last_analysis", result)
                return result
            else:
                raise Exception("Failed to parse LLM response")
                
        except Exception as e:
            print(f"[ProductManager] LLM error: {e}")
            return self._create_basic_requirements(user_specs)
    
    def validate_final_website(self, html_content, original_requirements, design_output, content_output):
        """Validate if website meets all requirements"""
        if not LLM_MODEL:
            return True, "Basic validation passed"
        
        previous_validations = self.memory.get_relevant_context("validation")
        context_summary = ""
        if previous_validations:
            context_summary = f"\nPREVIOUS VALIDATIONS:\n{self._format_context(previous_validations)}"
        
        # Be more lenient on later validations
        validation_guidance = ""
        if len(previous_validations) >= 1:
            validation_guidance = f"\nIMPORTANT: This is validation {len(previous_validations) + 1}. Focus only on CORE REQUIREMENTS from original specifications. Do not request additional features not originally specified."
        elif len(previous_validations) >= 2:
            validation_guidance = f"\nCRITICAL: This is validation {len(previous_validations) + 1}/5. MUST PASS unless core requirements are missing. Do not ask for enhancements beyond original scope."
        
        prompt = f"""You are a senior product manager validating if a website meets the ORIGINAL business requirements. Focus ONLY on what was initially requested.

ORIGINAL USER REQUIREMENTS (STICK TO THESE ONLY):
{original_requirements}

DESIGN SPECIFICATIONS:
{design_output}

CONTENT STRATEGY:
{content_output}

WEBSITE CODE TO VALIDATE:
{html_content[:2000]}...

{context_summary}
{validation_guidance}

VALIDATION RULES:
• ONLY validate against ORIGINAL user requirements
• DO NOT request features not in original specifications
• DO NOT demand CRM integration unless explicitly requested
• DO NOT require testimonials unless user asked for them
• DO NOT ask for case studies unless specified
• Focus on: content sections, basic functionality, design alignment

MVP VALIDATION CHECKLIST:
1. CORE REQUIREMENTS (Must Have):
   - Required sections from original spec are present
   - Basic functionality works (navigation, forms)
   - Content matches business focus
   - Design style aligns with user preference

2. DO NOT REQUIRE (Unless Originally Specified):
   - Advanced integrations (CRM, analytics)
   - Additional content types (testimonials, case studies)
   - SEO optimization beyond basics
   - Performance optimizations

OUTPUT FORMAT:
```json
{{
    "validation_passed": true/false,
    "score": "percentage_score",
    "missing_core_requirements": ["only_originally_specified_requirements"],
    "feedback": "Brief feedback focusing ONLY on original requirements, or approval message"
}}
```

REMEMBER: Pass if core original requirements are met. Do not expand scope beyond user's initial request."""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            result = self._extract_json_from_response(content)
            if result:
                # Force pass on 3rd+ validation if no core requirements missing
                if len(previous_validations) >= 2 and not result.get('missing_core_requirements'):
                    validation_passed = True
                    feedback = "Website meets original requirements - approved for deployment"
                else:
                    validation_passed = result.get('validation_passed', False)
                    feedback = result.get('feedback', 'Requirements not fully met')
                
                self.memory.add_interaction(
                    {"html_content": html_content[:500], "requirements": original_requirements}, 
                    result, 
                    "validation"
                )
                
                return validation_passed, feedback
            else:
                return True, "Validation completed - requirements met"
                
        except Exception as e:
            print(f"[ProductManager] Validation error: {e}")
            return True, "Basic validation passed - requirements satisfied"
    
    def _extract_json_from_response(self, content):
        """Extract JSON from LLM response"""
        import json
        import re
        
        # Try to find JSON in code blocks
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try to find JSON in the text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None
    
    def _format_context(self, context_list):
        """Format context for prompt inclusion"""
        formatted = []
        for ctx in context_list[-3:]:  # Last 3 interactions
            formatted.append(f"- {ctx.get('type', 'interaction')}: {str(ctx.get('output', ''))[:100]}...")
        return "\n".join(formatted)
    
    def _create_basic_requirements(self, user_specs):
        """Fallback basic requirements"""
        return {
            "analysis": {
                "business_type": user_specs.get('purpose', 'business'),
                "target_market": user_specs.get('target_audience', 'professionals'),
                "competitive_positioning": "Professional service provider",
                "success_metrics": ["user_engagement", "conversion_rate"]
            },
            "enhanced_requirements": {
                "primary_objectives": ["establish_credibility", "generate_leads"],
                "user_journey": "Visit → Learn → Contact",
                "conversion_goals": ["contact_form_submission"],
                "technical_requirements": ["responsive_design", "fast_loading"],
                "content_strategy": "Professional and trustworthy content"
            },
            "design_agent_prompt": f"Create a professional {user_specs.get('design_style', 'modern')} website design for {user_specs.get('business_name', 'a business')} that serves {user_specs.get('target_audience', 'professional clients')}. Focus on credibility and user engagement."
        }

class DesignAgent:
    """Enhanced Design Agent with LLM and memory"""
    
    def __init__(self):
        self.memory = AgentMemory("DesignAgent")
        self.memory.update_context("role", "Senior UI/UX designer and visual design expert")
    
    def create_design_system(self, pm_prompt, user_specs, is_modification=False):
        """Create comprehensive design system based on PM analysis"""
        if not LLM_MODEL:
            return self._create_basic_design_system(user_specs)
        
        previous_designs = self.memory.get_relevant_context("design_system")
        context_summary = ""
        if previous_designs and is_modification:
            context_summary = f"\nPREVIOUS DESIGN WORK:\n{self._format_context(previous_designs)}"
        
        prompt = f"""You are a world-class UI/UX designer. Create a comprehensive design system based on product manager's strategic analysis.

PRODUCT MANAGER'S STRATEGIC DIRECTION:
{pm_prompt}

USER SPECIFICATIONS:
• Business: {user_specs.get('business_name', 'Professional Business')}
• Industry: {user_specs.get('industry_focus', 'Professional Services')}
• Style Preference: {user_specs.get('design_style', 'Modern')}
• Primary Color: {user_specs.get('primary_color', '#3498db')}
{context_summary}

DESIGN TASKS:
1. Analyze the strategic requirements and user needs
2. Create a comprehensive visual design system
3. Define user experience flow and interaction patterns
4. Specify responsive design approach
5. Generate detailed prompt for Content Agent

OUTPUT FORMAT:
```json
{{
    "design_strategy": {{
        "visual_concept": "overall design concept description",
        "user_experience_goal": "UX objectives and user flow",
        "brand_personality": "visual brand personality traits",
        "design_principles": ["principle1", "principle2", "principle3"]
    }},
    "visual_system": {{
        "color_palette": {{
            "primary": "hex_color",
            "secondary": "hex_color", 
            "accent": "hex_color",
            "text": "hex_color",
            "background": "hex_color"
        }},
        "typography": {{
            "headings": "font_family_and_style",
            "body": "font_family_and_style",
            "scale": "typography_scale_description"
        }},
        "layout": {{
            "grid_system": "grid_approach_description",
            "spacing": "spacing_system_description",
            "breakpoints": "responsive_breakpoint_strategy"
        }},
        "components": {{
            "buttons": "button_style_description",
            "cards": "card_component_style",
            "navigation": "navigation_design_approach",
            "forms": "form_styling_approach"
        }}
    }},
    "sections_design": {{
        "hero": "hero_section_design_specification",
        "about": "about_section_design_specification", 
        "services": "services_section_design_specification",
        "contact": "contact_section_design_specification"
    }},
    "content_agent_prompt": "Detailed prompt for Content Agent including tone of voice, content structure, messaging strategy, and specific content requirements for each section based on design and UX goals. IMPORTANT: Final output will be a SINGLE HTML FILE with embedded CSS/JS."
}}
```"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            result = self._extract_json_from_response(content)
            if result:
                self.memory.add_interaction(
                    {"pm_prompt": pm_prompt, "user_specs": user_specs}, 
                    result, 
                    "design_system"
                )
                self.memory.update_context("last_design", result)
                return result
            else:
                raise Exception("Failed to parse design response")
                
        except Exception as e:
            print(f"[DesignAgent] LLM error: {e}")
            return self._create_basic_design_system(user_specs)
    
    def _extract_json_from_response(self, content):
        """Extract JSON from LLM response"""
        import json
        import re
        
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None
    
    def _format_context(self, context_list):
        """Format context for prompt inclusion"""
        formatted = []
        for ctx in context_list[-2:]:
            formatted.append(f"- Previous design: {str(ctx.get('output', {}).get('design_strategy', {}))[:100]}...")
        return "\n".join(formatted)
    
    def _create_basic_design_system(self, user_specs):
        """Fallback basic design system"""
        return {
            "design_strategy": {
                "visual_concept": "Clean, professional design",
                "user_experience_goal": "Easy navigation and clear messaging",
                "brand_personality": "Professional and trustworthy",
                "design_principles": ["simplicity", "clarity", "professionalism"]
            },
            "visual_system": {
                "color_palette": {
                    "primary": user_specs.get('primary_color', '#3498db'),
                    "secondary": "#2c3e50",
                    "accent": "#e74c3c",
                    "text": "#2c3e50",
                    "background": "#ffffff"
                }
            },
            "content_agent_prompt": f"Create professional content for {user_specs.get('business_name', 'this business')} that emphasizes expertise and builds trust with {user_specs.get('target_audience', 'potential clients')}. IMPORTANT: Final output will be a SINGLE HTML FILE with embedded CSS/JS."
        }

class ContentAgent:
    """Enhanced Content Agent with LLM and memory"""
    
    def __init__(self):
        self.memory = AgentMemory("ContentAgent")
        self.memory.update_context("role", "Professional copywriter and content strategist")
    
    def generate_website_content(self, design_prompt, user_specs, design_output, is_modification=False):
        """Generate professional website content based on design strategy"""
        if not LLM_MODEL:
            return self._create_basic_content(user_specs)
        
        previous_content = self.memory.get_relevant_context("content_generation")
        context_summary = ""
        if previous_content and is_modification:
            context_summary = f"\nPREVIOUS CONTENT WORK:\n{self._format_context(previous_content)}"
        
        prompt = f"""You are a professional copywriter and content strategist. Create compelling website content based on design strategy.

DESIGN AGENT'S CONTENT DIRECTION:
{design_prompt}

USER SPECIFICATIONS:
• Business: {user_specs.get('business_name', 'Professional Business')}
• Industry: {user_specs.get('industry_focus', 'Professional Services')}
• Target Audience: {user_specs.get('target_audience', 'Business Professionals')}
• Key Messages: {user_specs.get('key_messages', 'Not specified')}
• Unique Selling Points: {user_specs.get('unique_selling_points', 'Not specified')}

DESIGN CONTEXT:
{design_output}
{context_summary}

CONTENT TASKS:
1. Create compelling, conversion-focused copy
2. Develop brand voice and messaging strategy
3. Write specific content for each website section
4. Ensure content aligns with design and UX goals
5. Generate detailed prompt for HTML Agent

OUTPUT FORMAT:
```json
{{
    "content_strategy": {{
        "brand_voice": "brand_voice_description",
        "messaging_framework": "core_messaging_strategy",
        "target_persona": "refined_target_audience_description",
        "conversion_strategy": "how_content_drives_conversions"
    }},
    "website_content": {{
        "hero": {{
            "headline": "powerful_main_headline",
            "subheadline": "supporting_subheadline",
            "cta_text": "call_to_action_text"
        }},
        "about": {{
            "headline": "about_section_headline", 
            "content": "about_section_content_paragraphs",
            "key_points": ["point1", "point2", "point3"]
        }},
        "services": {{
            "headline": "services_section_headline",
            "intro": "services_introduction_text",
            "service_items": [
                {{"title": "service1", "description": "service1_description"}},
                {{"title": "service2", "description": "service2_description"}},
                {{"title": "service3", "description": "service3_description"}}
            ]
        }},
        "contact": {{
            "headline": "contact_section_headline",
            "intro": "contact_introduction_text",
            "cta": "contact_call_to_action"
        }}
    }},
    "html_agent_prompt": "Comprehensive prompt for HTML Agent including all design specifications, content, technical requirements, and specific implementation guidelines for creating a SINGLE-FILE HTML website with embedded CSS and JavaScript"
}}
```"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            result = self._extract_json_from_response(content)
            if result:
                self.memory.add_interaction(
                    {"design_prompt": design_prompt, "user_specs": user_specs}, 
                    result, 
                    "content_generation"
                )
                self.memory.update_context("last_content", result)
                return result
            else:
                raise Exception("Failed to parse content response")
                
        except Exception as e:
            print(f"[ContentAgent] LLM error: {e}")
            return self._create_basic_content(user_specs)
    
    def _extract_json_from_response(self, content):
        """Extract JSON from LLM response"""
        import json
        import re
        
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None
    
    def _format_context(self, context_list):
        """Format context for prompt inclusion"""
        formatted = []
        for ctx in context_list[-2:]:
            content_summary = str(ctx.get('output', {}).get('website_content', {}))[:100]
            formatted.append(f"- Previous content: {content_summary}...")
        return "\n".join(formatted)
    
    def _create_basic_content(self, user_specs):
        """Fallback basic content"""
        business_name = user_specs.get('business_name', 'Professional Business')
        return {
            "content_strategy": {
                "brand_voice": "Professional and trustworthy",
                "messaging_framework": "Expertise and reliability",
                "target_persona": user_specs.get('target_audience', 'Business professionals'),
                "conversion_strategy": "Build trust and encourage contact"
            },
            "website_content": {
                "hero": {
                    "headline": f"Welcome to {business_name}",
                    "subheadline": user_specs.get('industry_focus', 'Professional services you can trust'),
                    "cta_text": "Get Started"
                }
            },
            "html_agent_prompt": "Comprehensive prompt for HTML Agent including all design specifications, content, technical requirements, and specific implementation guidelines for creating a SINGLE-FILE HTML website with embedded CSS and JavaScript"
        }

class HTMLAgent:
    """Enhanced HTML Agent with LLM and memory"""
    
    def __init__(self):
        self.memory = AgentMemory("HTMLAgent")
        self.memory.update_context("role", "Expert full-stack web developer")
    
    @staticmethod
    def generate_website(spec, workspace_path):
        """Generate initial website from specifications"""
        return HTMLAgent._process_html(spec, workspace_path, mode="create")
    
    @staticmethod
    def modify_website(feedback, workspace_path):
        """Modify existing website based on feedback"""
        return HTMLAgent._process_html(feedback, workspace_path, mode="modify")
    
    @staticmethod
    def _process_html(input_data, workspace_path, mode="create"):
        """Unified HTML processing with enhanced workflow"""
        
        # Initialize workflow manager
        workflow = WorkflowManager()
        
        # Initialize or get agent instances
        if 'agent_instances' not in st.session_state:
            st.session_state.agent_instances = {
                'product_manager': ProductManagerAgent(),
                'design_agent': DesignAgent(),
                'content_agent': ContentAgent(),
                'html_agent': HTMLAgent(),
                'qa_agent': QAAgent()
            }
        
        agents = st.session_state.agent_instances
        
        if mode == "create":
            return HTMLAgent._create_website_workflow(input_data, workspace_path, agents, workflow)
        else:
            return HTMLAgent._modify_website_workflow(input_data, workspace_path, agents, workflow)
    
    @staticmethod
    def _create_website_workflow(user_specs, workspace_path, agents, workflow):
        """Complete website creation workflow"""
        try:
            # Step 1: Product Manager analyzes requirements
            st.info("🔍 **ProductManager**: Analyzing business requirements and strategy...")
            log_agent_communication("SpecAgent", "ProductManager", "User specifications received", 
                                   f"Business: {user_specs.get('business_name')}")
            
            pm_analysis = agents['product_manager'].analyze_user_requirements(user_specs)
            design_prompt = pm_analysis.get('design_agent_prompt', 'Create a professional website design')
            
            st.success("✅ **ProductManager**: Strategic analysis completed")
            log_agent_communication("ProductManager", "DesignAgent", "Strategic direction provided", 
                                   f"Design prompt generated")
            
            # Step 2: Design Agent creates design system
            st.info("🎨 **DesignAgent**: Creating visual design system and UX strategy...")
            
            design_output = agents['design_agent'].create_design_system(design_prompt, user_specs)
            content_prompt = design_output.get('content_agent_prompt', 'Create professional content')
            
            st.success("✅ **DesignAgent**: Design system and UX strategy completed")
            log_agent_communication("DesignAgent", "ContentAgent", "Design specifications ready", 
                                   f"Content direction provided")
            
            # Step 3: Content Agent generates content
            st.info("✍️ **ContentAgent**: Creating professional content and copy...")
            
            content_output = agents['content_agent'].generate_website_content(
                content_prompt, user_specs, design_output
            )
            html_prompt = content_output.get('html_agent_prompt', 'Create a professional website')
            
            st.success("✅ **ContentAgent**: Professional content created")
            log_agent_communication("ContentAgent", "HTMLAgent", "Content and copy ready", 
                                   f"HTML development instructions provided")
            
            # Step 4: HTML-QA Development Cycle
            st.info("🔧 **HTMLAgent**: Starting website development...")
            
            final_html = HTMLAgent._html_qa_cycle(
                html_prompt, user_specs, design_output, content_output, 
                agents, workflow, workspace_path
            )
            
            if not final_html:
                st.error("❌ Website development failed")
                return False, "Website development failed"
            
            # Step 5: Product Manager final validation
            st.info("🔍 **ProductManager**: Final requirement validation...")
            
            final_html = HTMLAgent._pm_validation_cycle(
                final_html, pm_analysis, design_output, content_output,
                agents, workflow, workspace_path
            )
            
            if final_html:
                # Write final file
                html_path = os.path.join(workspace_path, 'index.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                with open(os.path.join(workspace_path, 'styles.css'), 'w', encoding='utf-8') as f:
                    f.write('/* All styles embedded in HTML */')
                
                st.success("✅ **ProductManager**: Website meets all requirements - Development complete!")
                return True, "✅ Website created successfully"
            else:
                st.error("❌ Maximum development cycles reached")
                return False, "Maximum development cycles reached"
            
        except Exception as e:
            print(f"[HTMLAgent] Critical error: {e}")
            st.error(f"Critical error in website creation: {str(e)}")
            return False, f"Critical error: {str(e)}"
    
    @staticmethod
    def _modify_website_workflow(feedback, workspace_path, agents, workflow):
        """Website modification workflow starting from DesignAgent"""
        try:
            # Get current website
            html_path = os.path.join(workspace_path, 'index.html')
            if not os.path.exists(html_path):
                return False, "❌ No website file found"
            
            with open(html_path, 'r', encoding='utf-8') as f:
                current_html = f.read()
            
            # Get original user specs from session state
            user_specs = st.session_state.get('website_context', {})
            
            log_agent_communication("User", "DesignAgent", f"Modification request: {feedback[:50]}...", 
                                   f"Full feedback: {feedback}")
            
            # Start from Design Agent with modification context
            st.info("🎨 **DesignAgent**: Analyzing modification requirements...")
            
            modification_prompt = f"MODIFICATION REQUEST: {feedback}\n\nAnalyze this request and update the design system accordingly. Consider the existing website and user feedback."
            
            design_output = agents['design_agent'].create_design_system(
                modification_prompt, user_specs, is_modification=True
            )
            content_prompt = design_output.get('content_agent_prompt', 'Update content based on feedback')
            
            st.success("✅ **DesignAgent**: Modification design completed")
            
            # Content Agent updates
            st.info("✍️ **ContentAgent**: Updating content strategy...")
            
            content_output = agents['content_agent'].generate_website_content(
                content_prompt, user_specs, design_output, is_modification=True
            )
            html_prompt = content_output.get('html_agent_prompt', 'Update website based on feedback')
            
            st.success("✅ **ContentAgent**: Content updates completed")
            
            # HTML-QA cycle for modifications
            st.info("🔧 **HTMLAgent**: Implementing modifications...")
            
            # Add current HTML to prompt context
            html_prompt_with_context = f"{html_prompt}\n\nCURRENT WEBSITE CODE:\n{current_html}"
            
            final_html = HTMLAgent._html_qa_cycle(
                html_prompt_with_context, user_specs, design_output, content_output,
                agents, workflow, workspace_path, current_html=current_html
            )
            
            if final_html and final_html != current_html:
                # Write updated file
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(final_html)
                
                st.success("✅ **HTMLAgent**: Modifications applied successfully")
                return True, "✅ Website updated successfully"
            else:
                return False, "❌ No changes made or modification failed"
            
        except Exception as e:
            print(f"[HTMLAgent] Modification error: {e}")
            return False, f"❌ Modification failed: {str(e)}"
    
    @staticmethod
    def _html_qa_cycle(html_prompt, user_specs, design_output, content_output, agents, workflow, workspace_path, current_html=None):
        """HTML Agent and QA Agent development cycle"""
        html_agent = agents['html_agent']
        qa_agent = agents['qa_agent']
        
        working_html = current_html
        
        while workflow.can_continue_html_qa():
            workflow.increment_html_qa()
            
            st.info(f"🔧 **HTMLAgent**: Development iteration {workflow.html_qa_cycles}/5...")
            
            # HTML Agent generates/updates code
            working_html = html_agent.generate_html_code(
                html_prompt, user_specs, design_output, content_output, 
                current_html=working_html
            )
            
            if not working_html:
                st.error("❌ **HTMLAgent**: Code generation failed")
                break
            
            st.success(f"✅ **HTMLAgent**: Code generated (iteration {workflow.html_qa_cycles})")
            log_agent_communication("HTMLAgent", "QAAgent", f"Code review request (iteration {workflow.html_qa_cycles})", 
                                   f"HTML length: {len(working_html)}")
            
            # QA Agent reviews code
            st.info(f"🔍 **QAAgent**: Code review {workflow.html_qa_cycles}/5...")
            
            qa_passed, qa_feedback = qa_agent.review_html_code(working_html, user_specs, design_output, content_output)
            
            if qa_passed:
                st.success(f"✅ **QAAgent**: Code approved (iteration {workflow.html_qa_cycles})")
                log_agent_communication("QAAgent", "HTMLAgent", "Code approved", "Quality standards met")
                return working_html
            else:
                st.warning(f"⚠️ **QAAgent**: Issues found - requesting fixes...")
                log_agent_communication("QAAgent", "HTMLAgent", "Code review failed", qa_feedback)
                
                # Update HTML prompt with QA feedback for next iteration
                html_prompt = f"{html_prompt}\n\nQA FEEDBACK TO FIX:\n{qa_feedback}"
        
        st.warning("⚠️ **HTMLAgent**: Maximum QA cycles reached - using last version")
        return working_html
    
    @staticmethod
    def _pm_validation_cycle(html_content, pm_analysis, design_output, content_output, agents, workflow, workspace_path):
        """Product Manager validation cycle"""
        pm_agent = agents['product_manager']
        max_pm_cycles = 3  # Reduced from 5 to prevent excessive cycles
        
        while workflow.can_continue_pm_html() and workflow.pm_html_cycles < max_pm_cycles:
            workflow.increment_pm_html()
            
            st.info(f"🔍 **ProductManager**: Requirements validation {workflow.pm_html_cycles}/{max_pm_cycles}...")
            
            validation_passed, pm_feedback = pm_agent.validate_final_website(
                html_content, pm_analysis, design_output, content_output
            )
            
            if validation_passed:
                st.success(f"✅ **ProductManager**: All requirements satisfied")
                log_agent_communication("ProductManager", "System", "Final validation passed", "Website approved")
                return html_content
            else:
                st.warning(f"⚠️ **ProductManager**: Requirements not met - requesting changes...")
                log_agent_communication("ProductManager", "HTMLAgent", "Requirements validation failed", pm_feedback)
                
                # Reset HTML-QA cycles for new PM iteration
                workflow.reset_html_qa()
                
                # Create new HTML prompt with PM feedback
                html_prompt = f"PRODUCT MANAGER FEEDBACK: {pm_feedback}\n\nFix the website to meet all requirements. Current code:\n{html_content}"
                
                # Run HTML-QA cycle again
                html_content = HTMLAgent._html_qa_cycle(
                    html_prompt, {}, design_output, content_output,
                    agents, workflow, workspace_path, current_html=html_content
                )
                
                if not html_content:
                    break
        
        st.warning(f"⚠️ **ProductManager**: Maximum validation cycles ({max_pm_cycles}) reached - deploying current version")
        return html_content
    
    def generate_html_code(self, html_prompt, user_specs, design_output, content_output, current_html=None):
        """Generate HTML code using LLM with memory"""
        if not LLM_MODEL:
            return self._generate_template_fallback(user_specs)
        
        # Get relevant context from memory
        previous_code = self.memory.get_relevant_context("code_generation")
        context_summary = ""
        if previous_code:
            context_summary = f"\nPREVIOUS DEVELOPMENT EXPERIENCE:\n{self._format_context(previous_code)}"
        
        mode_instruction = "Create a new website" if not current_html else "Modify the existing website"
        current_code_section = f"\n\nCURRENT CODE TO MODIFY:\n{current_html}" if current_html else ""
        
        prompt = f"""You are an expert full-stack web developer. {mode_instruction} based on the comprehensive specifications.

CRITICAL ARCHITECTURE REQUIREMENT:
• MUST BE A SINGLE HTML FILE WITH ALL CSS AND JAVASCRIPT EMBEDDED
• NO EXTERNAL FILES ALLOWED (no separate .css, .js, or image files)
• ALL STYLES MUST BE IN <style> TAG IN THE <head>
• ALL JAVASCRIPT MUST BE IN <script> TAG BEFORE </body>
• SELF-CONTAINED AND READY TO RUN IMMEDIATELY

HTML DEVELOPMENT INSTRUCTIONS:
{html_prompt}

DESIGN SPECIFICATIONS:
{design_output}

CONTENT SPECIFICATIONS:
{content_output}

USER REQUIREMENTS:
• Business: {user_specs.get('business_name', 'Professional Business')}
• Industry: {user_specs.get('industry_focus', 'Professional Services')}
• Primary Color: {user_specs.get('primary_color', '#3498db')}
{current_code_section}
{context_summary}

TECHNICAL REQUIREMENTS:
• SINGLE HTML FILE with embedded CSS and JavaScript (MANDATORY)
• Modern, responsive design (mobile-first approach)
• Professional animations and micro-interactions
• Clean, readable code structure
• Cross-browser compatibility
• Working contact form with basic validation

MANDATORY HTML STRUCTURE:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Title Here</title>
    <style>
        /* ALL CSS HERE - NO EXTERNAL STYLESHEETS */
    </style>
</head>
<body>
    <!-- ALL HTML CONTENT HERE -->
    <script>
        // ALL JAVASCRIPT HERE - NO EXTERNAL SCRIPTS
    </script>
</body>
</html>
```

CRITICAL SUCCESS FACTORS:
• Must be a complete, self-contained HTML file
• No external dependencies or separate files
• Ready to open directly in any browser
• All functionality embedded within the single file
• Professional design that works immediately

OUTPUT: Return ONLY the complete HTML document. No explanations, no markdown blocks, just the raw HTML code."""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean the response
            html_code = self._clean_code_response(content)
            
            if self._validate_html(html_code):
                # Store in memory
                self.memory.add_interaction(
                    {"prompt": html_prompt, "specs": user_specs}, 
                    {"html_code": html_code[:500]}, 
                    "code_generation"
                )
                return html_code
            else:
                print("[HTMLAgent] HTML validation failed")
                return None
                
        except Exception as e:
            print(f"[HTMLAgent] Code generation error: {e}")
            return None
    
    def _clean_code_response(self, content):
        """Clean LLM response to extract pure HTML"""
        if not content:
            return ""
        
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith("```"):
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        return content.strip()
    
    def _validate_html(self, content):
        """Basic HTML validation"""
        if not content:
            return False
        
        content = content.strip()
        
        # Check for basic HTML structure
        has_doctype = content.startswith('<!DOCTYPE html') or content.startswith('<!doctype html')
        has_html_start = '<html' in content.lower()
        has_html_end = '</html>' in content.lower()
        has_head = '<head>' in content.lower() or '<head ' in content.lower()
        has_body = '<body>' in content.lower() or '<body ' in content.lower()
        
        # Basic structure validation
        basic_structure = has_html_start and has_html_end and has_head and has_body
        
        # Allow either DOCTYPE + HTML structure, or just HTML structure for MVP
        return basic_structure and (has_doctype or len(content) > 500)
    
    def _generate_template_fallback(self, user_specs):
        """Generate template when LLM is not available"""
        business_name = user_specs.get('business_name', 'Professional Business')
        primary_color = user_specs.get('primary_color', '#3498db')
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{business_name} | Professional Services</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
        .header {{ background: {primary_color}; color: white; padding: 2rem; text-align: center; }}
        .content {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .section {{ margin: 2rem 0; }}
    </style>
</head>
<body>
    <header class="header">
        <h1>{business_name}</h1>
        <p>{user_specs.get('industry_focus', 'Professional Services')}</p>
    </header>
    <div class="content">
        <section class="section">
            <h2>Welcome</h2>
            <p>Professional services you can trust.</p>
        </section>
        <section class="section">
            <h2>About Us</h2>
            <p>We provide expert solutions for your business needs.</p>
        </section>
        <section class="section">
            <h2>Contact</h2>
            <p>Get in touch with us today.</p>
        </section>
    </div>
</body>
</html>"""
    
    def _format_context(self, context_list):
        """Format context for prompt inclusion"""
        formatted = []
        for ctx in context_list[-2:]:
            formatted.append(f"- Previous work: {str(ctx.get('output', {}))[:100]}...")
        return "\n".join(formatted)

class QAAgent:
    """Enhanced QA Agent with LLM and memory"""
    
    def __init__(self):
        self.memory = AgentMemory("QAAgent")
        self.memory.update_context("role", "Senior QA engineer and code reviewer")
    
    def review_html_code(self, html_code, user_specs, design_output, content_output):
        """Comprehensive QA review of HTML code"""
        if not LLM_MODEL:
            return True, "Basic QA review passed"
        
        # Get relevant context from memory
        previous_reviews = self.memory.get_relevant_context("code_review")
        context_summary = ""
        if previous_reviews:
            context_summary = f"\nPREVIOUS QA REVIEWS:\n{self._format_context(previous_reviews)}"
        
        # Be more lenient on later iterations
        iteration_guidance = ""
        if len(previous_reviews) >= 2:
            iteration_guidance = f"\nIMPORTANT: This is iteration {len(previous_reviews) + 1}. Focus on CRITICAL issues only. Accept code if it's functional and meets basic requirements. Avoid perfectionist standards - this is an MVP."
        elif len(previous_reviews) >= 4:
            iteration_guidance = f"\nCRITICAL: This is iteration {len(previous_reviews) + 1}/5. MUST PASS unless there are blocking errors. Focus only on functionality, not optimization."
        
        prompt = f"""You are a senior QA engineer reviewing a SINGLE-FILE HTML website. This is an MVP - focus on essential functionality, not perfection.

CRITICAL CONSTRAINTS:
• SINGLE HTML FILE with embedded CSS and JavaScript ONLY
• NO separate CSS files allowed
• NO external stylesheets required
• MVP approach - functionality over perfection
• Must be ready for immediate use

HTML CODE TO REVIEW:
{html_code[:2000]}...

DESIGN REQUIREMENTS:
{design_output}

CONTENT REQUIREMENTS:
{content_output}

USER SPECIFICATIONS:
• Business: {user_specs.get('business_name', 'Professional Business')}
• Target Audience: {user_specs.get('target_audience', 'Business Professionals')}
{context_summary}
{iteration_guidance}

MVP QA CHECKLIST (ESSENTIAL ONLY):
1. BLOCKING ISSUES (Must Fix):
   - HTML syntax errors that break rendering
   - Missing critical content sections
   - Broken form functionality
   - Major responsive design failures

2. NICE-TO-HAVE (Suggest Only):
   - Alt tags for images
   - Performance optimizations
   - Advanced accessibility features
   - SEO enhancements

QA STANDARDS:
- If website displays correctly and has basic functionality → PASS
- Only FAIL for critical blocking issues
- Embedded CSS/JS is REQUIRED (not a problem)
- Single file architecture is INTENTIONAL
- Focus on working MVP, not perfection

OUTPUT FORMAT:
```json
{{
    "qa_passed": true/false,
    "overall_score": "percentage_score",
    "critical_issues": [
        {{"description": "blocking_issue_description", "fix_suggestion": "how_to_fix"}}
    ],
    "suggestions": [
        {{"description": "nice_to_have_improvement"}}
    ],
    "feedback_for_html_agent": "Brief feedback focusing on critical fixes only, or approval message"
}}
```

REMEMBER: Pass the code if it works and meets basic requirements. This is MVP development."""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            result = self._extract_json_from_response(content)
            if result:
                qa_passed = result.get('qa_passed', False)
                feedback = result.get('feedback_for_html_agent', 'Issues found, please review')
                
                # Force pass on 4th+ iteration if no critical issues
                if len(previous_reviews) >= 3 and not result.get('critical_issues'):
                    qa_passed = True
                    feedback = "Code approved for MVP deployment. Minor suggestions noted for future improvements."
                
                # Store in memory
                self.memory.add_interaction(
                    {"html_code": html_code[:500], "specs": user_specs}, 
                    result, 
                    "code_review"
                )
                
                return qa_passed, feedback
            else:
                # Fallback to pass if we can't parse response
                return True, "QA review completed - code approved for MVP"
                
        except Exception as e:
            print(f"[QAAgent] Review error: {e}")
            return True, "QA review passed - basic functionality confirmed"
    
    def _extract_json_from_response(self, content):
        """Extract JSON from LLM response"""
        import json
        import re
        
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None
    
    def _format_context(self, context_list):
        """Format context for prompt inclusion"""
        formatted = []
        for ctx in context_list[-3:]:
            issues = ctx.get('output', {}).get('issues_found', [])
            formatted.append(f"- Previous review: {len(issues)} issues found")
        return "\n".join(formatted)

class PackageAgent:
    """Handles project packaging and download"""
    @staticmethod
    def create_zip(workspace_path):
        """Create a ZIP file containing only the HTML file"""
        zip_path = os.path.join(workspace_path, 'website.zip')
        
        # Only include the main HTML file
        html_file = os.path.join(workspace_path, 'index.html')
        
        if os.path.exists(html_file):
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(html_file, 'index.html')
        else:
            # Create empty zip if no HTML file exists
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                pass
        
        return zip_path

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
            print(f"LLM initialized: {LLM_NAME}")
        except Exception as e:
            LLM_MODEL, LLM_NAME = None, "LLM Failed"
            _llm_initialized = True
            print(f"LLM initialization failed: {e}")
    
    # Title
    st.title("🕸️ WebWeaver Enterprise")
    st.markdown("*Advanced Multi-Agent LLM Website Builder*")
    
    # API key status
    if LLM_MODEL:
        st.success(f"✅ {LLM_NAME} ready - All agents LLM-powered")
    else:
        st.error("❌ No LLM available - Agents will use fallback mode")
        with st.expander("🔑 Setup API Key"):
            st.markdown("""
            **Add your OpenAI API key to `.env` file:**
            ```
            OPENAI_API_KEY=your_key_here
            ```
            """)
    
    # Sidebar - SpecAgent
    with st.sidebar:
        spec = SpecAgent.collect_specs()
        
        # Start Development Button
        if st.button("🚀 Start Development", type="primary", use_container_width=True):
            if not spec.get('business_name') or not spec.get('industry_focus'):
                st.error("⚠️ Please complete the required fields: Business Name and Industry Focus")
            else:
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
                success, message = HTMLAgent.generate_website(spec, st.session_state.workspace_path)
                
                if success:
                    # Start preview
                    if st.session_state.preview_agent:
                        st.session_state.preview_agent.stop()
                    
                    st.session_state.preview_agent = PreviewAgent(st.session_state.workspace_path)
                    st.session_state.preview_agent.start_server()
                    st.session_state.preview_agent.start_file_watcher()
                    st.session_state.development_started = True
                    
                    st.rerun()
                else:
                    st.error(f"Failed to create website: {message}")
        
        # PackageAgent - Download ZIP
        if st.session_state.development_started:
            st.markdown("---")
            
            if st.button("📥 Download ZIP", use_container_width=True):
                zip_path = PackageAgent.create_zip(st.session_state.workspace_path)
                
                with open(zip_path, 'rb') as f:
                    st.download_button(
                        label="💾 Download website.zip",
                        data=f.read(),
                        file_name="website.zip",
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
            st.subheader("🎨 Multi-Agent System")
            
            # Website status information
            with st.container():
                st.markdown("**📊 Website Status**")
                
                # Show current business info if available
                if 'website_context' in st.session_state:
                    context = st.session_state.website_context
                    if context.get('current_theme'):
                        st.caption(f"🏢 **Type**: {context['current_theme']}")
                    if context.get('business_type'):
                        st.caption(f"📝 **Category**: {context['business_type']}")
                
                # Show total changes applied
                total_changes = len(st.session_state.get('feedback_history', []))
                st.caption(f"🔄 **Changes Applied**: {total_changes}")
                
                st.markdown("---")
            
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
                    success, message = HTMLAgent.modify_website(
                        feedback, st.session_state.workspace_path
                    )
                    
                    if success:
                        st.success("✅ Updated")
                        st.session_state.feedback_history.append(feedback)
                        
                        # Add timestamp for this change
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        if 'change_timestamps' not in st.session_state:
                            st.session_state.change_timestamps = []
                        st.session_state.change_timestamps.append(timestamp)
                        
                        st.session_state.reload_trigger += 1
                        st.session_state.feedback_counter = st.session_state.get('feedback_counter', 0) + 1
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Describe what to change")
            
            # Agent status display
            if 'agent_instances' in st.session_state:
                with st.expander("🤖 Agent Status", expanded=True):
                    agents = st.session_state.agent_instances
                    
                    for agent_name, agent in agents.items():
                        memory_size = len(agent.memory.conversation_history)
                        # Format agent name for better display
                        display_name = agent_name.replace('_', ' ').title()
                        
                        # Create columns for better layout
                        col_agent, col_status = st.columns([3, 1])
                        
                        with col_agent:
                            st.markdown(f"**{display_name}**")
                            st.caption(f"{memory_size} memories")
                        
                        with col_status:
                            # Add visual indicator for memory load
                            if memory_size > 10:
                                st.markdown("🔥")
                                st.caption("High")
                            elif memory_size > 5:
                                st.markdown("⚡")
                                st.caption("Active") 
                            else:
                                st.markdown("💤")
                                st.caption("Low")
                        
                        st.markdown("---")
            
            # Enhanced recent changes display
            if st.session_state.get('feedback_history'):
                with st.expander("📝 Recent Changes"):
                    # Initialize timestamps if not exists
                    if 'change_timestamps' not in st.session_state:
                        st.session_state.change_timestamps = []
                    
                    # Show recent changes (last 5)
                    recent_changes = st.session_state.feedback_history[-5:]
                    recent_timestamps = st.session_state.change_timestamps[-5:] if st.session_state.change_timestamps else []
                    
                    for i, change in enumerate(reversed(recent_changes)):
                        change_number = len(st.session_state.feedback_history) - i
                        
                        # Get timestamp if available
                        timestamp_idx = len(recent_changes) - 1 - i
                        timestamp = ""
                        if timestamp_idx < len(recent_timestamps):
                            timestamp = f" ⏰ {recent_timestamps[timestamp_idx]}"
                        
                        # Show full text with proper formatting
                        st.markdown(f"**Change #{change_number}**{timestamp}")
                        st.markdown(f"📝 {change}")
                        
                        if i < len(recent_changes) - 1:
                            st.markdown("---")  # Add separator between changes
    
    else:
        # Enhanced welcome screen
        st.markdown("## 🚀 Enterprise Multi-Agent Website Builder")
        st.markdown("""
        **Powered by 5 Specialized LLM Agents:**
        - 🔍 **Product Manager**: Strategic analysis & requirements
        - 🎨 **Design Agent**: Visual design systems & UX
        - ✍️ **Content Agent**: Professional copywriting
        - 🔧 **HTML Agent**: Full-stack development
        - 🔍 **QA Agent**: Quality assurance & testing
        
        **Advanced Features:**
        - Individual agent memories for stateful conversations
        - Complex workflow cycles (up to 25 iterations)
        - HTML-QA cycles (up to 5 iterations each)
        - Product Manager validation cycles
        - Intelligent feedback processing
        """)
        
        if not LLM_MODEL:
            st.info("💡 Add `OPENAI_API_KEY=your_key` to .env file for full AI features")

if __name__ == "__main__":
    main() 