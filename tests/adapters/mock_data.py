SYSTEM_PROMPT = """You are an expert business coach skilled in analyzing conversation transcripts.
                    Your job is to provide insightful, concise summaries and recommend clear, actionable next steps
                    to help clients achieve their goals effectively."""

RAW_USER_PROMPT = """Given the transcript below, generate:
                    1. A brief, insightful summary highlighting key points discussed.
                    2. A clear, structured list of recommended next actions.

                    Transcript:
                    {transcript}"""

TRANSCRIPT = """Mark Foster | MCC, ACTC: Hey there, Liam. Glad we could find a few minutes for this one-on-one. How are things going?

Liam Garcia: Hey, Mark. Doing well, thanks. It’s been a busy week—my local dev environment is a bit cluttered from a new feature branch, but I’m making progress. Ready to dig in on Python best practices?

Mark Foster | MCC, ACTC: Absolutely. I know you wanted to focus on a handful of coding guidelines and how they tie into your team’s speed. Let’s start big picture: what’s motivating you to tighten up your Python practices right now?

Liam Garcia: Mainly two reasons. First, the codebase is growing, and I want to make sure we’re consistent in how we name things, structure modules, and write docstrings. Second, I’m onboarding new developers, and I’ve noticed they can get lost if we don’t have explicit standards in place.

Mark Foster | MCC, ACTC: Makes sense. So, if we look at code readability—PEP 8, docstrings, that sort of thing—what’s your first priority?

Liam Garcia: Definitely PEP 8. That’s sort of non-negotiable. I’d like us to adopt a tool like Black to auto-format. That alone can reduce the back-and-forth on code reviews. It’s a small step but a huge time-saver.

Mark Foster | MCC, ACTC: I love it. Automating style enforcement frees you up to focus on more important stuff—like logic, architecture, and performance. Any concerns about pushback from your devs?

Liam Garcia: A bit. Some folks are used to their own formatting quirks. But I keep reminding them it’s not about personal style—it’s about consistent style that benefits everyone. I think once they see the time saved, they’ll be on board.

Mark Foster | MCC, ACTC: Good call. How about docstrings? I know some devs skip them unless forced.

Liam Garcia: Right. I’m pushing for Google-style docstrings. For classes, methods, and modules, they clarify purpose and expected inputs/outputs. It’s a bit of extra effort at first, but it pays off when you come back months later or when a new dev jumps in.

Mark Foster | MCC, ACTC: So your plan is PEP 8 plus auto-formatting, then Google-style docstrings. Anything else on your radar?

Liam Garcia: Yes—test coverage. We’re aiming for 80% coverage in the short term. That ensures we catch regressions early. I’m also encouraging test-driven development for bigger features. It’s not mandatory, but I want the team comfortable with writing tests before the code whenever possible.

Mark Foster | MCC, ACTC: Great. You mentioned wanting to go faster as a team. How do you see these coding best practices speeding things up, rather than slowing them down?

Liam Garcia: Well, the time you invest in writing docstrings or running auto-format tools is minimal compared to the hassle of deciphering unstructured code. It’s like a Formula One pit stop—everyone knows their role, follows the same procedure, and the car is back on track fast. Consistency and clarity remove friction.

Mark Foster | MCC, ACTC: That’s an excellent analogy. So what’s your biggest concern about implementing all this?

Liam Garcia: Probably that initial pushback, or the fear that it’s “too much process.” But I think if I keep reminding folks it’s about removing headaches—like merges, weird naming conflicts, missing tests—they’ll adopt it.

Mark Foster | MCC, ACTC: It often helps to show quick wins. For instance, once your team sees how auto-formatting catches stray imports or how docstrings make a confusing function crystal clear, they’ll realize it’s worth it.

Liam Garcia: Exactly. I’ll start small, maybe run a pilot on one module, let them see the difference, and then expand.

Mark Foster | MCC, ACTC: That’s a solid plan, Liam. So to recap, you’re committing to:

PEP 8 compliance via Black (or a similar auto-formatting tool).

Google-style docstrings for all modules, classes, and major functions.

A drive toward 80% test coverage, with TDD on key features.

Anything else?

Liam Garcia: That’s the core. I might also do a weekly quick code review session—just me and one other developer—so we can keep each other honest on these standards.

Mark Foster | MCC, ACTC: That sounds like a perfect next step. How are you feeling as we wrap up?

Liam Garcia: Confident. I know it’ll take some nudging, but once everyone sees the impact, I think we’ll be coding cleaner, shipping faster.

Mark Foster | MCC, ACTC: Couldn’t have said it better. Thanks for the update, Liam. I look forward to hearing how it goes once you put these into practice.

Liam Garcia: Thanks, Mark. I appreciate the guidance and encouragement. We’ll talk again soon—hopefully with good news on the coverage front!

Mark Foster | MCC, ACTC: Sounds like a plan. Take care, Liam.

"""
