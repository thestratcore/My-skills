# Variant playbook

## The principle

One document cannot speak to a CTO evaluating a Head of IT candidate and an engineering lead
hiring an LLM engineer. Both readers see the same career, but they are scanning for different
evidence and they skim differently - the executive reader wants scope and accountability in the
first ten lines; the engineering reader wants to know what the person has actually built.

A variant is that same career, reordered and subtracted. It is never a different career. If you
find yourself writing a sentence into a variant that is not derivable from the master, stop: either
the master is missing a fact (add it there first, then propagate) or you are inventing.

## Derivation procedure

1. **Copy the master.** Start from the current master text, not from a previous variant, so
   corrections made since the last derivation come along.
2. **Set frontmatter** - `cv.role: variant`, `cv.derived_from`, `cv.target`.
3. **Reorder roles** so the one the audience cares about leads. Ordering is the loudest signal in a
   CV; a reader who sees a management role first reads the whole document as a manager's.
4. **Rewrite the summary** for the audience. Same facts, different emphasis and different first
   sentence. This paragraph does most of the work.
5. **Regroup and rename skills blocks.** The same skills, clustered the way this reader thinks
   about them, with the block they care about first.
6. **Subtract by audience** using the table below.
7. **Keep invariant:** contact block, education, certifications. Facts, not positioning - and
   divergence there reads as carelessness or, worse, as tailoring the truth.
8. **Cross-link** master and siblings so anyone opening one file can find the set.
9. **Lint** to confirm no drift was introduced.

## What each audience wants

### Leadership variant (CIO, IT Director, Head of IT, Head of AI, Head of Engineering)

The reader is assessing whether this person can be trusted with budget, people, and risk.

**Lead with:** scope and accountability. Team size, budget, portfolio breadth, who they report to,
what they own end to end. Governance and compliance responsibility. Strategy and vendor decisions.

**Keep, condensed:** technical depth, but as credibility rather than detail. One line saying the
person built the platform rather than only sponsoring it is worth more to this reader than a
paragraph of implementation detail - it separates them from candidates who only ever managed.

**Drop:** tool and library inventories, model names, framework lists, per-language year counts,
low-level administration, code-level delivery bullets. None of it is being evaluated, and its
presence makes the person read as a senior engineer rather than a leader.

**Rename sections toward outcomes** - a "Selected Projects" section becomes "Selected Programs",
written as ownership and result rather than stack.

### Engineering variant (AI Engineer, ML Engineer, Solutions Architect, Data Engineer)

The reader is assessing whether this person can build the thing.

**Lead with:** what they have built and shipped, with enough specificity to be checkable. Stack,
architecture decisions, the hard parts. Named systems and their status.

**Keep, condensed:** seniority signals. A single line about leading a team or owning a portfolio
establishes level without turning the document into a management CV. Do not delete leadership
entirely - it is the difference between a senior and a mid-level read.

**Drop:** budget figures, procurement and contracting, funding administration, service-management
and SLA oversight, managerial accounting, facilities projects. These do not just fail to help -
they actively suggest the person has moved away from building.

**Add a models/stack block** if the field has fast-moving named technologies; those names are what
the reader and their search tools are matching on.

### Specialist and consulting variants

Lead with domain evidence and client-facing outcomes. Keep the breadth that shows adaptability
across contexts; drop internal-only process detail that does not travel between employers.

## Failure modes

- **Derivation drift** - a variant slowly acquires claims through direct edits until it no longer
  matches the master. Prevented by editing facts only in the master and running the linter.
- **Over-subtraction** - so much removed that the person reads as junior or narrow. The seniority
  line and the credibility line exist to prevent this.
- **Positioning that becomes misrepresentation** - emphasis is fair; implying a different role,
  seniority, or scope than the master supports is not.
- **Divergent contact or education blocks** - almost always an accident, always looks bad.
