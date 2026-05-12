import hashlib
import pytest
from chromadb import EmbeddingFunction, Documents, Embeddings

from services.kb_loader import KBLoader
from services.rag import RAGService


# ── DummyEF — hash-based embedding, no model download ─────────────────

class DummyEF(EmbeddingFunction):
    """32-dimensional hash-based embedding for tests."""

    def __call__(self, input: Documents) -> Embeddings:
        return [
            [b / 255.0 for b in hashlib.sha256(t.encode()).digest()]
            for t in input
        ]


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def rag() -> RAGService:
    return RAGService(ephemeral=True, embedding_function=DummyEF())


@pytest.fixture
def rag_indexed(rag: RAGService) -> RAGService:
    kb = KBLoader()
    rag.index_kb(kb)
    return rag


# ── Before indexing ────────────────────────────────────────────────────

def test_is_indexed_false_before_indexing(rag):
    assert rag.is_indexed() is False


def test_count_zero_before_indexing(rag):
    assert rag.count() == 0


def test_query_returns_empty_string_before_indexing(rag):
    result = rag.query("créer une SARL AU")
    assert result == ""


# ── Indexing ───────────────────────────────────────────────────────────

def test_index_kb_sets_is_indexed(rag_indexed):
    assert rag_indexed.is_indexed() is True


def test_index_kb_document_count(rag_indexed):
    count = rag_indexed.count()
    assert count > 0


def test_index_kb_expected_count(rag_indexed):
    kb    = KBLoader()
    procs = kb.list_procedures()
    total_steps = sum(
        len(kb.load_procedure(p["id"]).get("etapes", []))
        for p in procs
    )
    expected = len(procs) + total_steps  # 1 overview + N steps per procedure
    assert rag_indexed.count() == expected


def test_index_kb_idempotent(rag):
    kb = KBLoader()
    rag.index_kb(kb)
    count_first = rag.count()
    rag.index_kb(kb)  # second call — should skip (not force)
    assert rag.count() == count_first


def test_index_kb_force_reruns(rag):
    kb = KBLoader()
    rag.index_kb(kb)
    count_first = rag.count()
    rag.index_kb(kb, force=True)
    assert rag.count() == count_first  # upsert = same result


# ── Query ──────────────────────────────────────────────────────────────

def test_query_returns_string(rag_indexed):
    result = rag_indexed.query("créer une SARL AU")
    assert isinstance(result, str)


def test_query_non_empty_for_kb_content(rag_indexed):
    result = rag_indexed.query("certificat negatif OMPIC")
    assert len(result) > 0


def test_query_respects_n_results(rag_indexed):
    result = rag_indexed.query("procédure Maroc", n_results=2)
    separators = result.count("---")
    assert separators <= 1  # 2 docs → max 1 separator


def test_query_with_procedure_filter(rag_indexed):
    result = rag_indexed.query("frais organisme", n_results=3,
                               procedure_id="sarl_au")
    assert isinstance(result, str)
    assert len(result) > 0


def test_query_all_procedure_ids_work(rag_indexed):
    for pid in ["sarl_au", "cnss", "ompic", "dgi", "rc"]:
        result = rag_indexed.query("etapes documents", n_results=2,
                                   procedure_id=pid)
        assert isinstance(result, str)
