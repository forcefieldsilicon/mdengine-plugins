---
name: forcefield-studies
description: >-
  Follow a ForceField Silicon study from the customer's own Claude through the
  studies connector. Use it when the request mentions a study key, a SOW, a
  ForceField Silicon study, "my study", campaign status, the campaign matrix,
  tiers, the study report, what is blocked or when prep is scheduled, a change
  order, or asking for a new study with campaign_request. Says how to connect,
  the first three calls, what each tool returns and never does, the launch
  grant, the claim scope and the honesty rule.
user-invocable: true
compatibility: any OS (hosted MCP); nothing to install
metadata:
  author: ForceField Silicon (Gitinama Inc.)
  version: "0.1.0"
license: Apache-2.0
---

# ForceField Silicon studies

## Who this is for

A named study customer. You hold a study key, issued with your SOW. A study key never
comes from a credit pack. If your user has a credit-pack key, this is the wrong door: use
the `mdengine` skill and the `mdengine-cloud` connector instead.

A study is fixed scope. It has a campaign grid, numbers with a stated uncertainty, a
compromises sheet on the front page, IP assigned to the customer, and a quote before any
run. ForceField Silicon runs the launch, setup and run commands under the SOW. The
customer's Claude watches the study and reads the results.

## Connect

The connector is a Streamable HTTP MCP server named `com.forcefieldsilicon/dsuite`, titled
"ForceField Silicon studies", at `https://api.forcefieldsilicon.com/dsuite/mcp`.

- **Claude Code.** Run
  `claude mcp add --scope user --transport http forcefield-studies https://api.forcefieldsilicon.com/dsuite/mcp`,
  then type `/mcp`, pick `forcefield-studies`, and press Authenticate.
- **claude.ai.** Settings, Connectors, Add custom connector, with that URL.
- **Claude desktop.** Settings, Connectors, Add custom connector, with that URL.

Sign-in is the same consent page as the GPU tier. Paste the study key there once. Never
paste a key in chat.

A GPU-tier key at the studies URL is refused with a sentence that names the GPU connector.
A study key at the GPU URL is refused with a sentence that names the studies connector.
If you see either refusal, the key is fine. It is at the wrong door.

## The first three calls

1. `campaign_list`. The studies this key can see. Note the campaign id.
2. `campaign_status` with that id. Where the study stands: cells done, running, pending
   and blocked.
3. `campaign_matrix` with that id. The grid, cell by cell, with tiers and uncertainty
   bands for the cells that have landed.

Then read the compromises sheet in `campaign_report` before you say anything about a number.

## What each tool returns, and what it never does

| Tool | Returns | Never |
| --- | --- | --- |
| `campaign_list` | The studies on this key | Shows another customer's study |
| `campaign_status` | Progress of one study: done, running, pending, blocked | Starts or stops a run |
| `campaign_matrix` | The grid with tiers and bands for landed cells | Turns tiers into a rank order |
| `campaign_report` | The report, with the compromises sheet on the front page | Reports a number without its band |
| `campaign_prep` | What is blocked and when its prep is scheduled | Promises a date the prep schedule does not show |
| `campaign_wait` | Results that have landed since you last looked | Spends anything |
| `campaign_quote` | Study terms: cells included under the SOW, cells pending, whether a change order is needed | Shows GPU prices |
| `campaign_request` | A request id for a new study or a change, the tier that fits, the price band, what we need | Starts any work before a quote |

None of these tools launches, sets up or runs anything. A cell outside the SOW shows in
`campaign_quote` as needing a change order. Read that back to your user. Do not work
around it.

## The launch grant

Some customers want to launch cells themselves. For them there is a launch grant with a
written compute allowance, agreed in writing and added to the SOW. With the grant,
`campaign_launch` appears on the connector, and every call needs `confirm_spend_usd`
against the allowance. Without the grant, the tool does not appear, so do not look for it.

## Ask for a new study

Call `campaign_request`. It is the same tool on both connectors, so a credit-pack user and
a study customer ask the same way. Send the customer type, the user's question, what they
already have, the grid in words, their data rules and their contact email. Read back the
request id, the tier that fits, the price band and what we need. Then gather what we need.

Price bands:

- **Drug discovery.** A pilot column is $2,500, credited against a full grid at $7,500.
  Compute is included.
- **Every other customer type.** A person confirms scope and price within one business day.

The quote comes before any run.

## Claim scope

These sentences hold for every study. Say them when the question comes near them.

- Tiers say which question a study answers. They are not a rank order.
- Preparing structures and inputs sets the schedule, not GPU compute.
- No study reports an absolute binding affinity. Results are relative within the grid.

## Honesty rule for you, their Claude

- Read the compromises sheet first. State the compromises next to the numbers, every time.
- Never invent a rank order. Two cells sit in different tiers only when their bands do not
  overlap. Cells in one tier are not ordered.
- Never report a number without its uncertainty band.
- A blocked cell is "needs prep", never a weak result. Say when `campaign_prep` schedules it.
- When a question is outside the grid, say "not in this study". Do not estimate an answer.
  Offer `campaign_request` if the user wants it studied.
- Never promise a date, a price or a result the tools do not show.
- If a tool returns an error or a refusal, read the sentence back as it is.
