"""Turn c-TF-IDF keywords into short readable names."""

from collections import defaultdict


class KeywordNamer:
    """Pick keywords for a topic or a group of topics and build a name from them.

    Groups combine the keywords of their topics. Each topic's keyword scores
    are first scaled to sum to one, then weighted by the topic's article
    count, so larger topics drive the group name.
    """

    # Short keywords that read better in upper case.
    ACRONYMS = set(
        "us uk eu un ai nfl nba fbi gop ipo ceo nhl mlb nhs cfp ufc bjp gta vi fm nasa fda cdc imf uae".split()
    )

    WEB_PARTS = {"com", "www", "http", "https", "html"}

    # Brand names with their own capitalization.
    SPECIAL_CASES = {
        "iphone": "iPhone",
        "ipad": "iPad",
        "openai": "OpenAI",
        "tiktok": "TikTok",
        "youtube": "YouTube",
        "linkedin": "LinkedIn",
        "mcgraw": "McGraw",
        "playstation": "PlayStation",
    }

    def __init__(self, words_in_name: int = 2, keywords_kept: int = 8):
        self.words_in_name = words_in_name
        self.keywords_kept = keywords_kept

    def combine(self, weighted_keywords: list[tuple[list[tuple[str, float]], float]]) -> list[str]:
        """Merge several keyword lists into one ranked list.

        Args:
            weighted_keywords: [(keywords with scores, weight)], one item per topic.
        """
        totals = defaultdict(float)
        for keywords, weight in weighted_keywords:
            score_sum = sum(score for _, score in keywords) or 1.0
            for word, score in keywords:
                totals[word] += weight * score / score_sum
        ranked = sorted(totals, key=lambda word: (-totals[word], word))
        return self.remove_overlaps(ranked)[: self.keywords_kept]

    @staticmethod
    def remove_overlaps(words: list[str]) -> list[str]:
        """Drop a keyword when it repeats a word already kept.

        For example "ghanamma com" is dropped after "ghanamma", and "senate"
        is dropped after "us senate".
        """
        kept = []
        kept_tokens = set()
        for word in words:
            tokens = set(word.split())
            if tokens & kept_tokens:
                continue
            kept.append(word)
            kept_tokens |= tokens
        return kept

    def name(self, keywords: list[str], avoid: set[str] | None = None) -> str:
        """Build a name such as "Election, Senate" from the best keywords.

        Keywords with a bare number (such as "18 2026") or a web address part
        (such as "ghanamma com") are skipped when there are enough others,
        because they rarely say what a story is about. They stay in the
        keyword list. Names in avoid are not reused: the next best pair of
        keywords is taken instead, so a group never shares a name with a
        topic or group inside it.
        """
        avoid = avoid or set()
        readable = [word for word in keywords if not self.is_noise(word)]
        words = readable if len(readable) >= self.words_in_name else keywords
        if not words:
            return "No descriptive terms"
        for chosen in self.keyword_pairs(words):
            name = ", ".join(self.capitalize(word) for word in chosen)
            if name not in avoid:
                return name
        return ", ".join(self.capitalize(word) for word in words[: self.words_in_name + 1])

    def keyword_pairs(self, words: list[str]) -> list[tuple[str, ...]]:
        """Candidate keyword combinations, best first: (1, 2), (1, 3), (2, 3), (1, 4) and so on."""
        if len(words) < self.words_in_name or self.words_in_name != 2:
            return [tuple(words[: self.words_in_name])]
        pairs = [(first, second) for first in range(len(words)) for second in range(first + 1, len(words))]
        pairs.sort(key=lambda pair: (pair[0] + pair[1], pair[0]))
        return [(words[first], words[second]) for first, second in pairs]

    def is_noise(self, word: str) -> bool:
        return any(part.isdigit() or part in self.WEB_PARTS for part in word.split())

    def capitalize(self, word: str) -> str:
        """Capitalize each part of a keyword, keeping acronyms and brand names as they are written."""
        return " ".join(self.capitalize_part(part) for part in word.split())

    def capitalize_part(self, part: str) -> str:
        if part in self.SPECIAL_CASES:
            return self.SPECIAL_CASES[part]
        if part in self.ACRONYMS:
            return part.upper()
        return part.capitalize()
