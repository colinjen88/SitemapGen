---
description: Auto-approve all safe commands and proceed without waiting for user confirmation
---

// turbo-all

This workflow enables automatic approval for all terminal commands in the SitemapGen project.

When this workflow is active:
1. All `run_command` tool calls will have `SafeToAutoRun` set to `true`
2. No need to wait for user confirmation on each step
3. Build, test, and git commands will execute automatically

To disable, simply delete this file or remove the `// turbo-all` annotation.
