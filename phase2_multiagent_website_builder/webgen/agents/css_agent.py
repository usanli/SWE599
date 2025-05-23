from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

class CSSAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o", # Good model for creative and structured output
            openai_api_key=openai_api_key,
            temperature=0.4 # Moderately creative for styling
        )
        
        prompt_template = """
        You are an expert CSS developer. Your task is to generate a single, cohesive CSS file 
        (named 'style.css') to style all the pages of a website. You will be given the overall 
        website requirements, the UI design specification, and the complete HTML code for all relevant pages.

        Overall Website Requirements Document:
        ---BEGIN REQUIREMENTS---
        {requirements_document}
        ---END REQUIREMENTS---

        UI Design Specification (covers all pages):
        ---BEGIN UI DESIGN SPEC---
        {ui_design_spec}
        ---END UI DESIGN SPEC---

        HTML Code for all pages (filename and content):
        ---BEGIN HTML FILES---
        {html_files_content}
        ---END HTML FILES---

        Based on all the above information, generate the content for 'style.css'.
        - Create well-structured, readable, and modern CSS.
        - Use CSS selectors that effectively target the elements in the provided HTML (refer to class names and IDs in the HTML).
        - Implement the styling cues mentioned in the UI Design Specification (e.g., color schemes, fonts, layout hints like Flexbox/Grid if appropriate).
        - Aim for a responsive design where possible (e.g., using relative units, media queries for basic breakpoints if complexity allows, but focus on a solid desktop-first base).
        - Include comments in your CSS to explain major sections or complex styles.
        - Do NOT include any HTML or JavaScript in your output.
        - The output should be ONLY the CSS code for the 'style.css' file.
        - Do not add any explanations or comments outside the CSS code itself (e.g., do not write "Here is the CSS code:").

        CSS code for 'style.css':
        """
        
        self.prompt = PromptTemplate(
            input_variables=["requirements_document", "ui_design_spec", "html_files_content"],
            template=prompt_template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def generate_css(self, requirements_document: str, ui_design_spec: str, html_files_content: dict):
        """
        Generates CSS code for the entire website.
        Args:
            requirements_document: The overall website requirements.
            ui_design_spec: The UI design specification for all pages.
            html_files_content: A dictionary where keys are filenames (e.g., "index.html") 
                                and values are their HTML content strings.
        Returns:
            A string containing the CSS code for 'style.css'.
        """
        try:
            # Format the HTML files content into a single string for the prompt
            formatted_html_content = ""
            for filename, content in html_files_content.items():
                formatted_html_content += f"\n\n--- HTML for {filename} ---\n{content}"
            
            response = self.chain.invoke({
                "requirements_document": requirements_document,
                "ui_design_spec": ui_design_spec,
                "html_files_content": formatted_html_content.strip()
            })
            
            if response and 'text' in response:
                css_code = response['text'].strip()
                # Clean up potential markdown code block fences
                if css_code.startswith("```css"):
                    css_code = css_code[len("```css"):].strip()
                if css_code.endswith("```"):
                    css_code = css_code[:-len("```")]
                return css_code.strip()
            return "/* Error: Could not generate CSS. No response text. */"
        except Exception as e:
            print(f"Error in CSSAgent: {e}")
            return f"/* Error generating CSS: {str(e)} */"

if __name__ == '__main__':
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = CSSAgent(openai_api_key=API_KEY)
        
        test_req_doc = """
        A website for "The Cozy Corner Cafe". Needs a homepage, menu, and contact page.
        Style should be rustic, warm, and friendly. Use a color palette of browns, creams, and a touch of dark orange.
        Font should be a readable serif for body and a slightly decorative one for headers.
        """
        
        test_ui_spec = """
        ## General Notes
        - Apply a consistent header and footer across all pages.
        - Header: Cafe logo on left, nav links (Home, Menu, Contact) on right.
        - Footer: Copyright, address, social media icons.
        - Use a max-width container for content to ensure readability on large screens.
        - Buttons should have rounded corners and a subtle hover effect.

        ## Homepage Design
        - Hero Section: Background image of coffee; Text overlay: "Welcome to The Cozy Corner".
        - Specials Section: 3 cards side-by-side for daily specials.
        
        ## Menu Page Design
        - Sections for Coffee, Tea, Pastries.
        - Each menu item: Name, description, price.
        
        ## Contact Page Design
        - Contact form (Name, Email, Message).
        - Embedded map (placeholder for now).
        """

        test_html_files = {
            "index.html": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Homepage - The Cozy Corner Cafe</title>
                <link rel="stylesheet" href="style.css">
            </head>
            <body>
                <header class="site-header">
                    <div class="logo">The Cozy Corner Cafe</div>
                    <nav class="main-nav">
                        <ul><li><a href="index.html">Home</a></li><li><a href="menu.html">Menu</a></li><li><a href="contact.html">Contact</a></li></ul>
                    </nav>
                </header>
                <main>
                    <section class="hero">
                        <h1>Welcome to The Cozy Corner</h1>
                    </section>
                    <section class="specials">
                        <div class="card">Special 1</div><div class="card">Special 2</div><div class="card">Special 3</div>
                    </section>
                </main>
                <footer class="site-footer"><p>&copy; 2024 The Cozy Corner Cafe</p></footer>
                <script src="script.js" defer></script>
            </body>
            </html>
            """,
            "menu.html": """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Menu - The Cozy Corner Cafe</title>
                <link rel="stylesheet" href="style.css">
            </head>
            <body>
                <header class="site-header">...</header>
                <main>
                    <section id="coffee-menu"><h2>Coffee</h2><div class="menu-item">Latte - $4.00</div></section>
                    <section id="tea-menu"><h2>Tea</h2><div class="menu-item">Green Tea - $3.00</div></section>
                </main>
                <footer class="site-footer">...</footer>
                <script src="script.js" defer></script>
            </body>
            </html>
            """
        }

        print("--- Testing CSS Agent ---")
        css_output = agent.generate_css(test_req_doc, test_ui_spec, test_html_files)
        print(css_output)
        print("-------------------------") 