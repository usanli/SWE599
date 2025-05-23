# 🕸️ WebWeaver - AI Website Builder

> A clean, minimalistic AI-powered website builder with multi-agent architecture

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![AI](https://img.shields.io/badge/AI-Multi--Agent-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)

## 📋 Project Overview

**WebWeaver** is a streamlined AI website builder that uses a sophisticated multi-agent system to create professional websites in seconds. Built with a clean, minimalistic interface and powered by OpenAI GPT-4, WebWeaver demonstrates how AI agents can work together to deliver instant, high-quality results.

## 🎯 Current Focus: Phase 3 Live Web Studio

**Location**: `phase3_live_web_studio/` ⭐ **Production Ready**

### Key Features
- **6 AI Agents**: SpecAgent, ProductManagerAgent, CodeAgent, PreviewAgent, FeedbackAgent, PackageAgent
- **Single HTML Architecture**: Complete websites in one file with embedded CSS/JS
- **Clean Interface**: Minimalistic UI without verbose explanations
- **Console Logging**: All agent communications logged to terminal
- **Smart Risk Management**: ProductManager coordinates safe changes
- **Live Preview**: Real-time preview with auto-reload
- **Natural Language Editing**: Simple feedback like "make header darker"

### Technology Stack
- **AI**: OpenAI GPT-4 with intelligent fallbacks
- **Framework**: Streamlit with clean, minimal design
- **Architecture**: Multi-agent coordination with console logging
- **Output**: Single HTML files with embedded CSS/JS

## 🤖 Multi-Agent Architecture

### Agent Workflow
```
User Input → SpecAgent → ProductManagerAgent → CodeAgent → Website
                ↓
    FeedbackAgent ←← ProductManagerAgent ←← User Feedback
```

### Agent Responsibilities
- **SpecAgent**: Collect website requirements through clean wizard
- **ProductManagerAgent**: Refine requirements and coordinate safe changes
- **CodeAgent**: Generate high-quality HTML/CSS using AI specifications
- **PreviewAgent**: Live preview server with file monitoring
- **FeedbackAgent**: Process user feedback with ProductManager coordination
- **PackageAgent**: Create downloadable ZIP files

### Console Logging
All agent communications appear in terminal:
```
[14:23:45] SpecAgent → ProductManager: Sending user specifications
[14:23:47] ProductManager → CodeAgent: Sending refined specifications
[14:23:49] CodeAgent → System: Website generation completed
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key (optional - falls back to templates)

### Setup
```bash
cd phase3_live_web_studio
pip install -r requirements.txt

# Add API key (optional)
echo "OPENAI_API_KEY=your_key_here" > .env

# Run (use separate commands in PowerShell)
cd phase3_live_web_studio
streamlit run app.py --server.port 8501
```

### Usage
1. **Configure**: Use sidebar wizard to specify your website
2. **Generate**: Click "Start Development" for instant AI creation
3. **Edit**: Use natural language commands like "make header darker"
4. **Download**: Get complete website as ZIP file

## 📊 Performance Metrics

| Metric | Performance |
|---------|-------------|
| **Website Generation** | <5 seconds |
| **Live Updates** | <1 second |
| **Agent Communication** | Console logged |
| **Risk Management** | Smart thresholds (85% for medium risk) |
| **UI Response** | Instant, clean interface |
| **Memory Usage** | Minimal, session-based |

## 🎯 Design Philosophy

### Current Principles
- **Clean & Minimal**: No verbose explanations or README-like UI
- **Console Logging**: All debug info in terminal, not UI
- **Smart AI**: ProductManager prevents changes from breaking sites
- **Single File**: Complete websites in one HTML file
- **Fast Feedback**: Instant preview and updates

### Recent Improvements
- ✅ Removed all verbose UI text and explanations
- ✅ Moved agent logging to console (like "OpenAI key loaded")
- ✅ Fixed overly conservative risk thresholds
- ✅ Clean, minimalistic interface design
- ✅ Better agent coordination and communication

## 🔧 Technical Details

### AI Model Usage
- **Primary**: OpenAI GPT-4 for intelligent generation
- **Fallback**: Template-based generation when no API key
- **Coordination**: ProductManager ensures quality and safety

### Architecture Benefits
- **Intelligent**: AI understanding of requirements and feedback
- **Safe**: ProductManager prevents breaking changes
- **Fast**: Single file generation with live preview
- **Clean**: Minimal UI focused on essential functionality
- **Debuggable**: Console logging for development insights

## 📈 Project Evolution

WebWeaver evolved through multiple phases:

1. **Phase 1**: Complex multi-agent system (research focus)
2. **Phase 2**: Website builder prototype (proof of concept)
3. **Phase 3**: Production-ready AI website builder (current)

Each phase refined the approach, leading to the current clean, fast, and intelligent system.

## 🎓 Educational Value

WebWeaver demonstrates:
- **Multi-agent AI coordination** with ProductManager pattern
- **Clean UI design** without overwhelming technical details
- **Console logging patterns** for development debugging
- **Risk management** in AI-generated content changes
- **Single-file architecture** for website deployment

## 🔮 Future Enhancements

- **Enhanced AI Models**: Support for newer models and providers
- **Advanced Templates**: More sophisticated fallback options
- **Cloud Integration**: Direct deployment to hosting platforms
- **Team Features**: Multi-user collaboration capabilities

---

## 📚 Archive: Previous Phases

### Phase 1: Advanced Multi-Agent System (`phase1_multiagent_django_streamlit/`)
- Complex 10+ agent system using Google Gemini
- Full Django + Streamlit applications
- Research-focused with extensive capabilities

### Phase 2: Multi-Agent Website Builder (`phase2_multiagent_website_builder/`)
- Multiple OpenAI models (GPT-4o + GPT-4)
- Prototype implementation
- Foundation for current architecture

*These phases provide valuable research insights but Phase 3 is the production-ready implementation.*