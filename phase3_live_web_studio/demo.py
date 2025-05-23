#!/usr/bin/env python3
"""
Demo script to test WebWeaver components independently
"""

import tempfile
import os
import shutil
from app import SpecAgent, CodeAgent, FeedbackAgent, PackageAgent

print("🕸️ WebWeaver Demo")
print("Build websites in minutes with AI-powered agents")
print("=" * 60)

def demo_agents():
    """Test all agents independently"""
    # Create temporary workspace
    workspace = tempfile.mkdtemp(prefix='webweaver_demo_')
    print(f"\n📁 Created workspace: {workspace}")
    
    # Demo SpecAgent
    print("\n🧙‍♂️ SpecAgent Demo")
    spec = {
        'site_title': 'Demo Website',
        'needs_nav': True,
        'primary_color': '#3498db',
        'sections': ['header', 'hero', 'features', 'contact form']
    }
    print(f"Spec: {spec}")
    
    # Demo CodeAgent
    print("\n🛠️ CodeAgent Demo")
    CodeAgent.generate_files(spec, workspace)
    
    # Check generated files
    html_file = os.path.join(workspace, 'index.html')
    css_file = os.path.join(workspace, 'styles.css')
    
    if os.path.exists(html_file) and os.path.exists(css_file):
        print("✅ Files generated successfully!")
        with open(html_file, 'r') as f:
            html_size = len(f.read())
        with open(css_file, 'r') as f:
            css_size = len(f.read())
        print(f"📄 HTML file size: {html_size} characters")
        print(f"🎨 CSS file size: {css_size} characters")
    else:
        print("❌ File generation failed")
        return
    
    # Demo FeedbackAgent
    print("\n🎨 FeedbackAgent Demo")
    feedback = "Make header background blue"
    print(f"Feedback: '{feedback}'")
    result = FeedbackAgent.parse_and_apply_feedback(feedback, workspace)
    print(f"Result: {result}")
    
    # Demo PackageAgent
    print("\n📦 PackageAgent Demo")
    zip_path = PackageAgent.create_zip(workspace)
    if zip_path and os.path.exists(zip_path):
        print(f"✅ ZIP created: {zip_path}")
        zip_size = os.path.getsize(zip_path)
        print(f"📦 ZIP size: {zip_size} bytes")
    else:
        print("❌ ZIP creation failed")
    
    print(f"\n🧹 Cleaning up workspace: {workspace}")
    shutil.rmtree(workspace, ignore_errors=True)
    
    print("\n✨ Demo completed successfully!")

if __name__ == "__main__":
    demo_agents() 