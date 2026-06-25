import json
import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

app = FastAPI(title="Antigravity OpenAI Bridge")

async def chat_completion_stream(prompt: str, system_instructions: str):
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
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send final chunk with finish_reason
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
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    
    # Process messages to build a prompt and extract system instructions
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
    
    return StreamingResponse(
        chat_completion_stream(prompt, system_instructions),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
