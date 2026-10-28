from src.rag.bm25 import bm25_scores, fold, tokenize


def test_fold_strips_vietnamese_diacritics():
    assert fold("Đà Nẵng, HỌC Python") == "da nang, hoc python"


def test_tokenize_adds_syllable_bigrams():
    tokens = tokenize("Học sinh giỏi")
    assert tokens[:3] == ["hoc", "sinh", "gioi"]
    assert "hoc_sinh" in tokens and "sinh_gioi" in tokens


def test_exact_term_ranks_first_and_unrelated_scores_zero():
    docs = ["Mình dùng Kubernetes để deploy", "Học Python ở đâu", "Giá xe máy tháng này"]
    scores = bm25_scores("kubernetes", docs)
    assert scores[0] > 0
    assert scores[1] == scores[2] == 0


def test_query_without_diacritics_matches_text_with_them():
    scores = bm25_scores("hoc python", ["Học Python ở đâu cho nhanh", "Xe máy nào bền"])
    assert scores[0] > scores[1] == 0


def test_bigram_prefers_the_phrase_over_reversed_syllables():
    scores = bm25_scores("học sinh", ["học sinh giỏi cấp ba", "môn sinh học khó quá"])
    assert scores[0] > scores[1] > 0


def test_empty_corpus():
    assert bm25_scores("python", []) == []
