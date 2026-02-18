import asyncio, json, sys
from typing import Dict, Any, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ollama import chat  # pip install ollama

SYSTEM = (
    "You are an assistant that MUST use tools when relevant.\n"
    "If the user asks about weather, ALWAYS call get_weather with latitude and longitude.\n\n"
    "Tool call format ONLY:\n"
    '{"action":"tool_name","args":{...}}\n\n'
    "After receiving tool output, you MUST respond with:\n"
    '{"action":"final","answer":"brief human readable answer"}\n\n'
    "Never stay silent. Never explain. Only JSON."
)

import re

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in:\n{text}")
    return json.loads(match.group())

def llm_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    resp = chat(
        model="mistral:7b",
        messages=messages,
        options={"temperature": 0.2}
    )

    txt = resp["message"]["content"]

    try:
        return extract_json(txt)
    except Exception:
        fix = chat(
            model="mistral:7b",
            messages=[
                {"role": "system", "content": "Return ONLY a JSON object. No text."},
                {"role": "user", "content": txt}
            ],
            options={"temperature": 0}
        )
        return extract_json(fix["message"]["content"])

async def main():
    server_path = sys.argv[1] if len(sys.argv) > 1 else "server_fun.py"
    exit_stack = AsyncExitStack()
    stdio = await exit_stack.enter_async_context(
        stdio_client(StdioServerParameters(command="python", args=[server_path]))
    )
    r_in, w_out = stdio
    session = await exit_stack.enter_async_context(ClientSession(r_in, w_out))
    await session.initialize()

    tools = (await session.list_tools()).tools
    tool_index = {t.name: t for t in tools}
    print("Connected tools:", list(tool_index.keys()))

    history = [{"role": "system", "content": SYSTEM}]
    try:
        while True:
            user = input("You: ").strip()
            if not user or user.lower() in {"exit","quit"}: break
            history.append({"role": "user", "content": user})

            for _ in range(4):  # small safety loop
                decision = llm_json(history)
                if decision.get("action") == "final":
                    answer = decision.get("answer","")
                    if not isinstance(answer, str):
                        answer = json.dumps(answer, indent=2)
                    # one-shot reflection
                    # reflect = chat(model="mistral:7b",
                    #                messages=[{"role":"system","content":"Check for mistakes or missing tool calls. If fine, reply 'looks good'; else give corrected answer."},
                    #                          {"role":"user","content": answer}],
                    #                options={"temperature": 0})
                    # if reflect["message"]["content"].strip().lower() != "looks good":
                    #     answer = reflect["message"]["content"]
                    print("Agent:", answer)
                    history.append({"role":"assistant","content": answer})
                    break

                tname = decision.get("action")
                args = decision.get("args", {})
                if tname not in tool_index:
                    history.append({"role":"assistant","content": f"(unknown tool {tname})"})
                    continue

                result = await session.call_tool(tname, args)
                payload = result.content[0].text if result.content else result.model_dump_json()
                history.append({"role":"assistant","content": f"[tool:{tname}] {payload}"})
    finally:
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())