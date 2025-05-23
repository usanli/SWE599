from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import json

class WebCodeAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o", # Using GPT-4o for best code generation
            openai_api_key=openai_api_key,
            temperature=0.4 # Balanced between predictability and creativity
        )
        
        # Comprehensive prompt for generating all website code at once
        prompt_template = """
        You are an expert full-stack web developer. Your task is to generate the complete code for a modern, responsive website
        based on the provided requirements and UI design specification. You will generate a SINGLE-PAGE WEBSITE with multiple sections.

        Overall Website Requirements Document:
        ---BEGIN REQUIREMENTS---
        {requirements_document}
        ---END REQUIREMENTS---

        UI Design Specification:
        ---BEGIN UI DESIGN SPEC---
        {ui_design_spec}
        ---END UI DESIGN SPEC---

        Selected Features/Sections to implement:
        {selected_features}

        User Uploaded Images:
        ---BEGIN UPLOADED IMAGES---
        {uploaded_images_info}
        ---END UPLOADED IMAGES---

        Theme Instructions:
        ---BEGIN THEME---
        {theme_info}
        ---END THEME---

        You MUST create a modern, aesthetically pleasing SINGLE-PAGE website that follows current design trends and best practices.
        Focus on creating a cohesive look and feel with attention to:
        - Modern typography and spacing
        - Thoughtful color schemes
        - Responsive design for all screen sizes
        - Interactive elements where appropriate
        - Clean, readable code structure
        - Smooth scrolling between sections

        Technical requirements:
        1. Create a single HTML file (index.html) with multiple sections
        2. Each "page" from the selected features should be implemented as a section with its own ID
        3. Use modern HTML5 semantic tags
        4. Implement a fixed or sticky navigation bar that links to each section using anchor links
        5. Implement responsive design using modern CSS techniques (Flexbox/Grid)
        6. Use CSS custom properties (variables) for consistent theming
        7. Include appropriate animations and transitions for a polished feel
        8. Implement smooth scrolling between sections with vanilla JavaScript
        9. Ensure accessibility compliance (WCAG) with proper ARIA attributes where needed
        10. For uploaded images, use the path format: "images/[image_filename]"
        11. If no uploaded images match a needed position, use high-quality placeholder images
        12. Include basic SEO metadata in the HTML head
        13. Add social media preview metadata (Open Graph and Twitter Card tags)

        Basic SEO requirements:
        1. Include title, description, and keywords meta tags
        2. Add proper Open Graph (og:) tags for social media sharing
        3. Add Twitter Card tags for Twitter sharing
        4. Ensure semantic HTML structure with proper heading hierarchy
        5. Include a descriptive title that includes the site's main purpose

        Your response should include separate code blocks for:
        1. A single HTML file (index.html) with all sections
        2. A single CSS file (style.css)
        3. A single JavaScript file (script.js)

        For each code file, start with ```filename.extension and end with ```.
        For example:
        ```index.html
        <!DOCTYPE html>
        <html>
        ...
        </html>
        ```

        ```style.css
        :root {
          --primary-color: #3498db;
          ...
        }
        ...
        ```

        ```script.js
        document.addEventListener('DOMContentLoaded', function() {
          ...
        });
        ```

        Generate a clean, modern single-page design that meets current web standards and looks professionally designed.
        """
        
        self.prompt = PromptTemplate(
            input_variables=["requirements_document", "ui_design_spec", "selected_features", "uploaded_images_info", "theme_info"],
            template=prompt_template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def generate_website_code(self, requirements_document, ui_design_spec, selected_features, uploaded_images=None, selected_theme=None, theme_colors=None):
        """
        Generates all code (HTML, CSS, JS) for the entire website in one go.
        
        Args:
            requirements_document: The overall website requirements
            ui_design_spec: The UI design specification for all pages
            selected_features: List of pages/features to generate
            uploaded_images: Optional dictionary of uploaded images with descriptions
            selected_theme: Optional name of the selected color theme
            theme_colors: Optional dictionary of color values for the theme
            
        Returns:
            A dictionary containing all the generated code files with filenames as keys.
        """
        try:
            # Format the uploaded images information for the prompt
            uploaded_images_info = "No images uploaded."
            if uploaded_images and len(uploaded_images) > 0:
                uploaded_images_info = "The following images have been uploaded:\n"
                for img_key, img_data in uploaded_images.items():
                    if 'description' in img_data:
                        uploaded_images_info += f"- {img_key} - Description: {img_data['description']}\n"
            
            # Format the theme information for the prompt
            theme_info = "Use a modern professional color scheme."
            if selected_theme and theme_colors:
                theme_info = f"""
                Use the following color theme: {selected_theme}
                
                Color values:
                - Primary color: {theme_colors.get('primary', '#4361ee')}
                - Secondary color: {theme_colors.get('secondary', '#3a0ca3')}
                - Accent color: {theme_colors.get('accent', '#f72585')}
                - Text color: {theme_colors.get('text', '#2b2d42')}
                - Background color: {theme_colors.get('bg', '#ffffff')}
                
                Please implement this exact color scheme in the website.
                """
            
            selected_features_str = ", ".join(selected_features) if isinstance(selected_features, list) else selected_features
            
            response = self.chain.invoke({
                "requirements_document": requirements_document,
                "ui_design_spec": ui_design_spec,
                "selected_features": selected_features_str,
                "uploaded_images_info": uploaded_images_info,
                "theme_info": theme_info
            })
            
            # Parse the response to extract individual code files
            generated_files = {}
            if response and 'text' in response:
                code_blocks = self._extract_code_blocks(response['text'])
                if code_blocks:
                    generated_files = code_blocks
                else:
                    # Fallback: If code block extraction fails, return the raw response
                    generated_files = {"error.txt": "Failed to parse code blocks from response. Raw response:\n\n" + response['text']}
            else:
                generated_files = {"error.txt": "No response text received from language model."}
                
            return generated_files
        
        except Exception as e:
            print(f"Error in WebCodeAgent: {e}")
            return {"error.txt": f"Error generating website code: {str(e)}"}
    
    def _extract_code_blocks(self, text):
        """
        Extracts code blocks from the LLM response text.
        Expects format like:
        ```filename.ext
        code content
        ```
        
        Returns a dictionary with filenames as keys and code content as values.
        """
        blocks = {}
        lines = text.split('\n')
        current_file = None
        current_content = []
        
        for line in lines:
            if line.startswith('```') and current_file is None:
                # Start of a code block
                filename = line[3:].strip()
                if filename and not filename.startswith('html') and not filename.startswith('css') and not filename.startswith('js'):
                    current_file = filename
                    current_content = []
            elif line.startswith('```') and current_file is not None:
                # End of a code block
                blocks[current_file] = '\n'.join(current_content)
                current_file = None
                current_content = []
            elif current_file is not None:
                # Inside a code block
                current_content.append(line)
        
        return blocks

if __name__ == '__main__':
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = WebCodeAgent(openai_api_key=API_KEY)
        
        test_req_doc = """
        A website for a local bakery called "Sweet Treats".
        It needs a homepage, an about us page, and a contact page.
        The overall style should be warm and inviting.
        """
        
        test_ui_spec = """
        ## Homepage Design
        - **Layout:** Header, Hero Section, Featured Products Section, Footer.
        - **Header:** Logo "Sweet Treats" (left), Navigation (Home, About, Contact - right).
        - **Hero Section:** Full-width image of delicious pastries. Headline: "Freshly Baked Goodness!". Button: "See Our Menu".
        - **Featured Products:** A section with 3 cards, each showing a product image, name, and short description.
        - **Footer:** Copyright 2024 Sweet Treats. Address and phone number.

        ## About Us Page Design
        - **Layout:** Header, Main Content (two columns), Footer.
        - **Header:** Consistent with Homepage.
        - **Main Content Left Column:** Text about the bakery's history and mission. An image of the founder.
        - **Main Content Right Column:** A quote from a happy customer. A small gallery of 3 shop interior photos.
        - **Footer:** Consistent with Homepage.

        ## Contact Page Design
        - **Layout:** Header, Contact Form Section, Map Section, Footer.
        - **Header:** Consistent with other pages.
        - **Contact Form:** Name, Email, Message fields with Submit button.
        - **Map:** A simple map showing the bakery location.
        - **Footer:** Consistent with other pages.
        """

        test_features = ["Homepage", "About Us Page", "Contact Page"]

        print("--- Testing WebCodeAgent for complete website generation ---")
        code_files = agent.generate_website_code(test_req_doc, test_ui_spec, test_features)
        print(f"Generated {len(code_files)} files:")
        for filename in code_files:
            print(f"- {filename}")
        print("---------------------------------------") 