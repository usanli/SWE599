from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

class HTMLAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o", # Using a more advanced model for code generation
            openai_api_key=openai_api_key,
            temperature=0.3 # Lower temperature for more predictable code
        )
        
        prompt_template = """
        You are an expert HTML developer. Your task is to generate a complete, semantic HTML5 document 
        for a specific page/feature of a website, based on the provided requirements and UI design specification.

        Overall Website Requirements Document:
        ---BEGIN REQUIREMENTS---
        {requirements_document}
        ---END REQUIREMENTS---

        UI Design Specification for the page/feature '{page_name}':
        ---BEGIN UI DESIGN SPEC---
        {ui_design_for_page}
        ---END UI DESIGN SPEC---

        User Uploaded Images:
        ---BEGIN UPLOADED IMAGES---
        {uploaded_images_info}
        ---END UPLOADED IMAGES---

        Based on the above, generate ONLY the full HTML code for the '{page_name}' page.
        - Ensure the HTML is well-structured and uses semantic HTML5 tags (e.g., <header>, <nav>, <main>, <article>, <section>, <aside>, <footer>).
        - Include a basic <head> section with a title (use '{page_name}' for the title), and placeholders for CSS and JavaScript links (e.g., <link rel="stylesheet" href="style.css">, <script src="script.js" defer></script>).
        - For text content areas like paragraphs or articles, use placeholder text (e.g., "Lorem ipsum...") if specific content is not detailed in the UI spec.
        
        - IMPORTANT: Incorporate the uploaded images in appropriate places based on their descriptions.
        - For uploaded images, use the path format: "images/[image_filename]" (all uploaded images will be in an "images" folder).
        - If specific image types are mentioned in the design (e.g., hero image, gallery image, etc.), try to use relevant uploaded images with similar descriptions.
        - If no uploaded images match a needed position, use placeholder images (e.g., 'https://via.placeholder.com/800x400?text=Placeholder+Image').
        
        - Create appropriate class names or IDs for elements that might need styling or JS interaction, based on the UI design (e.g., class="hero-section", id="contact-form").
        - Do NOT include any CSS within <style> tags or inline styles. CSS will be handled separately.
        - Do NOT include any JavaScript within <script> tags. JavaScript will be handled separately.
        - The output should be ONLY the HTML code, starting with <!DOCTYPE html> and ending with </html>.
        - Do not add any explanations or comments outside the HTML code itself.

        HTML code for '{page_name}':
        """
        
        self.prompt = PromptTemplate(
            input_variables=["requirements_document", "ui_design_for_page", "page_name", "uploaded_images_info"],
            template=prompt_template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def generate_html(self, requirements_document: str, ui_design_for_page: str, page_name: str, uploaded_images=None):
        """
        Generates HTML code for a specific page.
        
        Args:
            requirements_document: The overall website requirements
            ui_design_for_page: The UI design specification
            page_name: The name of the page to generate
            uploaded_images: Optional dictionary of uploaded images with descriptions
            
        Returns:
            A string containing the HTML code.
        """
        try:
            # Format the uploaded images information for the prompt
            uploaded_images_info = "No images uploaded."
            if uploaded_images and len(uploaded_images) > 0:
                uploaded_images_info = "The following images have been uploaded:\n"
                for img_key, img_data in uploaded_images.items():
                    if 'description' in img_data:
                        # Format as: "filename.jpg - Description: Hero image for homepage"
                        uploaded_images_info += f"- {img_key} - Description: {img_data['description']}\n"
            
            response = self.chain.invoke({
                "requirements_document": requirements_document,
                "ui_design_for_page": ui_design_for_page,
                "page_name": page_name,
                "uploaded_images_info": uploaded_images_info
            })
            
            if response and 'text' in response:
                # The LLM might sometimes include explanations before/after the code block.
                # We try to extract just the HTML code block.
                html_code = response['text'].strip()
                if html_code.startswith("```html"):
                    html_code = html_code[len("```html"):].strip()
                if html_code.endswith("```"):
                    html_code = html_code[:-len("```")]
                return html_code.strip()
            return f"<!-- Error: Could not generate HTML for {page_name}. No response text. -->"
        except Exception as e:
            print(f"Error in HTMLAgent for page '{page_name}': {e}")
            return f"<!-- Error generating HTML for {page_name}: {str(e)} -->"

if __name__ == '__main__':
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = HTMLAgent(openai_api_key=API_KEY)
        
        test_req_doc = """
        A website for a local bakery called "Sweet Treats".
        It needs a homepage, an about us page, and a contact page.
        The overall style should be warm and inviting.
        """
        
        test_ui_homepage = """
        ## Homepage Design
        - **Layout:** Header, Hero Section, Featured Products Section, Footer.
        - **Header:** Logo "Sweet Treats" (left), Navigation (Home, About, Contact - right).
        - **Hero Section:** Full-width image of delicious pastries. Headline: "Freshly Baked Goodness!". Button: "See Our Menu".
        - **Featured Products:** A section with 3 cards, each showing a product image, name, and short description.
        - **Footer:** Copyright 2024 Sweet Treats. Address and phone number.
        """

        print("--- Testing HTML Agent for Homepage ---")
        html_output_homepage = agent.generate_html(test_req_doc, test_ui_homepage, "Homepage")
        print(html_output_homepage)
        print("---------------------------------------")

        test_ui_about = """
        ## About Us Page Design
        - **Layout:** Header, Main Content (two columns), Footer.
        - **Header:** Consistent with Homepage.
        - **Main Content Left Column:** Text about the bakery's history and mission. An image of the founder.
        - **Main Content Right Column:** A quote from a happy customer. A small gallery of 3 shop interior photos.
        - **Footer:** Consistent with Homepage.
        """
        print("\n--- Testing HTML Agent for About Us Page ---")
        html_output_about = agent.generate_html(test_req_doc, test_ui_about, "About Us Page")
        print(html_output_about)
        print("-------------------------------------------") 