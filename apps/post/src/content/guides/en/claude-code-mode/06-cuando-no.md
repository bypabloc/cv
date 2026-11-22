**06**

# When it doesn't save (and is slower)

[← Index](README.md)

---

### Local files the shell already handled

If in normal mode Claude already wrote an `rg` or a Python script that walked the files in a single process, Code Mode has no trips to save. Worse: sometimes the script switches strategy and does **one read per file**. With hundreds of files, each read goes through permissions and hooks, and the task takes 1.4 to 2.8 times longer **[published]**.

| Task | What happens |
| :-- | :-- |
| Finding broken links in hundreds of Markdown files | Normal mode uses a one-pass script; Code Mode can end up with hundreds of `Read`s |
| Rule-based mass edit across 100 files | A bit cheaper, much slower |
| Answering a question about one file | Only the fixed tool saving |

### Blocks that print the raw data

If the script returns everything it read, the context grows as much as or more than in normal mode. In the published tests, on file tasks the context **added during the work** grew with Code Mode in 14 of 16 comparisons, even when total tokens dropped thanks to the fixed saving **[published]**.

### Filters that hide data

The filter is the point of the mode and also its risk: if the script drops something by mistake, **the model never finds out**. In the published tests, a keyword filter left out 4 of 9 tickets, and one answer claimed to have read them all while two were missing **[published]**.

How to protect yourself:

- Ask for counts per step (how many it read, how many it filtered, how many remain).
- Ask for the list of what failed or was dropped.
- For reading and judging free text, don't trust an "I read them all".

### Small models

With Haiku 5.5 results were more erratic: one run searched the wrong folder and 344 of 349 commands failed, even though the task "passed" **[published]**. With a small model, check the result more carefully.

### In my case

I saw it in my repos' file audits: when the task was reviewing many Markdown files or applying a mechanical change, normal mode already solved it with a one-pass script and Code Mode didn't improve it; in some runs it took longer. For that kind of task, I now explicitly ask "do it with a single shell command" or open a session without the mode.

`when-not` `performance` `risks`
