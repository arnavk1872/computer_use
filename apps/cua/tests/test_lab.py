import asyncio
import json
from pathlib import Path
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jsonschema import ValidationError
from computer_use.agent import run_agent
from computer_use.driver import connect
from computer_use.model import ChatModel
from computer_use.probes import probe

CONFIG = {'command': sys.executable, 'args': [str(Path(__file__).with_name('fixture_driver.py'))]}

class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_call_and_independent_readback(self):
        async with connect(CONFIG) as driver:
            self.assertEqual({t['name'] for t in await driver.tools()}, {'inspect', 'type_text', 'fail'})
            report = await probe(driver, [
                {'name': 'write', 'tool': 'type_text', 'arguments': {'text': 'Grüße 👋'}},
                {'name': 'readback', 'tool': 'inspect', 'assertions': [
                    {'kind': 'json_equals', 'path': ['structuredContent', 'text'], 'value': 'Grüße 👋'}]},
                {'name': 'incorrect expectation', 'tool': 'inspect', 'assertions': [
                    {'kind': 'text_contains', 'value': 'not present'}]},
                {'name': 'missing', 'tool': 'no_such_tool'},
                {'name': 'error', 'tool': 'fail'}])
            self.assertEqual([c['status'] for c in report['checks']],
                             ['delivered_unverified', 'verified', 'failed', 'unsupported', 'tool_error'])

    async def test_invalid_arguments_never_reach_driver(self):
        async with connect(CONFIG) as driver:
            with self.assertRaises(ValidationError):
                await driver.call('type_text', {'text': 123})
            with self.assertRaises(ValueError):
                await driver.call('invented', {})
            self.assertEqual((await driver.call('inspect', {}))['structuredContent']['text'], '')

    async def test_model_http_agent_mcp_round_trip(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                self.server.test_path = self.path
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append(body)
                if len(requests) == 1:
                    message = {'role': 'assistant', 'content': None, 'tool_calls': [
                        {'id': '1', 'type': 'function', 'function': {
                            'name': 'type_text', 'arguments': json.dumps({'text': 'hello'})}}]}
                elif len(requests) == 2:
                    message = {'role': 'assistant', 'content': None, 'tool_calls': [
                        {'id': '2', 'type': 'function', 'function': {'name': 'inspect', 'arguments': '{}'}}]}
                else:
                    message = {'role': 'assistant', 'content': 'Readback confirms hello'}
                data = json.dumps({'choices': [{'message': message}]}).encode()
                self.send_response(200); self.send_header('Content-Type', 'application/json')
                self.end_headers(); self.wfile.write(data)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            model = ChatModel({'base_url': f'http://127.0.0.1:{server.server_port}/v1', 'model': 'fixture'})
            async with connect(CONFIG) as driver:
                result = await run_agent(driver, model, 'Write hello and verify', {'type_text', 'inspect'})
            self.assertEqual(result['status'], 'agent_finished')
            self.assertEqual(result['trace'][1]['result']['structuredContent']['text'], 'hello')
            self.assertEqual(server.test_path, '/v1/chat/completions')
            self.assertEqual(len(requests), 3)
            self.assertIn('hello', requests[2]['messages'][-1]['content'])
        finally:
            await asyncio.to_thread(server.shutdown)
            server.server_close(); thread.join()

    async def test_timeout_stops_probe_sequence(self):
        class Slow:
            async def tools(self): return [{'name': 'slow'}]
            async def call(self, *args): await asyncio.sleep(1)
        report = await probe(Slow(), [{'name': 'one', 'tool': 'slow'}, {'name': 'two', 'tool': 'slow'}], .01)
        self.assertEqual(len(report['checks']), 1)
        self.assertEqual(report['checks'][0]['status'], 'timeout_unknown_effect')

    async def test_disabled_tool_is_not_executed_and_budget_stops(self):
        class Model:
            async def complete(self, messages, tools):
                return {'role': 'assistant', 'tool_calls': [{'id': 'x', 'function': {
                    'name': 'type_text', 'arguments': '{"text":"unwanted"}'}}]}
        async with connect(CONFIG) as driver:
            result = await run_agent(driver, Model(), 'inspect', {'inspect'}, max_steps=1)
            self.assertEqual(result['status'], 'step_limit')
            self.assertTrue(result['trace'][0]['result']['isError'])
            self.assertEqual((await driver.call('inspect', {}))['structuredContent']['text'], '')

    async def test_screenshot_is_forwarded_as_image(self):
        captured = []
        class Driver:
            async def tools(self): return [{'name': 'shot', 'inputSchema': {'type': 'object'}}]
            async def call(self, *args): return {'content': [{'type': 'image', 'mimeType': 'image/png', 'data': 'AAAA'}]}
        class Model:
            async def complete(self, messages, tools):
                captured.append(list(messages))
                if len(captured) == 1:
                    return {'role': 'assistant', 'tool_calls': [{'id': 'x', 'function': {'name': 'shot', 'arguments': '{}'}}]}
                return {'role': 'assistant', 'content': 'done'}
        await run_agent(Driver(), Model(), 'look', None)
        self.assertEqual(captured[1][-1]['content'][1]['image_url']['url'], 'data:image/png;base64,AAAA')

    async def test_missing_key_is_reported_without_network(self):
        model = ChatModel({'api_key_env': 'COMPUTER_USE_TEST_MISSING_KEY', 'base_url': 'http://unused', 'model': 'fixture'})
        with self.assertRaisesRegex(ValueError, 'absent'):
            await model.complete([], [])

if __name__ == '__main__':
    unittest.main()
