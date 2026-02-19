from flask import Flask, request, Response
import subprocess
import json
import uuid
import os
import sys

app = Flask(__name__)

# 自定義日誌輸出，確保能看到請求進來
def log_request(message):
    timestamp = subprocess.getoutput("date '+%Y-%m-%d %H:%M:%S'")
    print(f"[{timestamp}] [PROXY_LOG] {message}", file=sys.stderr)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    if not data:
        log_request("Received empty request body")
        return json.dumps({"error": "Missing JSON body"}), 400
        
    messages = data.get('messages', [])
    model = data.get('model', 'default')
    
    # 提取最後一條訊息作為 Prompt
    prompt = ""
    if messages and isinstance(messages, list):
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            prompt = last_msg.get('content', "")
    
    log_request(f"Received request for model: {model}, prompt length: {len(str(prompt))}")
    
    # 為代理請求生成唯一的 session id
    session_id = f"proxy-{uuid.uuid4()}"
    
    try:
        # 執行 openclaw agent 命令
        cmd = [
            "openclaw", "agent", 
            "--agent", "main",
            "--session-id", session_id,
            "--message", str(prompt),
            "--json"
        ]
        
        log_request(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        log_request("Execution successful")
        
        try:
            response_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            log_request(f"JSON Decode Error. Raw output: {result.stdout}")
            return json.dumps({
                "error": "Failed to parse OpenClaw response", 
                "raw": result.stdout,
                "stderr": result.stderr
            }), 500
        
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
        
        log_request("Returning OpenAI-compatible response")
        return json.dumps(openai_response), 200, {'Content-Type': 'application/json'}

    except subprocess.CalledProcessError as e:
        log_request(f"Subprocess Error: {str(e)}\nStderr: {e.stderr}")
        return json.dumps({
            "error": "OpenClaw agent execution failed", 
            "message": str(e),
            "stdout": e.stdout,
            "stderr": e.stderr
        }), 500
    except Exception as e:
        log_request(f"Unexpected Error: {str(e)}")
        return json.dumps({"error": str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    log_request("Models list requested")
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
    log_request("Starting openclaw-proxy on port 18790...")
    app.run(host='0.0.0.0', port=18790)
