"""OpenAI-compatible Chat Completions adapter, for hosted or local endpoints."""
import asyncio
import json
import os
import urllib.error
import urllib.request
from typing import Protocol


class Model(Protocol):
    async def complete(self, messages: list, tools: list) -> dict: ...


class ChatModel:
    def __init__(self, config):
        self.config = config

    async def complete(self, messages, tools):
        return await asyncio.to_thread(self._request, messages, tools)

    def _request(self, messages, tools):
        key_name = self.config.get('api_key_env')
        key = os.environ.get(key_name) if key_name else None
        if key_name and not key:
            raise ValueError(f'Required environment variable is absent: {key_name}')
        payload = {'model': self.config['model'], 'messages': messages}
        if tools:
            payload['tools'] = [{'type': 'function', 'function': {
                'name': t['name'], 'description': t.get('description', ''), 'parameters': t['inputSchema']}}
                for t in tools]
        headers = {'Content-Type': 'application/json'}
        if key:
            headers['Authorization'] = 'Bearer ' + key
        req = urllib.request.Request(self.config['base_url'].rstrip('/') + '/chat/completions',
                                     data=json.dumps(payload).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.config.get('timeout', 120)) as response:
                return json.load(response)['choices'][0]['message']
        except urllib.error.HTTPError as exc:
            # Provider bodies may echo private prompts or authentication details.
            raise RuntimeError(f'Model endpoint returned HTTP {exc.code}') from None
