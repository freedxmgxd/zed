import json
import asyncio
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

class AntigravityBridgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return
            
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            req_data = json.loads(body)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        messages = req_data.get("messages", [])
        
        # Process messages to build prompt and system instructions
        prompt_parts = []
        system_instructions = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_instructions = content
            else:
                prompt_parts.append(f"{role.capitalize()}: {content}")
                
        prompt = "\n".join(prompt_parts)

        # Set headers for Server-Sent Events (SSE)
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()

        # Run the async agent chat and stream response back to client
        asyncio.run(self.stream_response(prompt, system_instructions))

    async def stream_response(self, prompt, system_instructions):
        config = LocalAgentConfig(
            system_instructions=system_instructions or "You are an AI assistant.",
            capabilities=CapabilitiesConfig(),
        )
        async with Agent(config) as agent:
            response = await agent.chat(prompt)
            created_time = int(time.time())
            async for token in response:
                chunk = {
                    "id": "chatcmpl-antigravity",
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": "gemini-3.5-flash",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": token},
                            "finish_reason": None
                        }
                    ]
                }
                data_line = f"data: {json.dumps(chunk)}\n\n".encode('utf-8')
                try:
                    self.wfile.write(data_line)
                    self.wfile.flush()
                except Exception:
                    # Client disconnected
                    break
            
            # Send final stop chunk
            final_chunk = {
                "id": "chatcmpl-antigravity",
                "object": "chat.completion.chunk",
                "created": created_time,
                "model": "gemini-3.5-flash",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            try:
                self.wfile.write(f"data: {json.dumps(final_chunk)}\n\n".encode('utf-8'))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception:
                pass

def run(server_class=ThreadingHTTPServer, handler_class=AntigravityBridgeHandler, port=8000):
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    print(f"Antigravity OpenAI Bridge running on http://127.0.0.1:{port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run()
