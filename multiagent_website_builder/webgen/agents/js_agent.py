from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

class JSAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o", 
            openai_api_key=openai_api_key,
            temperature=0.4 # Moderate temperature for some creativity in JS logic
        )
        
        prompt_template = """
        You are an expert JavaScript developer. Your task is to generate a single JavaScript file 
        (named 'script.js') to add interactivity to a website. You will be given the overall 
        website requirements, the UI design specification, and the complete HTML code for all pages.

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

        Based on all the above information, generate the content for 'script.js'.
        - Write clean, vanilla JavaScript. Avoid frameworks unless specifically requested in requirements (which is unlikely for this basic setup).
        - Identify elements from the HTML (using their IDs and classes) that might require interactivity based on the requirements and UI design (e.g., navigation toggles for mobile, form submissions, image carousels/galleries, interactive tabs, simple animations on scroll, etc.).
        - Add event listeners and appropriate DOM manipulation.
        - For forms (like a contact form), include basic client-side validation (e.g., checking for empty required fields, email format). For submission, you can log to console or show an alert, as backend integration is out of scope for this task.
        - Ensure the script is defer-loaded or placed at the end of the body in HTML (the HTML agent should have added `<script src="script.js" defer></script>`).
        - Include comments in your JavaScript to explain functions and complex logic.
        - Do NOT include any HTML or CSS in your output.
        - The output should be ONLY the JavaScript code for the 'script.js' file.
        - If no specific JavaScript interactivity seems required from the inputs, output only a comment like "// No specific JavaScript interactivity required based on the provided information."
        - Do not add any explanations or comments outside the JavaScript code itself (e.g., do not write "Here is the JavaScript code:").

        JavaScript code for 'script.js':
        """
        
        self.prompt = PromptTemplate(
            input_variables=["requirements_document", "ui_design_spec", "html_files_content"],
            template=prompt_template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def generate_js(self, requirements_document: str, ui_design_spec: str, html_files_content: dict):
        """
        Generates JavaScript code for the entire website.
        Args:
            requirements_document: The overall website requirements.
            ui_design_spec: The UI design specification for all pages.
            html_files_content: A dictionary where keys are filenames (e.g., "index.html") 
                                and values are their HTML content strings.
        Returns:
            A string containing the JavaScript code for 'script.js'.
        """
        try:
            formatted_html_content = ""
            for filename, content in html_files_content.items():
                formatted_html_content += f"\n\n--- HTML for {filename} ---\n{content}"
            
            response = self.chain.invoke({
                "requirements_document": requirements_document,
                "ui_design_spec": ui_design_spec,
                "html_files_content": formatted_html_content.strip()
            })
            
            if response and 'text' in response:
                js_code = response['text'].strip()
                # Clean up potential markdown code block fences
                if js_code.startswith("```javascript"):
                    js_code = js_code[len("```javascript"):].strip()
                elif js_code.startswith("```js"):
                    js_code = js_code[len("```js"):].strip()
                if js_code.endswith("```"):
                    js_code = js_code[:-len("```")]
                return js_code.strip()
            return "// Error: Could not generate JavaScript. No response text."
        except Exception as e:
            print(f"Error in JSAgent: {e}")
            return f"// Error generating JavaScript: {str(e)}"

if __name__ == '__main__':
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = JSAgent(openai_api_key=API_KEY)
        
        test_req_doc = """
        A photography portfolio. Needs a homepage with a gallery, an about page, and a contact page with a form.
        The gallery should be interactive, maybe a simple lightbox or next/prev buttons.
        Contact form needs validation.
        Mobile navigation should be a toggle menu.
        """
        
        test_ui_spec = """
        ## General Notes
        - Header: Logo, Nav (Home, Gallery, About, Contact). On mobile, nav becomes a hamburger toggle.
        - Gallery Page: Grid of thumbnails. Clicking a thumbnail opens a larger view (modal/lightbox style).
        - Contact Page: Form with fields: Name, Email, Subject, Message. Submit button.
        """

        test_html_files = {
            "index.html": """
            <!DOCTYPE html><html lang="en"><head><title>Home</title><link rel="stylesheet" href="style.css"></head>
            <body>
                <header><button id="mobile-nav-toggle">Menu</button><nav id="main-nav">...</nav></header>
                <main>
                    <section class="gallery">
                        <img src="thumb1.jpg" data-large="large1.jpg" alt="Photo 1">
                        <img src="thumb2.jpg" data-large="large2.jpg" alt="Photo 2">
                    </section>
                    <div id="lightbox" class="hidden"><img id="lightbox-img" src=""><button id="close-lightbox">X</button></div>
                </main>
                <footer>...</footer><script src="script.js" defer></script></body></html>
            """,
            "contact.html": """
            <!DOCTYPE html><html lang="en"><head><title>Contact</title><link rel="stylesheet" href="style.css"></head>
            <body>
                <header>...</header>
                <main>
                    <form id="contact-form">
                        <div><label for="name">Name:</label><input type="text" id="name" required></div>
                        <div><label for="email">Email:</label><input type="email" id="email" required></div>
                        <div><label for="message">Message:</label><textarea id="message" required></textarea></div>
                        <button type="submit">Send</button>
                    </form>
                </main>
                <footer>...</footer><script src="script.js" defer></script></body></html>
            """
        }

        print("--- Testing JS Agent ---")
        js_output = agent.generate_js(test_req_doc, test_ui_spec, test_html_files)
        print(js_output)
        print("----------------------") 