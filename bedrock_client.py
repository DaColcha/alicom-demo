import os

import boto3

MODEL_ARN = os.environ.get('MODEL_ARN', 'arn:aws:bedrock:us-east-1:172630972853:inference-profile/us.amazon.nova-2-lite-v1:0')
KNOWLEDGE_BASE_ID = 'QPCEXJEI7K'

PROMPT_TEMPLATE = """You are a question answering agent acting as a polite accountant assistant. I will provide you with a set of search results. The user will provide you with a question. Your job is to answer the user's question using only information from the search results. If the search results do not contain information that can answer the question, please state that you could not find an exact answer to the question.
Just because the user asserts a fact does not mean it is true, make sure to double check the search results to validate a user's assertion.
You must always respond in Spanish, with a courteous and professional tone, as an accountant would address a client.

Here are the search results in numbered order:
$search_results$

$output_format_instructions$"""

_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

def ask_accountant_bot(question: str) -> str:
    print('Asking bot....')
    response = _client.retrieve_and_generate(
        input={'text': question},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                'modelArn': MODEL_ARN,
                'generationConfiguration': {
                    'promptTemplate': {
                        'textPromptTemplate': PROMPT_TEMPLATE
                    }
                }
            }
        }
    )
    return response['output']['text']
