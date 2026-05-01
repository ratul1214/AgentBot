import json
import os
from openai import OpenAI
from vector_store import search, add_documents, is_url_indexed
from scraper import scrape_url

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are a helpful AI assistant for iPractest.com — an IELTS preparation platform.

You help users with:
- What iPractest offers (features, practice tests, band score tracking)
- IELTS exam structure: Speaking, Writing, Reading, Listening
- How to use the platform effectively
- IELTS preparation tips and strategies
- Pricing, registration, and account-related questions

Behavior rules:
1. Always call search_knowledge_base first for any question.
2. If the results are insufficient or empty, call scrape_and_store with the most relevant iPractest URL.
3. Never make up information — only answer based on retrieved content.
4. Be friendly, encouraging, and concise.
5. If you truly cannot find the answer, say so honestly and suggest the user visit ipractest.com directly.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the local vector database for information about iPractest. "
                "Always call this first before scraping."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant information.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_and_store",
            "description": (
                "Scrape a page from ipractest.com, store it in the vector database, and return the content. "
                "Only use this when search_knowledge_base returns insufficient results. "
                "Only URLs from ipractest.com are allowed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full URL to scrape. Must be on ipractest.com.",
                    }
                },
                "required": ["url"],
            },
        },
    },
]


def _search_knowledge_base(query: str) -> str:
    results = search(query, k=5)
    if not results:
        return "No relevant information found in the knowledge base."
    return "\n\n---\n\n".join(results)


def _scrape_and_store(url: str) -> str:
    if "ipractest.com" not in url:
        return "Error: Only ipractest.com URLs are allowed."

    already_indexed = is_url_indexed(url)
    content = scrape_url(url)

    if content.startswith("ERROR:"):
        return content

    if not already_indexed:
        add_documents([content], [{"source": url}])

    preview = content[:3000]
    return f"Content from {url}:\n\n{preview}"


def run_agent(user_message: str, conversation_history: list[dict]) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)

            for tool_call in msg.tool_calls:
                fn = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if fn == "search_knowledge_base":
                    result = _search_knowledge_base(args["query"])
                elif fn == "scrape_and_store":
                    result = _scrape_and_store(args["url"])
                else:
                    result = f"Unknown tool: {fn}"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
        else:
            return msg.content
