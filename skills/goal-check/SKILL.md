---
name: goal-check
description: Before telling the owner that work is done, have a fresh agent check the real result against the owner's own words, goal by goal, with evidence it gathered itself. Use before the final report of any task that changed something, and when the Stop hook asks for it.
---

# Goal check

"Done" from the agent that did the work proves little. It checks what it built, not what was asked, and it reads its own summary as fact. A fresh agent that sees only the request and the real outputs catches the gap.

## 1. Brief a fresh agent

Spawn a new `general-purpose` agent, never a fork: a fork inherits your reading of the task. Its brief holds only:

- The owner's request, quoted word for word, plus any later owner messages that changed it. Not your paraphrase.
- Where the real outputs are: the PR or branch and commit, files, a URL, a data row, a command that shows the result.
- "Do not edit anything. PR descriptions, commit messages and summaries are claims, not evidence."

Leave out your summary of what you did, your checklist and your own test results.

## 2. What the checker does

1. Write the request as goals a reader could check, one line each. State outcomes ("an article cannot reach `ready` without a record of the sources checked"), not steps ("edited the review skill"). Include the purpose behind the ask when the request states or plainly implies it, because that is what usually goes missing.
2. For each goal, look at the real thing: read the diff, run the command, open the page, read the value. Try it the way the owner will use it.
3. Return this, and nothing else:

```
| Goal | Verdict | Evidence the checker gathered itself |
| --- | --- | --- |
| ... | met / not met / could not check | file:line, a command and its output, a URL and the quoted text |

Asked for but covered by no goal: ...
Claims in the work that the evidence contradicts: ...
```

A verdict with no evidence counts as "could not check".

## 3. Act on the result

- **not met:** fix it, then run a new goal check with a new agent.
- **could not check:** check it yourself and show the evidence, or tell the owner it is unverified and why.
- Report as done only the goals that are met with evidence. List the rest as open. Never round "could not check" up to done.

## How it differs from other checks

- Checking your own work (the prove-it-works principle) comes first. This check follows it, done by an agent that did not do the work.
- `interrogate` stress-tests a design. This checks the finished result against the request.
- A domain review with its own checklist, such as an article review, still runs. This checks that the whole ask was met.
