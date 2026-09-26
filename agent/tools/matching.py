from difflib import SequenceMatcher
import re
import unicodedata


_INTENT_WORDS = {
    "a",
    "called",
    "folder",
    "folders",
    "for",
    "i",
    "me",
    "my",
    "open",
    "project",
    "projects",
    "the",
    "use",
}


def normalize_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value.casefold()))


def intent_name(value: str) -> str:
    normalized = normalize_name(value)
    useful = [word for word in normalized.split() if word not in _INTENT_WORDS]
    return " ".join(useful) or normalized


def match_score(query: str, candidate: str) -> float:
    normalized_query = normalize_name(query)
    normalized_candidate = normalize_name(candidate)
    if not normalized_query or not normalized_candidate:
        return 0.0
    if normalized_query == normalized_candidate:
        return 0.95

    intended_query = intent_name(query)
    intended_candidate = intent_name(candidate)
    if intended_query == intended_candidate:
        return 0.92
    query_sequence = intended_query.split()
    candidate_sequence = intended_candidate.split()
    if (
        candidate_sequence[: len(query_sequence)] == query_sequence
        or query_sequence[: len(candidate_sequence)] == candidate_sequence
    ):
        return 0.82

    query_tokens = set(intended_query.split())
    candidate_tokens = set(intended_candidate.split())
    if query_tokens and candidate_tokens:
        query_coverage = len(query_tokens & candidate_tokens) / len(query_tokens)
        candidate_coverage = len(query_tokens & candidate_tokens) / len(candidate_tokens)
        if query_coverage == 1.0:
            return 0.78 + min(0.04, candidate_coverage * 0.04)
        if query_coverage >= 0.67 and candidate_coverage >= 0.5:
            return 0.70 + min(query_coverage, candidate_coverage) * 0.1

        fuzzy_matches = sum(
            1
            for query_token in query_tokens
            if max(
                SequenceMatcher(None, query_token, candidate_token).ratio()
                for candidate_token in candidate_tokens
            )
            >= 0.75
        )
        if fuzzy_matches == len(query_tokens):
            return 0.80 + (0.06 if len(query_tokens) == len(candidate_tokens) else 0.0)

    similarity = SequenceMatcher(None, intended_query, intended_candidate).ratio()
    return 0.45 + similarity * 0.4 if similarity >= 0.62 else 0.0
