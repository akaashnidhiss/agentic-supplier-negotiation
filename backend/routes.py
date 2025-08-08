from fastapi import APIRouter, Depends, HTTPException
from .models import Supplier, Document, Conversation, Evaluation, AgentRun, ToolCall, ConversationTurn, EvaluationTurn, ConversationSettings
from .agent_functions import agentic_dag_run
# Agentic DAG API endpoint
from fastapi import Request

from .supabase_client import supabase

router = APIRouter()


@router.post('/run_agentic_dag')
async def run_agentic_dag(request: Request):
    body = await request.json()
    supplier_id = body.get('supplier_id')
    conv_id = body.get('conv_id')
    input_event = body.get('input_event', {})
    # Use global supabase client
    print("CALLLING AGENTIC DAG RUN")
    result = agentic_dag_run(supplier_id, conv_id, supabase, input_event)
    return result

@router.get('/suppliers')
def get_suppliers():
    response = supabase.table('suppliers_table').select('*').execute()
    return response.data

@router.post('/suppliers')
def create_supplier(supplier: Supplier):
    data = supplier.dict(exclude_unset=True)
    # Remove id if not provided by frontend, let Supabase auto-generate
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('suppliers_table').insert(data).execute()
    return response.data

@router.get('/documents')
def get_documents():
    response = supabase.table('supplier_documents').select('*').execute()
    return response.data

@router.post('/documents')
def create_document(document: Document):
    data = document.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('supplier_documents').insert(data).execute()
    return response.data

@router.get('/conversations')
def get_conversations():
    response = supabase.table('supplier_conversations').select('*').execute()
    return response.data

@router.post('/conversations')
def create_conversation(conversation: Conversation):
    data = conversation.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    # Ensure conversation_turns is present
    if 'conversation_turns' not in data:
        data['conversation_turns'] = []
    response = supabase.table('supplier_conversations').insert(data).execute()
    return response.data
# Sprint 2 endpoints
@router.get('/agent_runs')
def get_agent_runs():
    response = supabase.table('agent_runs').select('*').execute()
    return response.data

@router.post('/agent_runs')
def create_agent_run(agent_run: AgentRun):
    data = agent_run.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('agent_runs').insert(data).execute()
    return response.data

@router.get('/tool_calls')
def get_tool_calls():
    response = supabase.table('tool_calls').select('*').execute()
    return response.data

@router.post('/tool_calls')
def create_tool_call(tool_call: ToolCall):
    data = tool_call.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('tool_calls').insert(data).execute()
    return response.data

@router.get('/conversation_turns')
def get_conversation_turns():
    response = supabase.table('conversation_turns').select('*').execute()
    return response.data

@router.post('/conversation_turns')
def create_conversation_turn(conversation_turn: ConversationTurn):
    data = conversation_turn.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('conversation_turns').insert(data).execute()
    return response.data

@router.get('/evaluation_turns')
def get_evaluation_turns():
    response = supabase.table('evaluation_turns').select('*').execute()
    return response.data

@router.post('/evaluation_turns')
def create_evaluation_turn(evaluation_turn: EvaluationTurn):
    data = evaluation_turn.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('evaluation_turns').insert(data).execute()
    return response.data

@router.get('/conversation_settings')
def get_conversation_settings():
    response = supabase.table('conversation_settings').select('*').execute()
    return response.data

@router.post('/conversation_settings')
def create_conversation_settings(conversation_settings: ConversationSettings):
    data = conversation_settings.dict(exclude_unset=True)
    response = supabase.table('conversation_settings').insert(data).execute()
    return response.data

@router.get('/evaluations')
def get_evaluations():
    response = supabase.table('supplier_evaluations').select('*').execute()
    return response.data

@router.post('/evaluations')
def create_evaluation(evaluation: Evaluation):
    data = evaluation.dict(exclude_unset=True)
    if 'id' in data and not data['id']:
        del data['id']
    response = supabase.table('supplier_evaluations').insert(data).execute()
    return response.data
