# 🤖 LLM Setup Guide for WebWeaver Multi-Agent System

## Quick Setup (2 minutes)

### Step 1: Get an API Key

**Option A: OpenAI (Recommended)**
1. Go to https://platform.openai.com/api-keys
2. Create an account if needed
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

**Option B: Google Gemini (Alternative)**
1. Go to https://makersuite.google.com/app/apikey
2. Create an account if needed
3. Click "Create API key"
4. Copy the key

### Step 2: Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your_actual_api_key_here"
# OR
$env:GEMINI_API_KEY="your_actual_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your_actual_api_key_here
# OR
set GEMINI_API_KEY=your_actual_api_key_here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="your_actual_api_key_here"
# OR
export GEMINI_API_KEY="your_actual_api_key_here"
```

### Step 3: Create .env File (Alternative)

Create a file named `.env` in the `phase3_live_web_studio` folder:

```
OPENAI_API_KEY=your_actual_api_key_here
```

### Step 4: Restart WebWeaver

```bash
python run.py
```

## ✅ Verification

When LLM is working, you'll see:
- 🤖 **Multiagent LLM System Active**: OpenAI GPT-4o (latest and most capable model)
- **Active AI Agents**: SpecAgent • CodeAgent (LLM-powered) • etc.

## 🔧 Troubleshooting

### "No LLM Available" Message
- ✅ Check API key is correct
- ✅ Check environment variable is set
- ✅ Restart the application
- ✅ Try the .env file approach

### Dependency Issues
If you get LangChain errors, try:
```bash
pip uninstall langchain langchain-openai langchain-google-genai langchain-core
pip install langchain-openai langchain-google-genai python-dotenv
```

### API Key Not Loading
Add this debug code to check:
```python
import os
print(f"OpenAI Key: {os.getenv('OPENAI_API_KEY')[:8] if os.getenv('OPENAI_API_KEY') else 'None'}...")
```

## 🎯 Why Use LLM?

**Without LLM (Fallback Mode):**
- ⚠️ Basic regex pattern matching
- ⚠️ Limited command understanding
- ⚠️ Template-only code generation

**With LLM (AI-Powered):**
- ✅ Natural language understanding with GPT-4o intelligence
- ✅ State-of-the-art code generation
- ✅ Advanced context-aware modifications
- ✅ True multiagent AI system with latest capabilities

## 💰 Cost Estimation

**OpenAI GPT-4o:**
- ~$0.005-0.010 per website generation (premium model)
- ~$0.002-0.005 per style modification
- Higher cost but significantly better quality and capabilities
- Best-in-class reasoning and code generation

## 🚀 Ready to Go!

Once set up, you'll have a fully functional multiagent LLM system for web development! 