# 🔄 LangGraph Workflow: Student Interview Guide

This guide covers potential interview questions and answers regarding the **LangGraph Orchestration & Workflow** configured in [workflow.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/graph/workflow.py).

---

## 🧠 Core Graph Questions

### Q1: Why did you choose LangGraph instead of a simple sequential chain (like LangChain Express) or a generic agent framework?
* **Student Answer**: 
  > "We chose LangGraph because it allows us to model our multi-agent system as a **Stateful Graph** (a state machine). 
  > 
  > A simple sequential chain is too linear—it cannot easily route requests conditionally based on user input. Generic agent frameworks can loop indefinitely, which is unpredictable and expensive. 
  > 
  > LangGraph gives us precise control: we can define exact nodes (our agents), custom conditional routing paths (like checking file keywords before running the LLM), and enforce state consistency across agent transitions."

### Q2: How does State Management work in your graph workflow?
* **Student Answer**: 
  > "All nodes in the graph share a common schema called `GraphState` (defined in [workflow.py](file:///Users/gattuvinaykumar/Documents/intelligent%20Research%20Assistant/research-assistant/backend/api/graph/workflow.py#L11)). 
  > 
  > The state holds shared parameters like `messages`, `active_document`, and `user_id`. When a node executes, it receives the current state and returns updates. LangGraph merges these updates into the central state. 
  > 
  > For the chat history, we annotate `messages` with `operator.add` so that whenever a node returns a message list, LangGraph automatically appends it to the history instead of overwriting it."

---

## 🔀 Routing & Edge Questions

### Q3: What is the difference between a normal edge and a "conditional edge" in your workflow?
* **Student Answer**: 
  > "A **normal edge** is a fixed transition from one node to another (like `START` directly going to `supervisor`).
  > 
  > A **conditional edge** (configured via `add_conditional_edges`) uses a routing function to decide the next step dynamically at runtime. 
  > 
  > In our workflow, we use the `router` function. After the `supervisor` node analyzes the query and sets `state["next_agent"]`, the conditional edge reads this value and directs the flow to either `document_agent`, `researcher_agent`, or `file_agent`."

### Q4: Why do all your worker agents (Document, Researcher, File) transition straight to the `END` node?
* **Student Answer**: 
  > "We designed the workflow to follow a **Single-Pass execution loop** per request. Once the supervisor routes the user query to the correct specialist worker, and that worker finishes its execution (generating the final answer or running the file tool), its job is done. 
  > 
  > Transitioning directly to `END` stops the graph execution and allows the system to return the response immediately to the user interface, preventing infinite agent loops and saving API latency/costs."

---

## 🛠️ Deep-Dive & Edge-Case Questions

### Q5: What would happen if a worker agent needed to route back to the supervisor or another agent? How would you implement that?
* **Student Answer**: 
  > "Right now, workers route directly to `END`. However, if we wanted to support multi-step agent collaboration (e.g., the researcher writes a summary to a file using the file agent), we would replace the `END` target with a conditional edge going back to the supervisor or a router node. 
  > 
  > We would modify `workflow.add_edge("researcher_agent", "supervisor")` or use conditional edges on the workers to inspect if further actions are needed in the shared state before terminating."

### Q6: How does the Django REST API pass user context (like `user_id` and `active_document`) into the LangGraph state?
* **Student Answer**: 
  > "When the Django API receives a chat request, it retrieves the logged-in user's ID and active document. It initializes the `GraphState` dictionary with these values:
  > ```python
  > initial_state = {
  >     "messages": [HumanMessage(content=user_query)],
  >     "active_document": active_doc_name,
  >     "user_id": request.user.id
  > }
  > ```
  > It then invokes the graph with `workflow.invoke(initial_state)`. This injects the Django session context straight into the LangGraph execution environment."
