# Step 0 probe: what does IFrameSrcdoc allow in GE chat?

The ELI5 explainer is an HTML page in an `IFrameSrcdoc`. Rendering with inline CSS, inside a card and inside a `Canvas`, is already proven (v0.9 concierge `guidelines.md` section 8.6). These are the open questions:

| # | question | why it matters |
|---|---|---|
| Q1 | Does JavaScript run inside the frame? | Level tabs (ELI5 to Expert) switch in the frame with no round trip. Without JS they become native `MaterialTabs` with one frame per level. |
| Q2 | Does JS work inside a `Canvas` too? | The explainer lives in the side panel. |
| Q3 | Does a `postMessage({type: 'a2ui_action'})` from the frame reach the agent? In what shape? | Follow-up chips inside the explainer ("Go deeper", related questions). Without it, follow-ups are native buttons under the frame. |
| Q4 | Does a ~200 KB page render? | A rich explainer with SVG is 30 to 100 KB; this gives headroom. |

The probe is deterministic: no model call, a callback picks the card from the exact word you type. Synthetic content only.

## Run it

Deploy and register as in the [README](README.md). Then, in GE chat, keep **F12, Console** open and type one trigger per message:

| # | type | look for |
|---|---|---|
| 0 | `help` | the trigger list renders. If not, stop. |
| 1 | `iframe-js` | green pill "JavaScript: running"; clicking ELI10, ELI15, Expert switches the text; the diagram shows |
| 2 | `iframe-canvas` | opener card in chat, side panel opens; same checks as 1 inside the panel |
| 3 | `iframe-action` | click **A**, then **B**, then **C** (native button), one at a time. Each that reaches the agent gets a **Received** card with the raw payload |
| 4 | `iframe-200kb` | renders like `iframe-js`, no error |

For row 3, copy each **Received** card's raw payload into the log below. If A and B produce nothing, note any Console line mentioning `postMessage`, `sandbox` or `a2ui_action`.

## Results log

| probe | result | exact observation / error |
|---|---|---|
| `help` renders | | |
| Q1 `iframe-js`: JS pill green? | | |
| Q1 `iframe-js`: tabs switch? | | |
| Q2 `iframe-canvas` | | |
| Q3 button A (`parent.postMessage`) | | |
| Q3 button B (`window.top.postMessage`) | | |
| Q3 button C (native `MaterialButton`) | | |
| Q3 raw payload shape | | |
| Q4 `iframe-200kb` | | |
| Console errors, if any | | |

## What the results mean

| outcome | design |
|---|---|
| JS runs, `postMessage` arrives | Planned design: tabs and follow-up chips inside the explainer page. |
| JS runs, `postMessage` doesn't arrive | Tabs in the page; follow-ups as native `MaterialButton`s under the frame. |
| JS blocked | Static HTML per level inside native `MaterialTabs`; follow-ups as native buttons. Diagram stays inline SVG. |
| 200 KB fails | Lower the page budget and re-test at 100 KB. |
