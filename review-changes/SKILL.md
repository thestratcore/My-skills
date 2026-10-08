---
name: review-changes
description: Conducting professional and thorough code reviews for local development. This skill is manually triggered — do not auto-load.
disable-model-invocation: true
---

# Code Reviewer

This skill guides thorough, professional code reviews of local changes (working tree, staged, or recent commits).

## Workflow

### 1. Gather Context

The user will tell you what to review — uncommitted changes, staged files, a specific commit range, etc. Run the appropriate `git diff` or `git show` command as instructed. Don't guess or run extra git commands unless you need them.

Once you have the diff, skim the surrounding code in any files you're unfamiliar with. A suggestion that contradicts the project's existing style — however "correct" in the abstract — is a bad suggestion. Reviewing a diff without understanding the codebase it lives in leads to shallow, unhelpful feedback.

### 2. Analyze the Changes

Work through each of these dimensions. Not every dimension will surface findings for every diff — that's fine. The goal is a thorough mental pass, not a checklist where every box must have a comment.

**Correctness** — Does the code do what it intends to? Look for logic errors, off-by-one mistakes, incorrect conditions, race conditions, broken control flow. Trace the important paths mentally; don't just skim.

**Edge cases and error handling** — What happens with empty inputs, null values, boundary conditions, concurrent access, or unexpected types? Is error handling present where it should be, and does it fail gracefully rather than silently swallowing problems?

**Security** — Are there injection risks (SQL, XSS, command injection)? Hardcoded secrets? Improper input validation? Overly permissive access? Think about what a malicious or unexpected input could do.

**Performance** — Are there unnecessary allocations, N+1 queries, unbounded loops, missing indexes, or work being repeated that could be cached or batched? Only flag performance issues that matter at the likely scale of the code; don't micro-optimize trivially.

**Maintainability** — Is the code well-structured? Will someone unfamiliar with this change be able to understand it in six months? Look at naming, modularity, coupling, and whether the change respects the existing architecture or fights against it.

**Readability** — Are names descriptive? Is the code flow easy to follow? Are comments present where logic is non-obvious (and absent where the code speaks for itself)? Does formatting match the project's style?

**Test coverage** — Are the changes tested? If tests exist, do they cover the meaningful cases (not just the happy path)? If tests are missing, suggest specific test cases that would add real value — not vague "add more tests" comments.

### 3. Deliver Feedback

Structure your review as follows:

**Summary** — A brief, high-level take: what the change does, your overall impression, and your recommendation. Lead with this so the author immediately knows where they stand.

**Findings** — Group issues by severity:

- *Critical* — Bugs, security vulnerabilities, data loss risks, breaking changes. These block merging/committing.
- *Improvements* — Suggestions that would meaningfully improve quality, performance, or maintainability. Worth addressing but not blockers.
- *Nitpicks* — Style, naming, minor consistency issues. Prefix these with "Nit:" so the author knows they're low-priority. Keep these brief and don't overload the review with them.

For each finding, include:
- The file and relevant location
- What the issue is
- *Why* it matters (not just "this is wrong" — explain the consequence)
- A suggested fix or direction when possible

**Conclusion** — One of:
- ✅ **Approved** — Changes look good. Acknowledge specific things done well.
- 🔧 **Request Changes** — Summarize what needs to change before this is ready.

### Tone

Be constructive and direct. Explain the reasoning behind your suggestions — a reviewer who explains *why* teaches; one who just says "change this" frustrates. Frame suggestions as collaborative ("have you considered..." or "this could be simplified by...") rather than commanding.

When approving, call out specific things done well. Good work deserves recognition, and it reinforces good patterns.

When requesting changes, be clear about what's blocking vs. what's optional. Nobody wants to guess which comments are "fix this or else" and which are "take it or leave it."
