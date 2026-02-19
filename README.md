# openclaw-proxy

> A secure, OpenAI-compatible proxy server specifically designed for **OpenClaw**. 
> 專為 **OpenClaw** 設計的安全、OpenAI 兼容代理伺服器。

---

## 🌐 Overview / 概述

**openclaw-proxy** is a standalone relay service that allows remote instances or other applications to access the AI models configured on your host machine via a standard OpenAI-compatible API.

**openclaw-proxy** 是一個獨立的轉傳服務，允許遠端實例或其他應用程式透過標準的 OpenAI 兼容 API，存取您主機上配置的 AI 模型。

### 🛡️ Security First / 安全至上
The core philosophy of this proxy is **Zero Key exposure**. It does not require you to store or transmit any raw API keys (like Google or Anthropic keys) within the proxy itself. Instead, it securely relays requests through your local **OpenClaw Gateway**, utilizing whatever authentication method (OAuth, Key, etc.) the host already has configured.

本代理的核心理念是**「零金鑰暴露」**。它不需要您在代理服務中存取或傳輸任何原始 API 金鑰（如 Google 或 Anthropic 金鑰）。相反，它透過您本地的 **OpenClaw Gateway** 安全地轉發請求，利用主機已經配置好的任何認證方式（OAuth、API Key 等）。

---

## ✨ Features / 功能亮點

- **🔗 OpenAI Compatibility**: Use your OpenClaw models in any software that supports OpenAI API endpoints. (在任何支援 OpenAI API 的軟體中使用您的 OpenClaw 模型)
- **🔒 Secure Relay**: No sensitive keys are stored in this project. (不存儲任何敏感金鑰)
- **🚀 Lightweight**: Minimal footprint, powered by Flask. (極輕量化，基於 Flask 構建)
- **🤝 Inter-gateway Communication**: Ideal for connecting multiple OpenClaw instances. (非常適合連接多個 OpenClaw 實例)

---

## 🚀 Getting Started / 快速上手

### Prerequisites / 前置需求
- Python 3.10+
- A running **OpenClaw Gateway** on the host machine. (主機需運行 OpenClaw Gateway)

### Setup / 安裝步驟

1. **Clone the repo / 複製專案:**
   ```bash
   git clone https://github.com/Mavisy75106/openclaw-proxy.git
   cd openclaw-proxy
   ```

2. **Install requirements / 安裝套件:**
   ```bash
   pip install flask
   ```

### Running the Proxy / 執行代理

```bash
python app.py
```
- **Endpoint**: `http://localhost:18790/v1/chat/completions`
- **Model**: Pass `default` or any specific model key configured in your OpenClaw.

---

## 📜 License / 授權

Distributed under the **MIT License**.

---
Built with ❤️ for the OpenClaw Community 🌿
