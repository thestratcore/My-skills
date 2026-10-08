---
name: linkedin-post
description: Post an image with a text caption to Lukáš's personal LinkedIn profile. Use whenever he asks to post/publish/share something to LinkedIn, or points at a folder/image+text pair and says something like "post this on LinkedIn" — even if he doesn't spell out every step. Handles locating the image and caption files, reading them, and calling the linkedin MCP tool to publish.
---

# LinkedIn image post

Publishes one image plus a text caption as a single post on the user's own
LinkedIn profile, via the `mcp__linkedin__create-post` tool.

## 1. Resolve the inputs

The user gives you either:
- **A folder path** (most common) — e.g. `/Users/admin/Pictures/Photoshop/StratCore/mcp_posts`.
  Look for an image (`.jpg`/`.jpeg`/`.png`/`.gif`/`.webp`) and a same-stem `.txt` file
  (e.g. `MCP_01.jpg` + `MCP_01.txt`). If there are several image/text pairs in the
  folder and it's not obvious which one he means, ask which one.
- **Explicit file paths**, or the caption typed inline instead of a file — use whatever
  he gives you directly.

## 2. Read both files before posting

Read the image (to see what you're about to publish) and the text file's exact
contents. Never post something you haven't actually looked at. The `.txt` file's
content becomes the post body **verbatim** — don't summarize, translate, or edit it
unless the user asks you to.

Write a one-line alt-text description of the image for accessibility (what's visibly
in it — you don't need to ask the user for this).

## 3. Post it

Call `mcp__linkedin__create-post` with:
- `content` — the caption text, verbatim
- `imagePath` — absolute path to the image
- `altText` — your short description from step 2

Give a brief one-line summary of what you're about to post (e.g. "Posting MCP_02.jpg
with the caption from MCP_02.txt to your LinkedIn — go ahead") only if something about
the request is ambiguous. Otherwise just post it — the user invoking this skill is the
approval; this is his own profile and he's already established he doesn't want a
confirmation prompt for this recurring task. Report back with a short confirmation once
LinkedIn returns success.

## If the tool is missing or fails auth

`mcp__linkedin__create-post` and `mcp__linkedin__authenticate` come from a local MCP
server at `/Users/admin/Documents/CodeProjects/LinkedInMCP-server` (custom stdio server,
token cached at `~/.linkedin-mcp/tokens.json`).

- **Tool not found at all**: the MCP server may need reconnecting. Ask the user to run
  `/mcp` and reconnect `linkedin` (you can't trigger this yourself).
- **Auth error / expired token**: call `mcp__linkedin__authenticate` (opens a browser
  for a one-time LinkedIn login), then retry `create-post`.
