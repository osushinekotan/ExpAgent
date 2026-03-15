---
name: backlog
description: This skill should be used when the user asks to "create a task", "list tasks", "show the board", "check project status", "add a milestone", "create a document", "record a decision", "search backlog", "initialize backlog", "show overview", "manage drafts", "update task status", or any project management operation using the backlog CLI. Also use this skill when the user starts working on a task, finishes a task, or wants to check what to work on next — backlog is the single source of truth for project context across sessions. Provides workflows for the Backlog.md project management system.
---

# Backlog - Project Management CLI

## Overview

This skill provides workflows for managing projects using the `backlog` CLI tool. Backlog enables local-first, markdown-based project management with tasks, milestones, documents, decisions, and Kanban boards.

## Important: Status Values

Status values are **case-sensitive and contain spaces**. Always quote them:

| Status          | Usage                     |
| --------------- | ------------------------- |
| `"To Do"`       | Default for new tasks     |
| `"In Progress"` | Currently being worked on |
| `"Done"`        | Completed                 |

**Wrong:** `-s "in-progress"`, `-s todo`, `-s "in progress"`
**Correct:** `-s "In Progress"`, `-s "To Do"`, `-s "Done"`

## Quick Start

To check if backlog is installed:

```bash
backlog --version
```

### Initialize a New Project

To set up backlog in a repository:

```bash
backlog init [projectName]
```

This creates a `backlog/` directory with the project structure. Run this once per repository before using other commands.

## Session Continuity (1 Task = 1 Session)

Each task should capture enough context so that a new Claude session (or a different person) can pick up the work seamlessly by reading the task. Think of each task as a handoff document.

### When starting work on a task

1. Read the task to load context: `backlog task view TASK-1 --plain`
2. Mark it as in progress: `backlog task edit TASK-1 -s "In Progress"`
3. Record your plan if not already set: `backlog task edit TASK-1 --plan "description of approach"`

### While working

Append implementation notes as you make progress — key decisions, files changed, issues encountered:

```bash
backlog task edit TASK-1 --append-notes "Refactored auth module to use JWT. Changed files: src/auth.py, src/middleware.py"
```

### When finishing a task

1. Check off acceptance criteria: `backlog task edit TASK-1 --check-ac 1 --check-ac 2`
2. Write a final summary so the next session knows what was done and any follow-ups:
   ```bash
   backlog task edit TASK-1 --final-summary "Implemented JWT auth. TODO: add refresh token support (see TASK-5)"
   ```
3. Mark as done: `backlog task edit TASK-1 -s "Done"`

### Key fields for session continuity

| Field                | Flag              | Purpose                              |
| -------------------- | ----------------- | ------------------------------------ |
| Description          | `-d`              | What needs to be done and why        |
| Acceptance Criteria  | `--ac`            | Concrete conditions for "done"       |
| Implementation Plan  | `--plan`          | How to approach the task             |
| Implementation Notes | `--append-notes`  | Progress log (append, don't replace) |
| Final Summary        | `--final-summary` | What was done, outcomes, follow-ups  |
| References           | `--ref`           | Relevant URLs, PRs, file paths       |

## Core Workflows

### Task Management

Create, list, edit, and track tasks:

```bash
# Create a task
backlog task create "Task title" -d "Description" --priority high

# Create with acceptance criteria and dependencies
backlog task create "Task title" --ac "Criterion 1" --ac "Criterion 2" --dep TASK-1,TASK-2

# Create as a subtask
backlog task create "Subtask title" -p TASK-1

# List all tasks (interactive UI)
backlog task list

# List with filters (use --plain for non-interactive output)
backlog task list -s "In Progress" --priority high -m "v1.0" --plain

# View task details
backlog task view TASK-1 --plain

# Edit task
backlog task edit TASK-1 -s "In Progress"
backlog task edit TASK-1 --priority high -a "username"
backlog task edit TASK-1 --check-ac 1 --check-dod 2

# Archive completed task
backlog task archive TASK-1
```

### Draft Management

Drafts are preliminary task ideas, promoted to tasks when ready:

```bash
# Create a draft
backlog draft create "Draft idea"

# List drafts
backlog draft list

# Promote draft to task
backlog draft promote DRAFT-1

# Demote task back to draft
backlog task demote TASK-1
```

### Kanban Board

Visualize task status:

```bash
# Show board (interactive)
backlog board

# Vertical layout
backlog board --vertical

# Group by milestone
backlog board -m

# Export to markdown
backlog board export kanban.md
```

### Milestones

Track project phases. There is no `milestone create` CLI command — create milestone files directly in `backlog/milestones/`:

```bash
# Create a milestone by writing the file directly
# IMPORTANT: File name must match pattern "m-{N}.md" (e.g., m-1.md, m-2.md)
# Frontmatter must have "id" and "title" fields. Content uses "## Description" section.
cat > backlog/milestones/m-1.md << 'EOF'
---
id: m-1
title: v1.0
---

## Description

Milestone description here.
EOF

# Assign milestone to a task (use milestone title as label)
backlog task create "Some task" # then reference in frontmatter: milestone: "v1.0"
backlog task edit TASK-1  # milestone field in task frontmatter links to milestone title

# List milestones with completion status
backlog milestone list
backlog milestone list --plain

# Archive completed milestone
backlog milestone archive "v1.0"
```

### Documents

Store project documentation:

```bash
# Create a document
backlog doc create "Architecture Overview"

# List documents
backlog doc list

# View document (opens pager - for interactive use)
backlog doc view DOC-1

# Read document programmatically (doc view uses a pager, so read the file directly)
# Files are in backlog/docs/ with format: "doc-N - Title.md"
cat "backlog/docs/doc-1 - Architecture-Overview.md"
```

### Decisions

Record architectural and project decisions:

```bash
# Create a decision record
backlog decision create "Use PostgreSQL for storage"
```

### Search

Search across tasks, documents, and decisions:

```bash
# Full-text search
backlog search "authentication"

# Filter by type
backlog search "auth" --type task --status "todo" --priority high

# Limit results
backlog search "query" --limit 5 --plain
```

### Project Overview

Display project statistics and metrics:

```bash
backlog overview
```

### Task Dependencies and Sequences

View execution order based on task dependencies:

```bash
# List computed sequences
backlog sequence list
backlog sequence list --plain
```

## Key Concepts

### Task Lifecycle

```
Draft -> Task ("To Do") -> "In Progress" -> "Done" -> archived
```

- **Draft**: Preliminary idea, not yet a committed task
- **promote**: Move draft to task
- **demote**: Move task back to draft
- **archive**: Remove completed task from active view

### Task Fields

| Field                | Flag                         | Description                                                       |
| -------------------- | ---------------------------- | ----------------------------------------------------------------- |
| Title                | positional / `-t`            | Task name                                                         |
| Description          | `-d` / `--desc`              | Detailed description                                              |
| Status               | `-s`                         | `"To Do"`, `"In Progress"`, `"Done"` (must quote, case-sensitive) |
| Priority             | `--priority`                 | high, medium, low                                                 |
| Assignee             | `-a`                         | Person responsible                                                |
| Labels               | `-l` / `--add-label`         | Categorization tags                                               |
| Parent               | `-p`                         | Parent task ID for subtasks                                       |
| Dependencies         | `--dep`                      | Comma-separated task IDs                                          |
| Acceptance Criteria  | `--ac`                       | Checkable criteria                                                |
| Definition of Done   | `--dod`                      | Checkable completion items                                        |
| Implementation Plan  | `--plan`                     | How to implement                                                  |
| Implementation Notes | `--notes` / `--append-notes` | Progress log (prefer `--append-notes` to preserve history)        |
| Final Summary        | `--final-summary`            | Summary after completion, follow-ups                              |
| References           | `--ref`                      | URLs, PRs, or file paths                                          |
| Documentation        | `--doc`                      | Documentation links                                               |

### Interactive vs Plain Output

Some commands support `--plain` for plain text output suitable for piping or scripting: `task list`, `task view`, `milestone list`, `search`, `sequence list`. Always use `--plain` when reading output programmatically — interactive UI can break parsing.

## Best Practices

### Task Granularity

タスクはコミット1つ分程度の小ささに切る。大きな作業は親タスク＋サブタスクに分解する。

```bash
# 親タスク: 大きな機能単位
backlog task create "JWT認証の実装" -d "ユーザー認証をJWTベースに移行" --priority high

# サブタスク: コミット1つで完結する単位
backlog task create "JWTトークン生成ユーティリティの追加" -p TASK-1
backlog task create "認証ミドルウェアの実装" -p TASK-1 --dep TASK-1.1
backlog task create "既存エンドポイントへの認証適用" -p TASK-1 --dep TASK-1.2
```

タスクが大きすぎるサイン: 「〜と〜をやる」と説明に「と」が入る場合は分割を検討する。

### Dependencies

依存関係は作業順序を明確にし、次に何をすべきかを判断する材料になる。タスク作成時に設定し、作業中に新たな依存が見つかったら都度更新する。

```bash
# 依存の設定（作成時）
backlog task create "APIテスト追加" --dep TASK-1.2,TASK-1.3

# 依存の更新（作業中に判明した場合）
backlog task edit TASK-3 --dep TASK-1.2,TASK-2

# 実行順序の確認
backlog sequence list --plain
```

### General

- **Always quote status values**: `-s "In Progress"`, not `-s in-progress`
- **Use `--plain` flag** when reading output programmatically (supported by: `task list`, `task view`, `milestone list`, `search`, `sequence list`)
- **Write for the next session**: Every task should have enough context (description, plan, notes, final-summary) that someone reading it cold can continue the work
- **Use `--append-notes`** instead of `--notes` to preserve history — `--notes` replaces existing content
- Set acceptance criteria (`--ac`) on tasks to define clear completion conditions
- Check `backlog overview` before planning new work to understand project state
- Use `backlog search` to find related tasks before creating duplicates

## Reference

For detailed command options and all available flags, see `references/commands.md`.
