import json
import os
import boto3

bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

AGENT_ID = os.environ['AGENT_ID']
AGENT_ALIAS_ID = os.environ['AGENT_ALIAS_ID']


def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '').strip()
        session_id = body.get('session_id', '')

        if not question:
            return response(400, {'error': 'question is required'})

        if not session_id:
            return response(400, {'error': 'session_id is required'})

        # Invoke Bedrock Agent — it handles KB retrieval + conversation memory
        agent_response = bedrock_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=question
        )

        # Collect streamed response
        answer = ''
        citations = []

        for event_stream in agent_response['completion']:
            if 'chunk' in event_stream:
                chunk = event_stream['chunk']
                answer += chunk['bytes'].decode('utf-8')

                # Extract citations if present
                if 'attribution' in chunk:
                    for citation in chunk['attribution'].get('citations', []):
                        for ref in citation.get('retrievedReferences', []):
                            source = ref.get('location', {}).get('s3Location', {}).get('uri', '')
                            text_snippet = ref.get('content', {}).get('text', '')[:200]
                            if source:
                                citations.append({
                                    'source': source,
                                    'snippet': text_snippet
                                })

        # Deduplicate citations by source
        seen = set()
        unique_citations = []
        for c in citations:
            if c['source'] not in seen:
                seen.add(c['source'])
                unique_citations.append(c)

        return response(200, {
            'answer': answer,
            'sources': unique_citations,
            'session_id': session_id
        })

    except bedrock_runtime.exceptions.ThrottlingException:
        return response(429, {'error': 'Too many requests. Please try again shortly.'})
    except Exception as e:
        print(f'Error: {str(e)}')
        return response(500, {'error': 'Something went wrong. Please try again.'})


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }
