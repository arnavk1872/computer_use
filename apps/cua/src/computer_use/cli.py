import argparse
import asyncio
import json
from pathlib import Path

from .agent import run_agent
from .driver import connect
from .model import ChatModel
from .probes import probe


def load(path):
    return json.loads(Path(path).read_text())


async def execute(args):
    config = load(args.config)
    if args.output and Path(args.output).exists():
        raise FileExistsError('Choose a new report path; no driver calls were made')
    async with connect(config['driver']) as driver:
        if args.command == 'discover':
            result = await probe(driver, [])
        elif args.command == 'call':
            result = await asyncio.wait_for(driver.call(args.tool, json.loads(args.arguments)), args.timeout)
        elif args.command == 'probe':
            result = await probe(driver, load(args.cases), args.timeout)
        else:
            result = await run_agent(driver, ChatModel(config['model']), args.goal,
                                     None if args.allow_all_tools else set(args.allow_tool), args.max_steps, args.timeout)
    output = json.dumps(result, indent=2)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Reports can contain screenshots/application data. Never silently overwrite one.
        with path.open('x', encoding='utf-8') as file:
            file.write(output + '\n')
    else:
        print(output)
    if args.command == 'probe':
        return 0 if all(c['status'] == 'verified' for c in result['checks']) and result['checks'] else 2
    if args.command == 'agent':
        return 0 if result['status'] == 'agent_finished' else 2
    return 2 if result.get('isError') else 0


def main():
    parser = argparse.ArgumentParser(description='Explore and operate a connected computer through replaceable drivers')
    parser.add_argument('--config', default='examples/cua.json')
    parser.add_argument('--output')
    parser.add_argument('--timeout', type=float, default=30)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('discover')
    call = sub.add_parser('call')
    call.add_argument('tool')
    call.add_argument('arguments', nargs='?', default='{}')
    check = sub.add_parser('probe')
    check.add_argument('cases')
    agent = sub.add_parser('agent')
    agent.add_argument('goal')
    agent.add_argument('--max-steps', type=int, default=12)
    grant = agent.add_mutually_exclusive_group(required=True)
    grant.add_argument('--allow-tool', action='append', default=[])
    grant.add_argument('--allow-all-tools', action='store_true')
    args = parser.parse_args()
    if args.timeout <= 0 or getattr(args, 'max_steps', 1) <= 0:
        parser.error('Timeout and max steps must be positive')
    try:
        raise SystemExit(asyncio.run(execute(args)))
    except KeyboardInterrupt:
        parser.exit(130, 'Canceled. Inspect the target before repeating any action.\n')
    except Exception as exc:
        parser.exit(1, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
