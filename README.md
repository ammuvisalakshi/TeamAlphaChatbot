# Team Alpha Chatbot

AI-powered document assistant for Team Alpha. Upload documents and ask questions — answers are grounded in your team's docs with source citations.

## Architecture

```
User → CloudFront → S3 (Chat UI)
           ↓
      API Gateway
       /       \
  Lambda       Lambda
  (query)      (upload)
     ↓            ↓
  Bedrock       S3 Docs → Bedrock KB → Aurora pgvector
  Agent           (Titan Embeddings v2)
  (Claude)
     ↑
  Guardrails
```

## Prerequisites

1. **AWS CLI** configured on your machine
2. **IAM Policy** `TeamAlpha-Chatbot-Deployer-Policy` created and attached to your user/role
   - Policy file: `../ChatBotInfrastructure/iam-deployer-policy-for-chatbot.json`
3. **Bedrock model access** enabled in AWS Console (us-east-1):
   - Claude Sonnet (`anthropic.claude-sonnet-4-20250514-v1:0`)
   - Titan Embeddings v2 (`amazon.titan-embed-text-v2:0`)

## Deploy

```powershell
cd c:\MyProjects\AWS\ChatBotInfrastructure
.\deploy.ps1
```

Options:
```powershell
.\deploy.ps1 -Environment prod -Region us-east-1
```

Deployment takes ~15-20 minutes (Aurora cluster creation).

## Usage

1. Open the CloudFront URL (printed after deploy)
2. Click **Upload Docs** → drag & drop PDF/HTML/TXT files
3. Wait ~30 seconds for knowledge base to sync
4. Start asking questions!

## Project Structure

```
ChatBotInfrastructure/              # Infrastructure (separate repo)
├── iam-deployer-policy-for-chatbot.json
├── template.yaml                   # CloudFormation stack
├── deploy.ps1                      # Deploy script
└── deployment-outputs.txt          # Generated after deploy

TeamAlphaChatbot/                   # App code (this repo)
├── backend/
│   ├── query/
│   │   └── lambda_function.py      # Chat: invokes Bedrock Agent
│   └── upload/
│       └── lambda_function.py      # Upload: S3 + KB sync
├── frontend/
│   └── index.html                  # Chat UI + file upload
└── README.md
```

## Cost Estimate

| Service | Monthly Cost |
|---|---|
| Aurora Serverless v2 (0.5 ACU min) | ~$30 |
| Bedrock (Claude + Titan) | ~$5-15 (usage-based) |
| S3 + CloudFront | ~$1 |
| Lambda + API Gateway | ~$1 |
| **Total** | **~$35-50** |

## Future Enhancements

- Confluence auto-sync (EventBridge + Lambda)
- Additional knowledge bases (attach to same agent)
- Action groups (Jira tickets, Slack notifications)
- Custom domain with ACM certificate
