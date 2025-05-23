# Multiagent Django Streamlit Application

This application combines Django and Streamlit with LangChain and Google Gemini to create a multiagent system powered by Google's latest AI technology.

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed on your system
- Google Gemini API key

### Steps to Run with Docker

1. **Create a .env file**

   Create a `.env` file in the project root with the following content:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   To get your Gemini API key:
   - Go to [Google AI Studio](https://ai.google.dev/)
   - Create an account if you haven't already
   - Generate an API key
   - Copy the key to your .env file

2. **Build and start the Docker container**

   ```bash
   docker-compose up --build
   ```

3. **Access the application**

   Open your browser and navigate to:
   ```
   http://localhost:8501
   ```

### Docker Commands

- Start the containers:
  ```bash
  docker-compose up
  ```

- Start in detached mode:
  ```bash
  docker-compose up -d
  ```

- Stop the containers:
  ```bash
  docker-compose down
  ```

- View logs:
  ```bash
  docker-compose logs -f
  ```

## Development

For local development without Docker:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a .env file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. Run the Streamlit app:
   ```bash
   streamlit run multiagent_django_streamlit.py
   ```

## Features

- **Powered by Google Gemini 2.0 Flash**: Uses the latest and most advanced Gemini model
- **Multimodal capabilities**: Can handle text, images, audio, and video inputs
- **Multi-agent architecture**: Specialized AI agents for different development tasks
- **Interactive workflow**: Get feedback and iterate on each development phase
- **Complete development pipeline**: From planning to documentation 