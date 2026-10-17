"""Explicit probes: discovery is never reported as verified computer access."""
import asyncio
import platform
from datetime import datetime, timezone


def assertion(result, check):
    if check['kind'] == 'text_contains':
        text = '\n'.join(c.get('text', '') for c in result.get('content', []) if c.get('type') == 'text')
        return check['value'] in text
    if check['kind'] == 'image_present':
        return any(c.get('type') == 'image' and c.get('data') for c in result.get('content', []))
    if check['kind'] == 'json_equals':
        value = result
        for key in check['path']:
            value = value[int(key)] if isinstance(value, list) else value[key]
        return value == check['value']
    raise ValueError(f"Unknown assertion kind: {check['kind']}")


async def probe(driver, cases, timeout=30):
    tools = await driver.tools()
    names = {t['name'] for t in tools}
    results = []
    for case in cases:
        record = {'name': case['name'], 'tool': case['tool'], 'status': 'unverified'}
        if case['tool'] not in names:
            record['status'] = 'unsupported'
        else:
            try:
                response = await asyncio.wait_for(driver.call(case['tool'], case.get('arguments', {})), timeout)
                record['response'] = response
                if response.get('isError'):
                    record['status'] = 'tool_error'
                elif case.get('assertions'):
                    record['status'] = 'verified' if all(assertion(response, c) for c in case['assertions']) else 'failed'
                else:
                    record['status'] = 'delivered_unverified'
            except TimeoutError:
                record.update(status='timeout_unknown_effect', error='Not retried; inspect state before repeating an action')
                results.append(record)
                break
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                record.update(status='failed', error=str(exc))
            except Exception as exc:
                record.update(status='error', error=str(exc))
        results.append(record)
    return {'created_at': datetime.now(timezone.utc).isoformat(), 'host': platform.system(),
            'advertised_tools': tools, 'checks': results,
            'note': 'Tool discovery is not a permission or successful-effect check. Assertions establish only their stated scope.'}
