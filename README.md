# Computer Use Lab

A small, replaceable-driver agent and probe runner for exploring the limits of computer access. Start with **Cua Driver on your Mac**. Switch MCP servers through configuration; a non-MCP driver implements the `Driver` protocol in `driver.py` and its connection lifecycle. This is not tied to Codex or another coding-agent product.

## Install on the computer you want to control

Python 3.12+ and uv:

```sh
uv sync --locked
```

Install Cua Driver using its [official instructions](https://cua.ai/docs/cua-driver/quickstart). On macOS, use the supported CuaDriver.app/daemon launch or direct MCP launch documented by the installed version. Grant Accessibility and Screen Recording to the responsible application identity; do not grant permissions to arbitrary helper binaries. See [upstream embedding and identity notes](https://github.com/trycua/cua/tree/main/libs/cua-driver#macos-process-identity-and-permissions).

```sh
cua-driver --version
cua-driver doctor
uv run computer-use discover
uv run computer-use --output reports/cua-discovery.json discover
```

Discovery outputs the actual tool names, descriptions, and JSON input schemas. It does **not** claim that advertised capabilities work or that permissions are granted. Reports can contain personal application information and screenshots; `reports/` is ignored by Git. Do not commit real screen recordings or credentials.

## Explore access without a model

Run explicit driver calls using the advertised schemas:

```sh
uv run computer-use call list_apps '{}'
uv run computer-use call list_windows '{}'
```

Select the actual `pid` and `window_id` returned by your driver. Use its advertised `get_window_state`, screenshot, and action schemas rather than hardcoding element identifiers. Read the target before acting; element tokens belong to a fresh snapshot. A delivered click is not proof that the intended change happened.

For repeatable checks, write a JSON list of probes and run:

```sh
uv run computer-use --output reports/my-probes.json probe my-probes.json
```

Probe format (replace the tool and arguments using discovery):

```json
[
  {
    "name": "Read target and find expected state",
    "tool": "get_window_state",
    "arguments": {"pid": 123, "window_id": 456, "query": "Hello"},
    "assertions": [{"kind": "text_contains", "value": "Hello"}]
  }
]
```

An assertion only proves what it checks. For a write, use a separate fresh readback or application/file check. Text presence alone does not prove correct file contents, background delivery, or unchanged focus. Additional assertion types:

- `{"kind":"image_present"}` checks that an image was returned.
- `{"kind":"json_equals","path":["structuredContent","field"],"value":"expected"}` checks a precise response field (integer array indices are supported).

Statuses distinguish `verified`, `failed`, `unsupported`, `tool_error`, `error`, `delivered_unverified`, and `timeout_unknown_effect`. A timeout halts the sequence without retrying; inspect state before continuing. Exit code 0 requires every probe to be verified; exit 2 means something is unverified or unsuccessful. `call` reports delivery only. The sample enumeration probes deliberately have no outcome assertions and therefore exit 2.

## Run your own cloud or local model

Edit a copy of `examples/cua.json`. The implemented model adapter supports **OpenAI-compatible Chat Completions with tool calling**; visual operation also requires image input support. This is not a claim that every model or provider implements the same protocol. Native Anthropic/Responses protocols need another `Model.complete` adapter.

For a hosted endpoint, configure `base_url`, `model`, and `api_key_env` (the name of an existing environment variable). Never put a key in the JSON file. For a local server such as a compatible vLLM deployment, use its URL and served model identifier; omit `api_key_env` if it needs no authentication.

```sh
uv run computer-use --config my-config.json agent \
  'List running applications and summarize them' --allow-tool list_apps

uv run computer-use --config my-config.json --output reports/agent-run.json agent \
  'In the blank TextEdit document I opened, type Hello and read it back. Do not save it.' \
  --allow-all-tools --max-steps 12
```

The agent passes the driver's native schemas to the model, returns tool results, forwards screenshots as images, and stops at a bounded number of model turns. It does not execute model-generated Python or shell code itself; such access exists only if the selected driver exposes it and you enable the corresponding tools. `--allow-all-tools` enables every advertised tool, including broad operations if the driver has them. Screen/document instructions are treated as untrusted data in the agent prompt; that prompt is not a hardened isolation boundary.

`agent_finished` records the agent's claim; it is not independent proof of success. A model or transport exception stops execution instead of replaying uncertain actions. Ctrl-C cancels the client session; an already delivered OS action may still have taken effect. No automatic mutation rollback is promised.

## Swap drivers

The `driver` entry contains a stdio MCP executable and argument array. Replace these with the alternative driver's **documented** server command. The runner discovers its native tools afresh; no Cua tool names are imposed by the agent loop.

Arc has not been installed or validated here, and no guessed Arc command is provided. Driver-specific saved probes must be ported to the new tool schemas. Non-MCP backends need a small implementation of `tools()` and `call()` plus a connection factory. Hosted/local model choice is independent of the driver choice.

## Establish the real limits on your Mac

Use a disposable document and record each case separately. The following is a test matrix, not a list of verified capabilities:

| Area | Check | Evidence required |
|---|---|---|
| Applications/windows | List, inspect, open, resize, switch | Fresh window/application state |
| Accessibility | Read labels/values; invoke exact control | Changed value or application state |
| Screenshots | Capture the correct window/display | Actual returned image; correct target |
| Text and clipboard | Unicode, multiline, exact replacement | Fresh readback, not echoed arguments |
| Mouse/keyboard | Click, scroll, shortcuts, drag | Intended final selection/position/state |
| Background | Covered/minimized windows, multiple windows | Target effect plus unchanged foreground/focus; manual observation if driver cannot expose it |
| Browsers | Native browser controls and page/DOM routes | Correct page state; record which route was used |
| Settings | Inspect settings; change a chosen reversible preference | Before/after state, then explicitly restore it |
| Files/terminal | Determine whether driver exposes these tools | Create/read a disposable file only if supported; absence is not model failure |
| Difficult UI | Canvas, Electron, dialogs, delayed updates | Correct effect after fresh observation |
| Permission limits | Missing/revoked grants, protected surfaces | Explicit denial or unavailable capability; do not infer from discovery |

Accessibility and Screen Recording do not grant Full Disk Access, Input Monitoring, Automation access to other applications, administrator privileges, or bypasses for Touch ID/Keychain/SIP. Test only the access relevant to the selected operation. Grant and revoke permissions through macOS normally.

## Validation in this repository

```sh
uv run python -m unittest discover -s tests -v
```

Tests run an actual stdio MCP fixture server and a local HTTP model fixture. They verify discovery, schema enforcement, Unicode write/readback, failure classification, unknown tools, timeouts, tool restrictions, image forwarding, and the model-to-driver round trip. They do not verify a real model, Cua, Arc, macOS permissions, or a physical desktop.

The development cloud machine is Linux without a graphical session. Actual Mac capability results remain pending execution there. No model benchmarks or workflow-learning features are included.
