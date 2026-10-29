from typing import List, Dict, Any


class GoldQuestion:
    def __init__(
        self,
        id: str,
        persona: str,
        question: str,
        expected_sources: List[str],
        expected_keywords: List[str],
        is_answerable: bool = True,
    ):
        self.id = id
        self.persona = persona
        self.question = question
        self.expected_sources = expected_sources
        self.expected_keywords = expected_keywords
        self.is_answerable = is_answerable


GOLD_QUESTIONS: List[GoldQuestion] = [
    # 1. Public questions
    GoldQuestion(
        id="GOLD-01",
        persona="intern",
        question="What are our core working hours and values?",
        expected_sources=["pub_001"],
        expected_keywords=["flexible", "10am", "3pm", "safety", "collaboration"],
        is_answerable=True,
    ),
    GoldQuestion(
        id="GOLD-02",
        persona="intern",
        question="What is the process for submitting an open source pull request?",
        expected_sources=["pub_002"],
        expected_keywords=["pull requests", "linting", "typechecks", "unit tests"],
        is_answerable=True,
    ),

    # 2. Engineering questions
    GoldQuestion(
        id="GOLD-03",
        persona="engineer",
        question="What database and retrieval architecture does our backend use?",
        expected_sources=["eng_001"],
        expected_keywords=["FastAPI", "pgvector", "Reciprocal Rank Fusion", "RRF"],
        is_answerable=True,
    ),
    GoldQuestion(
        id="GOLD-04",
        persona="engineer",
        question="Where do our production microservices deploy?",
        expected_sources=["eng_002"],
        expected_keywords=["AWS EKS", "us-west-2", "Istio", "Trivy"],
        is_answerable=True,
    ),

    # 3. HR questions
    GoldQuestion(
        id="GOLD-05",
        persona="engineer",
        question="How many days of paid time off do full time employees receive?",
        expected_sources=["hr_001"],
        expected_keywords=["25 days", "paid time off", "10 paid public holidays"],
        is_answerable=True,
    ),
    GoldQuestion(
        id="GOLD-06",
        persona="engineer",
        question="How many weeks of parental leave are employees eligible for?",
        expected_sources=["hr_002"],
        expected_keywords=["16 weeks", "fully paid", "parental leave"],
        is_answerable=True,
    ),

    # 4. Privileged questions by authorized persona
    GoldQuestion(
        id="GOLD-07",
        persona="hr_manager",
        question="What is the base salary and bonus target for the CEO?",
        expected_sources=["hr_sec_001"],
        expected_keywords=["$450,000", "80%"],
        is_answerable=True,
    ),
    GoldQuestion(
        id="GOLD-08",
        persona="finance_analyst",
        question="What is Target 1 valuation in the confidential Project Titan acquisition?",
        expected_sources=["fin_sec_001"],
        expected_keywords=["Apex Analytics", "$85M"],
        is_answerable=True,
    ),

    # 5. Unanswerable question (abstention test)
    GoldQuestion(
        id="GOLD-09",
        persona="engineer",
        question="What is our official company policy on quantum computing deployments on Mars?",
        expected_sources=[],
        expected_keywords=["not have sufficient accessible information"],
        is_answerable=False,
    ),
]
