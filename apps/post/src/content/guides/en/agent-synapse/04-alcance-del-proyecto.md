**04**

# Project scope and recoverable deletes

[← Index](README.md)

---

### What "inside the project" means

The `structure.outside_project` rule blocks modifying paths outside the allowed roots. Those roots come from git, not from the command text:

- The project repo's toplevel (`CLAUDE_PROJECT_DIR` or each agent's equivalent; otherwise the `cwd`).
- The superproject, if the repo is a submodule.
- Worktrees of the same repo, even if they live in another folder.

To know which path a command targets, Synapse follows `cd` (including `cd -`), resolves `$HOME`, `~` and variables assigned earlier on the same line, and skips prefixes like `sudo`, `VAR=value` or `timeout N`. So `p=~/; rm -rf "$p/other"` is seen for what it is.

### Disposable means no asking

Some paths hold content that can be lost without consequences. Operations on them are approved automatically:

| Type | Examples |
| :-- | :-- |
| Temporary | `./tmp/**`, the agent session's scratchpad, `*.log` |
| Build artifacts | `dist/`, `build/`, `.turbo/`, `target/`, `.cache/`, `node_modules/` |
| Untracked files | A file (not a directory) the agent just created |
| Interpreter caches | `__pycache__` and similar, ignored by git |

A detail that took a fix: a path ignored by a **parent** repo (for example, one that versions your home folder) doesn't count as disposable. What's ignored is evaluated in the project's repo.

### Deleting what git can restore

Deleting tracked, clean files (no local changes) is approved automatically: git can bring them back. Along with the approval, the agent receives how to restore them:

```text
git -C ~/code/my-app checkout -- src/legacy/
```

The `structure.git_recoverable_delete` rule had to close several holes before it was safe:

- An `rm -rf link/` on a tracked symlink could delete outside the repo: it's no longer auto-approved.
- Only interpreter caches count as regenerable ignored content; anything else ignored may be work.
- A compound command with subcommands that aren't deletes goes back to `ask`.
- Repos with their own `.git` and files marked `skip-worktree` or `assume-unchanged` are excluded.

### Cloning or touching another repo

`git clone` and `git -C <other-path>` outside the project also count as writes out of scope. If a task needs another repo, the way is to open a session in that repo, where it'll be the project.

### In my case

I work with several worktrees per repo and, at first, each session in a worktree saw the main checkout as "outside the project". Computing the root from git (toplevel, superproject and worktrees) solved it. The lesson from the recoverable-delete rule: an auto-allow has to prove that **everything** affected can be recovered; symlinks, parent repos and compound commands are exactly where work gets lost.

`scope` `git` `worktrees` `deletes`
