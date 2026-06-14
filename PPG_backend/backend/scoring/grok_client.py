import json
import urllib.request
import urllib.error
import logging
from django.conf import settings

logger = logging.getLogger('chatbot')

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "grok-2-1212"  # standard api config for Grok 2

def call_grok_api(messages: list) -> str:
    """
    Calls the xAI Grok API securely from the backend using the GROK_API_KEY setting.
    Raises ValueError or urllib exception on failure to trigger the fallback mechanism.
    """
    api_key = getattr(settings, 'GROK_API_KEY', '')
    if not api_key or 'placeholder' in api_key or 'REMPLACEZ' in api_key:
        raise ValueError("GROK_API_KEY is not configured or contains placeholder.")

    payload = {
        "model": GROK_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False
    }

    data = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    req = urllib.request.Request(
        GROK_API_URL,
        data=data,
        headers=headers,
        method="POST"
    )

    try:
        # 15 seconds timeout for chatbot responsiveness
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            if not content:
                raise ValueError("Empty response received from Grok.")
            return content.strip()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f"Grok API HTTP Error ({e.code}): {error_body}")
        raise ValueError(f"Grok API HTTP {e.code}: {error_body}")
    except urllib.error.URLError as e:
        logger.error(f"Grok API Connection/Network Error: {str(e)}")
        raise ValueError(f"Grok API Connection Error: {str(e)}")
    except Exception as e:
        logger.error(f"Grok API Unknown Error: {str(e)}")
        raise e
