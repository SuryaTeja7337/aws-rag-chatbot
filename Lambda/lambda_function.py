import boto3
import json
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# Configuration
REGION = os.environ.get('AWS_REGION', 'us-east-1')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'surya-rag-chatbot-knowledge-base-st-us-east-1')
COLLECTION_ENDPOINT = os.environ.get('COLLECTION_ENDPOINT', 'https://6d23aax18r2zjrdslptb.us-east-1.aoss.amazonaws.com')
INDEX_NAME = 'rag-documents'
EMBEDDING_MODEL = 'amazon.titan-embed-text-v1'
CLAUDE_MODEL = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

# AWS clients
s3_client = boto3.client('s3', region_name=REGION)
bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    REGION,
    'aoss',
    session_token=credentials.token
)

# OpenSearch client
host = COLLECTION_ENDPOINT.replace('https://', '')
opensearch_client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=300
)

def create_embeddings(text):
    body = json.dumps({"inputText": text})
    response = bedrock_runtime.invoke_model(
        modelId=EMBEDDING_MODEL,
        body=body,
        contentType='application/json',
        accept='application/json'
    )
    response_body = json.loads(response['body'].read())
    return response_body['embedding']

def search_similar(query, k=3):
    query_embedding = create_embeddings(query)
    search_body = {
        'size': k,
        'query': {
            'knn': {
                'embedding': {
                    'vector': query_embedding,
                    'k': k
                }
            }
        },
        '_source': ['text', 'source']
    }
    response = opensearch_client.search(index=INDEX_NAME, body=search_body)
    return response['hits']['hits']

def ask_claude(question, context):
    prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Answer:"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    })
    
    response = bedrock_runtime.invoke_model(
        modelId=CLAUDE_MODEL,
        body=body
    )
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
        
        question = body.get('question', '')
        
        if not question:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'error': 'No question provided'})
            }
        
        print(f"Searching for: {question}")
        results = search_similar(question, k=3)
        print(f"Found {len(results)} results")
        
        context_parts = []
        sources = []
        for result in results:
            source = result['_source']
            context_parts.append(f"[From {source['source']}]\n{source['text']}")
            sources.append(source['source'])
        
        context = "\n\n".join(context_parts)
        
        print("Generating answer with Claude...")
        answer = ask_claude(question, context)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'question': question,
                'answer': answer,
                'sources': list(set(sources))
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': str(e)})
        }