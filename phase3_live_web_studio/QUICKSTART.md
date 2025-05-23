# 🚀 WebWeaver QuickStart - PowerShell Edition

> Get WebWeaver running in under 2 minutes on Windows

## Prerequisites
- Python 3.10+
- PowerShell (Windows)

## Quick Setup

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Add API Key (Optional but Recommended)
```powershell
# Copy the example file
Copy-Item .env.example .env

# Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Launch WebWeaver
```powershell
# PowerShell method (separate commands)
cd phase3_live_web_studio
streamlit run app.py --server.port 8501
```

### 4. Open Browser
- Navigate to: http://localhost:8501
- Start building websites with AI!

## PowerShell Tips

### Running Commands
❌ **Don't use** `&&` (not supported in PowerShell)
```powershell
# Wrong:
cd directory && command
```

✅ **Use separate commands**
```powershell
# Correct:
cd directory
command
```

### Alternative Launch Methods
```powershell
# Method 1: Direct
streamlit run app.py --server.port 8501

# Method 2: Using Python module
python -m streamlit run app.py --server.port 8501
```

## Console Logging

All agent communications appear in the PowerShell terminal:
```
[14:23:45] SpecAgent → ProductManager: Sending user specifications
[14:23:47] ProductManager → CodeAgent: Sending refined specifications
[14:23:49] CodeAgent → System: Website generation completed
```

## Troubleshooting

### Dependencies Issue
```powershell
# If dependencies fail, install core packages only
pip install streamlit watchdog langchain-openai python-dotenv
```

### API Key Not Working
- Ensure .env file is in the same directory as app.py
- Check that the API key starts with "sk-"
- Restart the application after adding the key

### Port Already in Use
```powershell
# Use a different port
streamlit run app.py --server.port 8502
```

---

## What to Expect

1. **Clean Interface**: Minimalistic UI without verbose explanations
2. **Console Debug**: All technical info appears in PowerShell terminal
3. **Instant Generation**: Websites created in <5 seconds
4. **Natural Language**: Edit with commands like "make header darker"
5. **One-Click Download**: Get complete websites as ZIP files

**Ready to build?** Just run the commands above and start creating! 🎨 