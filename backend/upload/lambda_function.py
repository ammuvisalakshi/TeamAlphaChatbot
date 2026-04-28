import json
import os
import base64
import uuid
import boto3

s3 = boto3.client('s3')
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

DOCS_BUCKET = os.environ['DOCS_BUCKET']
KNOWLEDGE_BASE_ID = os.environ['KNOWLEDGE_BASE_ID']
DATA_SOURCE_ID = os.environ['DATA_SOURCE_ID']


def handler(event, context):
    try:
        content_type = event.get('headers', {}).get('content-type', '')

        # Handle presigned URL request (for large files)
        if 'application/json' in content_type:
            body = json.loads(event.get('body', '{}'))
            filename = body.get('filename', '')
            file_type = body.get('content_type', 'application/octet-stream')

            if not filename:
                return response(400, {'error': 'filename is required'})

            # Generate a unique key
            key = f"documents/{uuid.uuid4().hex}_{filename}"

            # Generate presigned URL for direct upload
            presigned = s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': DOCS_BUCKET,
                    'Key': key,
                    'ContentType': file_type
                },
                ExpiresIn=300
            )

            return response(200, {
                'upload_url': presigned,
                'key': key,
                'filename': filename
            })

        # Handle direct file upload (base64 encoded via API Gateway)
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)

        if is_base64:
            file_content = base64.b64decode(body)
        else:
            file_content = body.encode('utf-8')

        # Get filename from query params or headers
        params = event.get('queryStringParameters', {}) or {}
        filename = params.get('filename', f'upload_{uuid.uuid4().hex[:8]}')

        key = f"documents/{uuid.uuid4().hex}_{filename}"

        # Upload to S3
        s3.put_object(
            Bucket=DOCS_BUCKET,
            Key=key,
            Body=file_content,
            Metadata={'original_filename': filename}
        )

        # Trigger KB sync
        ingestion = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID
        )

        ingestion_id = ingestion['ingestionJob']['ingestionJobId']

        return response(200, {
            'status': 'uploaded',
            'filename': filename,
            'key': key,
            'sync_status': 'started',
            'ingestion_job_id': ingestion_id
        })

    except Exception as e:
        print(f'Error: {str(e)}')
        return response(500, {'error': 'Upload failed. Please try again.'})


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
