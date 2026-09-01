"""
Elaborations for the 50 outreach methods.

These are NOT from the source document. `ai-target-companies-and-outreach-strategy.html`
gives each method a title and one summary line; this file adds the "how it
actually works" paragraph underneath, written on request (2026-09-01).

They are kept in a separate file, and rendered under their own labelled block in
the UI, so the compiled source material and these additions never blur together.
Describing mechanics only - what you do, what the artifact is, why it reaches a
hiring team. No fit-ranking, no "your angle".

Delete an entry and the card falls back to the source's own one-liner.
"""

DETAILS = {

    # --- A. Open source and public proof of work -------------------------
    1: "Pick a repository whose issue tracker you can actually read - "
       "<code>huggingface/transformers</code>, <code>vllm-project/vllm</code>, "
       "<code>NVIDIA/TensorRT-LLM</code>. Start with a bug you hit yourself, then move to "
       "substantive fixes. Every merged PR puts your handle in the commit history and the "
       "release notes. Maintainers at those labs review the same names repeatedly, so a "
       "sustained streak reads as a working audition rather than an application.",

    2: "Take an open base model and fine-tune it on a domain nobody has covered well - "
       "Indian legal text, insurance claims, a regional language. Publish the weights with a "
       "real model card: training data, eval numbers, intended use, limitations. Downloads "
       "and trending placement are public metrics, so recruiters filtering for people who "
       "have actually shipped a model can find you without you applying to anything.",

    3: "Build a tool that makes a large model run on hardware people already own - "
       "aggressive quantisation, layer offloading, or a llama.cpp-style runtime wrapper. The "
       "audience is enormous because most developers cannot afford datacentre GPUs, so stars "
       "accumulate quickly. The work itself demonstrates the memory-layout and kernel "
       "knowledge that inference teams hire for.",

    4: "Most public agent repos are demos that fall apart outside the happy path. Ship one "
       "that handles retries, tool failures, state persistence and cost caps, with tests and "
       "a real deploy path, built on LangGraph or CrewAI so it drops into what teams already "
       "run. It becomes the reference implementation people fork, and your name stays on it.",

    5: "Go below the API surface into indexing, filtering and storage internals in Qdrant, "
       "Weaviate or Chroma - HNSW parameter handling, hybrid search, memory layout. These are "
       "small teams that read every external PR. It is unambiguous evidence of "
       "retrieval-systems depth, which is exactly what RAG-heavy companies struggle to "
       "verify from a CV.",

    6: "Target orchestration and monitoring projects such as ClearML or Evidently AI. The "
       "contributions that count are the unglamorous ones: a scheduler race condition, a "
       "metrics backend that collapses at scale, a broken retry path. Fixing those proves you "
       "have operated ML systems in production rather than only trained models in a notebook.",

    7: "Write Triton or CUDA kernels that make one operation measurably faster - a fused "
       "attention variant, a quantised matmul, a custom norm. Benchmark before and after on "
       "real hardware and publish the numbers. Very few engineers can do this at all, so a "
       "single credible kernel contribution carries disproportionate weight with inference "
       "and systems teams.",

    8: "Release a benchmark for something teams currently cannot measure: retrieval drift "
       "over time, jailbreak resistance, agent-loop detection. Ship the harness, not just the "
       "data, so others can reproduce your numbers. Benchmarks get cited, and citation puts "
       "your name in front of the researchers who built the models being measured.",

    9: "Ship small, genuinely useful utilities that plug AI into tools developers already "
       "live in - Raycast extensions, Warp workflows, VS Code commands, CLI tools. "
       "Distribution is the point: those ecosystems have built-in discovery. It also "
       "demonstrates product judgement and shipping discipline alongside model knowledge.",

    10: "Take a released model and work out how it behaves - tokenizer quirks, context "
        "handling, architecture inferences, likely data mixture - using only public artifacts "
        "and your own probing. Write it up rigorously, showing the evidence for each claim. "
        "This is the kind of post that circulates among the people who actually built the "
        "model you are analysing.",

    # --- B. Technical content and inbound --------------------------------
    11: "Write threads explaining how a real system handles scale: batching strategy, KV "
        "cache management, request routing, cost per million tokens. Concrete numbers, not "
        "general advice. Founders and staff engineers follow this category closely, and it is "
        "their replies - not the like count - that turn a thread into a conversation.",

    12: "Publish on one narrow, repeatable theme: specific failure modes and how you fixed "
        "them, such as why naive RAG degrades past a certain corpus size. Depth beats "
        "frequency - one genuinely technical post a month outperforms weekly summaries. Over "
        "time the archive becomes the credential, and hiring managers read it before the call.",

    13: "Run the same workload across providers or runtimes - serverless inference backends, "
        "hosted APIs, self-hosted vLLM - and publish latency, throughput and cost per token "
        "with your methodology fully exposed. Vendors amplify results that favour them, which "
        "carries your name into their audiences. State hardware, versions, and what you did "
        "not test.",

    14: "Write up an incident you actually debugged: a memory leak under load, a stale "
        "embeddings cache serving wrong answers, a queue that deadlocked. Include the wrong "
        "hypotheses, not just the fix. This is the strongest available signal that you have "
        "run systems in production, which is what separates senior candidates from strong "
        "junior ones.",

    15: "Produce clean diagrams of systems you have built - query routing, tool selection, "
        "error handling, memory and callback paths - and explain the trade-off at each "
        "decision point. Diagrams travel further than prose in this field. They also double "
        "as ready-made material for the system-design interview round.",

    16: "Read a new paper or release and translate it into what it changes commercially: "
        "cost, latency, what becomes newly possible. LinkedIn's audience is the hiring side "
        "rather than the research side, so the framing has to be business impact carried by "
        "accurate technical detail. Consistency matters more than any single post.",

    17: "Skip API-key tutorials - that category is saturated. Record the hard things: "
        "standing up distributed training on spot instances, profiling a serving stack, "
        "debugging a multi-GPU deadlock. The audience is small, but it is composed almost "
        "entirely of the people who hire for exactly those skills.",

    18: "Take a real model, quantise it to 8-bit and 4-bit, and publish accuracy deltas per "
        "task alongside the memory and latency gains. Show where it breaks, not only where it "
        "works. Inference cost pressure makes this one of the most sought-after skills right "
        "now, and the write-up is easy for a hiring manager to evaluate.",

    19: "When a founder posts a scaling or architecture problem publicly, reply with a "
        "specific, technically correct answer rather than encouragement. One substantive "
        "reply that solves their actual problem is worth more than months of posting. This is "
        "the shortest path there is from stranger to direct message.",

    20: "Maintain a public, growing log of failure modes - hallucination patterns, agent "
        "loops, prompt injections, tool-call misfires - each with a reproduction and a fix. "
        "It becomes a reference other engineers link to when they hit the same wall. "
        "Curation at that level reads as deep operational experience.",

    # --- C. Targeted cold technical outreach ------------------------------
    21: "Study a company's public product closely enough to infer its inference "
        "architecture, then estimate where money is being wasted: oversized models, no "
        "caching, no batching. Send the VP of Engineering a short note with a specific number "
        "attached. A credible cost estimate gets read because it maps onto a budget line "
        "someone is already accountable for.",

    22: "Probe publicly reachable endpoints for prompt-injection and data-leak exposure, "
        "staying strictly inside what is publicly accessible and within their disclosure "
        "policy. Report privately to the security lead with a proposed patch - never publish "
        "first. Done properly this is among the highest-response cold approaches, because the "
        "problem is genuinely urgent.",

    23: "Rather than describing an improvement, submit working code to their public SDK, docs "
        "site or web client that measurably cuts first-token or page latency, with before and "
        "after numbers in the PR description. Code that merges converts you from an applicant "
        "into a contributor to their codebase - a very different conversation.",

    24: "Record three minutes screen-sharing their product while narrating three specific "
        "things you would change and why. Video conveys seniority faster than a written note "
        "and is much harder to skim past. Keep it generous and precise; the goal is to be "
        "obviously useful, not to criticise their team's work.",

    25: "Load-test a public developer API - within its published rate limits and terms - and "
        "document how latency, error rates and throughput behave under pressure. Send the "
        "report with graphs to the head of infrastructure. Most companies do not have this "
        "data for their own edges, which is why it gets read.",

    26: "Join the company's community channel and consistently answer other users' "
        "integration questions well. The core team reads those channels and notices who is "
        "reducing their support load. Once that track record exists, mentioning availability "
        "lands as a known helper making an offer, not a stranger making an ask.",

    27: "Find where their semantic search returns the wrong thing by testing it yourself with "
        "real queries, then propose a concrete fix - hybrid sparse/dense retrieval, "
        "reranking, different chunking. Show the failing queries. Retrieval quality is a "
        "visible product problem, so this reaches product people as well as engineers.",

    28: "Newly funded companies have board-approved headcount and no backlog of applicants "
        "yet. Reach engineering leads within a few weeks of the announcement, referencing "
        "what the round is meant to fund. The funding lists in this hub are built for exactly "
        "this - but treat those figures as leads to verify, not as facts.",

    29: "Use a public chatbot or agent until you find a reproducible failure: a state loop, a "
        "tool call that never terminates, a context overflow. Document the reproduction "
        "precisely and email a proposed guardrail fix. Reproducible bug reports from outside "
        "the company are rare enough to be memorable.",

    30: "Read an engineer's recent paper or post properly and send substantive feedback - a "
        "question about their method, an edge case, a related result. Establish the technical "
        "relationship first and let it run. Only later, once there is genuine exchange, does "
        "asking about team expansion make any sense.",

    # --- D. Communities, hackathons and research spaces -------------------
    31: "Enter events run by AI companies themselves. Sponsors treat them partly as "
        "recruiting funnels and watch closely to see who ships a working system under time "
        "pressure. Placing well puts you in direct contact with their engineering staff, and "
        "the project itself becomes a portfolio piece you keep afterwards.",

    32: "The technical cores of projects like vLLM, the CUDA groups and the Hugging Face "
        "community are small enough that regular contributors are recognised by name. Answer "
        "hard questions, file precise bug reports, share benchmarks. Hiring in these circles "
        "often happens by reputation inside the channel before a role is ever posted.",

    33: "Submit to engineering tracks rather than research tracks - PyTorch Conference, Ray "
        "Summit, NeurIPS workshops, MLOps events. The bar for an engineering talk is a real "
        "system with real numbers, which production work already gives you. A recorded talk "
        "then becomes a durable credential you can link to for years.",

    34: "Partner with independent researchers or small labs on applied work: fine-tuning "
        "methods, distillation, evaluation. You contribute engineering and compute; they "
        "contribute framing and review. A publication with your name on it materially changes "
        "how research-adjacent teams read your profile.",

    35: "Choose tracks that need custom architectures rather than tabular feature "
        "engineering. A high finish is an externally verified skill signal that survives CV "
        "screening without needing to be explained. The solution write-up you publish "
        "afterwards is often worth more than the placement itself.",

    36: "Get into developer previews for infrastructure companies and give rigorous, "
        "structured feedback - what broke, under what conditions, with reproductions. "
        "Companies track which beta testers are actually useful, and that list is a natural "
        "recruiting pool when they open a role.",

    37: "Organise a deep-technical AI meetup in your city rather than a generalist one. "
        "Global remote-first firms sponsor these to build local presence. Being the organiser "
        "puts you in direct contact with sponsors and speakers, and hosting reads as "
        "leadership without requiring a title to prove it.",

    38: "Build reputation specifically in the <code>pytorch</code>, "
        "<code>huggingface-transformers</code> and <code>cuda</code> tags by answering the "
        "questions nobody else will. Those answers rank in search permanently, so the effort "
        "compounds instead of scrolling away. High reputation in a narrow technical tag is a "
        "checkable credential.",

    39: "Contribute code or research to networks such as Bittensor or Akash. The ecosystem is "
        "well funded and hires heavily from its own contributor base. Evaluate each project's "
        "technical substance separately from its token, and go in with clear eyes about the "
        "volatility of the sector.",

    40: "Take part in structured, sanctioned pre-launch model stress-tests run by labs and "
        "safety organisations. Finding and documenting real failure modes demonstrates the "
        "adversarial thinking that safety and trust teams hire for specifically. "
        "Participation is usually credited, which gives you a citable record.",

    # --- E. Referrals, talent networks and consult-to-hire -----------------
    41: "Instead of asking for a job, propose a scoped four-week paid engagement to fix one "
        "specific bottleneck you have already identified. It is a far easier yes because it "
        "needs no headcount approval. Deliver well and the permanent-role conversation starts "
        "from proven work rather than from an interview.",

    42: "These networks screen you once, then place you into pre-negotiated USD contract "
        "tracks - a different economic model from open marketplaces where you bid against "
        "everyone. The screening is genuinely hard, particularly the live technical rounds, "
        "but passing once pays off across every subsequent placement.",

    43: "Talent partners at these funds maintain candidate registries used across their "
        "entire portfolio, so one good conversation can surface roles at dozens of companies "
        "at once. They are also far more reachable than the companies themselves, because "
        "sourcing candidates is explicitly their job.",

    44: "Former colleagues from large Indian tech companies have dispersed into global "
        "remote-first firms. Their referrals carry weight because they can vouch for how you "
        "actually work, not just what your CV claims. Reconnect with specific context about "
        "what they are building now rather than a generic ask.",

    45: "Developer-advocate staff exist to talk to developers, so they are reachable, and "
        "they speak with hiring managers constantly. Show them something real you built with "
        "their product. A warm introduction from DevRel bypasses the application queue "
        "entirely and arrives with an implicit endorsement.",

    46: "Founders often want a public repository that showcases their technology but lack the "
        "time to build or clean it. Doing that work puts you inside their engineering "
        "conversation through a paid, low-risk entry point, and it converts into contract or "
        "full-time work more often than a cold application would.",

    47: "Participate substantively in a target repository's issue board over weeks - "
        "reproduce bugs, propose fixes, review other people's PRs - until maintainers "
        "recognise your name. Only then ask for a referral. By that point it is a request "
        "from a known contributor rather than from a stranger.",

    48: "Build the profile around infrastructure and systems language - throughput, latency, "
        "scaling, cost - rather than a list of frameworks. Founders search the platform "
        "directly and message candidates themselves, which skips ATS filtering entirely. "
        "Target funded seed and Series A companies where the founder still does the hiring.",

    49: "Build a plugin or extension for a developer tool with an active ecosystem. If it "
        "gets real adoption, the parent company has a direct incentive to bring both the tool "
        "and its author in-house. Even short of that, public usage numbers are a strong "
        "credential in their own right.",

    50: "On the monthly thread, search for \"remote\" and \"India\" to filter down to "
        "postings that can actually hire you where you live. Reply to or email the engineer "
        "who posted, since it is usually a team member rather than a recruiter. There is no "
        "ATS and no keyword filter anywhere in that path.",
}
