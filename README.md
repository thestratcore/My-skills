# myskills

A curated collection of [Claude](https://claude.com/claude-code) / Codex **Agent Skills** used across Stratcore projects. Each folder is a self-contained skill — a `SKILL.md` describing when it triggers and how it behaves, plus any supporting scripts, templates, and reference files the skill needs.

## About

Skills extend an AI coding agent with reusable, domain-specific expertise. Instead of re-explaining a workflow every time, the agent loads the matching skill on demand and follows its instructions — whether that's writing an article in a defined voice, modeling a Power BI dataset, or building an MCP server. This repository is Stratcore's working toolbox of such skills, spanning content creation, web and app development, data and BI, and knowledge-base operations. Drop a folder into your agent's skills directory to use it.

## Skills

### Writing & content
| Skill | Description |
|-------|-------------|
| [article-writing](article-writing) | Write articles, guides, blog posts, and newsletters in a distinctive, example-derived voice. |
| [marketing-campaign](marketing-campaign) | End-to-end multi-channel campaign planning: positioning, landing copy, emails, social, and ads. |
| [market-research](market-research) | Market sizing, competitive analysis, and investor due diligence with source attribution. |
| [academic-paper-review](academic-paper-review) | Structured review, critique, and summary of academic papers and preprints. |
| [cv-craft](cv-craft) | Build, tailor, and maintain Markdown CVs and their variants, with evidence-based claims and a linter. |

### Presentations & diagrams
| Skill | Description |
|-------|-------------|
| [keynote-slides](keynote-slides) | Build Keynote-style single-file HTML decks with brand templates and generated media. |
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

### App & platform development
| Skill | Description |
|-------|-------------|
| [swift-expert](swift-expert) | Build iOS/macOS/watchOS/tvOS apps: SwiftUI, async/await, actors, protocol-oriented design. |
| [appsmith](appsmith) | Build admin panels, internal tools, and dashboards on Appsmith with database integrations. |
| [mcp-builder](mcp-builder) | Create high-quality MCP servers in Python (FastMCP) or Node/TypeScript to integrate APIs. |
| [powerbi-modeling](powerbi-modeling) | Design optimized Power BI semantic models: star schemas, DAX measures, relationships, RLS. |

### Knowledge & workflow ops
| Skill | Description |
|-------|-------------|
| [maintain-obsidian-vault](maintain-obsidian-vault) | Audit, normalize, and cross-link an Obsidian vault for human navigation and AI/RAG indexing. |
| [n8n-docs-assistant](n8n-docs-assistant) | Answer n8n setup, credential, node, hosting, and API questions from current n8n docs. |
| [brainstorming](brainstorming) | Explore requirements and compare design alternatives before ambiguous feature work. |
| [skill-creator](skill-creator) | Create, edit, optimize, and evaluate skills — including trigger tuning and benchmarking. |
| [stratcore-skills-sync](stratcore-skills-sync) | Audit/install personal skills and explicitly commit/push MySKILLS changes without overwriting global entries. |

## Usage

Each skill lives in its own directory and is loaded automatically by a compatible agent (Claude Code, Codex) when a request matches the skill's description. To add a skill to your own setup, copy its folder into your agent's skills directory.

## License

[MIT](LICENSE)
