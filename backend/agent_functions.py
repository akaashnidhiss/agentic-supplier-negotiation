# # Main Agentic DAG Loop
# from .mem0_adapter import Mem0Adapter
# from .evaluator import evaluate_agent_draft
# from typing import Dict, Any, List, Optional

# def agentic_dag_run(supplier_id: str, conv_id: str, supabase_client, input_event: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Implements the agentic loop: trigger → context load → planner → tool executor → drafting → judge → delivery gate.
#     Delivery logic is set to AUTO.
#     """
#     mem0 = Mem0Adapter(supabase_client)

#     # 1. Load Context
#     long_term = mem0.read_semantic(supplier_id)
#     episodic = mem0.read_episodic(conv_id)
#     short_term = mem0.read_short_term(conv_id)
#     context = {
#         "long_term": long_term,
#         "episodic": episodic,
#         "short_term": short_term,
#         "input_event": input_event
#     }

#     # 2. Planner Agent
#     planner = PlannerAgent(supplier_id, conv_id)
#     plan = planner.plan_next_action(context, memories={"long_term": long_term, "episodic": episodic})
#     mem0.write_short_term(conv_id, {"plan": plan})

#     # 3. Tool Executor
#     tool_outputs = execute_tools(plan, context)
#     mem0.write_short_term(conv_id, {"tool_outputs": tool_outputs})

#     # 4. Drafting Agent
#     drafter = DraftingAgent(supplier_id, conv_id)
#     draft_message = drafter.draft_message(plan["thoughts"], tool_outputs)
#     mem0.write_short_term(conv_id, {"draft_message": draft_message})

#     # 5. LLM Judge
#     eval_result = evaluate_agent_draft(draft_message, str(long_term), auto_threshold=24)
#     mem0.write_short_term(conv_id, {"eval_result": eval_result})

#     # 6. Delivery Gate (AUTO)
#     delivery_status = "SENT" if eval_result["pass"] else "FLAGGED_FOR_REVIEW"

#     # 7. Persist Artifacts (simulate)
#     mem0.write_episodic(conv_id, {"role": "AGENT", "content": draft_message, "eval": eval_result, "status": delivery_status}, supplier_id=supplier_id)

#     return {
#         "plan": plan,
#         "tool_outputs": tool_outputs,
#         "draft_message": draft_message,
#         "eval_result": eval_result,
#         "delivery_status": delivery_status
#     }

# """
# Agent Functions Scaffolding
# """
# from typing import Any, Dict, List, Optional

# # Planner Agent
# class PlannerAgent:
#     def __init__(self, supplier_id: str, conv_id: str):
#         self.supplier_id = supplier_id
#         self.conv_id = conv_id

#     def plan_next_action(self, context: Dict[str, Any], memories: Dict[str, Any], open_tasks: Optional[List[Dict]] = None) -> Dict:
#         """
#         Decide next actions and tools based on context and memory.
#         Returns a plan dict with thoughts, selected_tools, arg_per_tool.
#         """
#         # Placeholder logic
#         return {
#             "thoughts": "Need to clarify delivery timeline; check latest contract.",
#             "selected_tools": ["DocSearch", "DraftReply"],
#             "arg_per_tool": {
#                 "DocSearch": {"query": "delivery terms", "scope": "supplier_docs"},
#                 "DraftReply": {"temperature": 0.2}
#             }
#         }

# # Tool Executor (managed code, not LLM)
# def execute_tools(plan: Dict, context: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Executes selected tools and returns their outputs.
#     """
#     # Placeholder for tool execution logic
#     tool_outputs = {}
#     for tool in plan.get("selected_tools", []):
#         # Simulate tool output
#         tool_outputs[tool] = f"Output of {tool}"
#     return tool_outputs

# # Drafting Agent
# class DraftingAgent:
#     def __init__(self, supplier_id: str, conv_id: str):
#         self.supplier_id = supplier_id
#         self.conv_id = conv_id

#     def draft_message(self, planner_thoughts: str, tool_outputs: Dict[str, Any], constraints: Optional[Dict] = None) -> str:
#         """
#         Drafts a supplier message using planner thoughts and tool outputs.
#         """
#         # Placeholder logic
#         return f"Dear Supplier, based on {planner_thoughts}, here is our response. [Citations: {tool_outputs}]"


"""
agentic_dag.py ── ONE-FILE MVP
──────────────────────────────
Implements:
  • Context load (mem0)
  • LLM Planner        (GPT-3.5-turbo)
  • Tool Executor      (_read_available_file_descriptions / _retrieve_relevant_chunks)
  • LLM Drafter        (GPT-3.5-turbo)
  • LLM Evaluator      (grounding / relevance / tone rubric)
  • Delivery Gate
  • Persist to Supabase (conversation_turns, supplier_evaluations)
All synchronous, no dependencies except openai + supabase-py.
"""

import os, json, datetime as dt, traceback, uuid
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
load_dotenv()

import openai


from .mem0_adapter import Mem0Adapter
from .evaluator import evaluate_agent_draft
from typing import Dict, Any, List, Optional

# ────────────────────────────────────────────────────────────────────────
#  0.  ENV / GLOBALS
# ────────────────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
SB: Client     = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


# ────────────────────────────────────────────────────────────────────────
#  2.  TOOLS
# ────────────────────────────────────────────────────────────────────────
def _read_available_file_descriptions(supplier_id:str)->dict:
    """
    Stub – replace by querying your `supplier_documents` table.
    """
    rsp = SB.table("supplier_documents").select("id,doc_type,version,summary").eq("supplier_id",supplier_id).limit(10).execute()
    return {r["id"]:f"{r['doc_type']} v{r['version']} – {r['summary']}" for r in rsp.data}

def _retrieve_relevant_chunks(query:str)->List[str]:
    """
    Stub – replace by proper vector search later.
    """
    return [f"[chunk about '{query}' #1]", f"[chunk about '{query}' #2]"]

TOOLS = {
    "read_files": _read_available_file_descriptions,
    "retrieve_chunks": _retrieve_relevant_chunks
}

# ────────────────────────────────────────────────────────────────────────
#  3.  LLM HELPERS
# ────────────────────────────────────────────────────────────────────────
def chat_completion(msgs, temp=0.2, model="gpt-3.5-turbo"):
    return openai.ChatCompletion.create(
        model=model,temperature=temp,messages=msgs
    ).choices[0].message.content

# ────────────────────────────────────────────────────────────────────────
#  4.  AGENTS
# ────────────────────────────────────────────────────────────────────────
class PlannerAgent:
    PROMPT = """You are a procurement assistant deciding the NEXT 3 tool calls.
Tools you can call:
  • read_files        {{"supplier_id":<str>}}
  • retrieve_chunks   {{"query":<str>}}
Return STRICT JSON list. Example:
[{{"tool":"read_files","args":{{"supplier_id":"abc"}}}},
 {{"tool":"retrieve_chunks","args":{{"query":"delivery timeline"}}}}]"""
    def __init__(self,supplier_id,conv_id): self.supplier_id=supplier_id; self.conv_id=conv_id
    def plan_next_action(self,context,memories,open_tasks=None)->Dict:
        msgs=[{"role":"system","content":self.PROMPT},
              {"role":"user","content":f"Last supplier message:\n{context['input_event']['content']}\n"}]
        try:
            plan=json.loads(chat_completion(msgs,0))
        except Exception:
            plan=[{"tool":"retrieve_chunks","args":{"query":context['input_event']['content'][:50]}}]
        return {"thoughts":"auto-generated","selected_tools":[p["tool"] for p in plan],"arg_per_tool":{p["tool"]:p["args"] for p in plan}}

class DraftingAgent:
    PROMPT="""You write concise, polite business replies on behalf of the client.
Use information from TOOL_OUTPUTS if helpful.
Reply only with the message to the supplier."""
    def __init__(self,supplier_id,conv_id): pass
    def draft_message(self,planner_thoughts,tool_outputs,constraints=None)->str:
        ctx=json.dumps(tool_outputs,indent=2)
        msgs=[{"role":"system","content":self.PROMPT},
              {"role":"user","content":f"Supplier wrote:\n{planner_thoughts}\n\nTOOL_OUTPUTS:\n{ctx}"}]
        return chat_completion(msgs,0.3).strip()

# ────────────────────────────────────────────────────────────────────────
#  5.  EVALUATOR
# ────────────────────────────────────────────────────────────────────────
EVAL_PROMPT="""You are QA. Score AGENT_DRAFT 1-5 for grounding, relevance, tone.
Respond ONLY JSON:
{"grounding":int,"relevance":int,"tone":int,"feedback":"<free text>"}"""
def evaluate_agent_draft(draft:str,long_term:str,auto_threshold=24)->Dict:
    msgs=[{"role":"system","content":EVAL_PROMPT},
          {"role":"user","content":f"AGENT_DRAFT:\n{draft}\n\nSUPPORTING_INFO:\n{long_term}"}]
    try:
        raw=json.loads(chat_completion(msgs,0))
    except Exception:
        raw={"grounding":1,"relevance":1,"tone":1,"feedback":"parse fail"}
    overall=round((raw["grounding"]+raw["relevance"]+raw["tone"])/3,2)
    raw["overall"]=overall
    raw["pass"]=overall>=4 and min(raw["grounding"],raw["relevance"],raw["tone"])>=3
    return raw

# ────────────────────────────────────────────────────────────────────────
#  6.  TOOL EXECUTION WRAPPER
# ────────────────────────────────────────────────────────────────────────
def execute_tools(plan:Dict,context:Dict)->Dict[str,Any]:
    out={}
    for tool in plan.get("selected_tools",[]):
        fn=TOOLS.get(tool)
        args=plan["arg_per_tool"].get(tool,{})
        try:
            out[tool]=fn(**args)
        except Exception as e:
            out[tool]={"error":repr(e),"trace":traceback.format_exc()}
    return out

# ────────────────────────────────────────────────────────────────────────
#  7.  MAIN DAG
# ────────────────────────────────────────────────────────────────────────
def _sb_insert(supabase_client, table:str,payload:dict):
    supabase_client.table(table).insert(payload).execute()

def agentic_dag_run(supplier_id:str, conv_id:str, supabase_client,
                    input_event:Dict[str,Any])->Dict[str,Any]:
    """
    Runs the Agentic loop once for a new supplier message (input_event).
    input_event MUST contain at least: {"turn_id":..., "content":...}
    """
    mem0=Mem0Adapter(supabase_client)

    # 1. Context ----------------------------------------------------------------
    long_term=mem0.read_semantic(supplier_id)
    episodic =mem0.read_episodic(conv_id)
    short_term=mem0.read_short_term(conv_id)
    context={"long_term":long_term,"episodic":episodic,"short_term":short_term,"input_event":input_event}

    # 2. Planner ----------------------------------------------------------------
    planner=PlannerAgent(supplier_id,conv_id)
    plan=planner.plan_next_action(context,memories={"long_term":long_term,"episodic":episodic})
    mem0.write_short_term(conv_id,{"plan":plan})

    # 3. Tools -------------------------------------------------------------------
    tool_outputs=execute_tools(plan,context)
    mem0.write_short_term(conv_id,{"tool_outputs":tool_outputs})

    # 4. Drafter -----------------------------------------------------------------
    drafter=DraftingAgent(supplier_id,conv_id)
    draft_message=drafter.draft_message(input_event["content"],tool_outputs)
    mem0.write_short_term(conv_id,{"draft_message":draft_message})

    # 5. Evaluation --------------------------------------------------------------
    eval_result=evaluate_agent_draft(draft_message,str(long_term))
    mem0.write_short_term(conv_id,{"eval_result":eval_result})

    # 6. Delivery Gate -----------------------------------------------------------
    delivery_status="SENT" if eval_result["pass"] else "FLAGGED_FOR_REVIEW"

    # 7. Persist conversation_turn + evaluation ---------------------------------
    now=dt.datetime.utcnow().isoformat()
    if eval_result["pass"]:
        agent_turn=SB.table("conversation_turns").insert({
            "conv_id":conv_id,
            "role":"AGENT",
            "content":draft_message,
            "sent_at":now,
            "meta":{"exec_trace":tool_outputs,"eval_overall":eval_result["overall"]}
        }).execute().data[0]
        turn_id=agent_turn["id"]
    else:
        turn_id=None  # only evaluation row

    _sb_insert(supabase_client,"supplier_evaluations",{
        "conv_id":conv_id,
        "turn_id":turn_id,
        "judge_prompt_version":"v0.1",
        "scores_json":json.dumps(eval_result),
        "comments":eval_result.get("feedback",""),
        "blocked":not eval_result["pass"],
        "created_at":now
    })

    # 8. Save episodic memory ----------------------------------------------------
    mem0.write_episodic(conv_id,{
        "role":"AGENT","content":draft_message,
        "eval":eval_result,"status":delivery_status
    },supplier_id)

    # 9. Return summary ----------------------------------------------------------
    return {
        "plan":plan,
        "tool_outputs":tool_outputs,
        "draft_message":draft_message,
        "eval_result":eval_result,
        "delivery_status":delivery_status
    }