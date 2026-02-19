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
    
    # Generate a unique session key for the proxy turn
    # This prevents the "Pass --to or --agent" error by creating an isolated session
    session_id = f"proxy-{uuid.uuid4()}"
    
    try:
        # Run openclaw agent command
        # We add --agent main and a unique session key to ensure execution works headlessly
        cmd = [
            "openclaw", "agent", 
            "--agent", "main",
            "--session-key", session_id,
            "--message", str(prompt),
            "--json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        try:
            response_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            return json.dumps({
                "error": "Failed to parse OpenClaw response", 
                "raw": result.stdout,
                "stderr": result.stderr
            }), 500
        
        # Map OpenClaw response back to OpenAI format
        openai_response = {
            "id": f"chatcmpl-{session_id}",
            "object": "chat.completion",
            "created": 1771500000,
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
            "stdout": e.stdout,
            "stderr": e.stderr
        }), 500
    except Exception as e:
        return json.dumps({"error": str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
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
    app.run(host='0.0.0.0', port=18790)
