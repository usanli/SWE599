#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    # Check if .env file exists and is a file (not a directory)
    if os.path.isfile('.env'):
        print("Using existing .env file")
        
        # Check if the OPENAI_API_KEY is valid in the .env file
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            if 'OPENAI_API_KEY=your_api_key_here' in env_content or not env_content.strip():
                print("\n⚠️  WARNING: No valid OpenAI API key found in .env file.")
                print("Please update the .env file with your actual API key and restart the container.")
                print("\nYou can do this by:")
                print("1. Creating a .env file in your project directory with your API key")
                print("2. Running 'docker-compose down' and then 'docker-compose up' again\n")
        except Exception as e:
            print(f"Error reading .env file: {e}")
    else:
        # If .env exists but is a directory, remove it
        if os.path.exists('.env'):
            try:
                if os.path.isdir('.env'):
                    import shutil
                    shutil.rmtree('.env')
                    print("Removed .env directory")
            except Exception as e:
                print(f"Error removing .env directory: {e}")
                
        # Create .env file
        try:
            with open('.env', 'w') as f:
                f.write("OPENAI_API_KEY=your_api_key_here\n")
            print("\n⚠️  Created .env file with placeholder API key.")
            print("Please update the .env file with your actual OpenAI API key and restart the container.")
            print("\nYou can do this by:")
            print("1. Editing the .env file in your project directory with your API key")
            print("2. Running 'docker-compose down' and then 'docker-compose up' again\n")
        except Exception as e:
            print(f"Error creating .env file: {e}")

    # Run Streamlit
    print("\nStarting Streamlit app...")
    subprocess.run(["streamlit", "run", "multiagent_django_streamlit.py"])

if __name__ == "__main__":
    main() 