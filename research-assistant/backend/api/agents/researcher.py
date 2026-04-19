import operator
import requests
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from bs4 import BeautifulSoup

from api.utils.llm_factory import get_llm


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    active_document: str


@tool
def scrape_website(url: str) -> str:
    """
    Scrapes and returns text content from a given URL.
    Use this when the user provides a specific link to read.
    """
    # --- SPECIAL CASE: LEETCODE PROFILES ---
    if "leetcode.com/u/" in url:
        try:
            username = url.rstrip('/').split('/')[-1]
            graphql_url = "https://leetcode.com/graphql/"
            payload = {
                "query": """
                query leetcodeProfileInfo($username: String!) {
                  matchedUser(username: $username) {
                    profile { ranking reputation }
                    submitStatsGlobal {
                      acSubmissionNum { difficulty count }
                    }
                  }
                }
                """,
                "variables": {"username": username},
                "operationName": "leetcodeProfileInfo"
            }
            headers = {"Content-Type": "application/json"}
            res = requests.post(graphql_url, json=payload, headers=headers).json()
            user_data = res.get('data', {}).get('matchedUser', {})
            profile = user_data.get('profile', {}) if user_data else {}
            stats = user_data.get('submitStatsGlobal', {}).get('acSubmissionNum', []) if user_data else []
            result = f"LeetCode Profile Data for {username}:\n"
            result += f"Ranking: {profile.get('ranking')}\nReputation: {profile.get('reputation')}\n"
            for stat in stats:
                result += f"{stat.get('difficulty')} Problems Solved: {stat.get('count')}\n"
            return result
        except Exception as e:
            return f"Failed to fetch LeetCode profile: {str(e)}"

    # --- NORMAL WEBSITES ---
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:8000]
    except Exception as e:
        return f"Failed to scrape the website: {str(e)}"


def researcher_node(state: AgentState):
    """Web researcher agent — searches the internet and scrapes URLs to answer questions."""
    messages = state["messages"]
    question = messages[-1].content

    search = DuckDuckGoSearchRun()

    history_msgs = messages[-5:-1] if len(messages) > 1 else []
    conversation_history = ""
    if history_msgs:
        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in history_msgs])
        conversation_history = f"Recent Conversation:\n{history_str}\n"

    llm = get_llm(temperature=0.7)
    agent_executor = create_react_agent(llm, tools=[search, scrape_website])

    system_prompt = SystemMessage(content=f"""You are a helpful AI research assistant.
You have tools to search the web (DuckDuckGo) and scrape specific URLs.
If the user provides a specific link, ALWAYS use the scrape_website tool to read it first before answering.
If search results are missing, failed, or irrelevant, fallback to your own general knowledge.

{conversation_history}""")

    inputs = {"messages": [system_prompt, messages[-1]]}
    result = agent_executor.invoke(inputs)
    return {"messages": [result["messages"][-1]]}
