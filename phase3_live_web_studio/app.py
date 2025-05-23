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
    """Generates single HTML file with embedded CSS and JavaScript"""
    @staticmethod
    def generate_files(spec, workspace_path):
        """Generate single index.html file with embedded CSS and JS"""
        
        if LLM_MODEL:
            # Use LLM for intelligent single-file generation
            html_content = CodeAgent.generate_single_file_with_llm(spec)
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
    def generate_single_file_with_llm(spec, retry_count=0):
        """Generate Fortune 500-quality single HTML file with embedded CSS and JS"""
        if not LLM_MODEL:
            st.error("❌ No LLM available for HTML generation")
            return CodeAgent.generate_single_file_template(spec)
        
        # Fetch professional images for the business
        with st.spinner("🖼️ Fetching professional images..."):
            business_type = spec.get('purpose', 'business')
            sections = spec.get('core_sections', [])
            images = ImageService.get_business_images(business_type, sections, count=4)
        
        if images:
            st.success(f"✅ Found {len(images)} professional images for {business_type}")
        else:
            st.info("ℹ️ Using placeholder images")
        
        # Create comprehensive prompt for professional single-file websites
        sections_list = ', '.join(spec.get('core_sections', ['Hero/Welcome', 'About Us', 'Contact']))
        features_list = ', '.join(spec.get('special_features', []))
        
        # Prepare image information for the prompt
        image_info = ""
        if images:
            hero_img = images[0]
            image_info = f"""
PROFESSIONAL IMAGES AVAILABLE:
• Hero Background: {hero_img['url']} (Use as hero section background)
• Gallery Images: {len(images)-1} additional professional images available
• All images are high-quality, professional, and relevant to {business_type}
• Use images strategically to enhance visual appeal and professionalism"""
        
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

{image_info}

SINGLE-FILE ARCHITECTURE REQUIREMENTS:

**1. COMPLETE EMBEDDED DESIGN:**
• All CSS embedded in <style> tags in the <head>
• Optional JavaScript embedded in <script> tags
• No external dependencies except Google Fonts (optional)
• Self-contained, deployable anywhere

**2. PROFESSIONAL VISUAL DESIGN WITH IMAGES:**
• Use the hero background image for a stunning visual impact
• Implement professional image galleries where appropriate
• Ensure all images are responsive and optimized
• Add subtle overlay effects and proper image styling
• Professional color palette with sophisticated gradients
• Modern typography (Inter, SF Pro, or web-safe alternatives)  
• Perfect spacing and visual hierarchy with images
• Subtle shadows, rounded corners, and premium effects

**3. ENTERPRISE-GRADE CONTENT:**
• Compelling headlines that communicate value instantly
• Industry-specific expertise and credibility signals
• Professional contact information and trust indicators
• Clear calls-to-action that drive business conversations
• Social proof through testimonials and case studies

**4. MODERN CSS ARCHITECTURE:**
• CSS custom properties for consistent theming
• Mobile-first responsive design with proper breakpoints
• Smooth transitions and hover effects
• Professional button styling with gradients/shadows
• Modern card designs with subtle elevation
• Clean navigation with proper accessibility
• Responsive image handling and optimization

**5. INTERACTIVE ELEMENTS (Optional JS):**
• Smooth scrolling navigation
• Mobile menu toggle functionality
• Contact form validation
• Subtle animations on scroll (if appropriate)
• Professional micro-interactions

**6. INDUSTRY-SPECIFIC EXCELLENCE:**

For Consulting/SAP: Navy/blue gradients, trust badges, "Fortune 500 clients", enterprise credibility, ROI focus
For Healthcare: Calming blues/greens, certifications, patient care focus, accessibility compliance
For Technology: Modern gradients, innovation messaging, cutting-edge aesthetics, security emphasis  
For Creative: Bold visual elements, portfolio showcases, artistic layouts, unique typography
For Legal: Professional authority, credentials emphasis, trust building, conservative elegance

**7. CONVERSION OPTIMIZATION:**
• Clear value propositions throughout
• Multiple contact methods (phone, email, form)
• Strategic placement of credibility indicators
• Professional testimonials with company names
• Easy-to-find contact information
• Mobile-optimized user experience

QUALITY BENCHMARKS:
Create a website that looks like it was designed for:
• McKinsey & Company (consulting authority)
• Stripe (clean, modern, professional)
• Apple (premium design and typography)
• Memorial Sloan Kettering (healthcare trust)
• Cravath (legal prestige)

The final result should make visitors immediately think: "This company is clearly the premium choice in their industry."

TECHNICAL REQUIREMENTS:
• Valid HTML5 semantic structure
• Embedded CSS with modern techniques
• Responsive design (mobile, tablet, desktop)
• Accessibility compliance (WCAG 2.1 AA)
• Fast loading with optimized code
• Cross-browser compatibility
• Professional image integration and responsive handling

CRITICAL OUTPUT INSTRUCTIONS:
- Return ONLY the complete HTML document
- Start with <!DOCTYPE html> and end with </html>
- Do NOT include any explanatory text before or after the HTML
- Do NOT include markdown code blocks or formatting
- Do NOT include feature lists or descriptions
- The response should be pure, clean HTML code that can be used directly
- Include the professional images using the URLs provided above

Generate the complete HTML document now:"""

        try:
            response = LLM_MODEL.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'html')
            
            # If no images were embedded by LLM, add them manually
            if images and 'background-image:' not in content:
                image_html = ImageService.create_image_html(images, business_type)
                # Insert before closing </head> tag
                content = content.replace('</head>', f'{image_html}\n</head>')
            
            if FeedbackAgent._validate_html(content):
                st.success("✅ Premium single-file website with professional images generated!")
                return content
            else:
                if retry_count < 2:
                    st.warning(f"🔄 HTML validation failed, retrying with enhanced requirements... ({retry_count + 1}/3)")
                    return CodeAgent.generate_single_file_with_llm(spec, retry_count + 1)
                else:
                    st.error("❌ LLM failed to generate valid HTML after 3 attempts")
                    return CodeAgent.generate_single_file_template(spec)
                    
        except Exception as e:
            if retry_count < 2:
                st.warning(f"🔄 LLM error in generation, retrying... ({retry_count + 1}/3): {str(e)[:100]}")
                return CodeAgent.generate_single_file_with_llm(spec, retry_count + 1)
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
            
            # Update conversation memory
            FeedbackAgent._update_conversation_memory(feedback)
            
            # Analyze feedback in context of previous changes
            change_analysis = FeedbackAgent._analyze_incremental_change(feedback)
            
            # Read current single HTML file
            html_path = os.path.join(workspace_path, 'index.html')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                current_html = f.read()
            
            # Apply changes to the single file
            new_html = FeedbackAgent._apply_single_file_changes(
                feedback, current_html, change_analysis
            )
            
            if not new_html:
                new_html = current_html
            
            # Write updated file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_html)
            
            # Update website context and memory
            FeedbackAgent._update_website_context(feedback, change_analysis)
            
            # Log the change for future reference
            FeedbackAgent._log_incremental_change(feedback, change_analysis)
            
            if new_html != current_html:
                return True, f"✅ Single-file website updated: '{feedback}'"
            else:
                return False, f"⚠️ No changes needed. Current state already matches your request."
            
        except Exception as e:
            return False, f"❌ Error applying changes to single file: {str(e)}"
    
    @staticmethod
    def _apply_single_file_changes(feedback, current_html, analysis):
        """Apply changes to the single HTML file using enhanced LLM prompts"""
        if not LLM_MODEL:
            return None
        
        context = st.session_state.website_context
        
        # Create enhanced prompt for single-file modifications
        enhanced_prompt = FeedbackAgent._create_single_file_prompt(
            feedback, context, analysis, current_html
        )
        
        if not enhanced_prompt:
            st.warning("⚠️ Failed to create enhanced prompt")
            return None
        
        try:
            response = LLM_MODEL.invoke(enhanced_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean and validate
            content = FeedbackAgent._clean_code_response(content, 'html')
            
            if FeedbackAgent._validate_html(content):
                change_ratio = FeedbackAgent._calculate_change_ratio(current_html, content)
                
                if change_ratio > 0.6:  # More than 60% changed = too much for single file
                    st.warning("⚠️ Change too extensive, keeping current version to preserve functionality")
                    return None
                elif change_ratio > 0:
                    st.success(f"✅ Single-file website updated ({change_ratio:.1%} changed)")
                    return content
                else:
                    return None
            else:
                st.warning("⚠️ HTML validation failed, keeping current version")
                return None
                
        except Exception as e:
            st.error(f"❌ Single-file update error: {str(e)[:100]}")
            return None
    
    @staticmethod
    def _create_single_file_prompt(feedback, context, analysis, current_html):
        """Create enhanced prompt for single-file website modifications"""
        if not LLM_MODEL:
            return None
        
        prompt = f"""You are a professional web developer updating a single HTML file (with embedded CSS and JavaScript) based on user feedback.

USER FEEDBACK: "{feedback}"

CURRENT WEBSITE CONTEXT:
- Business Type: {context['business_type']} ({context['current_theme']})
- Key Features: {', '.join(context['key_features']) if context['key_features'] else 'basic structure'}
- Style Preferences: {context.get('style_preferences', {})}
- Change Type: {analysis.get('change_type', 'incremental')}
- Change Scope: {analysis.get('scope', 'medium')}

SINGLE-FILE MODIFICATION INSTRUCTIONS:

**1. UNDERSTAND THE REQUEST:**
- Interpret the user's intent and desired outcome
- Identify specific elements that need modification
- Determine if this requires HTML structure, CSS styling, or JavaScript changes

**2. TARGETED MODIFICATIONS:**
- Make MINIMAL, focused changes to achieve the request
- Preserve all existing functionality and working elements
- Maintain the embedded CSS and JavaScript structure
- Keep the professional quality and visual consistency

**3. SINGLE-FILE BEST PRACTICES:**
- All styles remain embedded in the <style> section
- All scripts remain embedded in the <script> section  
- Maintain clean, organized code structure
- Preserve responsive design and accessibility

**4. QUALITY STANDARDS:**
- Keep the professional, enterprise-grade appearance
- Maintain modern design principles and visual hierarchy
- Ensure cross-browser compatibility and performance
- Preserve mobile responsiveness

**5. CHANGE SAFETY:**
- Don't break existing navigation or functionality
- Maintain form submissions and interactive elements
- Keep the overall design cohesion and brand consistency
- Test that all sections remain accessible

CURRENT SINGLE HTML FILE:
{current_html}

TASK: Apply the requested changes while maintaining the single-file architecture and professional quality.

CRITICAL OUTPUT INSTRUCTIONS:
- Return ONLY the complete, updated HTML document
- Start with <!DOCTYPE html> and end with </html>
- Do NOT include any explanatory text before or after the HTML
- Do NOT include markdown code blocks or formatting
- Do NOT include feature lists or descriptions
- The response should be pure, clean HTML code that can be used directly

Return the complete, updated HTML file now:"""

        try:
            return prompt.strip()
        except Exception as e:
            st.error(f"❌ Single-file prompt creation error: {str(e)[:100]}")
            return None
    
    @staticmethod
    def _fallback_single_file_parsing(feedback, workspace_path):
        """Fallback single-file parsing when no LLM is available"""
        try:
            html_path = os.path.join(workspace_path, 'index.html')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            feedback_lower = feedback.lower()
            changes_made = False
            
            # Basic single-file modifications
            if 'blue' in feedback_lower and ('header' in feedback_lower or 'background' in feedback_lower):
                html_content = html_content.replace('--primary-color: #3498db', '--primary-color: #007bff')
                changes_made = True
            elif 'red' in feedback_lower and ('header' in feedback_lower or 'background' in feedback_lower):
                html_content = html_content.replace('--primary-color: #3498db', '--primary-color: #dc3545')
                changes_made = True
            elif 'green' in feedback_lower and ('header' in feedback_lower or 'background' in feedback_lower):
                html_content = html_content.replace('--primary-color: #3498db', '--primary-color: #28a745')
                changes_made = True
            elif 'bigger' in feedback_lower and 'text' in feedback_lower:
                html_content = html_content.replace('font-size: 3rem', 'font-size: 4rem')
                html_content = html_content.replace('font-size: 2.5rem', 'font-size: 3rem')
                changes_made = True
            
            # Write updated file
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            if changes_made:
                return True, "✅ Applied basic changes to single file using fallback parsing"
            else:
                return False, "⚠️ No patterns matched. Try: 'make header blue', 'bigger text'"
            
        except Exception as e:
            return False, f"❌ Error in single-file fallback parsing: {str(e)}"
    
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
        """Analyze what type of change is needed for single file updates"""
        # Simplified analysis for single-file approach
        return {
            'change_type': 'incremental',
            'scope': 'medium',
            'intent': feedback,
            'priority_areas': ['styling', 'content']
        }
    
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
        """Clean LLM response to extract pure code, removing explanatory text"""
        content = content.strip()
        
        # Handle HTML responses specifically
        if code_type == 'html':
            # Look for DOCTYPE declaration - this is where actual HTML starts
            doctype_match = content.find('<!DOCTYPE html>')
            if doctype_match != -1:
                # Extract from DOCTYPE to end of HTML
                content = content[doctype_match:]
                
                # Find the closing </html> tag
                html_end = content.rfind('</html>')
                if html_end != -1:
                    content = content[:html_end + 7]  # Include the </html> tag
        
        # Remove markdown code blocks
        if '```html' in content:
            # Extract content between ```html and ```
            start = content.find('```html')
            if start != -1:
                start = content.find('\n', start) + 1  # Start after the newline
                end = content.find('```', start)
                if end != -1:
                    content = content[start:end].strip()
        elif '```' in content:
            # Generic code block handling
            start = content.find('```')
            if start != -1:
                start = content.find('\n', start) + 1  # Start after the newline
                end = content.find('```', start)
                if end != -1:
                    content = content[start:end].strip()
        
        # Additional cleanup for HTML
        if code_type == 'html':
            # Remove any text before DOCTYPE if it still exists
            doctype_pos = content.find('<!DOCTYPE html>')
            if doctype_pos > 0:
                content = content[doctype_pos:]
                
            # Remove any text after </html>
            html_end = content.find('</html>')
            if html_end != -1:
                # Look for any text after </html> and remove it
                after_html = content[html_end + 7:].strip()
                if after_html:
                    content = content[:html_end + 7]
        
        return content.strip()
    
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
        """Log the change for future reference"""
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
        if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_key_here":
            return ImageService._get_unsplash_images(business_type, sections, count)
        else:
            return ImageService._get_placeholder_images(business_type, count)
    
    @staticmethod
    def _get_unsplash_images(business_type, sections, count=4):
        """Fetch professional images from Unsplash API"""
        try:
            # Map business types to search keywords
            keyword_map = {
                'sap consultancy': 'business meeting professional office',
                'consultancy': 'business consulting professional meeting',
                'consulting': 'corporate office business team',
                'technology': 'technology computer modern office',
                'software': 'developer coding technology office',
                'healthcare': 'medical healthcare professional doctor',
                'medical': 'hospital medical professional clean',
                'legal': 'law office professional business suit',
                'restaurant': 'restaurant food chef kitchen',
                'food': 'food restaurant chef cooking',
                'creative': 'creative design office modern workspace',
                'agency': 'creative agency modern office team',
                'education': 'education learning students classroom',
                'real estate': 'real estate modern house architecture',
                'non-profit': 'community people helping volunteer'
            }
            
            # Get relevant keywords
            keywords = keyword_map.get(business_type.lower(), 'professional business office')
            
            # Fetch images from Unsplash
            url = "https://api.unsplash.com/search/photos"
            params = {
                'query': keywords,
                'per_page': count,
                'orientation': 'landscape',
                'content_filter': 'high',
                'order_by': 'relevant'
            }
            headers = {
                'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                images = []
                
                for photo in data.get('results', []):
                    images.append({
                        'url': photo['urls']['regular'],
                        'url_small': photo['urls']['small'],
                        'alt': photo.get('alt_description', f'Professional {business_type} image'),
                        'photographer': photo['user']['name'],
                        'photographer_url': photo['user']['links']['html']
                    })
                
                return images
            else:
                st.warning(f"Unsplash API error: {response.status_code}")
                return ImageService._get_placeholder_images(business_type, count)
                
        except Exception as e:
            st.warning(f"Image fetch error: {str(e)[:50]}... Using placeholders")
            return ImageService._get_placeholder_images(business_type, count)
    
    @staticmethod
    def _get_placeholder_images(business_type, count=4):
        """Generate placeholder images as fallback"""
        # Business-themed placeholder images
        placeholder_themes = {
            'consultancy': 'business/meeting',
            'consulting': 'business/team', 
            'technology': 'tech/office',
            'software': 'tech/coding',
            'healthcare': 'medical/hospital',
            'medical': 'medical/clinic',
            'legal': 'business/law',
            'restaurant': 'food/restaurant',
            'food': 'food/kitchen',
            'creative': 'design/creative',
            'agency': 'design/agency',
            'education': 'education/learning',
            'real estate': 'architecture/house'
        }
        
        theme = placeholder_themes.get(business_type.lower(), 'business/office')
        base_url = "https://picsum.photos"
        
        images = []
        sizes = ['1200x600', '800x400', '1000x500', '900x450']
        
        for i in range(count):
            size = sizes[i % len(sizes)]
            images.append({
                'url': f"{base_url}/{size}?random={i+1}",
                'url_small': f"{base_url}/400x200?random={i+1}",
                'alt': f'Professional {business_type} image',
                'photographer': 'Placeholder Image',
                'photographer_url': '#'
            })
        
        return images
    
    @staticmethod
    def create_image_html(images, business_type):
        """Create HTML code for embedding images"""
        if not images:
            return ""
        
        hero_image = images[0] if images else None
        gallery_images = images[1:] if len(images) > 1 else []
        
        html_parts = []
        
        # Hero image
        if hero_image:
            html_parts.append(f"""
            <!-- Hero Background Image -->
            <style>
                .hero-section {{
                    background-image: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('{hero_image['url']}');
                    background-size: cover;
                    background-position: center;
                    color: white;
                }}
            </style>""")
        
        # Gallery section
        if gallery_images:
            gallery_html = ""
            for img in gallery_images[:3]:  # Max 3 gallery images
                gallery_html += f"""
                <div class="gallery-item">
                    <img src="{img['url_small']}" alt="{img['alt']}" loading="lazy">
                </div>"""
            
            html_parts.append(f"""
            <!-- Image Gallery -->
            <div class="image-gallery">
                {gallery_html}
            </div>
            
            <style>
                .image-gallery {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 1rem;
                    margin: 2rem 0;
                }}
                .gallery-item img {{
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
            </style>""")
        
        return "\n".join(html_parts)

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
        st.success(f"🤖 **Single-File AI System**: Using {LLM_NAME}")
        st.info("🗂️ **Embedded Architecture**: Complete websites in one HTML file with embedded CSS/JS")
        
        # Image service status
        if UNSPLASH_ACCESS_KEY and UNSPLASH_ACCESS_KEY != "your_unsplash_key_here":
            st.success("🖼️ **Professional Images**: Unsplash API connected - High-quality business images")
        else:
            st.info("🖼️ **Image Service**: Using placeholder images - Add Unsplash API for professional photos")
    else:
        st.warning("⚠️ **Fallback Mode**: Basic template generation")
        
        with st.expander("Setup LLM for Full Multiagent Capabilities"):
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
        
        with st.expander("Setup Professional Image Integration (Optional)"):
            st.markdown("""
            For automatic professional business images, add Unsplash API:
            
            **Unsplash API** (Free - 50 requests/hour)
            1. Create account at [unsplash.com/developers](https://unsplash.com/developers)
            2. Create a new application to get your Access Key
            3. Add to your `.env` file:
            ```bash
            UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
            ```
            4. Restart the application
            
            **Features with Unsplash:**
            - High-quality professional photos
            - Business-specific imagery (consulting, tech, medical, etc.)
            - Hero backgrounds and gallery images
            - Automatic selection based on your business type
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
                        **Architecture**: Single HTML file
                        """)
            
            # Chat-style feedback input with auto-clear
            feedback_key = f"feedback_input_{st.session_state.get('feedback_counter', 0)}"
            feedback = st.text_area(
                "Describe your next improvement:",
                placeholder="Examples:\n• 'Make this an SAP consultancy website'\n• 'Add a pricing section with 3 tiers'\n• 'Make the header darker and more professional'\n• 'Add team member photos and bios'\n• 'Include client testimonials'",
                height=120,
                key=feedback_key
            )
            
            if st.button("🚀 Apply Single-File Update", type="primary", use_container_width=True):
                if feedback.strip():
                    with st.spinner("🗂️ AI updating single HTML file with embedded styles..."):
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
            
            # Show single-file development capabilities
            with st.expander("🗂️ Single-File Architecture Benefits"):
                if LLM_MODEL:
                    st.markdown("""
                    **🎯 Complete Websites in One File:**
                    - All HTML, CSS, and JavaScript embedded in single index.html
                    - No broken links or missing files - everything is self-contained
                    - Perfect for deployment - just upload one file anywhere
                    - Better AI context - LLM sees complete design in one view
                    
                    **🧠 Cohesive Design Generation:**
                    - LLM creates HTML and CSS together for better consistency
                    - No conflicting styles between separate files
                    - Professional responsive design with embedded media queries
                    - Modern CSS variables and JavaScript interactions included
                    
                    **📦 Deployment Simplicity:**
                    - Download one complete file - ready to deploy anywhere
                    - Works on any web server without configuration
                    - No dependencies or external resources (except optional Google Fonts)
                    - Perfect for quick prototypes or production websites
                    
                    **⚡ Performance Benefits:**
                    - Fewer HTTP requests - everything loads together
                    - No external CSS/JS file dependencies
                    - Optimized for fast loading and caching
                    - Self-contained and portable across platforms
                    """)
                else:
                    st.markdown("""
                    **Limited template mode:**
                    - Basic single-file template generation
                    - Simple color and size modifications
                    """)
            
            # Recent changes with context
            if st.session_state.get('incremental_changes'):
                st.subheader("📈 Single-File Development History")
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
            - 🖼️ **Professional Images**: Automatic integration of high-quality business photos
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
            - 🖼️ **Placeholder Images**: Generic placeholder images only
            
            **To unlock the full AI multiagent capabilities:**
            - Add an OpenAI API key to your `.env` file: `OPENAI_API_KEY=your_key_here`
            - Optionally add Unsplash API key for professional images: `UNSPLASH_ACCESS_KEY=your_key`
            - Restart the application to activate GPT-4o powered generation
            """)
        
        st.markdown("""
        **Get started by configuring your site in the sidebar!**
        """)

if __name__ == "__main__":
    main() 