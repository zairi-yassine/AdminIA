from pathlib import Path
from typing import Any

import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.utils import embedding_functions

VECTORS_DIR = Path(__file__).parent.parent / "data" / "vectors"
_COLLECTION  = "maa_kb"


class RAGService:

    def __init__(
        self,
        persist_dir:        str | None = None,
        ephemeral:          bool       = False,
        embedding_function: Any | None = None,
    ):
        if ephemeral:
            self.client: chromadb.ClientAPI = chromadb.EphemeralClient()
        else:
            path = persist_dir or str(VECTORS_DIR)
            Path(path).mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=path)

        self._ef = (
            embedding_function
            or embedding_functions.DefaultEmbeddingFunction()
        )
        self.collection = self.client.get_or_create_collection(
            name=_COLLECTION,
            embedding_function=self._ef,
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_kb(self, kb_loader: Any, force: bool = False):
        if not force and self.is_indexed():
            return

        documents: list[str]  = []
        metadatas: list[dict] = []
        ids:       list[str]  = []

        for proc_meta in kb_loader.list_procedures():
            pid       = proc_meta["id"]
            procedure = kb_loader.load_procedure(pid)

            overview = (
                f"Procedure : {procedure['titre']}\n"
                f"Organismes : {', '.join(procedure.get('organisme', []))}\n"
                f"Duree estimee : {procedure.get('duree_est', '-')}\n"
                f"Description : {procedure.get('description', '')}\n"
            )
            documents.append(overview)
            metadatas.append(
                {"procedure_id": pid, "type": "overview", "step_id": 0}
            )
            ids.append(f"{pid}_overview")

            for step in procedure.get("etapes", []):
                step_doc = (
                    f"Etape {step['id']} - {step['titre']}\n"
                    f"Procedure : {procedure['titre']}\n"
                    f"Organisme : {step.get('organisme', '-')}\n"
                    f"Description : {step.get('description', '')}\n"
                    f"Documents requis : {', '.join(step.get('docs_requis', []))}\n"
                    f"Frais : {step.get('frais', 0)} MAD\n"
                    f"Delai : {step.get('delai', '-')}\n"
                )
                if step.get("lien_officiel"):
                    step_doc += f"Lien officiel : {step['lien_officiel']}\n"
                documents.append(step_doc)
                metadatas.append(
                    {"procedure_id": pid, "type": "step", "step_id": step["id"]}
                )
                ids.append(f"{pid}_step_{step['id']}")

        if documents:
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def query(
        self,
        text:         str,
        n_results:    int        = 3,
        procedure_id: str | None = None,
    ) -> str:
        count = self.collection.count()
        if count == 0:
            return ""

        kwargs: dict = {
            "query_texts": [text],
            "n_results":   min(n_results, count),
        }
        if procedure_id:
            kwargs["where"] = {"procedure_id": procedure_id}

        results = self.collection.query(**kwargs)

        if not results or not results.get("documents") or not results["documents"][0]:
            return ""

        return "\n---\n".join(results["documents"][0])

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------

    def is_indexed(self) -> bool:
        return self.collection.count() > 0

    def count(self) -> int:
        return self.collection.count()
