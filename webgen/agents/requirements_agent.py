from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import re # For parsing list output

class RequirementsAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4", 
            openai_api_key=openai_api_key,
            temperature=0.3 # Slightly lower temperature for more deterministic suggestions
        )
        
        # Prompt for suggesting features
        suggest_features_template = """
        You are an expert requirements analyst for websites.
        A user wants to build a website and has provided an initial idea.
        They may have also provided a list of pages/features they have already considered or selected.

        User's Initial Website Idea:
        {user_idea}

        Previously Selected/Considered Pages/Features (if any, comma-separated):
        {existing_requirements}

        Based on the user's idea and any existing selections, suggest a concise list of 5-10 additional relevant pages or key features for their website.
        - Prioritize essential pages first (e.g., Homepage, About Us, Contact, Services/Products if applicable).
        - Then suggest other useful features or sections based on the website type.
        - If existing requirements are provided, try to suggest complementary features or expand on them, avoiding direct duplication if possible unless it's a very generic term like 'Homepage'.
        - Output ONLY a Python-style list of strings. For example: ['Homepage', 'About Page', 'Contact Form', 'Photo Gallery', 'Blog Section']
        - Do not add any explanations or comments outside the list. Do not say "Here are some suggestions:".
        - If the idea is too vague, suggest very generic starting points.

        Suggested Pages/Features List:
        """
        self.suggest_features_prompt = PromptTemplate(
            input_variables=["user_idea", "existing_requirements"],
            template=suggest_features_template
        )
        self.suggest_features_chain = LLMChain(llm=self.llm, prompt=self.suggest_features_prompt, verbose=True)

        # Prompt and chain for generating the initial consolidated document
        initial_document_template = """
        You are a requirements analyst. Based on the user's initial website idea and a list of selected pages/features,
        generate a well-structured and detailed "Consolidated Requirements Document". This document should elaborate
        on the purpose of the website, describe each selected page/feature in a paragraph or two, and outline any key functionalities or
        user interactions implied by the selections. Structure it with clear headings for each section (e.g., Overall Purpose, Page: Homepage, Page: About Us, Feature: Contact Form).
        Be comprehensive but concise.

        User's Initial Website Idea:
        {user_idea}

        Selected Pages/Features:
        {selected_features}

        Consolidated Requirements Document:
        """
        self.initial_document_prompt = PromptTemplate(
            input_variables=["user_idea", "selected_features"],
            template=initial_document_template
        )
        self.initial_document_chain = LLMChain(llm=self.llm, prompt=self.initial_document_prompt, verbose=True)

        # Prompt and chain for refining the document based on chat
        refine_document_template = """
        You are a requirements analyst. You are helping a user refine an existing "Consolidated Requirements Document"
        for their website. You will be given the current document and the user's latest message requesting changes.
        Incorporate the user's request into the document. Provide the full, updated "Consolidated Requirements Document" as your response.
        Ensure your response *only* contains the full, updated document. Do not add conversational filler, apologies, or any text outside the document itself.
        If the user's request is unclear, try your best to interpret it and update the document, or ask for clarification *within* the document content itself, for example, by adding a note like "[Analyst Note: Clarification needed on ...]".
        Preserve the structure and existing content as much as possible, only making the requested changes.

        Current Consolidated Requirements Document:
        ---BEGIN CURRENT DOCUMENT---
        {current_document}
        ---END CURRENT DOCUMENT---

        User's Request for Change:
        {user_request}

        Updated and Complete Consolidated Requirements Document:
        """
        self.refine_document_prompt = PromptTemplate(
            input_variables=["current_document", "user_request"],
            template=refine_document_template
        )
        self.refine_document_chain = LLMChain(llm=self.llm, prompt=self.refine_document_prompt, verbose=True)

    def suggest_features(self, user_idea: str, existing_requirements: str = ""):
        """
        Suggests a list of pages/features for the website.
        Args:
            user_idea: The user's initial website idea.
            existing_requirements: A comma-separated string of already selected features.
        Returns:
            A list of suggested feature strings, or an empty list if an error occurs.
        """
        if not user_idea:
            return []
        try:
            response = self.suggest_features_chain.invoke({
                "user_idea": user_idea, 
                "existing_requirements": existing_requirements
            })
            if response and 'text' in response:
                # The LLM is asked to return a Python-style list of strings.
                # We use regex to robustly extract the list items.
                text_response = response['text'].strip()
                
                # Try to evaluate as a list directly
                try:
                    # Ensure it's a string that looks like a list
                    if text_response.startswith("[") and text_response.endswith("]"):
                        evaluated_list = eval(text_response)
                        if isinstance(evaluated_list, list):
                            return [str(item).strip() for item in evaluated_list if str(item).strip()]
                    # Fallback to regex if eval fails or not a list
                except: 
                    pass # eval can fail, so we try regex

                # Regex to find quoted strings within brackets (more robust)
                suggestions = re.findall(r"['"](.*?)['"]", text_response)
                
                # Fallback: if no quotes, try splitting by comma if it looks like a simple list
                if not suggestions and '[' not in text_response and ']' not in text_response:
                    suggestions = [s.strip() for s in text_response.split(',') if s.strip()]

                return [s.strip() for s in suggestions if s.strip()] # Clean up
            return []
        except Exception as e:
            print(f"Error in RequirementsAgent - suggest_features: {e}")
            return []

    def generate_initial_document(self, user_idea: str, selected_features: list):
        """
        Generates the initial consolidated requirements document.
        """
        if not user_idea or not selected_features:
            return "Error: User idea and selected features are required to generate the document."
        
        features_str = "\n- " + "\n- ".join(selected_features)
        try:
            response = self.initial_document_chain.invoke({
                "user_idea": user_idea,
                "selected_features": features_str
            })
            if response and 'text' in response:
                return response['text'].strip()
            return "Error: Could not generate the initial requirements document."
        except Exception as e:
            print(f"Error in RequirementsAgent - generate_initial_document: {e}")
            return f"Error generating initial document: {str(e)}"

    def refine_document(self, current_document: str, user_request: str):
        """
        Refines the consolidated requirements document based on user chat input.
        """
        if not current_document or not user_request:
            # Return current document if user request is empty, to avoid error and allow just display
            if not user_request and current_document:
                 return current_document
            return "Error: Current document and user request are required for refinement."
        
        try:
            response = self.refine_document_chain.invoke({
                "current_document": current_document,
                "user_request": user_request
            })
            if response and 'text' in response:
                return response['text'].strip()
            return "Error: Could not refine the requirements document. Agent returned no text."
        except Exception as e:
            print(f"Error in RequirementsAgent - refine_document: {e}")
            return f"Error refining document: {str(e)}"


if __name__ == '__main__':
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = RequirementsAgent(openai_api_key=API_KEY)
        
        test_idea = "A bakery website that sells custom cakes and pastries."
        print(f"--- Testing suggest_features with idea: '{test_idea}' ---")
        suggestions = agent.suggest_features(test_idea)
        print(f"Suggestions: {suggestions}")

        print(f"--- Testing suggest_features with idea and existing: '{test_idea}', existing: 'Homepage, Cake Gallery' ---")
        suggestions_existing = agent.suggest_features(test_idea, existing_requirements="Homepage, Cake Gallery")
        print(f"Suggestions with existing: {suggestions_existing}")

        if suggestions:
            test_selected_features = suggestions[:3] # Take first 3 suggestions
            print(f"\n--- Testing generate_initial_document with idea: '{test_idea}' and selected features: {test_selected_features} ---")
            initial_doc = agent.generate_initial_document(test_idea, test_selected_features)
            print(f"Initial Document:\n{initial_doc}")

            if not initial_doc.startswith("Error:"):
                test_user_request = "Can we also add a section for seasonal specials on the homepage and make sure the contact page has a map?"
                print(f"\n--- Testing refine_document with user request: '{test_user_request}' ---")
                refined_doc = agent.refine_document(initial_doc, test_user_request)
                print(f"Refined Document:\n{refined_doc}")
        else:
            print("Skipping document generation tests as no initial suggestions were made.") 