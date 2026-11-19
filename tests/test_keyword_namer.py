from analytics.KeywordNamer import KeywordNamer


def test_larger_topics_drive_the_group_name():
    namer = KeywordNamer()
    small = ([("storm", 1.0), ("rain", 0.5)], 10)
    large = ([("election", 1.0), ("senate", 0.8)], 90)
    keywords = namer.combine([small, large])
    assert namer.name(keywords) == "Election, Senate"


def test_overlapping_keywords_are_dropped():
    assert KeywordNamer.remove_overlaps(["ghana", "ghanamma com", "ghanamma", "us senate", "senate"]) == [
        "ghana",
        "ghanamma com",
        "us senate",
    ]


def test_numbers_and_web_parts_are_skipped_in_names():
    namer = KeywordNamer()
    assert namer.name(["18 2026", "ghanamma com", "measles", "outbreak"]) == "Measles, Outbreak"


def test_avoided_names_pick_the_next_pair():
    namer = KeywordNamer()
    assert namer.name(["ai", "nigeria", "music"], avoid={"AI, Nigeria"}) == "AI, Music"


def test_empty_keywords_get_a_clear_name():
    assert KeywordNamer().name([]) == "No descriptive terms"
