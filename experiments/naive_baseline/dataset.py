"""
Fixed synthetic test workload for the naive baseline.

Per the handbook: the workload must be defined before running the benchmark, and must include
irrelevant/contradictory memories, preferences that change over time, long conversations with a
constrained context budget, multiple users with similarly worded information, sensitive
information that should not be retained, and cold-start/no-relevant-memory cases.

No randomness anywhere in this file -- every case is hand-written and fixed, so the run is fully
reproducible without needing a seed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

BASE_TIME = datetime(2026, 1, 1, 9, 0, 0)


def days(n: int) -> datetime:
    return BASE_TIME + timedelta(days=n)


@dataclass
class StoredMemory:
    text: str
    timestamp: datetime
    sensitive: bool = False


@dataclass
class TestCase:
    case_id: str
    category: str
    user_id: str
    stored: list[StoredMemory]          # memories to seed into the store before the query
    query: str
    correct_texts: list[str]            # ground-truth text(s) that should be retrieved/ranked highest
    stale_texts: list[str] = field(default_factory=list)   # superseded memories that should NOT outrank correct_texts
    sensitive_texts: list[str] = field(default_factory=list)  # should never surface in retrieval/injection
    expect_no_result: bool = False      # cold-start cases: nothing relevant should be found
    token_budget: int = 200             # per-case injection budget; overridden for the long-conversation cases
    notes: str = ""


CASES: list[TestCase] = [

    # --- Category 1: irrelevant and contradictory memories ---
    TestCase(
        case_id="c1-irrelevant-noise",
        category="irrelevant_and_contradictory",
        user_id="alice",
        stored=[
            StoredMemory("Alice's favorite coffee order is a flat white.", days(0)),
            StoredMemory("Alice mentioned she watched a documentary about deep sea creatures.", days(1)),
            StoredMemory("Alice's project uses PostgreSQL as the primary database.", days(2)),
            StoredMemory("Alice complained about traffic on her commute this morning.", days(3)),
        ],
        query="What database is Alice's project using?",
        correct_texts=["Alice's project uses PostgreSQL as the primary database."],
        notes="Simple relevance check with plausible distractors in the same store.",
    ),
    TestCase(
        case_id="c1-direct-contradiction",
        category="irrelevant_and_contradictory",
        user_id="bob",
        stored=[
            StoredMemory("Bob said the project deadline is flexible and can slip a week if needed.", days(0)),
            StoredMemory("Bob later said the deadline is now hard -- no slippage allowed, client-mandated.", days(5)),
        ],
        query="Is Bob's project deadline flexible?",
        correct_texts=["Bob later said the deadline is now hard -- no slippage allowed, client-mandated."],
        stale_texts=["Bob said the project deadline is flexible and can slip a week if needed."],
        notes="Two memories directly contradict each other; the naive baseline has no supersession mechanism.",
    ),

    # --- Category 2: preferences that change over time ---
    TestCase(
        case_id="c2-payment-gateway-wording",
        category="preferences_over_time",
        user_id="carla",
        stored=[
            StoredMemory("Carla decided to integrate a payment gateway using Stripe.", days(0)),
            StoredMemory("Carla later switched and is now using a checkout integration built on Adyen instead of Stripe.", days(10)),
        ],
        query="Which provider is Carla using for checkout integration?",
        correct_texts=["Carla later switched and is now using a checkout integration built on Adyen instead of Stripe."],
        stale_texts=["Carla decided to integrate a payment gateway using Stripe."],
        notes="Directly modeled on Deliverable 1's own failure evidence example (payment gateway vs checkout integration wording).",
    ),
    TestCase(
        case_id="c2-tech-stack-preference",
        category="preferences_over_time",
        user_id="dev_raj",
        stored=[
            StoredMemory("Raj prefers to write backend services in Python with Flask.", days(0)),
            StoredMemory("Raj has since moved his team fully onto Node.js and no longer wants Python suggested for new backend work.", days(20)),
        ],
        query="What backend language should be suggested for Raj's new service?",
        correct_texts=["Raj has since moved his team fully onto Node.js and no longer wants Python suggested for new backend work."],
        stale_texts=["Raj prefers to write backend services in Python with Flask."],
        notes="Directly mirrors the 'contradictory suggestions' failure from Deliverable 1's personal evidence.",
    ),

    # --- Category 3: long conversations with a constrained context budget ---
    TestCase(
        case_id="c3-long-history-budget",
        category="long_conversation_budget",
        user_id="elena",
        stored=[
            StoredMemory(f"Elena mentioned minor detail number {i} about her project setup.", days(i))
            for i in range(0, 18)
        ] + [
            StoredMemory("Elena's actual architectural decision: the system must run fully offline with no external API calls.", days(19)),
        ],
        query="Does Elena's system need to work offline?",
        correct_texts=["Elena's actual architectural decision: the system must run fully offline with no external API calls."],
        token_budget=40,  # deliberately tight -- forces truncation with a naive rank-order injector
        notes="Nineteen memories total; the one that matters is buried among low-value filler, under a tight token budget.",
    ),

    # --- Category 4: multiple users with similarly worded information ---
    TestCase(
        case_id="c4-cross-user-similar-wording",
        category="multiple_users_similar_wording",
        user_id="farah",
        stored=[
            StoredMemory("Farah's team uses a microservices architecture with gRPC between services.", days(0)),
        ],
        query="What architecture does Farah's team use?",
        correct_texts=["Farah's team uses a microservices architecture with gRPC between services."],
        notes=(
            "Paired with c4-cross-user-similar-wording-b (different user, near-identical wording). "
            "Isolation is checked by confirming Farah's query never returns the other user's memory."
        ),
    ),
    TestCase(
        case_id="c4-cross-user-similar-wording-b",
        category="multiple_users_similar_wording",
        user_id="george",
        stored=[
            StoredMemory("George's team uses a microservices architecture with gRPC between services too.", days(0)),
        ],
        query="What architecture does Farah's team use?",  # deliberately George's store queried with Farah's question
        correct_texts=[],
        expect_no_result=False,  # George's own memory will match lexically -- that's the point being tested
        notes=(
            "Cross-tenant check: this query is run against George's store using Farah's question text. "
            "A correct system would return nothing relevant to *this specific user's actual question intent* "
            "since George's memory is superficially similar but not what was asked about. The naive store is "
            "isolated by user_id at query time (see memory_store.py), so no literal cross-user leak occurs -- "
            "the risk this case actually demonstrates is that near-identical wording across users would collide "
            "immediately if isolation were ever done by content similarity alone instead of a hard user_id filter."
        ),
    ),

    # --- Category 5: sensitive information that should not be retained ---
    TestCase(
        case_id="c5-sensitive-leak-check",
        category="sensitive_information",
        user_id="hana",
        stored=[
            StoredMemory("Hana's project uses AWS for hosting.", days(0)),
            StoredMemory("Hana mentioned her home address while explaining a shipping integration test case.", days(1), sensitive=True),
            StoredMemory("Hana pasted a database password into the chat while debugging a connection issue.", days(2), sensitive=True),
        ],
        query="What hosting provider does Hana's project use, and what other details came up recently?",
        correct_texts=["Hana's project uses AWS for hosting."],
        sensitive_texts=[
            "Hana mentioned her home address while explaining a shipping integration test case.",
            "Hana pasted a database password into the chat while debugging a connection issue.",
        ],
        notes="Naive retrieval has no admission-time or retrieval-time sensitivity filter, so these should surface -- that's the failure being measured.",
    ),

    # --- Category 6: cold-start and no-relevant-memory cases ---
    TestCase(
        case_id="c6-cold-start-new-user",
        category="cold_start",
        user_id="ivan",
        stored=[],
        query="What did we agree on for the deployment pipeline?",
        correct_texts=[],
        expect_no_result=True,
        notes="Brand-new user, empty store -- correct behavior is returning nothing, not hallucinating a match.",
    ),
    TestCase(
        case_id="c6-no-relevant-memory-exists",
        category="cold_start",
        user_id="julia",
        stored=[
            StoredMemory("Julia likes her documentation written in Markdown.", days(0)),
            StoredMemory("Julia's favorite lunch spot is the taco place near the office.", days(1)),
        ],
        query="What testing framework does Julia want to use for the new service?",
        correct_texts=[],
        expect_no_result=True,
        notes="Store is non-empty but nothing in it is relevant to the query -- tests whether similarity search forces a false match.",
    ),
]


def all_cases() -> list[TestCase]:
    return CASES
