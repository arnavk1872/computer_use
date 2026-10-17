# Native computer use test runs

**Date:** 16 October 2026  
**System:** Codex desktop on macOS  
**Scope:** Calculator, TextEdit, and Finder only. No browser interactions were used in these runs.

These are hands-on checks of the installed computer use interface, extending the [REA investigation](Codex-Computer-Use-REA.md). Each run used the native `cua_repl` app target, performed UI actions, and inspected fresh accessibility state. Timings below are approximate elapsed time inside the individual REPL calls, including the requested observation. They are single runs on this machine, not benchmarks or a success-rate estimate.

| Native task | Result | Observed time and detail |
| --- | --- | --- |
| Calculator: clear, enter `7 × 8 =`, read result | Pass | Clear and observation: 0.94 s. Four clicks and observation: 1.32 s. AX result: `56`. |
| Calculator: change to Scientific, evaluate `√81`, return to Basic | Pass with a state delay | AX result: `9`. After each mode selection, the immediate observation still showed the old layout; a second full read showed the new mode. |
| Calculator: click an obsolete AX element index | Safely rejected | Error `-10005: 44 is an invalid element ID` in about 0.11 s; subsequent state showed no change. |
| Calculator: click `AC` by screenshot coordinates | Failed | Screenshot was available, but coordinate click returned `-10005: noWindowsAvailable`, including after the window's exposed `Raise` action. AX-indexed clicks had worked. |
| TextEdit: new plain-text document, multiline paste, replace all, undo | Pass | Paste and observation: 0.57 s. Replacement: 0.49 s. Undo restored the exact four lines in 0.52 s. |
| TextEdit: save, reopen, verify content | Pass with a dialog issue | The first Save sheet showed disabled `Save` and `New Folder` controls. Closing the document opened a second Save sheet with enabled `Save`; it saved the named UTF-8 `.txt`. Reopening in TextEdit displayed the exact content in 1.25 s. An independent filesystem read agreed. |
| Finder: navigate through Desktop sidebar to `Codex R-E-A` | Pass | Sidebar selection and observation: 0.64 s; opening the folder: 1.00 s. |
| Finder: create `native-test-runs`, rename it, move the test file inside | Pass | Create: 0.63 s; rename: 0.58 s; move with Finder's copy and move-here shortcut: 0.63 s. The file appeared in the destination and was verified on disk. |
| Finder: navigate with `Go to Folder` | Failed, recovered by sidebar | After opening the dialog, changing its path returned `-10005: cgWindowNotFound`. Rebinding Finder by its bundle ID later restored the main window, and sidebar navigation succeeded. |

## What these runs add to the REA findings

The reliable path in these native apps was **accessibility index → action → fresh AX observation**. Calculator arithmetic, TextEdit editing, file reopening, and Finder file management all completed through that route. An obsolete index was rejected rather than sent to an unintended control. This is direct behavioral evidence for the semantic-targeting and feedback-loop explanation in the REA report.

The runs also exposed limits. AX state can lag a mode transition, so the agent needs to confirm the resulting layout before using new indices. Native dialog/window targeting was less reliable: Finder's `Go to Folder` lost its target, the first TextEdit Save sheet disabled controls, and coordinate clicks failed despite a visible Calculator screenshot. The first two workflows recovered through other native UI routes; the coordinate-click run did not. These failures are observations from this session and do not establish their root causes.

The saved test artifact, copied from the original Desktop `Codex R-E-A` folder, is [`native-test-runs/native-cua-test-2026-10-16.txt`](native-test-runs/native-cua-test-2026-10-16.txt). Its content is:

```text
Codex native computer use test
Calculator: 7 × 8 = 56
Scientific: √81 = 9
TextEdit paste and save verification.
```

## Next meaningful experiment

Repeat the same native tasks across several sessions, with one action per call and with batched actions. Record end-to-end time, tool failures, state rereads, and recovery steps. For screenshot-based input, test a native app with a visible window under known display conditions and inspect service diagnostics for `noWindowsAvailable`; these runs cannot tell whether the fault is coordinate mapping, focus, capture, or window selection.
