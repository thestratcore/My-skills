# My-skills

A curated collection of [Claude](https://claude.com/claude-code) / Codex **Agent Skills** used across Stratcore projects. Each folder is a self-contained skill — a `SKILL.md` describing when it triggers and how it behaves, plus any supporting scripts, templates, and reference files the skill needs.

## About

Skills extend an AI coding agent with reusable, domain-specific expertise. Instead of re-explaining a workflow every time, the agent loads the matching skill on demand and follows its instructions — whether that's writing an article in a defined voice, modeling a Power BI dataset, or building an MCP server. This repository is Stratcore's working toolbox of such skills, spanning content creation, web and app development, data and BI, legal, and knowledge-base operations. Drop a folder into your agent's skills directory to use it.

## Skills

### Writing & content
| Skill | Description |
|-------|-------------|
| [article-writing](article-writing) | Write articles, guides, blog posts, and newsletters in a distinctive, example-derived voice. |
| [crosspost](crosspost) | Distribute content across X, LinkedIn, Threads, and Bluesky, adapted per platform. |
| [marketing-campaign](marketing-campaign) | End-to-end multi-channel campaign planning: positioning, landing copy, emails, social, and ads. |
| [market-research](market-research) | Market sizing, competitive analysis, and investor due diligence with source attribution. |
| [academic-paper-review](academic-paper-review) | Structured review, critique, and summary of academic papers and preprints. |
| [read-arxiv-paper](read-arxiv-paper) | Read and work from an arXiv paper given its URL. |
| [research-paper-writing](research-paper-writing) | Write ML papers for NeurIPS/ICML/ICLR, from design to submission. |
| [cv-craft](cv-craft) | Build, tailor, and maintain Markdown CVs and their variants, with evidence-based claims and a linter. |
| [meeting-minutes](meeting-minutes) | Concise internal meeting minutes: attendees, decisions, action items with owners and due dates. |
| [pdf-report](pdf-report) | Generate branded Stratcore PDF reports (dark theme) for summaries and client deliverables. |
| [md-to-pdf](md-to-pdf) | Turn any Markdown file into a branded Stratcore PDF with cover page and running footer. |
| [writing-for-agents](writing-for-agents) | Write documents for agents: skills, `AGENTS.md`, and `CLAUDE.md`. |
| [agents-md](agents-md) | Create, review, or update concise `AGENTS.md`/`CLAUDE.md` instructions for code repositories. |
| [research-summarizer](research-summarizer) | Structured summaries of papers, articles, and reports with comparisons and citations. |
| [linkedin-post](linkedin-post) | Publish an image with a caption to Lukáš's personal LinkedIn profile. |

### Legal
| Skill | Description |
|-------|-------------|
| [draft-nda](draft-nda) | Draft a detailed NDA covering information types, jurisdiction, and clauses needing legal review. |
| [legal-response](legal-response) | Templated responses to common legal inquiries, with escalation checks. |
| [review-contract](review-contract) | Review a contract against a negotiation playbook: flag deviations, redline, assess business impact. |

### Business & strategy
| Skill | Description |
|-------|-------------|
| [chief-revenue-officer](chief-revenue-officer) | Revenue engine decisions: pricing, sales coverage, pipeline, churn, expansion, partnerships. |
| [coo-advisor](coo-advisor) | Operations leadership: process design, OKRs, operational cadence, scaling playbooks. |
| [good-strategy-bad-strategy](good-strategy-bad-strategy) | Formulate and audit strategy with Rumelt's kernel: diagnosis, guiding policy, coherent action. |
| [strategy-memo](strategy-memo) | Write a strategy memo that commits to a bet and states explicit non-goals. |

### Presentations & diagrams
| Skill | Description |
|-------|-------------|
| [keynote-slides](keynote-slides) | Build Keynote-style single-file HTML decks with brand templates and generated media. |
| [frontend-slides](frontend-slides) | Animation-rich HTML presentations from scratch or converted from PowerPoint. |
| [html-ppt-zhangzara-monochrome](html-ppt-zhangzara-monochrome) | Monochrome "grant-review" HTML slide decks for research briefs and committee proposals. |
| [drawio](drawio) | Generate draw.io diagrams and export them to PNG/SVG/PDF with embedded XML. |

### Web & UI development
| Skill | Description |
|-------|-------------|
| [frontend-design](frontend-design) | Aesthetic direction for distinctive, intentional UI — typography, layout, non-templated design. |
| [html-coder](html-coder) | Semantic HTML5 pages, forms, and interactive content with accessibility best practices. |
| [shadcn](shadcn) | Add, compose, and debug shadcn/ui components, registries, and presets. |
| [vercel-react-best-practices](vercel-react-best-practices) | React/Next.js performance patterns from Vercel Engineering for writing and reviewing code. |
| [brand-extract](brand-extract) | Extract a complete brand kit (colors, fonts, logo) from a live website by driving the browser. |
| [stratcore-website-inspection](stratcore-website-inspection) | Inspect a live site for content, brand-voice, visual, and accessibility issues; ranked punch-list. |
| [stratcore-design](stratcore-design) | Stratcore's dark-only design system: colors, type, assets, and UI kit for branded interfaces. |

### Apple platforms
| Skill | Description |
|-------|-------------|
| [swift-expert](swift-expert) | Build iOS/macOS/watchOS/tvOS apps: SwiftUI, async/await, actors, protocol-oriented design. |
| [swiftui-patterns](swiftui-patterns) | SwiftUI architecture: `@Observable` state, view composition, navigation, performance. |
| [apple-swiftui-specialist](apple-swiftui-specialist) | Best practices and idiomatic patterns for writing and reviewing SwiftUI. |
| [apple-swiftui-whats-new-27](apple-swiftui-whats-new-27) | New SwiftUI APIs, behaviors, and deprecations in the 2027 OS releases. |
| [apple-uikit-app-modernization](apple-uikit-app-modernization) | Modernize UIKit apps for multi-window environments and scene lifecycle. |
| [apple-test-modernizer](apple-test-modernizer) | Modernize test suites with Swift Testing, or migrate from XCTest. |
| [apple-device-interaction](apple-device-interaction) | Verify app behavior on device or simulator via screenshots, UI hierarchy, and touch. |
| [apple-audit-xcode-security-settings](apple-audit-xcode-security-settings) | Audit and enable security-oriented Xcode build settings, analyzer checkers, and hardening. |
| [apple-c-bounds-safety](apple-c-bounds-safety) | Guide to the C `-fbounds-safety` extension: annotations, adoption, and runtime debugging. |

### Data & platforms
| Skill | Description |
|-------|-------------|
| [appsmith](appsmith) | Build admin panels, internal tools, and dashboards on Appsmith with database integrations. |
| [erpnext](erpnext) | Frappe/ERPNext operating knowledge: DocType model, bench CLI, REST/RPC API, module map. |
| [mcp-builder](mcp-builder) | Create high-quality MCP servers in Python (FastMCP) or Node/TypeScript to integrate APIs. |
| [powerbi-modeling](powerbi-modeling) | Design optimized Power BI semantic models: star schemas, DAX measures, relationships, RLS. |
| [m-query](m-query) | Power Query M conventions for pbiflow models. |
| [jira-expert](jira-expert) | Jira projects, JQL, workflows, custom fields, automation, and reporting. |
| [connect-to-vps](connect-to-vps) | Context for connecting to and working on the Stratcore Hetzner VPS. |

### Knowledge & workflow ops
| Skill | Description |
|-------|-------------|
| [maintain-obsidian-vault](maintain-obsidian-vault) | Audit, normalize, and cross-link an Obsidian vault for human navigation and AI/RAG indexing. |
| [obsidian-vault-maintainer](obsidian-vault-maintainer) | Maintain an Obsidian memory-wiki vault with wikilinks, frontmatter, and Obsidian CLI awareness. |
| [n8n-docs-assistant](n8n-docs-assistant) | Answer n8n setup, credential, node, hosting, and API questions from current n8n docs. |
| [brainstorming](brainstorming) | Explore requirements and compare design alternatives before ambiguous feature work. |
| [grill-me](grill-me) | A relentless interview to sharpen a plan or design. |
| [grilling](grilling) | Stress-test a plan, decision, or idea through relentless questioning. |
| [review-changes](review-changes) | Thorough code review of local changes (manual trigger only). |
| [handoff](handoff) | Compact the current conversation into a handoff document for another agent. |
| [teach](teach) | Teach a new skill or concept within the current workspace. |
| [to-questionnaire](to-questionnaire) | Turn a decision you can't fully answer into a questionnaire for someone else. |
| [wait-what](wait-what) | Re-pitch a message that didn't land. |
| [skill-creator](skill-creator) | Create, edit, optimize, and evaluate skills — including trigger tuning and benchmarking. |
| [stratcore-skills-sync](stratcore-skills-sync) | Sync skills across MySKILLS, `~/.codex/skills`, and `~/.claude/skills`: missing copied everywhere, newest version wins. |

## Usage

Each skill lives in its own directory and is loaded automatically by a compatible agent (Claude Code, Codex) when a request matches the skill's description. To add a skill to your own setup, copy its folder into your agent's skills directory.

## Syncing

To keep MySKILLS, `~/.codex/skills`, and `~/.claude/skills` identical, run `python3 sync_skills.py` (plan) then `--apply`; see [stratcore-skills-sync](stratcore-skills-sync).

The local copy is the source of truth for Git. Run `./sync.sh ["message"]` to commit and push everything. If the remote ever holds commits that local lacks, they are archived as an `archive/remote-<timestamp>` tag before being overwritten.

## License

[MIT](LICENSE)
