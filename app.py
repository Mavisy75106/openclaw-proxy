from flask import Flask, request, Response, stream_with_context
import subprocess
import json
import uuid
import os

app = Flask(__name__)

# This is a basic proxy that uses `openclaw agent` to fulfill requests.
# It securely relays requests through the local OpenClaw Gateway.

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    if not data:
        return json.dumps({"error": "Missing JSON body"}), 400
        
    messages = data.get('messages', [])
    model = data.get('model', 'default')
    
    # Extract the last message as the prompt for OpenClaw
    prompt = ""
    if messages and isinstance(messages, list):
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            prompt = last_msg.get('content', "")
    
    # Generate a session key for tracking
    session_id = str(uuid.uuid4())
    
    try:
        # Run openclaw agent command using list format for subprocess (security best practice)
        cmd = [
            "openclaw", "agent", 
            "--message", str(prompt),
            "--json"
        ]
        
        # Ensure we are executing with correct env if needed
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        try:
            response_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Failed to parse OpenClaw response", 
                "raw": result.stdout
            }), 500
        
        # Map OpenClaw response back to OpenAI format
        openai_response = {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion",
            "created": 1771500000, # Approximate timestamp
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
            "usage": response_data.get("usage", {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            })
        }
        
        return json.dumps(openai_response), 200, {'Content-Type': 'application/json'}

    except subprocess.CalledProcessError as e:
        return json.dumps({
            "error": "OpenClaw agent execution failed", 
            "message": str(e),
            "stderr": e.stderr
        }), 500
    except Exception as e:
        return json.dumps({"error": str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    # Return a basic model list to satisfy discovery
    models = {
        "object": "list",
        "data": [
            {
                "id": "default",
                "object": "model",
                "created": 1771500000,
                "owned_by": "openclaw"
            }
        ]
    }
    return json.dumps(models), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    # Default proxy port is 18790
    app.run(host='0.0.0.0', port=18790)
