from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import json # For parsing structured output if needed

class UIDesignAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o", # Upgraded to the most advanced model
            openai_api_key=openai_api_key,
            temperature=0.6 
        )
        
        # Note: The prompt asks for a description. We might refine this to ask for a 
        # more structured output (e.g., JSON) if parsing text descriptions becomes too complex.
        # For now, a detailed text description per page is the goal.
        prompt_template = """
        You are an expert UI/UX designer for websites.
        Based on the following approved website requirements, generate a wireframe-like description 
        for each key page/feature listed. 

        For each page/feature, describe:
        1.  The overall layout (e.g., header, footer, sidebar, main content area).
        2.  Key UI elements and their placement (e.g., "Header: Logo on left, Navigation links (Home, About, Contact) on right").
        3.  Content placeholders (e.g., "Hero Section: Large background image with a headline text overlay and a Call-to-Action button below it").
        4.  Basic styling notes if crucial (e.g., "Use a clean, modern sans-serif font").

        Website Requirements Document:
        ---BEGIN REQUIREMENTS---
        {requirements_document}
        ---END REQUIREMENTS---

        Selected Pages/Features to design (from requirements):
        {selected_features}

        Provide the UI design description for each selected page/feature. 
        Structure your output clearly, perhaps using markdown headers for each page/feature.
        For example:
        ## Homepage Design
        - **Layout:** Standard Header, Main Content Area, Footer.
        - **Header:** Logo (left), Navigation (Home, Services, About, Contact - right).
        - **Hero Section (Main Content):** Full-width image with a centered headline 'Welcome to Our Bakery!' and a button 'View Our Products'.
        - **About Us Snippet (Main Content):** A small section with a heading 'Our Story', a paragraph of text, and an image.
        - **Footer:** Copyright notice, social media links.

        ## About Us Page Design
        - **Layout:** Standard Header, Two-Column Main Content Area, Footer.
        - **Header:** Consistent with Homepage.
        - **Left Column (Main Content):** Detailed company history text.
        - **Right Column (Main Content):** Image of the team or premises.
        - **Footer:** Consistent with Homepage.
        
        Focus on clear, descriptive language that can be used to create a basic visual mock-up.
        Avoid generating actual HTML or CSS code.

        Your UI Design Description:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["requirements_document", "selected_features"],
            template=prompt_template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        
        # Add a new prompt template for design refinement based on user feedback
        feedback_prompt_template = """
        You are an expert UI/UX designer for websites.
        You've previously created the following UI design descriptions based on the website requirements.
        
        Original Website Requirements Document:
        ---BEGIN REQUIREMENTS---
        {requirements_document}
        ---END REQUIREMENTS---
        
        Selected Pages/Features:
        {selected_features}
        
        Your previous UI design description was:
        ---BEGIN PREVIOUS DESIGN---
        {previous_design}
        ---END PREVIOUS DESIGN---
        
        The user provided the following feedback about your design:
        ---BEGIN USER FEEDBACK---
        {user_feedback}
        ---END USER FEEDBACK---
        
        Please revise your UI design descriptions based on this feedback. Maintain the same structure with 
        markdown headers for each page/feature, but incorporate the requested changes.
        
        Make sure to keep the page names consistent with your previous design and maintain the same 
        level of detail in your descriptions.
        
        Your Revised UI Design Description:
        """
        
        self.feedback_prompt = PromptTemplate(
            input_variables=["requirements_document", "selected_features", "previous_design", "user_feedback"],
            template=feedback_prompt_template
        )
        
        self.feedback_chain = LLMChain(llm=self.llm, prompt=self.feedback_prompt)

    def generate_design_spec(self, requirements_document: str, selected_features: list):
        """
        Generates a textual UI design specification based on the requirements.
        Returns a string (markdown formatted preferably).
        """
        try:
            selected_features_str = ", ".join(selected_features)
            response = self.chain.invoke({
                "requirements_document": requirements_document,
                "selected_features": selected_features_str
            })
            
            if response and 'text' in response:
                return response['text'].strip()
            return "Could not generate UI design specification."
        except Exception as e:
            print(f"Error in UIDesignAgent: {e}")
            # Consider raising the exception or returning a more specific error message
            return f"Error generating UI design: {str(e)}"
    
    def generate_design_spec_with_feedback(self, requirements_document: str, selected_features: list, 
                                          previous_design: str, user_feedback: str):
        """
        Refines an existing UI design specification based on user feedback.
        
        Args:
            requirements_document: The original requirements document
            selected_features: List of pages/features to design
            previous_design: The previously generated design spec
            user_feedback: User's feedback/requests for changes
            
        Returns:
            Updated design specification as a string
        """
        try:
            selected_features_str = ", ".join(selected_features)
            response = self.feedback_chain.invoke({
                "requirements_document": requirements_document,
                "selected_features": selected_features_str,
                "previous_design": previous_design,
                "user_feedback": user_feedback
            })
            
            if response and 'text' in response:
                return response['text'].strip()
            return "Could not refine UI design specification."
        except Exception as e:
            print(f"Error in UIDesignAgent feedback processing: {e}")
            return f"Error refining UI design: {str(e)}"

if __name__ == '__main__':
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = UIDesignAgent(openai_api_key=API_KEY)
        
        test_requirements = """
        The user wants to build a website for their local coffee shop.
        It should be welcoming and modern.

        Key Pages/Features Selected:
        - Homepage
        - Menu Page
        - Contact Us Page
        """
        test_features = ["Homepage", "Menu Page", "Contact Us Page"]

        print(f"Testing UI Design Agent with requirements:\n{test_requirements}")
        print(f"And selected features: {test_features}\n")
        
        design_spec = agent.generate_design_spec(test_requirements, test_features)
        print("--- Generated UI Design Specification ---")
        print(design_spec)
        print("---------------------------------------")

        test_requirements_2 = """
        A personal blog for a travel writer. Needs to be image-heavy and easy to read.
        
        Key Pages/Features Selected:
        - Blog Post List (Homepage)
        - Single Blog Post View
        - About Me Page
        """
        test_features_2 = ["Blog Post List (Homepage)", "Single Blog Post View", "About Me Page"]
        print(f"\nTesting UI Design Agent with requirements:\n{test_requirements_2}")
        print(f"And selected features: {test_features_2}\n")
        design_spec_2 = agent.generate_design_spec(test_requirements_2, test_features_2)
        print("--- Generated UI Design Specification ---")
        print(design_spec_2)
        print("---------------------------------------") 