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

# Configure Streamlit page
st.set_page_config(
    page_title="WebWeaver",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    """Handles requirement gathering wizard"""
    @staticmethod
    def collect_specs():
        """Collect user specifications through sidebar wizard"""
        st.sidebar.header("🧙‍♂️ SpecAgent - Project Wizard")
        
        # Question 1: Site title
        site_title = st.sidebar.text_input(
            "Site title?", 
            value=st.session_state.get('site_title', 'My Awesome Website'),
            key='site_title'
        )
        
        # Question 2: Navigation bar
        needs_nav = st.sidebar.checkbox(
            "Do you need navigation bar?", 
            value=st.session_state.get('needs_nav', True),
            key='needs_nav'
        )
        
        # Question 3: Primary color
        primary_color = st.sidebar.color_picker(
            "Primary color?", 
            value=st.session_state.get('primary_color', '#3498db'),
            key='primary_color'
        )
        
        # Question 4: Sections
        section_options = ['header', 'hero', 'features', 'about', 'services', 'contact form', 'footer']
        selected_sections = st.sidebar.multiselect(
            "Sections you want (e.g. header, features, contact form)?",
            section_options,
            default=st.session_state.get('selected_sections', ['header', 'hero', 'features', 'contact form']),
            key='selected_sections'
        )
        
        # Create spec object
        spec = {
            'site_title': site_title,
            'needs_nav': needs_nav,
            'primary_color': primary_color,
            'sections': selected_sections
        }
        
        # Display summary
        nav_text = "with navigation" if needs_nav else "without navigation"
        sections_text = ", ".join(selected_sections) if selected_sections else "no sections"
        
        st.sidebar.markdown("### 📋 Project Summary")
        st.sidebar.info(f"You'll get a **{site_title}** site {nav_text} with **{sections_text}** sections in **{primary_color}** theme.")
        
        return spec

class CodeAgent:
    """Generates initial HTML and CSS scaffolding"""
    @staticmethod
    def generate_files(spec, workspace_path):
        """Generate index.html and styles.css based on spec"""
        
        # Generate HTML
        html_content = CodeAgent.generate_html(spec)
        with open(os.path.join(workspace_path, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate CSS
        css_content = CodeAgent.generate_css(spec)
        with open(os.path.join(workspace_path, 'styles.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    @staticmethod
    def generate_html(spec):
        """Generate HTML content"""
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
    def generate_css(spec):
        """Generate CSS content"""
        return f"""/* CSS Variables */
:root {{
    --primary-color: {spec['primary_color']};
    --secondary-color: #2c3e50;
    --text-color: #333;
    --background-color: #f8f9fa;
    --white: #ffffff;
    --border-radius: 8px;
    --box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}

/* Reset and Base Styles */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}}

/* Header Styles */
.header {{
    background-color: var(--primary-color);
    color: var(--white);
    padding: 1rem 0;
    box-shadow: var(--box-shadow);
}}

.header h1 {{
    font-size: 2rem;
    text-align: center;
}}

/* Navigation Styles */
.navbar {{
    background-color: var(--secondary-color);
    padding: 1rem 0;
}}

.navbar a {{
    color: var(--white);
    text-decoration: none;
    padding: 0.5rem 1rem;
    margin: 0 0.5rem;
    border-radius: var(--border-radius);
    transition: background-color 0.3s;
}}

.navbar a:hover {{
    background-color: var(--primary-color);
}}

/* Section Styles */
.section {{
    padding: 3rem 0;
    border-bottom: 1px solid #eee;
}}

.section h2 {{
    color: var(--primary-color);
    margin-bottom: 1rem;
    font-size: 2rem;
}}

/* Hero Section */
.hero-content {{
    text-align: center;
    padding: 2rem 0;
}}

.hero-content h2 {{
    font-size: 2.5rem;
    margin-bottom: 1rem;
}}

.cta-button {{
    background-color: var(--primary-color);
    color: var(--white);
    padding: 1rem 2rem;
    border: none;
    border-radius: var(--border-radius);
    font-size: 1.1rem;
    cursor: pointer;
    transition: background-color 0.3s;
}}

.cta-button:hover {{
    background-color: var(--secondary-color);
}}

/* Features Grid */
.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}}

.feature-card {{
    background: var(--white);
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    text-align: center;
}}

.feature-card h3 {{
    color: var(--primary-color);
    margin-bottom: 1rem;
}}

/* Contact Form */
.contact-form {{
    max-width: 600px;
    margin: 2rem auto;
    background: var(--white);
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
}}

.contact-form input,
.contact-form textarea {{
    width: 100%;
    padding: 1rem;
    margin-bottom: 1rem;
    border: 1px solid #ddd;
    border-radius: var(--border-radius);
    font-size: 1rem;
}}

.contact-form button {{
    background-color: var(--primary-color);
    color: var(--white);
    padding: 1rem 2rem;
    border: none;
    border-radius: var(--border-radius);
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s;
}}

.contact-form button:hover {{
    background-color: var(--secondary-color);
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .header h1 {{
        font-size: 1.5rem;
    }}
    
    .hero-content h2 {{
        font-size: 2rem;
    }}
    
    .navbar a {{
        display: block;
        margin: 0.2rem 0;
    }}
}}"""

class FeedbackAgent:
    """Handles style tweaks and feedback parsing"""
    @staticmethod
    def parse_and_apply_feedback(feedback, workspace_path):
        """Parse user feedback and apply style changes"""
        try:
            # Read current files
            html_path = os.path.join(workspace_path, 'index.html')
            css_path = os.path.join(workspace_path, 'styles.css')
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Parse feedback for common style commands
            feedback_lower = feedback.lower()
            
            # Color changes
            if 'background' in feedback_lower and 'blue' in feedback_lower:
                css_content = FeedbackAgent.update_css_property(css_content, 'header', 'background-color', '#007bff')
            elif 'background' in feedback_lower and 'red' in feedback_lower:
                css_content = FeedbackAgent.update_css_property(css_content, 'header', 'background-color', '#dc3545')
            elif 'background' in feedback_lower and 'green' in feedback_lower:
                css_content = FeedbackAgent.update_css_property(css_content, 'header', 'background-color', '#28a745')
            
            # Font size changes
            if 'bigger' in feedback_lower or 'larger' in feedback_lower:
                if 'title' in feedback_lower or 'heading' in feedback_lower:
                    css_content = FeedbackAgent.update_css_property(css_content, '.header h1', 'font-size', '2.5rem')
                else:
                    css_content = FeedbackAgent.increase_font_sizes(css_content)
            elif 'smaller' in feedback_lower:
                if 'title' in feedback_lower or 'heading' in feedback_lower:
                    css_content = FeedbackAgent.update_css_property(css_content, '.header h1', 'font-size', '1.5rem')
                else:
                    css_content = FeedbackAgent.decrease_font_sizes(css_content)
            
            # Layout changes
            if 'center' in feedback_lower:
                css_content = FeedbackAgent.update_css_property(css_content, '.section', 'text-align', 'center')
            elif 'left' in feedback_lower:
                css_content = FeedbackAgent.update_css_property(css_content, '.section', 'text-align', 'left')
            
            # Add footer if requested
            if 'footer' in feedback_lower and 'add' in feedback_lower:
                html_content = FeedbackAgent.add_footer(html_content)
                css_content += FeedbackAgent.get_footer_css()
            
            # Write updated files
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            return True, "Applied your changes successfully!"
            
        except Exception as e:
            return False, f"Error applying changes: {str(e)}"
    
    @staticmethod
    def update_css_property(css_content, selector, property_name, value):
        """Update a CSS property for a given selector"""
        pattern = rf'({re.escape(selector)}\s*\{{[^}}]*?){property_name}\s*:[^;]*;'
        replacement = rf'\1{property_name}: {value};'
        
        if re.search(pattern, css_content):
            return re.sub(pattern, replacement, css_content)
        else:
            # Add property if selector exists
            selector_pattern = rf'({re.escape(selector)}\s*\{{[^}}]*?)(\}})'
            if re.search(selector_pattern, css_content):
                replacement = rf'\1    {property_name}: {value};\2'
                return re.sub(selector_pattern, replacement, css_content)
        
        return css_content
    
    @staticmethod
    def increase_font_sizes(css_content):
        """Increase font sizes across the site"""
        # Increase header font size
        css_content = re.sub(r'(\.header h1.*?font-size:\s*)([^;]+)', r'\g<1>2.5rem', css_content)
        # Increase section heading font size
        css_content = re.sub(r'(\.section h2.*?font-size:\s*)([^;]+)', r'\g<1>2.5rem', css_content)
        return css_content
    
    @staticmethod
    def decrease_font_sizes(css_content):
        """Decrease font sizes across the site"""
        # Decrease header font size
        css_content = re.sub(r'(\.header h1.*?font-size:\s*)([^;]+)', r'\g<1>1.5rem', css_content)
        # Decrease section heading font size
        css_content = re.sub(r'(\.section h2.*?font-size:\s*)([^;]+)', r'\g<1>1.5rem', css_content)
        return css_content
    
    @staticmethod
    def add_footer(html_content):
        """Add footer to HTML"""
        footer_html = '''
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 Your Website. All rights reserved.</p>
        </div>
    </footer>
</body>'''
        return html_content.replace('</body>', footer_html)
    
    @staticmethod
    def get_footer_css():
        """Get CSS for footer"""
        return '''

/* Footer Styles */
.footer {
    background-color: var(--secondary-color);
    color: var(--white);
    text-align: center;
    padding: 2rem 0;
    margin-top: 2rem;
}'''

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
    # Initialize
    initialize_session()
    cleanup_old_workspaces()
    
    # Title
    st.title("🕸️ WebWeaver")
    st.markdown("*Build websites in minutes with AI-powered agents*")
    
    # Sidebar - SpecAgent
    with st.sidebar:
        spec = SpecAgent.collect_specs()
        
        # Start Development Button
        if st.button("🚀 Start Development", type="primary", use_container_width=True):
            with st.spinner("Generating your website..."):
                # Generate files
                CodeAgent.generate_files(spec, st.session_state.workspace_path)
                
                # Start preview
                if st.session_state.preview_agent:
                    st.session_state.preview_agent.stop()
                
                st.session_state.preview_agent = PreviewAgent(st.session_state.workspace_path)
                st.session_state.preview_agent.start_server()
                st.session_state.preview_agent.start_file_watcher()
                st.session_state.development_started = True
                
                st.success("Website generated successfully!")
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
            
            # Chat-style feedback input
            feedback = st.text_area(
                "Style tweaks:",
                placeholder="e.g. 'Make header background blue', 'Add footer', 'Make text bigger'",
                height=100
            )
            
            if st.button("Apply Changes", type="primary"):
                if feedback.strip():
                    success, message = FeedbackAgent.parse_and_apply_feedback(
                        feedback, st.session_state.workspace_path
                    )
                    
                    if success:
                        st.success(message)
                        # Add to history
                        st.session_state.feedback_history.append(feedback)
                        # Trigger reload
                        st.session_state.reload_trigger += 1
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter some feedback!")
            
            # Feedback history
            if st.session_state.feedback_history:
                st.subheader("📝 Recent Changes")
                for i, hist_feedback in enumerate(reversed(st.session_state.feedback_history[-5:])):
                    st.text(f"{len(st.session_state.feedback_history)-i}: {hist_feedback}")
    
    else:
        # Instructions when not started
        st.markdown("""
        ## 👋 Welcome to the WebWeaver!
        
        **How to use:**
        1. **Configure your site** using the wizard in the sidebar
        2. **Click "Start Development"** to generate your website
        3. **Use the live preview** to see your site in real-time
        4. **Give feedback** to make style tweaks
        5. **Download your site** as a ZIP file when ready
        
        ### Features:
        - 🧙‍♂️ **SpecAgent**: Guided setup wizard
        - 🛠️ **CodeAgent**: Generates HTML/CSS scaffolding
        - 🔍 **PreviewAgent**: Live preview with auto-reload
        - 🎨 **FeedbackAgent**: Natural language style tweaks
        - 📦 **PackageAgent**: Download ready-to-deploy ZIP
        
        **Get started by filling out the form in the sidebar!**
        """)

if __name__ == "__main__":
    main() 