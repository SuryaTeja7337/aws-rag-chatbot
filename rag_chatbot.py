import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import os

# Configuration
REGION = 'us-east-1'
BUCKET_NAME = 'surya-rag-chatbot-knowledge-base-st-us-east-1'
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
    """Create embeddings using Amazon Titan"""
    body = json.dumps({"inputText": text})
    response = bedrock_runtime.invoke_model(
        modelId=EMBEDDING_MODEL,
        body=body,
        contentType='application/json',
        accept='application/json'
    )
    response_body = json.loads(response['body'].read())
    return response_body['embedding']

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def create_index():
    """Create OpenSearch index with vector mapping"""
    index_body = {
        'settings': {
            'index': {
                'knn': True,
                'knn.algo_param.ef_search': 512
            }
        },
        'mappings': {
            'properties': {
                'embedding': {
                    'type': 'knn_vector',
                    'dimension': 1536,
                    'method': {
                        'name': 'hnsw',
                        'engine': 'faiss',
                        'parameters': {
                            'ef_construction': 512,
                            'm': 16
                        }
                    }
                },
                'text': {'type': 'text'},
                'source': {'type': 'keyword'}
            }
        }
    }
    
    try:
        if opensearch_client.indices.exists(index=INDEX_NAME):
            print(f"Index {INDEX_NAME} already exists")
        else:
            opensearch_client.indices.create(index=INDEX_NAME, body=index_body)
            print(f"Created index {INDEX_NAME}")
    except Exception as e:
        print(f"Error creating index: {e}")

def ingest_documents():
    """Read documents from S3, chunk, embed, and store in OpenSearch"""
    print("Starting document ingestion...")
    
    # List objects in S3 bucket
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
    
    if 'Contents' not in response:
        print("No files found in S3 bucket")
        return
    
    doc_count = 0
    for obj in response['Contents']:
        key = obj['Key']
        if not key.endswith('.txt'):
            continue
            
        print(f"Processing: {key}")
        
        try:
            # Get file content
            file_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
            
            # Try UTF-8 first, then fall back to latin-1
            try:
                content = file_obj['Body'].read().decode('utf-8')
            except UnicodeDecodeError:
                file_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
                content = file_obj['Body'].read().decode('latin-1')
            
            # Chunk the content
            chunks = chunk_text(content)
            print(f"  Created {len(chunks)} chunks")
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                # Create embedding
                embedding = create_embeddings(chunk)
                
                # Store in OpenSearch
                document = {
                    'text': chunk,
                    'embedding': embedding,
                    'source': key,
                    'chunk_id': i
                }
                
                opensearch_client.index(
                    index=INDEX_NAME,
                    body=document,
                    refresh=False
                )
                doc_count += 1
            
            print(f"  Indexed {len(chunks)} chunks from {key}")
        
        except Exception as e:
            print(f"  Error processing {key}: {e}")
            continue
    
    print(f"\nTotal chunks indexed: {doc_count}")

def search_similar(query, k=3):
    """Search for similar documents using vector similarity"""
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
    """Ask Claude a question with retrieved context"""
    prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Answer:"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    })
    
    response = bedrock_runtime.invoke_model(
        modelId=CLAUDE_MODEL,
        body=body
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def chat():
    """Interactive chat loop"""
    print("\n" + "="*60)
    print("RAG Chatbot Ready! (Type 'quit' to exit)")
    print("="*60 + "\n")
    
    while True:
        question = input("\nYou: ").strip()
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not question:
            continue
        
        # Search for relevant context
        print("Searching knowledge base...")
        results = search_similar(question, k=3)
        
        # Combine context
        context_parts = []
        for result in results:
            source = result['_source']
            context_parts.append(f"[From {source['source']}]\n{source['text']}")
        
        context = "\n\n".join(context_parts)
        
        # Ask Claude
        print("Generating answer...")
        answer = ask_claude(question, context)
        
        print(f"\nClaude: {answer}")
        print("\n" + "-"*60)

def main():
    """Main function"""
    if not COLLECTION_ENDPOINT:
        print("Error: COLLECTION_ENDPOINT not set")
        print("Run: export COLLECTION_ENDPOINT='your-endpoint-here'")
        return
    
    print("RAG Chatbot Setup")
    print("="*60)
    
    # Create index
    create_index()
    
    # Ask if user wants to ingest documents
    ingest = input("\nDo you want to ingest documents from S3? (y/n): ").strip().lower()
    if ingest == 'y':
        ingest_documents()
    
    # Start chat
    chat()

if __name__ == "__main__":
    main()
