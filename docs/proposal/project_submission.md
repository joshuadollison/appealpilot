# Tab 1


“AppealPilot” - AI insurance denial appeal copilot (healthcare)
- Use case: Generate medically-grounded appeal letters + assemble evidence packet
from chart notes.
- Customer: Small- to mid-size specialty clinics (buyer = practice admin, user =
billing/RCM staff).
- v1 boundary: Only denial appeals for top 3 payers + top 10 CPT codes; no full RCM.
- Industry: Denial management / RCM tooling for outpatient specialty clinics.
- Why now: LLMs + doc parsing can cut labor-heavy appeal work and improve hit rate.
- Moat: Workflow embedding + switching costs (templates, payer-specific playbooks,
integrated outcomes loop).

Submit a proposal that pitches an AI-enabled new entrant (a startup or a new business line) in
an industry of your choice. The goal is to lock in a strong opportunity where AI is central to
competitive advantage.

Your proposal must contain the following 7 elements (under these numbered headings):
1) The AI-enabled product idea (job-to-be-done/use case)
Describe the AI-enabled product or service you propose. Explain what problem it solves (job-
to-be-done), who it’s for, and what the user experience looks like. Be specific: what does the
AI do, what does the user do, and what output is produced?

2) Mission, values, vision
Define the mission (why you exist), values (what you believe in/how you behave), and vision
(what you want to be) for your proposed business.

3) Target customer segment and needs
Identify the target customer segment(s) and explain the needs, pain points, or “jobs” that
customers are trying to get done. Explain why your chosen segment is attractive.

4) Industry definition and key competitors
Define the industry you are entering. Identify key competitors and substitutes. Use Porter’s
definition of industry (customers perceive the offerings as satisfying the same needs).

5) How the business makes money
Explain the revenue model (pricing, who pays, what they pay for). Explain cost structure at a
high level. Tie to unit economics if possible.

6) Competitive advantage and strategic positioning
Explain why your business will win. Use strategy concepts: where you compete, how you
compete, unique value proposition, tradeoffs, and the logic of sustainable advantage.

7) Sources and AI tool disclosure
List sources used for facts (with citations). Disclose any AI tools used.

# Tab 2


The target customers are small to mid-sized clinics that encounter a high volume of insurance
denial claims. The buyer is usually the clinic manager or the person in charge of the money
side, and the people who use it every day are the staff members who fight denials and gather
paperwork, with doctors stepping in to sign off when needed. These clinics are a great fit
because denials eat up hours every week, slow down cash flow, and burn out staff, but they
often can’t afford enterprise-level RCM automation or dedicated appeal teams. They need a
tool that makes appeals faster, more consistent, and more likely to win, without requiring the
clinic to change its entire billing workflow.

Their biggest pain points are time, uncertainty, and documentation chaos. Denials require a
lot of manual work - reading the denial, figuring out what the payer actually wants, hunting
down the right chart notes, and writing a letter that sounds credible and “medical enough” to
overturn the decision. Staff frequently don’t know which cases are worth appealing, and
payers all have slightly different rules, deadlines, and required evidence. So clinics either
appeal too few cases (leaving money on the table) or appeal inefficiently (wasting time on
low-probability wins). AppealPilot solves this by turning a denial into a structured workflow: it
classifies the denial reason, suggests what evidence is needed, pulls the right documents,
and generates a grounded, payer-ready appeal letter with citations to the record.

# Tab 3


The product idea is an AI denial appeal copilot called “AppealPilot.” The job-to-be-done is
turning an insurance denial into a high-quality appeal packet quickly, so the clinic gets paid
without wasting staff time. In the user experience, a billing staff member uploads or pastes
the denial letter and relevant chart notes (or selects them from an integrated EMR export).
AppealPilot then extracts key details - payer, requested service, diagnosis, denial rationale,
and deadlines. It classifies the denial into a category (medical necessity, experimental,
insufficient documentation, etc.) and generates a checklist of required evidence (e.g., MRI
report, prior failed therapy, guideline excerpt, physician attestation). It then drafts an appeal
letter that is structured in payer-friendly format and includes citations like “See Attachment
B: Provider Note dated 1/10/26” to ground every factual claim. The output is a downloadable
appeal letter plus an evidence packet index.

The AI is doing three main things:
1) Document extraction and structuring (turning messy denial letters and notes into
structured fields),
2) Denial classification and retrieval (matching the case to similar historical appeal decisions
and policy guidance),
3) Grounded generation (writing a letter using only retrieved facts and docs, with a citation
trail).

In v1, the scope is narrow: focus on one specialty clinic type (e.g., outpatient PT or imaging),
a handful of high-volume CPT codes, and 2-3 major payers in one state. The goal is a tight,
demoable workflow, not a full revenue cycle platform.

# Tab 4


Mission: Help clinics win fair reimbursement by turning denial paperwork into clean, evidence-
grounded appeal packets.
Values: Accuracy and groundedness (no claim without support), speed and simplicity, respect
for patient privacy, and practical workflow-first design.
Vision: Become the default denial appeals workflow layer that clinics rely on to recover revenue
and reduce admin burden, while building the most trusted payer-by-payer appeals playbook in
the market.

# Tab 5


The industry is denial management and RCM tooling for outpatient specialty clinics. The main
competitors are RCM platforms and denial management vendors that offer analytics, workflow
tools, and in some cases outsourced appeal services. Substitutes include manual staff work
(using templates in Word), outsourcing to billing services, or using general-purpose AI tools
without workflow integration.

Key competitors include established RCM vendors (Athenahealth, Waystar, Availity, etc.) and
specialized denial management solutions. Many of these focus on analytics and claim
submission, but their appeal workflows are often manual, templated, or require significant
setup. AppealPilot positions as a workflow-native “copilot” specifically for appeals, with fast
time-to-value and a learning loop tied to outcomes.

# Tab 6


Revenue model: subscription SaaS sold to clinics, priced by claim volume or number of users.
Example: $500-$2,000/month depending on volume and specialty. Clinics pay because winning
even a handful of denials per month can cover the subscription.

Costs: main costs are compute (LLM inference + retrieval), ingestion/processing, and customer
support/onboarding. Since appeals are episodic but high value, unit economics can work well:
if the tool saves staff hours and recovers reimbursements, willingness to pay is strong.

# Tab 7


Competitive advantage comes from workflow embedding + a compounding payer-specific
playbook. General LLMs can draft letters, but they don’t know which evidence wins for a payer
and denial type, and they don’t integrate with clinic workflows. AppealPilot’s strategy is to
compete in a narrow wedge (one specialty, top codes, top payers) and win by delivering
grounded, structured outputs fast. As clinics use it, the system collects de-identified patterns
of what evidence and arguments lead to overturns. That creates a proprietary “appeals
playbook” by payer and denial reason, improving performance over time and raising switching
costs.

Strategic positioning: not a full RCM platform. It’s a denial-appeal workflow layer that plugs
into existing systems. Tradeoff is tight scope in v1 for higher win rate and better UX, instead of
trying to cover everything.

# Tab 8


- https://www.cms.gov/marketplace/resources/data/public-use-files?utm_source=chatgpt.com
-

If you tell me which direction you’re going (Option #1 or #2), I’ll lay out a v1 dataset pipeline
(what to scrape/download, how to label, what your evaluation metric is, and what your demo
looks like) in a way that plugs straight into your proposal headings.

# Tab 3


Hell yeah. AppealPilot it is. Here’s the end-to-end pipeline - datasets, ingestion, labeling,
modeling, eval, and a demo that’ll make your professor nod like “okay, this is real.”

AppealPilot - the full pipeline

0) What you’re building in v1 (tight boundary)
V1 goal: Given a denial (or prior auth denial) + basic clinical context, generate:
1. A payer-ready appeal letter (with citations to evidence in the packet),
2. A complete evidence packet checklist (what’s missing, what to attach),
3. A structured case summary (diagnosis, treatment requested, denial reason, next
steps, deadlines).
You are not “doing medicine.” You are turning paperwork hell into a clean, defensible
packet.

1) Data sources (and what each is used for)
A) Outcomes + targeting (where appeals matter)
- CMS Transparency in Coverage PUF (TC-PUF) - issuer/plan-level claims + appeals
data. Use it to pick payers/plans and quantify “appeals exist, volume exists.”
- WA Health Plan Prior Authorization Data - includes “codes initially denied then
approved on appeal.” Use it to pick your starter specialty/CPT/HCPCS targets.
B) The actual decision language (the gold)
- NY DFS external appeals decisions database - real determinations and rationale
patterns. This becomes your “what winning arguments look like” corpus.
C) Rules + workflow deadlines (so your product feels legit)
- CMS appeal guidance (internal appeals, expedited, etc.) - use this to drive workflow
steps, timers, and “do this next.”

2) Ingestion pipeline (documents -> clean structured
cases)
Step 2.1 - Grab the data
- Download TC-PUF (CSV/Excel) from CMS - store as raw/tc_puf/…
- Pull WA prior auth dataset - store as raw/prior_auth_wa/…
- Scrape/collect NY DFS decisions - store as raw/dfs_external_appeals/html_or_pdf/…
Step 2.2 - Normalize into a common “Case” schema
Create a canonical record like:
case_id
payer / plan
service_requested (CPT/HCPCS)
diagnosis (ICD-ish if available)
denial_reason_category (medical necessity, experimental/investigational, out-of-network,
paperwork/insufficient documentation, etc.)
clinical_facts (age range, symptoms, prior treatments tried, test results - de-identified/synthetic
if needed)
decision_outcome (overturned/upheld/partially)
rationale_text (from DFS decisions)
citations (medical literature references if present)
Step 2.3 - Text cleaning + sectioning
For each DFS decision, segment into:
- Summary of request
- Denial reason
- Clinical background
- Reviewer rationale
- Decision (overturn/uphold)
This matters because your model should learn structure, not just vibes.

3) Modeling pipeline (3 small models, not “one big LLM”)
Model A - Denial reason classifier
Input: denial text
Output: denial_reason_category + urgency + deadline flags
Why: drives workflow and retrieval.
Start simple: fine-tuned BERT/DistilBERT or even a TF-IDF + logistic regression baseline.
Model B - Similar-case retriever (RAG)
Input: denial category + service_requested + diagnosis keywords
Output: top 3-5 similar DFS decisions + rationale snippets + any cited policies
Why: gives your letter generator grounded precedent language + structure.
Implementation: embed DFS decisions, index in vector DB, retrieve by query.
Model C - Appeal letter generator
Prompted to produce:
- Patient-safe de-identified narrative
- Point-by-point rebuttal of denial reason
- Checklist-anchored citations (“See Attachment A: …”)
- A short cover + longer detailed justification
Guardrails:
- Must cite only retrieved sources or provided clinical facts
- Must include “missing info” callouts if facts are absent
- Must output in a payer-ready format (headers, dates, provider info placeholders)

4) Labeling plan (how you create training signal)
- For Model A: label 300-1,000 denial texts (or DFS “denial reason” sections) into your
denial_reason_category taxonomy.
- For retrieval: label “similarity relevance” for 200 pairs (does this DFS case match the
current case category + therapy?).
- For generation: you’re not training the LLM from scratch - you’re evaluating it with a rubric
and grounding constraints.

5) Evaluation pipeline (how you prove it works)
Offline metrics (your proposal loves these)
- Structure completeness score: all required sections present (Y/N)
- Evidence coverage: letter references required attachments (Y/N)
- Groundedness: every factual claim traceable to case facts or retrieved docs
- Denial-reason accuracy: classifier precision/recall on labeled set
- Similarity relevance: retrieved DFS cases match category + therapy
Human-in-the-loop rubric (simple, brutal, effective)
Have 2-3 reviewers grade 30 outputs:
- Would you send this? (1-5)
- Missing anything critical? (list)
- Hallucinations detected? (Y/N)
- Clarity + professionalism (1-5)

6) Product workflow (your demo flow - this is the money
shot)
Demo script (5 minutes)
1. Upload denial letter (or paste text)
2. System auto-detects denial reason category + urgency + deadlines guidance
3. Shows evidence checklist (“missing MRI report,” “prior failed therapy,” etc.)
4. Pulls 3 similar DFS cases + common winning rationale patterns
5. Generates appeal letter + packet index
6. Exports: PDF letter + packet checklist + “call your payer” script

7) What your “moat” is (so it’s not just ChatGPT with a
logo)
Pick 2-3 and commit:
- Workflow embedding in RCM/clinic ops (where work actually happens)
- Proprietary playbook + labeled case library from DFS-style decisions (structured
arguments taxonomy)
- Outcomes loop: track overturn/uphold, refine templates, build payer-specific patterns
- Trust assets: audit trail + citation discipline + “no claim without source” policy

8) Your v1 “starter wedge” (so it’s not too broad)
Use WA prior auth dataset to pick:
- 1 specialty (PT, imaging, oncology supportive care, etc.)
- Top 10 codes with “denied then approved on appeal”
That becomes your v1 scope and your “why this niche” justification.