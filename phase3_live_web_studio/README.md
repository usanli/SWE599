# 🕸️ WebWeaver: AI Website Builder

> Clean, minimalistic AI-powered website builder with multi-agent architecture

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.43-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)

## 🎯 Project Overview

WebWeaver is a production-ready AI website builder that combines **clean, minimalistic design** with **sophisticated multi-agent AI coordination**. Built for speed and simplicity, it creates professional websites in seconds with natural language editing capabilities.

**Key Innovation**: ProductManager-coordinated AI agents with console logging and smart risk management.

## ✨ Features

- 🎯 **Clean Interface**: Minimalistic UI without verbose explanations
- 🤖 **6 AI Agents**: Coordinated multi-agent system for intelligent website creation
- 📟 **Console Logging**: All agent communications logged to terminal (like "OpenAI key loaded")
- 🛡️ **Smart Risk Management**: ProductManager prevents breaking changes
- ⚡ **Single HTML**: Complete websites in one file with embedded CSS/JS
- 🔄 **Live Preview**: Real-time updates with auto-reload
- 💬 **Natural Language**: Simple feedback like "make header darker"
- 📦 **Instant Download**: Get complete websites as ZIP files

## 🤖 Multi-Agent Architecture

### 6-Agent System
```
User → SpecAgent → ProductManagerAgent → CodeAgent → Website
         ↓              ↓                    ↓
    FeedbackAgent ←← ProductManagerAgent ←← User Feedback
         ↓
    PackageAgent (Download) | PreviewAgent (Live Server)
```

### Agent Responsibilities
- **SpecAgent**: Clean wizard for website requirements
- **ProductManagerAgent**: Refine specs and coordinate safe changes (NEW)
- **CodeAgent**: Generate HTML/CSS using AI specifications
- **PreviewAgent**: Live preview server with file monitoring
- **FeedbackAgent**: Process feedback with ProductManager coordination
- **PackageAgent**: Create downloadable ZIP files

### Console Logging (NEW)
All agent communications appear in terminal instead of cluttering UI:
```bash
[14:23:45] SpecAgent → ProductManager: Sending user specifications
  Details: Business: TechCorp, Style: Professional Corporate
[14:23:47] ProductManager → CodeAgent: Sending refined specifications
  Details: Risk assessment completed, brand strategy defined
[14:23:49] CodeAgent → LLM: Generating HTML with specifications
  Details: Prompt length: 1247 chars
[14:23:52] CodeAgent → System: Website generation completed
  Details: HTML length: 8934 chars
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key (recommended for AI features)

### Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure AI (Recommended)**:
   ```bash
   # Create .env file with your API key
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

3. **Launch WebWeaver**:
   ```bash
   # For PowerShell (use separate commands)
   cd phase3_live_web_studio
   streamlit run app.py --server.port 8501
   
   # For Bash/Linux
   cd phase3_live_web_studio && streamlit run app.py --server.port 8501
   ```

4. **Access Clean Interface**:
   - Open http://localhost:8501
   - Clean, minimal interface loads
   - All debug info appears in terminal

## 💡 How to Use WebWeaver

### 1. **Configure Your Site** (Clean Sidebar)
- **Business name**: Enter your business name
- **Purpose**: Select from dropdown (Consulting, Business, etc.)
- **Design style**: Choose your preferred style
- **Sections**: Select needed sections (About, Services, Contact, etc.)

### 2. **Generate Website** (Instant AI)
- Click "🚀 Start Development"
- Watch console for agent communications
- Website appears in live preview (<5 seconds)

### 3. **Edit with Natural Language** (Smart Updates)
- Type simple commands: "make header darker", "add pricing section"
- ProductManager analyzes risk and coordinates safe changes
- Changes apply instantly with live reload

### 4. **Download & Deploy** (One-Click)
- Click "📥 Download ZIP"
- Get complete website ready for deployment
- Single HTML file with embedded CSS/JS

## 🎨 Natural Language Commands

| Command | Effect | Risk Level |
|---------|--------|------------|
| `make header darker` | Changes header background color | Low |
| `add pricing section` | Adds complete pricing section | Medium |
| `make it look more modern` | Updates design aesthetics | Medium |
| `remove all images` | Removes image tags and references | High |
| `change to dark theme` | Switches to dark color scheme | High |

**Smart Risk Management**: ProductManager evaluates each change and applies appropriate safety limits.

## 📊 Performance & Architecture

### Performance Metrics
| Metric | Performance |
|--------|-------------|
| **Initial Generation** | <5 seconds |
| **Live Updates** | <1 second |
| **Risk Assessment** | Real-time |
| **Agent Communication** | Console logged |
| **Memory Usage** | Session-based, minimal |

### Architecture Benefits
- **Clean UI**: No verbose explanations or README-like text
- **Console Debug**: All technical info in terminal
- **Smart AI**: ProductManager prevents breaking changes
- **Fast Feedback**: Instant preview and updates
- **Single File**: Easy deployment and sharing

## 🔧 Technical Implementation

### AI Model Integration
```python
# Primary AI with intelligent fallback
if LLM_MODEL:
    # Use OpenAI GPT-4 for intelligent generation
    refined_specs = ProductManagerAgent.refine_initial_requirements(spec)
    html_content = CodeAgent.generate_single_file_with_llm(spec, refined_specs)
else:
    # Template fallback when no API key
    html_content = CodeAgent.generate_single_file_template(spec)
```

### Console Logging Pattern
```python
def log_agent_communication(source, target, message, details=None):
    """Log agent-to-agent communication to console"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {source} → {target}: {message}")
    if details:
        print(f"  Details: {details}")
```

### Risk Management
```python
# Smart risk thresholds (fixed from overly conservative)
max_change_ratio = {
    'low': 0.95,     # Allow 95% changes for low risk
    'medium': 0.85,  # Allow 85% changes for medium risk  
    'high': 0.60     # Allow 60% changes for high risk
}
```

## 📁 Project Structure

```
phase3_live_web_studio/
├── app.py              # Main application (1400+ lines)
│   ├── SpecAgent           # Clean requirement wizard
│   ├── ProductManagerAgent # NEW: Coordinate safe changes
│   ├── CodeAgent           # AI-powered HTML/CSS generation
│   ├── PreviewAgent        # Live server with auto-reload
│   ├── FeedbackAgent       # Natural language processing
│   └── PackageAgent        # ZIP download functionality
├── requirements.txt    # Minimal dependencies
├── .env.example       # API key configuration template
└── README.md          # This file
```

## ✅ Quality Improvements

### Recent Enhancements
- ✅ **Clean UI**: Removed all verbose explanations and README-like text
- ✅ **Console Logging**: Moved all debug info to terminal (like "OpenAI key loaded")
- ✅ **Smart Risk Management**: Added ProductManagerAgent for safe change coordination
- ✅ **Fixed Thresholds**: Corrected overly conservative risk limits (85% vs 60%)
- ✅ **Single File Architecture**: Complete websites in one HTML file
- ✅ **Better Agent Communication**: Clear workflow and coordination

### Architecture Evolution
1. **Clean Interface**: No overwhelming technical details in UI
2. **Console Debug**: All agent communications in terminal
3. **ProductManager Pattern**: Central coordination for safe changes
4. **Risk-Based Updates**: Smart limits prevent breaking changes
5. **Single File Output**: Easy deployment and sharing

## 🧪 Testing & Validation

### Automated Validation
- **HTML Validation**: Ensures all generated code is valid
- **Change Ratio Monitoring**: Prevents excessive modifications
- **Risk Assessment**: Evaluates every change for safety
- **Agent Communication**: Logs all interactions for debugging

### Manual Testing
```bash
# Watch console for agent communications
streamlit run app.py

# Test natural language commands
"make header darker"          # Should apply safely
"remove all img tags"         # Should work (fixed thresholds)
"add pricing section"         # Should create new section
```

## 🔧 Development & Debugging

### Console Monitoring
Watch the terminal where you ran `streamlit run app.py` to see:
- Agent-to-agent communications with timestamps
- LLM prompt previews and response lengths
- Risk assessments and change ratios
- Error messages and warnings

### Key Debug Info
```bash
[14:23:45] SpecAgent → ProductManager: Sending user specifications
[14:23:47] ProductManager → CodeAgent: Sending refined specifications
[14:23:49] CodeAgent → LLM: Generating HTML with specifications
[14:23:52] FeedbackAgent → ProductManager: Requesting feedback analysis
[14:23:54] ProductManager → FeedbackAgent: Analysis complete
```

## 🔮 Future Enhancements

### Immediate Opportunities
- **Enhanced Templates**: More sophisticated fallback options
- **Additional AI Models**: Support for Claude, Gemini, etc.
- **Advanced Risk Management**: More granular change controls
- **Cloud Integration**: Direct deployment to hosting platforms

### Long-term Vision
- **Team Collaboration**: Multi-user editing capabilities
- **Version Control**: Track and revert changes
- **Advanced Styling**: More sophisticated design systems
- **Framework Support**: React, Vue.js generation

---

## 📚 Comparison with Previous Phases

| Feature | Phase 1 | Phase 2 | Phase 3 (Current) |
|---------|---------|---------|-------------------|
| **Interface** | Complex | Intermediate | Clean & Minimal |
| **Debug Info** | In UI | In UI | Console Only |
| **Agents** | 10+ complex | 6+ specialized | 6 coordinated |
| **Risk Management** | None | Basic | ProductManager |
| **Setup Time** | 5+ minutes | 3+ minutes | 30 seconds |
| **Learning Curve** | Advanced | Intermediate | Beginner |

**Phase 3 is the production-ready implementation** with the best balance of functionality, simplicity, and reliability. 