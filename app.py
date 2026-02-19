from flask import Flask, request, Response
import subprocess
import json
import uuid
import os
import sys

app = Flask(__name__)

# 自定義日誌輸出
def log_request(message):
    timestamp = subprocess.getoutput("date '+%Y-%m-%d %H:%M:%S'")
    print(f"[{timestamp}] [PROXY_LOG] {message}", file=sys.stderr)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    if not data:
        return json.dumps({"error": "Missing JSON body"}), 400
        
    messages = data.get('messages', [])
    model = data.get('model', 'default')
    
    # 修正：確保提取 content 字串，而不是整個對象清單
    prompt = ""
    if messages and isinstance(messages, list):
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            content = last_msg.get('content', "")
            # 如果 content 是 OpenClaw 格式的清單 [{'type':'text','text':'...'}]
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get('type') == 'text':
                        prompt += part.get('text', "")
            else:
                prompt = str(content)
    
    log_request(f"Received request for model: {model}, extracted prompt: {prompt}")
    
    session_id = f"relay-{uuid.uuid4()}"
    
    try:
        # 強制使用 --agent proxy 確保隔離
        cmd = [
            "openclaw", "agent", 
            "--agent", "proxy",
            "--session-id", session_id,
            "--message", prompt,
            "--json"
        ]
        
        log_request(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        try:
            response_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            log_request(f"JSON Parse Error. Output: {result.stdout}")
            return json.dumps({
                "error": "Failed to parse OpenClaw response", 
                "raw": result.stdout
            }), 500
        
        # 構建 OpenAI 格式回傳
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
            "usage": response_data.get("usage", {"total_tokens": 0})
        }
        
        log_request("Successfully returned response to client")
        return json.dumps(openai_response), 200, {'Content-Type': 'application/json'}

    except subprocess.CalledProcessError as e:
        log_request(f"CLI Error: {e.stderr}")
        return json.dumps({
            "error": "OpenClaw proxy agent execution failed", 
            "stderr": e.stderr
        }), 500
    except Exception as e:
        log_request(f"Internal Error: {str(e)}")
        return json.dumps({"error": str(e)}), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    models = {
        "object": "list",
        "data": [{"id": "default", "object": "model", "owned_by": "openclaw"}]
    }
    return json.dumps(models), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    log_request("Starting openclaw-proxy on port 18790...")
    app.run(host='0.0.0.0', port=18790)
