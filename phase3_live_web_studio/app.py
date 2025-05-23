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

# Debug: Check if API keys are loaded (without exposing them)
if OPENAI_API_KEY:
    print(f"OpenAI API key loaded: {OPENAI_API_KEY[:8]}...")

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
        st.sidebar.header("🧙‍♂️ SpecAgent - Custom Website Builder")
        
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
        
        # Display comprehensive summary
        st.sidebar.markdown("### 📋 Website Specification")
        with st.sidebar.expander("📝 Full Specification Summary"):
            st.markdown(f"""
            **Purpose**: {purpose}  
            **Business**: {business_name}  
            **Focus**: {industry_focus[:50]}{'...' if len(industry_focus) > 50 else ''}  
            **Audience**: {target_audience}  
            **Style**: {design_style}  
            **Colors**: {color_scheme}  
            **Sections**: {', '.join(core_sections[:3])}{'...' if len(core_sections) > 3 else ''}  
            **Features**: {', '.join(special_features[:2])}{'...' if len(special_features) > 2 else ''}
            """)
        
        # Validation
        if not business_name:
            st.sidebar.warning("⚠️ Please enter a business name")
        elif not industry_focus:
            st.sidebar.warning("⚠️ Please describe what you do")
        else:
            st.sidebar.success("✅ Specification complete!")
        
        return spec

class CodeAgent:
    """Generates initial HTML and CSS scaffolding using LLM"""
    @staticmethod
    def generate_files(spec, workspace_path):
        """Generate index.html and styles.css based on spec using LLM or templates"""
        
        if LLM_MODEL:
            # Use LLM for intelligent code generation
            html_content = CodeAgent.generate_html_with_llm(spec)
            css_content = CodeAgent.generate_css_with_llm(spec)
        else:
            # Only use templates when NO LLM is available
            st.warning("⚠️ No LLM available - using basic templates. Add API keys for AI generation!")
            html_content = CodeAgent.generate_html_template(spec)
            css_content = CodeAgent.generate_css_template(spec)
        
        # Write files
        with open(os.path.join(workspace_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        with open(os.path.join(workspace_path, 'styles.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    @staticmethod
    def generate_html_with_llm(spec, retry_count=0):
        """Generate truly custom HTML based on detailed specifications"""
        if not LLM_MODEL:
            st.error("❌ No LLM available for HTML generation")
            return CodeAgent.generate_html_template(spec)
        
        # Create detailed prompt based on comprehensive spec
        sections_list = ', '.join(spec.get('core_sections', ['Hero/Welcome', 'About Us', 'Contact']))
        features_list = ', '.join(spec.get('special_features', []))
        
        prompt = f"""You are a professional web developer and copywriter creating a premium website. Create compelling, professional content that converts visitors.

DETAILED BUSINESS REQUIREMENTS:
Business Name: {spec.get('business_name', 'Business')}
Industry: {spec.get('purpose', 'Business')}
What They Do: {spec.get('industry_focus', 'Provide services')}
Target Audience: {spec.get('target_audience', 'General customers')}
Design Style: {spec.get('design_style', 'Modern & Minimalist')}
Color Theme: {spec.get('color_scheme', 'Professional')}

CONTENT STRATEGY:
Key Messages: {spec.get('key_messages', 'Professional service')}
Unique Selling Points: {spec.get('unique_selling_points', 'Quality and reliability')}

REQUIRED SECTIONS: {sections_list}
SPECIAL FEATURES: {features_list if features_list else 'Basic functionality'}

PROFESSIONAL CONTENT REQUIREMENTS:

1. **COMPELLING COPY & MESSAGING**:
   - Write powerful, benefit-focused headlines that grab attention
   - Use industry-specific language that resonates with target audience
   - Include social proof, credibility indicators, and trust signals
   - Create compelling calls-to-action that drive conversions
   - Write in active voice with strong, confident language

2. **PROFESSIONAL STRUCTURE**:
   - Modern semantic HTML5 with proper hierarchy
   - Strategic use of headings (h1, h2, h3) for SEO and readability
   - Well-organized sections with logical flow
   - Professional navigation with descriptive labels
   - Clean, semantic class names (hero-section, services-grid, etc.)

3. **MODERN COMPONENTS**:
   - Hero section with powerful headline and clear value proposition
   - Professional services/features grid with benefits-focused descriptions
   - Compelling about section that builds trust and credibility
   - Contact section with multiple engagement options
   - Modern button designs with action-oriented text

4. **TRUST & CREDIBILITY ELEMENTS**:
   - Include years of experience, certifications, or awards
   - Add testimonial placeholders with realistic names and companies
   - Show expertise through detailed service descriptions
   - Include contact information that builds trust
   - Add professional social proof indicators

5. **INDUSTRY-SPECIFIC EXCELLENCE**:
   - Consulting: Focus on expertise, results, Fortune 500 clients
   - Healthcare: Emphasize safety, certifications, patient care
   - Technology: Highlight innovation, cutting-edge solutions
   - Restaurant: Showcase atmosphere, quality ingredients, experience
   - Creative: Display portfolio, unique approach, artistic vision

6. **CONVERSION-FOCUSED DESIGN**:
   - Clear primary and secondary calls-to-action
   - Multiple contact methods (phone, email, form, chat)
   - Easy navigation with logical user journey
   - Mobile-first responsive structure
   - Fast-loading, performance-optimized HTML

CONTENT QUALITY STANDARDS:
- Write like a professional copywriter for Fortune 500 companies
- Every headline should be compelling and benefit-focused
- Every section should have a clear purpose and value proposition
- Use specific, concrete language instead of generic phrases
- Make visitors think "This company knows what they're doing"

TECHNICAL EXCELLENCE:
- Perfect HTML5 semantic structure
- Proper meta tags, title, and viewport
- Link to "styles.css" for styling
- Clean, professional class names
- Accessibility-friendly markup

Create a website that immediately conveys professionalism, expertise, and trustworthiness.

Return ONLY the complete HTML5 document:"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'html')
            if FeedbackAgent._validate_html(content):
                st.success("✅ Custom HTML generated successfully!")
                return content
            else:
                if retry_count < 2:
                    st.warning(f"🔄 HTML validation failed, retrying... ({retry_count + 1}/3)")
                    return CodeAgent.generate_html_with_llm(spec, retry_count + 1)
                else:
                    st.error("❌ LLM failed to generate valid HTML after 3 attempts")
                    return CodeAgent.generate_html_template(spec)
                    
        except Exception as e:
            if retry_count < 2:
                st.warning(f"🔄 LLM error in HTML generation, retrying... ({retry_count + 1}/3): {str(e)[:100]}")
                return CodeAgent.generate_html_with_llm(spec, retry_count + 1)
            else:
                st.error(f"❌ LLM HTML generation failed after 3 attempts: {str(e)}")
                return CodeAgent.generate_html_template(spec)
    
    @staticmethod
    def generate_css_with_llm(spec, retry_count=0):
        """Generate truly custom CSS based on detailed specifications"""
        if not LLM_MODEL:
            st.error("❌ No LLM available for CSS generation")
            return CodeAgent.generate_css_template(spec)
        
        prompt = f"""You are a world-class UI/UX designer from a top design agency (like Apple, Google, or Stripe). Create a stunning, professional website that looks premium and modern.

BUSINESS CONTEXT:
Industry: {spec.get('purpose', 'Business')} 
Business Focus: {spec.get('industry_focus', 'Professional services')}
Target Audience: {spec.get('target_audience', 'General customers')}
Design Style: {spec.get('design_style', 'Modern & Minimalist')}
Color Scheme: {spec.get('color_scheme', 'Professional')}
Primary Color: {spec.get('primary_color', '#3498db')}

DESIGN EXCELLENCE REQUIREMENTS:
Create a website that looks like it was designed by Apple, Google, or Stripe's design team:

1. **VISUAL HIERARCHY & TYPOGRAPHY**:
   - Use premium font combinations (Inter, SF Pro, or similar)
   - Perfect font sizing: h1(48-56px), h2(36-42px), h3(24-28px), body(16-18px)
   - Proper line heights (1.4-1.6) and letter spacing
   - Strong visual hierarchy with clear content organization

2. **MODERN LAYOUT & SPACING**:
   - Generous whitespace and perfect spacing ratios
   - CSS Grid and Flexbox for professional layouts
   - Maximum width containers (1200px) with proper margins
   - Consistent spacing system (8px, 16px, 24px, 32px, 48px, 64px)

3. **PREMIUM VISUAL ELEMENTS**:
   - Subtle shadows: box-shadow: 0 4px 6px rgba(0,0,0,0.1)
   - Modern gradients and depth
   - Rounded corners (8px-16px) for modern feel
   - High-quality hover effects and micro-interactions

4. **PROFESSIONAL COLOR SYSTEM**:
   - Build sophisticated color palette around primary color
   - Use color psychology for the specific industry
   - Proper contrast ratios (WCAG AA compliance)
   - Subtle background variations and tonal differences

5. **MODERN COMPONENTS**:
   - Professional navigation with proper hover states
   - Beautiful buttons with gradient/shadow effects
   - Modern cards with subtle elevation
   - Professional forms with floating labels or modern styling
   - Hero sections with compelling visual impact

6. **INDUSTRY-SPECIFIC EXCELLENCE**:
   - Consulting/Corporate: Clean, trustworthy, premium feel
   - Healthcare: Calming blues/greens, accessible, trustworthy
   - Technology: Modern, innovative, cutting-edge aesthetics
   - Creative: Bold, artistic, unique visual elements
   - Restaurant: Warm, appetizing, inviting atmosphere

7. **RESPONSIVE & MODERN**:
   - Mobile-first responsive design
   - Smooth animations and transitions
   - Modern CSS techniques (CSS custom properties, clamp(), etc.)
   - Perfect on all device sizes

INSPIRATION LEVEL: Make this look like websites from:
- Apple.com (clean, premium, perfect spacing)
- Stripe.com (professional, modern, excellent typography)
- Linear.app (beautiful gradients, modern design)
- Vercel.com (clean, developer-focused, professional)
- Framer.com (creative, modern, visually stunning)

Return CSS that creates a website people will say "Wow, this looks professional!" when they see it.

Return ONLY the complete, professional CSS code:"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'css')
            if FeedbackAgent._validate_css(content):
                st.success("✅ Custom CSS generated successfully!")
                return content
            else:
                if retry_count < 2:
                    st.warning(f"🔄 CSS validation failed, retrying... ({retry_count + 1}/3)")
                    return CodeAgent.generate_css_with_llm(spec, retry_count + 1)
                else:
                    st.error("❌ LLM failed to generate valid CSS after 3 attempts")
                    return CodeAgent.generate_css_template(spec)
                    
        except Exception as e:
            if retry_count < 2:
                st.warning(f"🔄 LLM error in CSS generation, retrying... ({retry_count + 1}/3): {str(e)[:100]}")
                return CodeAgent.generate_css_with_llm(spec, retry_count + 1)
            else:
                st.error(f"❌ LLM CSS generation failed after 3 attempts: {str(e)}")
                return CodeAgent.generate_css_template(spec)
    
    @staticmethod
    def generate_html_template(spec):
        """Template-based HTML generation (fallback)"""
        nav_html = ""
        if spec['needs_nav']:
            nav_items = ['Home', 'About', 'Services', 'Contact']
            nav_links = ''.join([f'<a href="#{item.lower()}">{item}</a>' for item in nav_items])
            nav_html = f"""
        <nav class="navbar">
            {nav_links}
        </nav>"""
        
        sections_html = ""
        for section in spec['sections']:
            section_id = section.replace(' ', '-').lower()
            sections_html += f"""
        <section id="{section_id}" class="section">
            <div class="container">
                <h2>{section.title()}</h2>
                <p>This is the {section} section. Content will be added here.</p>
                {CodeAgent.get_section_content(section)}
            </div>
        </section>"""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec['site_title']}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>{spec['site_title']}</h1>
        </div>
    </header>{nav_html}{sections_html}
</body>
</html>"""
    
    @staticmethod
    def get_section_content(section):
        """Generate specific content for different sections"""
        if section == 'contact form':
            return """
                <form class="contact-form">
                    <input type="text" placeholder="Your Name" required>
                    <input type="email" placeholder="Your Email" required>
                    <textarea placeholder="Your Message" rows="4" required></textarea>
                    <button type="submit">Send Message</button>
                </form>"""
        elif section == 'features':
            return """
                <div class="features-grid">
                    <div class="feature-card">
                        <h3>Feature 1</h3>
                        <p>Description of feature 1</p>
                    </div>
                    <div class="feature-card">
                        <h3>Feature 2</h3>
                        <p>Description of feature 2</p>
                    </div>
                    <div class="feature-card">
                        <h3>Feature 3</h3>
                        <p>Description of feature 3</p>
                    </div>
                </div>"""
        elif section == 'hero':
            return """
                <div class="hero-content">
                    <h2>Welcome to Our Amazing Website</h2>
                    <p>This is a hero section with compelling content.</p>
                    <button class="cta-button">Get Started</button>
                </div>"""
        else:
            return ""
    
    @staticmethod
    def generate_css_template(spec):
        """Template-based CSS generation (fallback)"""
        return f"""/* Modern CSS Variables */
:root {{
    --primary-color: {spec['primary_color']};
    --primary-light: {spec['primary_color']}20;
    --primary-dark: color-mix(in srgb, {spec['primary_color']} 80%, black);
    --secondary-color: #2c3e50;
    --accent-color: #e74c3c;
    --text-color: #2c3e50;
    --text-light: #7f8c8d;
    --background-color: #ffffff;
    --surface-color: #f8fafc;
    --border-color: #e1e8ed;
    --shadow-light: 0 2px 10px rgba(0,0,0,0.08);
    --shadow-medium: 0 4px 20px rgba(0,0,0,0.12);
    --shadow-heavy: 0 8px 30px rgba(0,0,0,0.15);
    --border-radius: 12px;
    --border-radius-sm: 8px;
    --spacing-xs: 0.5rem;
    --spacing-sm: 1rem;
    --spacing-md: 1.5rem;
    --spacing-lg: 2rem;
    --spacing-xl: 3rem;
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-heading: 'Poppins', var(--font-primary);
}}

/* Modern Reset and Base Styles */
*, *::before, *::after {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: var(--font-primary);
    line-height: 1.7;
    color: var(--text-color);
    background: linear-gradient(135deg, var(--surface-color) 0%, #ffffff 100%);
    min-height: 100vh;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-md);
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: var(--font-heading);
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: var(--spacing-sm);
    color: var(--text-color);
}}

h1 {{ font-size: 3.5rem; }}
h2 {{ font-size: 2.75rem; }}
h3 {{ font-size: 2rem; }}

p {{
    margin-bottom: var(--spacing-sm);
    color: var(--text-light);
    font-size: 1.1rem;
}}

/* Modern Header */
.header {{
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
    color: white;
    padding: var(--spacing-lg) 0;
    box-shadow: var(--shadow-medium);
    position: relative;
    overflow: hidden;
}}

.header::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%);
    pointer-events: none;
}}

.header h1 {{
    font-size: 3.5rem;
    text-align: center;
    font-weight: 800;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    letter-spacing: -0.02em;
}}

/* Modern Navigation */
.navbar {{
    background: rgba(255,255,255,0.98);
    backdrop-filter: blur(10px);
    padding: var(--spacing-sm) 0;
    box-shadow: var(--shadow-light);
    position: sticky;
    top: 0;
    z-index: 100;
    border-bottom: 1px solid var(--border-color);
}}

.navbar a {{
    color: var(--text-color);
    text-decoration: none;
    padding: var(--spacing-xs) var(--spacing-md);
    margin: 0 var(--spacing-xs);
    border-radius: var(--border-radius-sm);
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    display: inline-block;
}}

.navbar a:hover {{
    background: var(--primary-light);
    color: var(--primary-color);
    transform: translateY(-2px);
    box-shadow: var(--shadow-light);
}}

/* Modern Sections */
.section {{
    padding: var(--spacing-xl) 0;
    position: relative;
}}

.section:nth-child(even) {{
    background: var(--surface-color);
}}

.section h2 {{
    color: var(--text-color);
    margin-bottom: var(--spacing-md);
    font-size: 2.75rem;
    text-align: center;
    position: relative;
}}

.section h2::after {{
    content: '';
    position: absolute;
    bottom: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    border-radius: 2px;
}}

/* Hero Section */
.hero-content {{
    text-align: center;
    padding: var(--spacing-xl) 0;
    max-width: 800px;
    margin: 0 auto;
}}

.hero-content h2 {{
    font-size: 3.5rem;
    margin-bottom: var(--spacing-md);
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.hero-content p {{
    font-size: 1.3rem;
    margin-bottom: var(--spacing-lg);
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}}

.cta-button {{
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
    color: white;
    padding: var(--spacing-sm) var(--spacing-xl);
    border: none;
    border-radius: var(--border-radius);
    font-size: 1.2rem;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-medium);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: relative;
    overflow: hidden;
}}

.cta-button:hover {{
    transform: translateY(-3px);
    box-shadow: var(--shadow-heavy);
}}

.cta-button:active {{
    transform: translateY(-1px);
}}

/* Modern Features Grid */
.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: var(--spacing-lg);
    margin-top: var(--spacing-xl);
}}

.feature-card {{
    background: white;
    padding: var(--spacing-xl);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-light);
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid var(--border-color);
    position: relative;
    overflow: hidden;
}}

.feature-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
}}

.feature-card:hover {{
    transform: translateY(-8px);
    box-shadow: var(--shadow-heavy);
    border-color: var(--primary-color);
}}

.feature-card h3 {{
    color: var(--text-color);
    margin-bottom: var(--spacing-sm);
    font-size: 1.5rem;
}}

.feature-card p {{
    color: var(--text-light);
    line-height: 1.6;
}}

/* Modern Contact Form */
.contact-form {{
    max-width: 600px;
    margin: var(--spacing-xl) auto;
    background: white;
    padding: var(--spacing-xl);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-medium);
    border: 1px solid var(--border-color);
}}

.contact-form input,
.contact-form textarea {{
    width: 100%;
    padding: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
    border: 2px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    font-size: 1rem;
    font-family: var(--font-primary);
    transition: all 0.3s ease;
    background: white;
}}

.contact-form input:focus,
.contact-form textarea:focus {{
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px var(--primary-light);
    transform: translateY(-1px);
}}

.contact-form button {{
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
    color: white;
    padding: var(--spacing-sm) var(--spacing-xl);
    border: none;
    border-radius: var(--border-radius-sm);
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    box-shadow: var(--shadow-medium);
}}

.contact-form button:hover {{
    transform: translateY(-2px);
    box-shadow: var(--shadow-heavy);
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .header h1 {{
        font-size: 2.5rem;
    }}
    
    .hero-content h2 {{
        font-size: 2.5rem;
    }}
    
    .section h2 {{
        font-size: 2rem;
    }}
    
    .features-grid {{
        grid-template-columns: 1fr;
        gap: var(--spacing-md);
    }}
    
    .container {{
        padding: 0 var(--spacing-sm);
    }}
    
    .navbar a {{
        display: block;
        margin: var(--spacing-xs) 0;
        text-align: center;
    }}
}}

/* Loading Animations */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(30px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.feature-card {{
    animation: fadeInUp 0.6s ease-out;
}}

.feature-card:nth-child(2) {{
    animation-delay: 0.1s;
}}

.feature-card:nth-child(3) {{
    animation-delay: 0.2s;
}}"""

class FeedbackAgent:
    """Handles stateful, incremental website updates with memory and context awareness"""
    @staticmethod
    def parse_and_apply_feedback(feedback, workspace_path):
        """Parse user feedback with full context memory and apply incremental changes"""
        try:
            if not LLM_MODEL:
                return FeedbackAgent._fallback_regex_parsing(feedback, workspace_path)
            
            # Update conversation memory
            FeedbackAgent._update_conversation_memory(feedback)
            
            # Analyze feedback in context of previous changes
            change_analysis = FeedbackAgent._analyze_incremental_change(feedback)
            
            # Read current files
            html_path = os.path.join(workspace_path, 'index.html')
            css_path = os.path.join(workspace_path, 'styles.css')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                current_html = f.read()
            with open(css_path, 'r', encoding='utf-8') as f:
                current_css = f.read()
            
            # Apply incremental changes based on analysis
            new_html = current_html
            new_css = current_css
            
            if change_analysis['needs_html_update']:
                new_html = FeedbackAgent._apply_incremental_html_changes(
                    feedback, current_html, change_analysis
                )
                if not new_html:
                    new_html = current_html
            
            if change_analysis['needs_css_update']:
                new_css = FeedbackAgent._apply_incremental_css_changes(
                    feedback, new_html, current_css, change_analysis
                )
                if not new_css:
                    new_css = current_css
            
            # Write updated files
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(new_css)
            
            # Update website context and memory
            FeedbackAgent._update_website_context(feedback, change_analysis)
            
            # Log the change for future reference
            FeedbackAgent._log_incremental_change(feedback, change_analysis)
            
            changes_made = []
            if new_html != current_html:
                changes_made.append("content")
            if new_css != current_css:
                changes_made.append("styling")
            
            if changes_made:
                return True, f"✅ Incrementally updated {' and '.join(changes_made)}: '{feedback}'"
            else:
                return False, f"⚠️ No changes needed. Current state already matches your request."
            
        except Exception as e:
            return False, f"❌ Error applying incremental changes: {str(e)}"
    
    @staticmethod
    def _update_conversation_memory(feedback):
        """Update conversation memory with new user input"""
        st.session_state.conversation_memory.append({
            'timestamp': time.time(),
            'type': 'user_feedback',
            'content': feedback,
            'context_snapshot': st.session_state.website_context.copy()
        })
        
        # Keep only last 10 interactions to manage memory
        if len(st.session_state.conversation_memory) > 10:
            st.session_state.conversation_memory.pop(0)
    
    @staticmethod
    def _analyze_incremental_change(feedback):
        """Analyze what type of incremental change is needed based on context and history"""
        if not LLM_MODEL:
            return {'type': 'simple', 'needs_html_update': False, 'needs_css_update': True}
        
        # Create context summary for analysis
        context = st.session_state.website_context
        recent_changes = st.session_state.incremental_changes[-3:] if st.session_state.incremental_changes else []
        conversation_summary = FeedbackAgent._get_conversation_summary()
        
        prompt = f"""You are analyzing user feedback for incremental website development. 

CURRENT WEBSITE CONTEXT:
- Business Type: {context['business_type']}
- Theme: {context['current_theme']}
- Key Features: {', '.join(context['key_features']) if context['key_features'] else 'basic structure'}
- Content Focus: {context['content_focus']}

RECENT CONVERSATION:
{conversation_summary}

RECENT CHANGES MADE:
{chr(10).join([f"- {change['description']}" for change in recent_changes]) if recent_changes else "No recent changes"}

NEW USER FEEDBACK: "{feedback}"

TASK: Analyze what type of incremental change is needed. Consider:
1. Is this building on previous requests or changing direction?
2. What specifically needs to be updated?
3. Should this be a small tweak or larger update?

Respond in this exact JSON format:
{{
    "change_type": "incremental|major|redirect",
    "needs_html_update": true|false,
    "needs_css_update": true|false,
    "priority_areas": ["content", "structure", "styling", "features"],
    "building_on_previous": true|false,
    "scope": "small|medium|large",
    "intent": "brief description of user intent"
}}"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON response
            import json
            try:
                analysis = json.loads(content.strip())
                return analysis
            except:
                # Fallback if JSON parsing fails
                return {
                    'change_type': 'incremental',
                    'needs_html_update': 'content' in feedback.lower() or 'add' in feedback.lower(),
                    'needs_css_update': True,
                    'priority_areas': ['styling'],
                    'building_on_previous': True,
                    'scope': 'medium',
                    'intent': feedback[:100]
                }
                
        except Exception as e:
            st.warning(f"Analysis error, using fallback: {str(e)[:50]}")
            return {
                'change_type': 'incremental',
                'needs_html_update': True,
                'needs_css_update': True,
                'priority_areas': ['content', 'styling'],
                'building_on_previous': False,
                'scope': 'medium',
                'intent': feedback
            }
    
    @staticmethod
    def _get_conversation_summary():
        """Get a summary of recent conversation for context"""
        if not st.session_state.conversation_memory:
            return "No previous conversation"
        
        recent = st.session_state.conversation_memory[-5:]
        summary = []
        for item in recent:
            if item['type'] == 'user_feedback':
                summary.append(f"User: {item['content'][:80]}...")
        
        return '\n'.join(summary[-3:]) if summary else "No recent conversation"
    
    @staticmethod
    def _apply_incremental_html_changes(feedback, current_html, analysis):
        """Apply surgical HTML changes using two-stage LLM pipeline"""
        if not LLM_MODEL:
            return None
        
        context = st.session_state.website_context
        conversation_summary = FeedbackAgent._get_conversation_summary()
        preserved_elements = FeedbackAgent._extract_preserved_elements(current_html)
        
        # STAGE 1: Create enhanced prompt using Prompt Engineering LLM
        enhanced_prompt = FeedbackAgent._create_enhanced_coding_prompt(
            feedback, context, analysis, preserved_elements, current_html, 'html'
        )
        
        if not enhanced_prompt:
            st.warning("⚠️ Failed to create enhanced prompt, using fallback")
            return None
        
        # STAGE 2: Generate code using the enhanced prompt
        try:
            response = LLM_MODEL.invoke(enhanced_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'html')
            
            if FeedbackAgent._validate_html(content):
                change_ratio = FeedbackAgent._calculate_change_ratio(current_html, content)
                
                if change_ratio > 0.7:
                    st.warning("⚠️ Change too extensive, keeping current version to preserve functionality")
                    return None
                elif change_ratio > 0:
                    st.success(f"✅ Enhanced two-stage HTML edit applied ({change_ratio:.1%} changed)")
                    return content
                else:
                    return None
            else:
                st.warning("⚠️ HTML validation failed, keeping current version")
                return None
                
        except Exception as e:
            st.error(f"❌ Enhanced HTML generation error: {str(e)[:100]}")
            return None
    
    @staticmethod
    def _apply_incremental_css_changes(feedback, html_content, current_css, analysis):
        """Apply surgical CSS changes using two-stage LLM pipeline"""
        if not LLM_MODEL:
            return None
        
        context = st.session_state.website_context
        preserved_rules = FeedbackAgent._extract_preserved_css_rules(current_css)
        
        # STAGE 1: Create enhanced prompt using Prompt Engineering LLM
        enhanced_prompt = FeedbackAgent._create_enhanced_coding_prompt(
            feedback, context, analysis, preserved_rules, current_css, 'css'
        )
        
        if not enhanced_prompt:
            st.warning("⚠️ Failed to create enhanced CSS prompt, using fallback")
            return None
        
        # STAGE 2: Generate code using the enhanced prompt
        try:
            response = LLM_MODEL.invoke(enhanced_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'css')
            
            if FeedbackAgent._validate_css(content):
                change_ratio = FeedbackAgent._calculate_change_ratio(current_css, content)
                
                if change_ratio > 0.5:
                    st.warning("⚠️ CSS change too extensive, keeping current version")
                    return None
                elif change_ratio > 0:
                    st.success(f"✅ Enhanced two-stage CSS edit applied ({change_ratio:.1%} changed)")
                    return content
                else:
                    return None
            else:
                st.warning("⚠️ CSS validation failed, keeping current version")
                return None
                
        except Exception as e:
            st.error(f"❌ Enhanced CSS generation error: {str(e)[:100]}")
            return None
    
    @staticmethod
    def _create_enhanced_coding_prompt(feedback, context, analysis, preserved_elements, current_code, code_type):
        """Stage 1: Create enhanced, detailed coding prompt from user feedback"""
        if not LLM_MODEL:
            return None
        
        prompt_engineering_request = f"""You are a senior technical product manager and prompt engineer. Your job is to translate user feedback into precise, actionable prompts for developers.

USER FEEDBACK: "{feedback}"

CURRENT SYSTEM CONTEXT:
- Business Type: {context['business_type']} ({context['current_theme']})
- Key Features: {', '.join(context['key_features']) if context['key_features'] else 'basic structure'}
- Style Preferences: {context.get('style_preferences', {})}
- Change Analysis: {analysis}

CURRENT {code_type.upper()} CODE CONTEXT:
- Code Length: {len(current_code)} characters
- Preserved Elements: {preserved_elements}
- Code Type: {code_type}

YOUR TASK:
Create a detailed, professional prompt for a {code_type.upper()} developer that will produce high-quality results.

PROMPT ENHANCEMENT REQUIREMENTS:

1. **INTERPRET USER INTENT**:
   - What is the user really trying to achieve?
   - What business outcome do they want?
   - What specific elements need to change?

2. **ADD TECHNICAL SPECIFICITY**:
   - Specify exact CSS properties, selectors, or HTML elements to modify
   - Include specific measurements, colors, or layout requirements
   - Define responsive behavior and browser compatibility

3. **INCLUDE INDUSTRY BEST PRACTICES**:
   - Add modern web development standards
   - Include accessibility requirements
   - Specify performance considerations
   - Add UX/UI best practices relevant to their business

4. **SPECIFY PRESERVATION REQUIREMENTS**:
   - Clearly identify what must NOT be changed
   - Specify backward compatibility requirements
   - Define how to integrate changes without breaking existing functionality

5. **ADD QUALITY STANDARDS**:
   - Include specific design quality benchmarks
   - Reference professional websites as inspiration
   - Specify code quality and maintainability requirements

EXAMPLE ENHANCEMENT:
User says: "make the header blue"
Enhanced prompt: "Update the header background to a professional navy blue (#1e3a8a) with subtle gradient (linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)). Ensure text remains accessible with white/light text. Preserve existing header functionality including navigation hover states. Add subtle box-shadow for depth. Maintain responsive behavior on mobile devices."

Create a comprehensive, technical prompt that will produce professional results:

ENHANCED {code_type.upper()} DEVELOPMENT PROMPT:"""

        try:
            response = LLM_MODEL.invoke(prompt_engineering_request)
            enhanced_prompt = response.content if hasattr(response, 'content') else str(response)
            
            # Add the current code context to the enhanced prompt
            final_prompt = f"""{enhanced_prompt}

CURRENT {code_type.upper()} CODE TO MODIFY:
{current_code}

IMPORTANT: Follow the requirements above and return ONLY the updated {code_type.upper()} code."""
            
            return final_prompt.strip()
            
        except Exception as e:
            st.error(f"❌ Prompt enhancement error: {str(e)[:100]}")
            return None
    
    @staticmethod
    def _extract_preserved_elements(html_content):
        """Extract key elements that should be preserved in HTML"""
        preserved = []
        
        # Check for working forms
        if '<form' in html_content.lower():
            preserved.append("Contact forms and form functionality")
        
        # Check for navigation
        if '<nav' in html_content.lower() or 'navbar' in html_content.lower():
            preserved.append("Navigation menu and links")
        
        # Check for interactive elements
        if '<button' in html_content.lower():
            preserved.append("Buttons and their functionality")
        
        # Check for structured content
        if '<section' in html_content.lower():
            preserved.append("Section structure and layout")
        
        return "; ".join(preserved) if preserved else "Basic HTML structure"
    
    @staticmethod
    def _extract_preserved_css_rules(css_content):
        """Extract key CSS rules that should be preserved"""
        preserved = []
        
        # Check for animations
        if 'animation' in css_content.lower() or 'transition' in css_content.lower():
            preserved.append("Animations and transitions")
        
        # Check for responsive design
        if '@media' in css_content.lower():
            preserved.append("Responsive design rules")
        
        # Check for form styling
        if 'form' in css_content.lower() or 'input' in css_content.lower():
            preserved.append("Form styling and input styles")
        
        # Check for layout systems
        if 'grid' in css_content.lower() or 'flex' in css_content.lower():
            preserved.append("Grid and flexbox layouts")
        
        return "; ".join(preserved) if preserved else "Basic styling rules"
    
    @staticmethod
    def _calculate_change_ratio(original, modified):
        """Calculate how much of the code has changed (0.0 to 1.0)"""
        if original == modified:
            return 0.0
        
        # Simple line-by-line comparison
        original_lines = set(original.split('\n'))
        modified_lines = set(modified.split('\n'))
        
        if not original_lines:
            return 1.0
        
        unchanged_lines = original_lines.intersection(modified_lines)
        change_ratio = 1.0 - (len(unchanged_lines) / len(original_lines))
        
        return min(change_ratio, 1.0)
    
    @staticmethod
    def _clean_code_response(content, code_type):
        """Clean LLM response to extract pure code"""
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith(f'```{code_type}'):
            content = content[len(f'```{code_type}'):].strip()
        elif content.startswith('```'):
            content = content[3:].strip()
        if content.endswith('```'):
            content = content[:-3].strip()
        
        return content
    
    @staticmethod
    def _validate_html(content):
        """Basic HTML validation"""
        content_lower = content.lower()
        return (
            '<!doctype html>' in content_lower and
            '<html' in content_lower and
            '<body>' in content_lower and
            '</html>' in content_lower and
            len(content) > 200
        )
    
    @staticmethod
    def _validate_css(content):
        """Basic CSS validation"""
        return (
            len(content) > 50 and
            '{' in content and
            '}' in content and
            ':' in content
        )
    
    @staticmethod
    def _update_website_context(feedback, analysis):
        """Update website context based on the changes made"""
        context = st.session_state.website_context
        
        # Update business type if changed
        business_keywords = {
            'restaurant': 'restaurant', 'food': 'restaurant', 'menu': 'restaurant',
            'law': 'law firm', 'legal': 'law firm', 'lawyer': 'law firm',
            'medical': 'medical', 'clinic': 'medical', 'doctor': 'medical',
            'tech': 'technology', 'startup': 'technology', 'software': 'technology',
            'consulting': 'consultancy', 'consultancy': 'consultancy', 'sap': 'sap consultancy'
        }
        
        feedback_lower = feedback.lower()
        for keyword, business_type in business_keywords.items():
            if keyword in feedback_lower:
                context['business_type'] = business_type
                context['current_theme'] = f"{business_type} website"
                break
        
        # Update features based on feedback
        feature_keywords = {
            'pricing': 'pricing section', 'testimonial': 'testimonials', 'team': 'team profiles',
            'contact': 'contact form', 'gallery': 'image gallery', 'portfolio': 'portfolio',
            'menu': 'menu display', 'booking': 'appointment booking'
        }
        
        for keyword, feature in feature_keywords.items():
            if keyword in feedback_lower and feature not in context['key_features']:
                context['key_features'].append(feature)
        
        # Update style preferences
        if 'blue' in feedback_lower:
            context['style_preferences']['primary_color'] = 'blue'
        elif 'dark' in feedback_lower:
            context['style_preferences']['theme'] = 'dark'
        elif 'professional' in feedback_lower:
            context['style_preferences']['style'] = 'professional'
        
        # Log evolution
        context['evolution_log'].append({
            'feedback': feedback,
            'timestamp': time.time(),
            'analysis': analysis
        })
        
        # Keep evolution log manageable
        if len(context['evolution_log']) > 20:
            context['evolution_log'].pop(0)
    
    @staticmethod
    def _log_incremental_change(feedback, analysis):
        """Log the incremental change for future reference"""
        change_log = {
            'feedback': feedback,
            'timestamp': time.time(),
            'type': analysis.get('change_type', 'incremental'),
            'scope': analysis.get('scope', 'medium'),
            'description': f"{analysis.get('intent', feedback)[:100]}",
            'areas_changed': analysis.get('priority_areas', [])
        }
        
        st.session_state.incremental_changes.append(change_log)
        
        # Keep only last 15 changes
        if len(st.session_state.incremental_changes) > 15:
            st.session_state.incremental_changes.pop(0)
    
    @staticmethod
    def _fallback_regex_parsing(feedback, workspace_path):
        """Fallback regex-based parsing when no LLM is available"""
        try:
            html_path = os.path.join(workspace_path, 'index.html')
            css_path = os.path.join(workspace_path, 'styles.css')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            feedback_lower = feedback.lower()
            changes_made = False
            
            # Basic regex patterns for common requests
            if 'blue' in feedback_lower and ('header' in feedback_lower or 'background' in feedback_lower):
                css_content = css_content.replace('#3498db', '#007bff')
                css_content = css_content.replace('#68dff9', '#007bff')
                changes_made = True
            elif 'red' in feedback_lower and ('header' in feedback_lower or 'background' in feedback_lower):
                css_content = css_content.replace('#3498db', '#dc3545')
                css_content = css_content.replace('#68dff9', '#dc3545')
                changes_made = True
            elif 'green' in feedback_lower and ('header' in feedback_lower or 'background' in feedback_lower):
                css_content = css_content.replace('#3498db', '#28a745')
                css_content = css_content.replace('#68dff9', '#28a745')
                changes_made = True
            elif 'center' in feedback_lower and 'button' in feedback_lower:
                css_content = FeedbackAgent.center_buttons(css_content)
                changes_made = True
            elif 'bigger' in feedback_lower and 'text' in feedback_lower:
                css_content = css_content.replace('font-size: 2rem;', 'font-size: 2.5rem;')
                css_content = css_content.replace('font-size: 1.5rem;', 'font-size: 2rem;')
                changes_made = True
            
            # Write updated files
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            if changes_made:
                return True, "✅ Applied basic changes using fallback regex parsing"
            else:
                return False, "⚠️ No patterns matched. Try: 'make header blue', 'center buttons', 'bigger text'"
            
        except Exception as e:
            return False, f"❌ Error in fallback parsing: {str(e)}"
    
    @staticmethod
    def center_buttons(css_content):
        """Center buttons across the site (fallback method)"""
        button_center_css = '''

/* Button Centering */
.contact-form {
    text-align: center;
}
.contact-form button {
    display: block;
    margin: 1rem auto 0 auto;
}'''
        
        if 'margin: 1rem auto' not in css_content:
            css_content += button_center_css
        return css_content

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
            if LLM_MODEL:
                st.success(f"✅ LLM initialized successfully: {LLM_NAME}")
        except Exception as e:
            st.error(f"❌ LLM initialization failed: {e}")
            LLM_MODEL, LLM_NAME = None, "LLM Initialization Failed"
            _llm_initialized = True
    
    # Title and LLM Status
    st.title("🕸️ WebWeaver")
    st.markdown("*Live multi-agent LLM system for web development*")
    
    # Display AI System Status
    if LLM_MODEL:
        st.success(f"🤖 **Multiagent LLM System Active**: {LLM_NAME}")
        st.info("**Active AI Agents**: SpecAgent (wizard) • CodeAgent (LLM-powered) • PreviewAgent (live) • FeedbackAgent (LLM-powered) • PackageAgent (utility)")
    else:
        st.warning("⚠️ **No LLM Available** - Running in fallback mode with regex parsing")
        st.info("**Available**: SpecAgent • CodeAgent (template) • PreviewAgent • FeedbackAgent (regex) • PackageAgent")
        
        with st.expander("🔧 Setup LLM for Full Multiagent Capabilities"):
            st.markdown("""
            To enable the full multiagent LLM system, add one of these API keys:
            
            **Option 1: OpenAI** (Recommended)
            ```bash
            OPENAI_API_KEY=your_openai_api_key_here
            ```
            
            **Option 2: Google Gemini**
            ```bash
            GEMINI_API_KEY=your_gemini_api_key_here
            ```
            
            Add to your `.env` file or environment variables, then restart the application.
            """)
    
    # Sidebar - SpecAgent
    with st.sidebar:
        spec = SpecAgent.collect_specs()
        
        # Start Development Button
        if st.button("🚀 Start Development", type="primary", use_container_width=True):
            if not spec.get('business_name') or not spec.get('industry_focus'):
                st.error("⚠️ Please complete the required fields: Business Name and Industry Focus")
            else:
                with st.spinner("🤖 Creating your custom website based on detailed specifications..."):
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
                    
                    st.success("✅ Custom website generated successfully!")
                    st.rerun()
        
        # PackageAgent - Download ZIP
        if st.session_state.development_started:
            st.markdown("---")
            st.subheader("📦 PackageAgent")
            
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
            
            if LLM_MODEL:
                st.success(f"🤖 **AI-Powered**: Using {LLM_NAME}")
                st.info("🧠 **Stateful & Incremental**: Remembers context and builds progressively")
            else:
                st.warning("⚠️ **Fallback Mode**: Basic pattern matching only")
            
            # Show current website context/memory
            if st.session_state.get('website_context'):
                context = st.session_state.website_context
                with st.expander("🧠 Current Website Memory"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"""
                        **Business**: {context['business_type']}  
                        **Theme**: {context['current_theme']}  
                        **Focus**: {context['content_focus']}
                        """)
                    with col_b:
                        features_text = ', '.join(context['key_features'][:3]) if context['key_features'] else 'None'
                        if len(context['key_features']) > 3:
                            features_text += f" +{len(context['key_features'])-3} more"
                        st.markdown(f"""
                        **Features**: {features_text}  
                        **Changes Made**: {len(st.session_state.get('incremental_changes', []))}  
                        **Conversations**: {len(st.session_state.get('conversation_memory', []))}
                        """)
            
            # Chat-style feedback input with auto-clear
            feedback_key = f"feedback_input_{st.session_state.get('feedback_counter', 0)}"
            feedback = st.text_area(
                "Describe your next improvement:",
                placeholder="Examples:\n• 'Make this an SAP consultancy website'\n• 'Add a pricing section with 3 tiers'\n• 'Make the header darker and more professional'\n• 'Add team member photos and bios'\n• 'Include client testimonials'",
                height=120,
                key=feedback_key
            )
            
            if st.button("🚀 Apply Incremental Update", type="primary", use_container_width=True):
                if feedback.strip():
                    with st.spinner("🧠 AI analyzing context and applying incremental changes..."):
                        success, message = FeedbackAgent.parse_and_apply_feedback(
                            feedback, st.session_state.workspace_path
                        )
                    
                    if success:
                        st.success(message)
                        # Add to history
                        st.session_state.feedback_history.append(feedback)
                        # Trigger reload
                        st.session_state.reload_trigger += 1
                        # Auto-clear the textbox by incrementing the counter
                        st.session_state.feedback_counter = st.session_state.get('feedback_counter', 0) + 1
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please describe what you'd like to improve!")
            
            # Show incremental development capabilities
            with st.expander("💡 Incremental Development Features"):
                if LLM_MODEL:
                    st.markdown("""
                    **🧠 Context Awareness:**
                    - Remembers your business type and previous requests
                    - Builds on existing content rather than starting over
                    - Maintains consistency across all changes
                    
                    **🔄 Incremental Building:**
                    - "Add a contact form" → Adds form keeping existing design
                    - "Make it more professional" → Enhances current styling  
                    - "Add pricing section" → Integrates seamlessly with layout
                    
                    **💬 Progressive Conversation:**
                    - "Make this a restaurant" → Changes to restaurant theme
                    - "Add menu sections" → Builds on restaurant concept
                    - "Make it more elegant" → Refines restaurant styling
                    - "Add online ordering" → Adds feature to restaurant site
                    """)
                else:
                    st.markdown("""
                    **Limited to basic patterns:**
                    - "Make header blue/red/green"
                    - "Center all buttons" 
                    - "Make text bigger"
                    """)
            
            # Recent changes with context
            if st.session_state.get('incremental_changes'):
                st.subheader("📈 Incremental Development History")
                recent_changes = st.session_state.incremental_changes[-5:]
                for i, change in enumerate(reversed(recent_changes)):
                    scope_icon = {"small": "🔹", "medium": "🔸", "large": "🔶"}.get(change.get('scope', 'medium'), "🔸")
                    type_icon = {"incremental": "➕", "major": "🔄", "redirect": "↗️"}.get(change.get('type', 'incremental'), "➕")
                    
                    st.text(f"{scope_icon}{type_icon} {change['description'][:50]}{'...' if len(change['description']) > 50 else ''}")
            
            # Legacy feedback history (shorter format)
            elif st.session_state.feedback_history:
                st.subheader("📝 Recent Changes")
                for i, hist_feedback in enumerate(reversed(st.session_state.feedback_history[-3:])):
                    st.text(f"{len(st.session_state.feedback_history)-i}: {hist_feedback[:40]}{'...' if len(hist_feedback) > 40 else ''}")
    
    else:
        # Instructions when not started
        st.markdown(f"""
        ## 👋 Welcome to WebWeaver Multi-Agent AI System!
        
        **Current Status**: {'🤖 **Pure AI Mode**' if LLM_MODEL else '⚠️ **Template Fallback Mode**'} | **Model**: {LLM_NAME}
        
        **How the AI multiagent system works:**
        1. **SpecAgent** collects your requirements through an intelligent wizard
        2. **CodeAgent** uses {LLM_NAME if LLM_MODEL else 'basic templates'} to generate completely custom HTML/CSS
        3. **PreviewAgent** provides live preview with auto-reload capabilities
        4. **FeedbackAgent** uses {'AI to understand and apply' if LLM_MODEL else 'pattern matching for'} natural language modifications
        5. **PackageAgent** prepares your site for deployment
        
        ### 🤖 Active AI Agents:
        - **SpecAgent**: 🧙‍♂️ Requirement gathering wizard
        - **CodeAgent**: {'🧠 AI-powered custom generation' if LLM_MODEL else '📄 Template-based generation'} 
        - **PreviewAgent**: 🔍 Live preview server with file monitoring
        - **FeedbackAgent**: {'🎨 AI-powered natural language processing' if LLM_MODEL else '🔍 Regex pattern matching'} 
        - **PackageAgent**: 📦 ZIP packaging and deployment prep
        
        ### {'✨ AI-First Capabilities' if LLM_MODEL else '⚠️ Limited Template Mode'}:
        """)
        
        if LLM_MODEL:
            st.markdown("""
            - 🎯 **Truly Custom Websites**: No templates - each site is designed from scratch by AI
            - 🧠 **Intelligent Understanding**: AI interprets your requirements and creates unique designs
            - 🎨 **Creative Design Generation**: Professional layouts, color schemes, and styling
            - 💬 **Natural Language Control**: Make changes by simply describing what you want
            - 🔄 **Iterative Improvement**: AI learns from your feedback to refine the design
            - 📱 **Modern Standards**: Responsive, accessible, and contemporary web design
            
            **This is a pure AI-driven system - no default templates or fallbacks when API keys are working!**
            """)
        else:
            st.markdown("""
            - ⚠️ **Basic Template Mode**: Uses predefined templates instead of AI generation
            - 🔍 **Pattern Matching**: Limited feedback processing using regex patterns
            - 📄 **Standard Layouts**: Generic designs that aren't customized to your needs
            
            **To unlock the full AI multiagent capabilities:**
            - Add an OpenAI API key to your `.env` file: `OPENAI_API_KEY=your_key_here`
            - Restart the application to activate GPT-4o powered generation
            """)
        
        st.markdown("""
        **Get started by configuring your site in the sidebar!**
        """)

if __name__ == "__main__":
    main() 