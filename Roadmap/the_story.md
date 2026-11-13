# The Story: POP Roadmap talk track

Speaker narrative for `pop_roadmap.html`. Written to be said out loud, one beat per click. Roughly 8 to 10 minutes without questions.

**The one-line story:** POP started as a productivity tool for product owners. This roadmap turns it into a product intelligence layer for Neuro: first make it dependable, then give it knowledge it can trust, then put guardrails around it, then use all of that to show what a change will touch before work starts. And we measure it the whole way.

---

## Slide 1: Cover

> Thanks for the time. Over the next ten minutes I want to show you where the Product Owner Plugin is going and how we will know it is working.
>
> Coming out of the offsite, we have moved from discovery into structured execution. What you are about to see is one roadmap, in outcomes, not features. I will build it up one theme at a time, and each theme sets up the one after it.

*(Next)*

---

## Slide 2: Roadmap

**Before the first lane, set up how to read it:**

1. Three columns. **Now** is work in progress or starting this PI. **Next** starts when something in Now frees up. **Later** is blocked or not yet committed.
2. These are relative waves, not dates.
3. Each box is an outcome; the backlog items sit behind it if you want to go deeper.

### Lane 1: Usability and Reliability
*"Start with the basics."*

1. **Why this row is first:** We start with the basics, because nothing else matters if product owners do not trust the tool in front of them.
2. **Now, keeping users current:** Today, fixes we ship do not always reach users, so people report problems we have already solved. That is the first thing we close: every user gets the latest fixes and sees what changed.
3. **Now, the calendar fix:** We also fix something that would otherwise break on a known date. POP's PI planning calendar is a saved copy that runs out in February 2027; after that, PI planning in POP would have no dates to work with. We are switching it to the live calendar well before then.
4. **Next, less friction:** Product owners can refine an epic in place and re-submit it, instead of exporting it, editing it somewhere else and uploading it again.
5. **Next, more useful for API work:** We make POP more usable for API-related projects. API product owners are a key user group, and POP will draft the visuals they need, such as a business flow and an API consumer interaction diagram, so they can walk into PMO and Architecture conversations with something concrete before an architect is involved.
6. **Bridge to the next row:** This lane is deliberately short. It is quick, concrete, and it buys us the credibility for what follows.

*(Next)*

### Lane 2: Product Knowledge Base
*"The foundation."*

1. **Why it matters:** This is the strategic bet. POP is only as good as what it knows about our products, and today every initiative starts close to zero on product context.
2. **The gap we are closing:** Today the Neuro Knowledge Hub holds summarized code: the architecture and engineering view of our applications. It does not hold product knowledge. So we are creating custom Product Knowledge Bases to complement it, not replace it. Knowledge Hub tells POP how the systems work; the Product Knowledge Bases tell it what our products are, who owns them and what they depend on.
3. **Now, one model:** The "Product Context model" is the agreed template for how we describe a product: its areas and features, the capabilities behind them, the systems they depend on, and who owns each piece. Today that knowledge lives in different shapes in different places, including local copies. Product, Architecture and Engineering are settling on one structure so everyone, and POP, describes products the same way. We are piloting it with Vault first.
4. **Now, a Knowledge Base that learns:** We want the Knowledge Base to recursively learn and get smarter over time. The groundwork starts now: on every run, POP checks where each fact it wrote came from. That shows us what the Knowledge Base got right, what it got wrong and what it was missing, and those gaps are what we feed back to improve it.
5. **Next, live and governed:** That becomes a governed Knowledge Base, live for the pilot areas, with a named owner for each area. When a run exposes a gap, the gap goes into a queue for that owner.
6. **Later, the loop closes:** Two things. Jira and ServiceNow delivery history becomes product context. And the learning loop we started in Now closes: approved fixes update the Knowledge Base automatically, so it gets better with every initiative that uses it.
7. **Bridge to the next row:** Almost everything below this row depends on it. That is why it is here, second.

*(Next)*

### Lane 3: Governance and Standardization
*"The guardrails."*

1. **Why it matters:** As POP produces more of what goes to governance, we need to be able to stand behind it.
2. **Now, one Jira policy:** One Jira access policy that the tool, the documentation and our users all follow. Today those three do not agree, and it confuses people.
3. **Now, recorded sign-off:** Every artifact published to Working Hub carries a record of who reviewed it and when. A person is accountable for every publish.
4. **Next, close the loop:** After delivery, POP checks what was delivered against what was asked for and traces requirements through to code.
5. **Next, auditable artifacts:** Every artifact is stamped with the version and sources that produced it, so we can always show how it was made.
6. **Next, one standard for spec-driven development:** We agree one standard for how much detail a spec needs, how it is approved, and how Dev picks it up.
7. **Bridge to the next row:** That close-out step is the only route to the traceability goal leadership has set, and it is what makes realized value measurable later.

*(Next)*

### Lane 4: Cross-Impact Analysis
*"The payoff."*

1. **Why it matters:** This is where the first three rows pay off.
2. **Now, shared services early:** Today shared services such as SRE, Data Engineering and Risk often hear about a deliverable late. Starting now, POP proposes which shared services are likely impacted as each deliverable is drafted, so those teams are engaged well before PBR 3.
3. **Next, every engine owns its piece:** For a deliverable that touches several engines, POP proposes the epic for each impacted engine and hands it to that engine's product owner to own and sign off. No more chasing other teams for their piece.
4. **Later, see the impact up front:** A product owner describes a change, and POP shows what it touches: capabilities, systems, components. A change to UPG surfaces Boarding.
5. **Later, check the portfolio:** It also checks a new initiative against the rest of the portfolio and the strategic roadmap, so overlaps and conflicts show up at the start, not in the middle.
6. **Why the order matters:** That last box is Later for an honest reason. It needs the Knowledge Base from row two and the policy from row three to exist first.

*(Next)*

### Lane 5: Metrics
*"How we will know."*

1. **Why it matters:** The last row is how we hold ourselves to account. Six categories, lined up with the Neuro OKRs, and each one sits in the wave where we can first measure it honestly.
2. **Now:** Adoption, onboarding, quality and governance we can start measuring now.
3. **Next:** Speed comes next, once we have an agreed definition of when a Pod has accepted the work.
4. **Later:** Realized value comes later, because it depends on the close-out step you saw in Governance.
5. **Bridge to the metrics:** Let me take you through them.

*(Next, into Metrics)*

---

## Slide 3: Metrics

**Say this once, on the first screen, and mean it:**

1. Only the first headline number you will see is real data today.
2. Everything marked "Illustrative" is a preview of what the dashboard will show and the kind of statement it will let us make.
3. I would rather show you the shape now and fill it with real numbers than wait.

### 1. Adoption (actual data)

1. **The question:** How many of the people who could use Neuro are using it?
2. **The number:** As of October, a third: 33 percent, up from 28.
3. **The candid part:** Most of the increase came from a smaller headcount; only ten more people are active. And 44 percent have installed it, so roughly a quarter of the people who installed it are not using it yet.
4. **What we watch instead:** Reach is not the number we should care about most. The two below it are: are product owners using POP for real work month after month, and do they say it made the work straightforward.

### 2. Onboarding

1. **The question:** How quickly does a new product owner get to their first real output?
2. **Why it matters:** It tells us whether getting started is still a barrier.
3. **What we do with it:** It points at exactly who is stuck, so we can help them.

### 3. Quality

1. **The question:** Are the documents POP helps produce approved at governance the first time?
2. **Why it matters:** Every rejected document is a review cycle that slows an initiative down, so this is quality you can feel in the schedule.
3. **The guardrails behind it:** Whether work handed to a Pod was truly ready, and whether defects after release stay flat as delivery speeds up.
4. **The point:** Going faster only counts if quality holds.

### 4. Governance

1. **The question:** How well-sourced is what POP writes?
2. **Why it matters:** Today we have no automated way to identify which claims in a POP document are unsourced, so we cannot fully trust what it writes. Identifying them is what makes the output trustworthy, and it gives us a number we can track as it improves.
3. **How we measure it:** The share of claims in POP's documents that cannot be traced to a source. Today that is a manual sample; it covers every document once the tracing is automated.
4. **What it tells you:** How much of what POP writes is unsourced. Each of those claims is reviewed by a person before the document is published, so nothing unsourced goes to governance unchecked.
5. **Alongside it:** Is the Knowledge Base giving answers we can use, and can each requirement be traced to the code that delivered it.
6. **Link to the roadmap:** That last one is the leadership traceability goal, and it comes online with close-out.

### 5. Speed

1. **The question:** How long does it take to get a piece of work ready for a delivery Pod?
2. **Why this one:** It is POP's direct share of the Speed OKR, intake to Pod-accepted.
3. **Behind it:** The full idea-to-production number. That one belongs to the whole Neuro programme; this one tells you how much of the gain is coming from getting work ready.

### 6. Realized Value

1. **The question:** Do initiatives deliver the business outcomes they promised? This is the question that matters most.
2. **Why it arrives last:** Outcomes often show up months after go-live, and it depends on the close-out work.
3. **How we will report it:** As Neuro's contribution, not as proof of cause.
4. **The point:** It is the one that moves this conversation from activity to value.

---

## Close

> So, to bring it together. We make POP dependable. We give it knowledge it can trust. We put guardrails around what it produces. And that lets it show us what a change will touch before we commit to it. That is POP moving from a productivity tool for product owners to a product intelligence layer for Neuro.
>
> I have two asks.
>
> First, please validate the Knowledge Base liaisons and confirm an accountable content owner for each product area. The Knowledge Base only works if someone owns what is in it.
>
> Second, several of the items in Now do not yet have a named owner. The Now column is only real once they do, and I would like your help closing that.

---

## If they ask (short answers, click in only if needed)

| Question | Answer |
|---|---|
| Why no dates? | Waves are relative on purpose: several items wait on other teams. The two fixed points are the roadmap date and liaison validation on 11/30, and the planning-calendar fix before February 2027. |
| What is blocking the Knowledge Base going live? | Two things outside POP: Knowledge Hub supporting custom knowledge bases POP can query, and named owners for each product area. |
| Why is impact analysis in Later? | It needs dependency relationships recorded in the Knowledge Base, one product and capability hierarchy, and the strategic roadmap available as data. None exist yet. |
| Are these metric numbers real? | Only Active User Rate. The rest are illustrative until the data is flowing; four categories can be measured starting now. |
| What do you need from Engineering? | Commits that reference Jira keys. Without that, close-out still works but traceability cannot reach 100 percent. |
| What do you need from Working Hub? | Agreement on the Jira policy, and the ability for a second product owner to author within the same deliverable. |
| Why did adoption barely move in real terms? | Correct, ten more active users. That is exactly why we lead with sustained use and onboarding time, not reach. |
| Who owns the metrics programme? | Not yet named. The measurement framework is proposed under the AI-XDLC work. |

---

## Delivery notes

- **Pace:** one lane, one idea. Say the tagline thought (start with the basics, foundation, guardrails, payoff, how we will know), then the numbered points, then click.
- **Do not read the boxes.** The boxes are the outcomes; your job is the why and the link to the next row.
- **Use the dependency dot once, not five times.** The best moment is on the Later box in Cross-Impact: click the link dot and the lines run up to the Knowledge Base and Governance rows. It makes the "order matters" point for you.
- **The illustrative caveat is a strength.** Say it plainly, once, early. It is far better coming from you than as a question from the room.
- **If short on time:** cut Onboarding and Speed to one sentence each. Never cut Governance (trust) or Realized Value.
