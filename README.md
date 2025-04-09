# 🤖 SWE599 - Interactive Django & Streamlit Multi-Agent Developer

> An advanced AI-powered system for automating Django & Streamlit application development using specialized agents with bidirectional workflows

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.43-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-🔗-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT4o-orange.svg)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-AI-yellow.svg)

## 📋 Table of Contents
- [About](#-about-this-project)
- [Interactive Multi-Agent System](#-interactive-multi-agent-system)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [How It Works](#-how-it-works)
- [Contributing](#-contributing)
- [License](#-license)

## 🔍 About This Project

This repository contains an **SWE599 capstone project**, which implements an **Interactive Multi-Agent System** for automating software development tasks with dynamic bidirectional workflows, specialized agents, visual previews, and comprehensive human feedback integration.

The system features:

1. **Project Management & Planning** with dynamic work plans
2. **Ten Specialized Agents** with distinct roles and capabilities
3. **Bidirectional Workflow** allowing for non-sequential development
4. **Visual UI Previews** with interactive containers
5. **Extensive Feedback Integration** at every development stage
6. **Different Models for Different Tasks** based on complexity

## 🚀 Interactive Multi-Agent System

The system employs ten specialized AI agents working together:

| Agent | Role | Model |
|-------|------|-------|
| **Project Manager/Planner** | Creates development plans, coordinates workflow | GPT-4o |
| **Backend Developer** | Creates Django models, views, serializers, URLs | GPT-4o |
| **UI Designer** | Creates mockups and wireframes with visual previews | GPT-4o |
| **Frontend Developer** | Develops Streamlit frontend components | GPT-4o |
| **Integration Expert** | Connects frontend and backend components | GPT-4o |
| **Testing Expert** | Develops comprehensive test suites | GPT-4 |
| **Debugger** | Identifies and fixes issues found in testing | GPT-4o |
| **Security Expert** | Audits code for vulnerabilities | GPT-4 |
| **Performance Expert** | Optimizes code for better efficiency | GPT-4 |
| **Documentation Expert** | Creates comprehensive documentation | GPT-4 |

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Frameworks:** Django 4.2, Streamlit 1.43
- **AI Integration:** OpenAI GPT-4 and GPT-4o models via LangChain
- **Memory Management:** LangChain ConversationBufferMemory
- **Frontend Visualization:** HTML/CSS with Streamlit components
- **State Management:** Streamlit session state for reactive UI
- **Environment:** dotenv for configuration

## 📥 Installation

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/SWE599-Multi-Agent-Developer.git
   cd SWE599-Multi-Agent-Developer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r multiagent_django_streamlit/requirements.txt
   ```

4. **Configure your API key**
   
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

5. **Launch the application**
   ```bash
   streamlit run multiagent_django_streamlit/multiagent_django_streamlit.py
   ```

## 💡 How It Works

### Dynamic Bidirectional Workflow

1. **Request**: User describes their application requirements in the Request tab
2. **Planning**: The Planner Agent creates a detailed development plan with tasks, timelines and requirements
3. **Backend**: Backend Developer Agent generates Django models, views, serializers and URLs
4. **UI Design**: UI Designer creates mockups displayed in visual interactive containers
5. **Frontend**: Frontend Developer creates Streamlit interface components
6. **Integration**: Integration Expert connects frontend and backend systems
7. **Testing**: Testing Expert creates comprehensive test suites
8. **Debugging**: Debugger identifies and fixes issues found during testing
9. **Security & Performance**: Security and Performance Experts audit and optimize the code
10. **Documentation**: Documentation Expert creates technical and user documentation

At each stage, users can:
- Review the generated content
- Accept and continue to the next stage
- Provide feedback and request revisions

### Key Features

#### Bidirectional Development
Unlike linear workflows, this system allows for revisiting and revising earlier stages when needed. Changes in one stage trigger appropriate updates in dependent stages.

#### Visual UI Previews
The UI Design phase includes interactive HTML/CSS previews of the application design, not just textual descriptions.

#### Memory & Context Management
Each agent has dedicated conversation memory to maintain context across interactions and iterations.

#### Customizable Security & Performance
Users can enable/disable Security Audit and Performance Optimization features based on project requirements.

#### Interactive Development Status
A visual dashboard shows development progress across all phases with color-coded indicators.

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License © 2025 **Umut Şanlı**