# Codex computer use: REA investigation

**Date:** 16 October 2026  
**Target:** installed `/Applications/ChatGPT.app`, bundle ID `com.openai.codex`, version `26.1007.71326`  
**REA:** [morluto/rea](https://github.com/morluto/rea), commit `60bf1024592888b5efb78f9c9458b4633da298bd`, package version `6.5.0`

This report was copied from the local `Codex R-E-A` research folder. Its `evidence/` and `rea/` paths refer to that original folder. The raw Evidence and the upstream REA checkout are not included here; see [this investigation's README](README.md) for provenance and availability.

## Executive finding

The installed computer-use stack is a **hybrid, app-aware control system**. For native macOS apps, a persistent JavaScript REPL calls a local Sky client, which talks to a separate signed `Codex Computer Use.app` service. That service returns an app-scoped accessibility description and a screenshot; actions can target an accessibility element index or image coordinates. For browser tabs, the same public `cua` interface selects a browser provider and can use a DOM/Playwright interface where available. The agent can batch deterministic actions in one REPL call, then request fresh state to verify the outcome.

The strongest explanation for its apparent reliability is the combination of **semantic targets, visual fallback, fresh feedback, and persistent tool state**. This is a mechanism-based inference, supported by shipped interfaces and one live probe; it is not a controlled comparison against other computer-use systems. The model's private training, planning policy, and the native service's implementation remain unobserved.

## Architecture observed in this build

```mermaid
flowchart LR
    A[Agent plan] --> B[cua_repl JavaScript tool]
    B --> C[@oai/cua adapter]
    C --> D{Target}
    D -->|macOS app| E[@oai/sky client]
    E --> F[Local native pipe and JSON-RPC]
    F --> G[Codex Computer Use service]
    G --> H[App accessibility state and screenshot]
    G --> I[Element or coordinate action]
    D -->|browser tab| J[Browser provider]
    J --> K[DOM or accessibility state and screenshot]
    J --> L[Playwright or supported tab actions]
    H --> A
    I --> A
    K --> A
    L --> A
```

**Installed components.** The app contains `@oai/cua` `0.2.6`, `@oai/sky` `0.7.7`, and `@oai/cua-repl` `0.1.0` under `/Applications/ChatGPT.app/Contents/Resources/cua_node/lib/node_modules/`. The nested service is `/Applications/ChatGPT.app/Contents/Resources/cua_node/lib/node_modules/@oai/sky/Codex Computer Use.app`; its bundle ID is `com.openai.sky.CUAService`. Both the host and service are signed by OpenAI OpCo, LLC. Package names and signatures establish shipped components, not which component handled every possible user action.

**REPL and bindings.** `@oai/cua-repl` launches a Node REPL with enabled `browser` and/or `computer` surfaces. `@oai/cua` binds apps and tabs to a unified interface. On macOS, `getApp()` calls `get_app_state()` and returns a bound app object; its `getAXState()`, `getScreenshot()`, `click()`, `setValue()`, and related methods translate to Sky calls. The bound object and JavaScript variables persist across tool calls. The source locations are `@oai/cua-repl/dist/lib/js/oai_js_cua_repl/src/launch.js`, `@oai/cua/dist/lib/js/oai_js_cua/src/tinysky_alt/create_tinysky_alt.js`, and `bind_mac_app.js` within the installed root above.

**Native transport.** Sky's macOS client uses a local native pipe to reach the separate service. Its shipped `native-pipe.js` implements framed JSON-RPC 2.0, request IDs, response validation, a version ping, timeouts, bounded frames, and a startup path for the service. `client.js` labels the client protocol `CodexComputerUseIPC-5`, sends typed app-state and action requests, and serializes requests through the transport. This is a code-level observation of the JavaScript client; the service's internal handling was not decompiled or traced.

**Native binary clues.** Direct Mach-O metadata inspection shows that the service links `ApplicationServices`, `AppKit`, `CoreGraphics`, and `ScreenCaptureKit` among other frameworks. Those links are consistent with accessibility, input, and capture work but do not prove which APIs are called in a given operation. A REA `inspect-macho` attempt also stopped at the sandbox's process-table restriction; its diagnostic is saved as `evidence/service-macho-rea.json`.

**Policy boundary.** `@oai/sky/.../targets/mac/computer-use-policy.js` checks the target app policy and invokes an approval flow before app-scoped operations. The client also sends turn metadata and records tool status. This plausibly enables broad app support while keeping the selected app and user consent explicit. It does not by itself establish the full enforcement logic inside the native service.

**Browser routing.** `@oai/cua/.../tinysky_alt/bind_tab.js` uses an accessibility interface when a tab exposes one. Otherwise it can return a DOM snapshot and screenshot, while native input wrappers reject actions on DOM-only tabs and direct the caller to Playwright. `create_browser_api.js` binds tabs by exact IDs, browser/profile, URL, or tab mention and rejects ambiguous or stale matches. The [official computer-use integration guide](https://developers.openai.com/api/docs/guides/tools-computer-use-integration) likewise describes combining UI text/locators with screenshots, preserving sessions, and verifying state, but that guide is general API advice rather than proof of this app's private internals.

## Why this likely performs well

| Mechanism | Evidence | Practical effect (inference) |
| --- | --- | --- |
| Accessibility tree with roles, labels, and element indices | Shipped Sky API; live Calculator state | The agent can select `Add` or `Equals` by meaning instead of estimating pixels. |
| Screenshot in the same app-state interface | Shipped Sky API and `bind_mac_app.js` | Visual context remains available for custom controls or weak accessibility data. |
| Optional app-specific guidance in returned state | Sky `window_result.js` | May help the agent handle unusual app controls; this pass did not measure its contribution. |
| Fresh state and compact diffs | Shipped REPL instructions; live probe | Reduces stale-element mistakes and keeps follow-up observations small. |
| Persistent REPL with batched actions | `@oai/cua-repl` and live probe | Cuts tool round trips while retaining app/tab bindings. |
| Browser-specific DOM/Playwright path | `bind_tab.js` and browser provider code | Uses structural web controls when the browser supports them. |
| Versioned local service protocol | `native-pipe.js` and `client.js` | Detects incompatible or failed service connections instead of silently acting on uncertain state. |
| App policy and approval flow | `computer-use-policy.js` | Keeps control scoped to a selected app, supporting dependable, authorized execution. |

The [official OpenAI computer-use guide](https://developers.openai.com/api/docs/guides/tools-computer-use) documents the general observe → act → screenshot → verify loop, recommends preserving the environment, and describes both structured action and code-execution integrations. It does **not** say the Codex desktop app uses that exact API loop. The local package evidence above is the basis for claims about this installed build.

## Live probe

I bound Calculator through the available `cua_repl` tool. The first response contained a structured accessibility tree with `1` at index 18, `Add` at 21, `2` at 19, and `Equals` at 24. In one tool call I clicked those four indices and requested fresh AX state. The returned diff replaced the input text with a result section showing `1+2` and `3`. The action-and-observation call took **0.67 seconds** as reported by the tool. This confirms the batching, element targeting, persistent binding, and diff behavior for one simple macOS app. It is one observation, not a latency or success-rate benchmark.

A follow-up set of native Calculator, TextEdit, and Finder runs is documented in [Native computer use test runs](Native-Computer-Use-Test-Runs.md). It includes successful editing and file management, plus observed failures in coordinate clicking and some native dialog targeting.

## REA evidence and limits

I cloned and built REA, then used its `analyze-javascript-application` CLI on the installed package trees. The focused `@oai/cua` source pass parsed **56/56** relevant files with **0 parse failures** and produced **204 nodes / 284 edges**. The `@oai/sky` source pass parsed **206/206** relevant files with **0 parse failures** and produced **665 nodes / 929 edges**, with partial graph coverage. The `@oai/cua-repl` pass parsed **6/6** relevant files and produced **33 nodes / 36 edges**. A broad `@oai/cua` package pass parsed **512 JavaScript files** but hit REA's parent-result budget, so I used the focused tree for architecture work. REA's `trace-application-feature` and `inspect-analysis-view` projections ran on the focused partial Evidence; their outputs are in the original local `evidence/` folder.

Every analysis command returned `cleanup_incomplete` because this managed sandbox denied REA's process-table inspection (`spawn EPERM`) during worker cleanup. The retained output is therefore **partial Evidence**, not a successful completed REA run. I did not disable REA's ownership check. The source and graph claims are corroborated by direct inspection of the shipped files, but I cannot claim REA verified worker cleanup. No runtime instrumentation, network capture, native decompilation, or model-side trace was performed.

The saved compressed REA outputs in the original local folder are `evidence/cua-core-rea.json.gz`, `evidence/sky-core-rea.json.gz`, `evidence/cua-repl-rea.json.gz`, and `evidence/cua-rea.json.gz`. `evidence/cua-core-view.json` is the compact projected summary; `evidence/bind-mac-trace.json` is a module-seeded static trace. These files contain local analysis data and may include shipped code-derived facts. They are not committed to this repository.

## What remains unknown and how to test it

1. **Native capture/action implementation.** The macOS service is an arm64 Mach-O executable, but its AX traversal, screenshot capture, focus management, and input synthesis were not analyzed. A native REA provider or a documented runtime trace would be needed to attribute those steps precisely.
2. **Model contribution.** This pass cannot isolate model visual grounding, training data, prompts, or planner heuristics from tool quality. That needs controlled tasks with the same model and different tool surfaces.
3. **Accuracy gain.** Run paired tasks across Calculator, a complex native app, and a browser using AX/DOM-only, screenshot-only, and hybrid modes. Measure task completion, misclicks, recovery after UI changes, tool calls, and elapsed time. Repeat each condition; one Calculator run cannot estimate these rates.
4. **Dynamic state handling.** Introduce dialogs, moving controls, delayed rendering, and stale tabs. Check whether fresh-state checks and exact tab identity improve recovery, and where coordinate fallback still fails.

## Reproduction details

The original REA clone is in the local `rea/` folder at the pinned commit above. The analyzed app archive SHA-256 is `2f231a64e6dd30111bcd09e03c149cd06c8679b25914842772423251c4608ded`. The nested service executable SHA-256 is `ac8bfe406d01a7cb43f7550c080587ae3a5f404f82fa6dcc399bf72a85cd765d`. The focused `@oai/cua` source tree digest reported by REA is `7be998b1359a2da9b43417f9cc4cedb7e5297c763729bb05cadaee34f592d2a7`.

For public context, see [REA's CLI and Evidence guide](https://github.com/morluto/rea/blob/60bf1024592888b5efb78f9c9458b4633da298bd/docs/cli.md), [REA's JavaScript application workflows](https://github.com/morluto/rea/blob/60bf1024592888b5efb78f9c9458b4633da298bd/docs/javascript-application-workflows.md), and [OpenAI's computer/browser walkthrough](https://developers.openai.com/training/walkthroughs/using-your-computer-and-browser).
