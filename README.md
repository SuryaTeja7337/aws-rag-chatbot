# AWS RAG Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot built entirely with AWS services.

![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Python](https://img.shields.io/badge/Python-3.9-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🚀 Features

- **Semantic Search**: Vector embeddings for meaning-based document retrieval
- **AI-Powered**: Claude Sonnet 4.5 via Amazon Bedrock
- **Serverless**: AWS Lambda + API Gateway (scales automatically)
- **Web Interface**: Beautiful, responsive chat UI
- **Source Citations**: Shows which documents answers came from
- **Cost-Effective**: ~$3-4/month for light usage

## 🏗️ Architecture
```
┌─────────┐
│  User   │
└────┬────┘
     │ HTTPS
     ▼
┌────────────────┐
│  API Gateway   │
└────┬───────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│           AWS Lambda                     │
│  ┌─────────────────────────────────┐   │
│  │  1. Create query embedding      │   │
│  │  2. Search OpenSearch           │   │
│  │  3. Retrieve relevant chunks    │   │
│  │  4. Generate answer with Claude │   │
│  └─────────────────────────────────┘   │
└──┬──────────┬──────────┬───────────────┘
   │          │          │
   ▼          ▼          ▼
┌──────┐  ┌──────────┐  ┌─────────────┐
│  S3  │  │OpenSearch│  │   Bedrock   │
│      │  │Serverless│  │             │
│Docs  │  │Vector DB │  │Titan+Claude │
└──────┘  └──────────┘  └─────────────┘
```

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Storage** | Amazon S3 | Source documents |
| **Vector DB** | OpenSearch Serverless | Embedding storage & similarity search |
| **Embeddings** | Bedrock - Titan | Text → 1536-dimensional vectors |
| **LLM** | Bedrock - Claude Sonnet 4.5 | Answer generation |
| **Compute** | AWS Lambda (Python 3.9) | Serverless backend |
| **API** | API Gateway | REST endpoint with CORS |
| **Frontend** | HTML/CSS/JavaScript | Chat interface |

## 📁 Project Structure
```
aws-rag-chatbot/
├── Lambda/
│   ├── lambda_function.py       # Serverless handler
│   └── requirements.txt          # Dependencies
├── chatbot-ui.html              # Web interface
├── rag_chatbot.py               # Local development script
└── README.md
```

## 💡 How It Works

### Ingestion Phase (One-time)
1. Documents stored in S3 (6 text files)
2. Split into 500-word chunks with 50-word overlap
3. Convert each chunk to embeddings using Titan
4. Store embeddings in OpenSearch Serverless

### Query Phase (Every question)
1. User asks question via web UI
2. API Gateway triggers Lambda function
3. Lambda converts question to embedding
4. OpenSearch finds 3 most similar chunks (kNN search)
5. Lambda sends chunks + question to Claude
6. Claude generates answer based on context
7. Response returned to user with source citations

**Average response time:** 3-4 seconds

## 💰 Cost Breakdown

| Service | Monthly Cost |
|---------|--------------|
| OpenSearch Serverless | $2-3 |
| Bedrock - Claude | $0.50 |
| Bedrock - Titan | $0.01 |
| Lambda | Free (under 1M requests) |
| API Gateway | Free (under 1M requests) |
| S3 | <$0.01 |
| **Total** | **~$3-4** |

## 🎯 Use Cases

- Internal knowledge base chatbot
- Customer support automation
- Document Q&A system
- Research assistant
- Technical documentation helper

## 🔐 Security Features

- IAM roles with least-privilege access
- HTTPS-only API endpoint
- Encryption at rest (S3, OpenSearch)
- AWS-managed KMS keys
- CORS properly configured

## 📈 Performance

- **Embedding Dimension:** 1536 (Titan)
- **Vector Search Algorithm:** HNSW
- **Context Window:** Up to 200K tokens (Claude)
- **Similarity Metric:** Cosine similarity

## 👤 Author

**Surya Teja**
- GitHub: [@SuryaTeja7337](https://github.com/SuryaTeja7337)

