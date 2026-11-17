import os
import google.generativeai as genai

# Load Gemini API key securely from environment variables
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def process_agent_directive(directive: str, target_file: str = "viral_master.py") -> str:
    """Agentic code evolution function using Gemini."""
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is not set."
        
    try:
        if not os.path.exists(target_file):
            return f"Error: Target file {target_file} not found."
            
        with open(target_file, "r") as f:
            code_content = f.read()
            
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""You are an expert Python autonomous coding agent. 
Analyze the following Python file ({target_file}) and apply this directive: "{directive}".
Return ONLY the complete updated Python code block. No markdown wrappers around the whole response if possible, just the raw code or standard code block."""

        response = model.generate_content([prompt, code_content])
        new_code = response.text.strip()
        
        # Clean markdown code blocks if the model included them
        if new_code.startswith("```python"):
            new_code = new_code[9:]
        if new_code.startswith("```"):
            new_code = new_code[3:]
        if new_code.endswith("```"):
            new_code = new_code[:-3]
            
        new_code = new_code.strip()
        
        with open(target_file, "w") as f:
            f.write(new_code)
            
        return f"Successfully evolved {target_file} based on directive: '{directive}'"
    except Exception as e:
        return f"Agent Error: {str(e)}"
