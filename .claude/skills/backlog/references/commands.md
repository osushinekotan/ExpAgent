# Backlog CLI - Full Command Reference

## backlog init

Initialize backlog project in a repository.

```bash
backlog init [projectName] [options]
```

| Option                        | Description                                                    |
| ----------------------------- | -------------------------------------------------------------- |
| `--agent-instructions <list>` | Comma-separated: claude, agents, gemini, copilot, cursor, none |
| `--check-branches <bool>`     | Check task states across active branches (default: true)       |
| `--include-remote <bool>`     | Include remote branches when checking (default: true)          |
| `--branch-days <number>`      | Days to consider branch active (default: 30)                   |
| `--bypass-git-hooks <bool>`   | Bypass git hooks when committing (default: false)              |
| `--zero-padded-ids <number>`  | Digits for zero-padding IDs (0 to disable)                     |
| `--default-editor <editor>`   | Default editor command                                         |
| `--web-port <number>`         | Web UI port (default: 6420)                                    |
| `--auto-open-browser <bool>`  | Auto-open browser for web UI (default: true)                   |
| `--integration-mode <mode>`   | AI tool connection mode: mcp, cli, or none                     |
| `--task-prefix <prefix>`      | Custom task prefix, letters only (default: task)               |
| `--defaults`                  | Use default values for all prompts                             |

## Task Commands

### backlog task create

```bash
backlog task create [title] [options]
```

| Option                             | Description                                |
| ---------------------------------- | ------------------------------------------ |
| `-d, --description <text>`         | Task description (multi-line supported)    |
| `--desc <text>`                    | Alias for --description                    |
| `-a, --assignee <assignee>`        | Assign to person                           |
| `-s, --status <status>`            | Set initial status                         |
| `-l, --labels <labels>`            | Add labels                                 |
| `--priority <priority>`            | high, medium, low                          |
| `--plain`                          | Plain text output                          |
| `--ac <criteria>`                  | Acceptance criteria (repeatable)           |
| `--acceptance-criteria <criteria>` | Alias for --ac                             |
| `--dod <item>`                     | Definition of Done item (repeatable)       |
| `--no-dod-defaults`                | Disable DoD defaults                       |
| `--plan <text>`                    | Implementation plan                        |
| `--notes <text>`                   | Implementation notes                       |
| `--final-summary <text>`           | Final summary                              |
| `--draft`                          | Create as draft                            |
| `-p, --parent <taskId>`            | Parent task ID (subtask)                   |
| `--depends-on <taskIds>`           | Dependencies (comma-separated, repeatable) |
| `--dep <taskIds>`                  | Shortcut for --depends-on                  |
| `--ref <reference>`                | Reference URL/path (repeatable)            |
| `--doc <documentation>`            | Documentation URL/path (repeatable)        |

### backlog task list

```bash
backlog task list [options]
```

| Option                        | Description                                                         |
| ----------------------------- | ------------------------------------------------------------------- |
| `-s, --status <status>`       | Filter by status: `"To Do"`, `"In Progress"`, `"Done"` (must quote) |
| `-a, --assignee <assignee>`   | Filter by assignee                                                  |
| `-m, --milestone <milestone>` | Filter by milestone (closest match)                                 |
| `-p, --parent <taskId>`       | Filter by parent task ID                                            |
| `--priority <priority>`       | Filter by priority                                                  |
| `--sort <field>`              | Sort by field (priority, id)                                        |
| `--plain`                     | Plain text output                                                   |

### backlog task edit

```bash
backlog task edit [taskId] [options]
```

| Option                             | Description                              |
| ---------------------------------- | ---------------------------------------- |
| `-t, --title <title>`              | Update title                             |
| `-d, --description <text>`         | Update description                       |
| `-a, --assignee <assignee>`        | Update assignee                          |
| `-s, --status <status>`            | Update status                            |
| `-l, --label <labels>`             | Set labels                               |
| `--priority <priority>`            | Set priority                             |
| `--ordinal <number>`               | Set custom ordering                      |
| `--plain`                          | Plain text output                        |
| `--add-label <label>`              | Add a label                              |
| `--remove-label <label>`           | Remove a label                           |
| `--ac <criteria>`                  | Add acceptance criteria (repeatable)     |
| `--dod <item>`                     | Add DoD item (repeatable)                |
| `--remove-ac <index>`              | Remove AC by 1-based index (repeatable)  |
| `--remove-dod <index>`             | Remove DoD by 1-based index (repeatable) |
| `--check-ac <index>`               | Check AC by index (repeatable)           |
| `--check-dod <index>`              | Check DoD by index (repeatable)          |
| `--uncheck-ac <index>`             | Uncheck AC by index (repeatable)         |
| `--uncheck-dod <index>`            | Uncheck DoD by index (repeatable)        |
| `--acceptance-criteria <criteria>` | Set all AC (comma-separated)             |
| `--plan <text>`                    | Set implementation plan                  |
| `--notes <text>`                   | Set implementation notes (replaces)      |
| `--final-summary <text>`           | Set final summary (replaces)             |
| `--append-notes <text>`            | Append to notes (repeatable)             |
| `--append-final-summary <text>`    | Append to final summary (repeatable)     |
| `--clear-final-summary`            | Remove final summary                     |
| `--depends-on <taskIds>`           | Set dependencies                         |
| `--dep <taskIds>`                  | Shortcut for --depends-on                |
| `--ref <reference>`                | Set references (repeatable)              |
| `--doc <documentation>`            | Set documentation (repeatable)           |

### backlog task view

```bash
backlog task view <taskId> [--plain]
```

### backlog task archive

```bash
backlog task archive <taskId>
```

### backlog task demote

```bash
backlog task demote <taskId>
```

Move a task back to drafts.

## Draft Commands

### backlog draft create

```bash
backlog draft create <title> [options]
```

| Option                      | Description |
| --------------------------- | ----------- |
| `-d, --description <text>`  | Description |
| `-a, --assignee <assignee>` | Assignee    |
| `-s, --status <status>`     | Status      |
| `-l, --labels <labels>`     | Labels      |

### backlog draft list

```bash
backlog draft list [--plain]
```

### backlog draft view

```bash
backlog draft view <taskId> [--plain]
```

### backlog draft promote

```bash
backlog draft promote <taskId>
```

### backlog draft archive

```bash
backlog draft archive <taskId>
```

## Board Commands

```bash
backlog board [options]
backlog board view [options]
backlog board export [filename]
```

| Option                  | Description                  |
| ----------------------- | ---------------------------- |
| `-l, --layout <layout>` | horizontal or vertical       |
| `--vertical`            | Shortcut for vertical layout |
| `-m, --milestones`      | Group by milestone           |

## Milestone Commands

```bash
backlog milestone list [--plain]
backlog milestone archive <name>
```

## Document Commands

```bash
backlog doc create <title> [-p <path>] [-t <type>]
backlog doc list [--plain]
backlog doc view <docId>
```

## Decision Commands

```bash
backlog decision create <title>
```

## Search

```bash
backlog search [query] [options]
```

| Option                  | Description              |
| ----------------------- | ------------------------ |
| `--type <type>`         | task, document, decision |
| `--status <status>`     | Filter by status         |
| `--priority <priority>` | Filter by priority       |
| `--limit <number>`      | Limit results            |
| `--plain`               | Plain text output        |

## Other Commands

```bash
backlog overview                    # Project statistics
backlog sequence list [--plain]     # Task dependency sequences
backlog cleanup                     # Move completed tasks to completed folder
backlog config get <key>            # Get config value
backlog config set <key> <value>    # Set config value
backlog config list                 # List all config
backlog agents --update-instructions  # Update agent instruction files
backlog browser                     # Open web UI (Ctrl+C to stop)
```
