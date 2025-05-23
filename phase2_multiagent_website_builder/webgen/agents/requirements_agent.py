from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

# It's good practice to ensure the API key is loaded,
# though in the main Streamlit app it should already be.
# from dotenv import load_dotenv
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class RequirementsAgent:
    def __init__(self, openai_api_key):
        self.llm = ChatOpenAI(
            model_name="gpt-4o",  # Upgraded to more advanced model
            openai_api_key=openai_api_key,
            temperature=0.5  # Adjust for creativity vs. predictability
        )
        
        prompt_template = """
        You are an expert web development consultant.
        A user wants to build a website and has provided the following initial idea:
        "{user_idea}"

        Based on this idea, suggest a list of relevant pages and key features for this website.
        Format your output as a flat list of items, where each item is a potential page or a significant feature.
        For example:
        - Homepage
        - About Us Page
        - Contact Form
        - Services Section
        - Blog
        - User Login
        - Product Gallery

        If the user provides existing requirements or selected features, refine them or suggest additions if appropriate:
        Existing Requirements/Selections: "{existing_requirements}"

        Your suggested list of pages/features:
        """
        
        self.prompt = PromptTemplate(
            input_variables=["user_idea", "existing_requirements"],
            template=prompt_template
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def suggest_features(self, user_idea: str, existing_requirements: str = ""):
        """
        Suggests pages and features based on the user's idea and existing selections.
        Returns a list of strings.
        """
        try:
            response = self.chain.invoke({
                "user_idea": user_idea,
                "existing_requirements": existing_requirements
            })
            
            # Assuming the LLM returns a string with items separated by newlines,
            # often starting with '-' or '*'
            suggestions = []
            if response and 'text' in response:
                raw_suggestions = response['text'].strip().split('\n')
                for suggestion in raw_suggestions:
                    # Clean up common list prefixes
                    clean_suggestion = suggestion.replace("- ", "").replace("* ", "").strip()
                    if clean_suggestion:
                        suggestions.append(clean_suggestion)
                return suggestions
            return []
        except Exception as e:
            # In a real app, you'd want more robust logging here
            print(f"Error in RequirementsAgent: {e}")
            return []

if __name__ == '__main__':
    # This is for testing the agent directly
    # You'd need to set your OPENAI_API_KEY environment variable
    # or pass it directly for this test to run.
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        print("OPENAI_API_KEY not found. Skipping direct agent test.")
    else:
        agent = RequirementsAgent(openai_api_key=API_KEY)
        
        test_idea = "I want to build a website for my new bakery."
        print(f"Testing with idea: {test_idea}")
        features = agent.suggest_features(test_idea)
        print("Suggested Features:")
        for feature in features:
            print(f"- {feature}")
        
        print("\nTesting with refinement:")
        existing = "Homepage, About Us"
        features_refined = agent.suggest_features(test_idea, existing_requirements=existing)
        print("Refined/New Features:")
        for feature in features_refined:
            print(f"- {feature}")

        test_idea_2 = "A portfolio site for a photographer"
        print(f"\nTesting with idea: {test_idea_2}")
        features_2 = agent.suggest_features(test_idea_2)
        print("Suggested Features:")
        for feature in features_2:
            print(f"- {feature}") 