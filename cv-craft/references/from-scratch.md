# Writing a CV from scratch

Use this when there is no CV yet. The rest of the skill works by comparing a document against
evidence; here there is no document, so the evidence comes from the user directly through a
structured interview.

The no-fabrication rule does not relax because the source is conversation rather than a file. If
anything it matters more: in an interview it is easy to offer a plausible-sounding achievement and
have the user accept it out of politeness, and now it is on their CV and they cannot defend it in
the room. Ask, record what they say, and leave gaps visible.

## How to run the interview

Work through the sections below in order, one at a time, and wait for an answer before moving on.
Going in order matters: the skills section is built from what they tell you about their jobs, so
asking about skills first produces a list of things they have heard of rather than things they have
done.

Keep each turn short. Ask two or three questions, not twelve. If an answer is vague ("a few years
ago", "quite a big team"), ask once for the specific value, and if they still do not know, record
it as unknown rather than settling on a number - see *Handling what they do not know* below.

## 1. Contact and logistics

Name, email, phone, city and country. Then, where relevant to the roles they are targeting:
LinkedIn, GitHub, personal site, languages with honest proficiency levels, work authorization, and
whether they are open to relocation or remote work.

Do not infer nationality, work authorization, or language ability from a name or a location. These
are facts with legal weight and guessing them is worse than leaving them out.

## 2. Target

What kind of role is this CV for? Ask for two or three concrete job titles rather than a field.

This populates `cv.target` and shapes everything after it - which achievements matter, how the
skills are grouped, how much leadership versus hands-on content the CV should carry. It is also
what makes the audience-balance check in the review pass meaningful.

If they want to apply for genuinely different kinds of role, say so now: that is a master plus
variants, not one document trying to do both. Write the master first; derive variants later using
`references/variants.md`.

## 3. Experience

Most recent role first, working backwards. For each one, capture in this order:

- Exact job title, as it appeared on the contract or in the system of record. Not a tidied-up
  version - the title is checkable.
- Employer, and a one-line description if the company is not widely known.
- Start and end month and year. Ask; do not estimate.
- Location, and whether it was remote.
- Whether it overlapped with another role. Concurrent roles need marking, or a reader sums the
  durations and gets a wrong total.
- Three to six achievements.

For achievements, ask what changed because they were there, not what their responsibilities were.
"Responsible for the deployment pipeline" says nothing a job description would not; "cut deployment
time from a day to under an hour" is a claim. If a number comes up, ask where it came from - a
figure the user cannot source is a figure that will not survive an interview, and it is better to
find that out now.

Stop at roughly ten to fifteen years, or at the point where earlier roles no longer support the
target. Older roles can collapse into a single line.

## 4. Skills

Build this from what they have just described rather than asking cold. Read back the technologies,
tools, and methods that appeared in their own answers, grouped sensibly, and ask what is missing.

Then ask the useful filtering question: which of these would they be comfortable being interviewed
on? Anything that fails that test either comes out or moves to a clearly weaker grouping. A skills
list is a list of invitations to be questioned.

## 5. Education

Institution, qualification, field, and dates.

Incomplete study is labelled as incomplete in the heading itself - "Bachelor's studies (not
completed)" - not softened elsewhere or quietly omitted in a way that leaves an unexplained gap.
It costs very little and being caught costs a lot.

## 6. Certifications, projects, research, affiliations

Ask whether each applies. Skip the ones that do not rather than padding them - an empty section
signals more than a missing one.

For projects, apply the same status vocabulary the rest of the skill uses: `implemented`,
`in production`, `in validation`, `prototype`, `documented handoff`, `proposed`. Ask which each one
is. Side projects and proposals are worth listing when labelled honestly and damaging when not.

## 7. Conventions and constraints

Two questions that populate the `cv:` block:

- Will this go through applicant tracking systems, job boards, or automated screening? If yes, set
  `ascii_only: true` and follow the machine-ingestion rules in `references/conventions.md`. Also
  agree a date format.
- Is there anything they do not want disclosed - figures, client names, employer-internal detail?
  This populates `never_disclose`, which the linter then enforces on every future edit.

## Then write it

Write the master with a fully populated `cv:` block: `role: master`, `target` from section 2,
`conventions` and `never_disclose` from section 7, plus `required_sections` reflecting what the CV
actually contains.

Then rejoin the standard workflow: run `scripts/cv_lint.py`, do the step 5 review pass, and report
- including, explicitly, whatever is still missing. A first draft with three known gaps that are
named is more useful than one that looks finished and quietly is not.

## Handling what they do not know

Missing information is normal and is not a licence to fill it in.

- **A date they cannot recall** - write what they gave you at the precision they gave it (a year
  alone if that is all they have) and list it as something to confirm. Never split the difference
  on a range.
- **A number they cannot source** - drop the number and write the achievement qualitatively. The
  scope statement survives scrutiny; the invented figure does not.
- **A whole role they are vague about** - capture the outline, mark it as needing detail, and move
  on. Coming back to one role later is cheaper than stalling the whole interview.
- **A gap in the timeline** - ask once, neutrally. If they would rather not explain it, leave it
  unexplained. Do not invent a bridging entry.

Collect these as you go and put them in the closing report as a short list of open items.
