from flask import Flask, request, Response, stream_with_context
import subprocess
import json
import uuid
import os

app = Flask(__name__)

# This is a very basic proxy that uses `openclaw agent` to fulfill requests.
# In a real-world scenario, you'd want to handle multiple models, 
# streaming (if supported), and better error handling.

GATEWAY_TOKEN = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "8a172740595ae2ba83447c65c340594f4b3af00e291ee067")

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    messages = data.get('messages', [])
    model = data.get('model', 'default')
    
    # Extract the last message as the prompt for OpenClaw
    prompt = messages[-1]['content'] if messages else ""
    
    # Generate a session key to keep turns separated if needed
    session_id = str(uuid.uuid4())
    
    try:
        # Run openclaw agent command
        # Note: we use --json to get a structured response
        cmd = [
            "openclaw", "agent", 
            "--message", prompt,
            "--json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response_data = json.loads(result.stdout)
        
        # Map OpenClaw response back to OpenAI format
        openai_response = {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion",
            "created": 123456789, # Placeholder
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_data.get("reply", "")
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": response_data.get("usage", {})
        }
        
        return json.dumps(openai_response), 200, {'Content-Type': 'application/json'}

    except subprocess.CalledProcessError as e:
        return json.dumps({"error": str(e), "details": e.stderr}), 500
    except Exception as e:
        return json.dumps({"error": str(e)}), 500

if __name__ == '__main__':
    # Default OpenClaw port is 18789, let's use 18790 for the proxy
    app.run(host='0.0.0.0', port=18790)
