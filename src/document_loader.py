import os
from typing import List, Iterable, Tuple

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)


class DocumentLoader:
    def __init__(self, documents_path: str, encoding: str = "utf-8"):
        """
        Initialize a loader for reading plain-text documents.

        :param documents_path: Base directory containing .txt documents.
        :param encoding: File encoding to use when reading.
        """
        self.documents_path = documents_path
        self.encoding = encoding

    def _iter_files(self) -> Iterable[Tuple[str, List[str]]]:
        """Yield a single (root, files) pair for the target directory."""
        if not os.path.isdir(self.documents_path):
            return []
        root = self.documents_path
        try:
            files = os.listdir(root)
        except OSError:
            files = []
        yield root, files

    def load_documents(self, chunk_size=1000, chunk_overlap=200) -> List[Document]:
        """
        Load .txt documents from the configured directory.

        - Skips hidden files.
        - Ignores read errors and undecodable characters.
        - Returns documents in deterministic (sorted) order.
        """
        output: List[Document] = []
        if not os.path.isdir(self.documents_path):
            return output

        for root, files in self._iter_files():
            for filename in sorted(
                f
                for f in files
                if (f.endswith(".txt") or f.endswith(".md")) and not f.startswith(".")
            ):
                path = os.path.join(root, filename)
                try:
                    loader = TextLoader(file_path=path, encoding=self.encoding)
                    raw_docs: List[Document] = loader.load()

                    # 1) Split por headers SOLO si es .md
                    docs_to_split: List[Document] = []
                    if filename.endswith(".md"):
                        mds = []
                        md_splitter = MarkdownHeaderTextSplitter(
                            headers_to_split_on=[
                                ("#", "h1"),
                                ("##", "h2"),
                                ("###", "h3"),
                            ],
                            strip_headers=False,
                        )
                        for d in raw_docs:
                            mds.extend(md_splitter.split_text(d.page_content))
                        docs_to_split = mds

                        chunks = []
                        for d in docs_to_split:
                            # Añade metadatos útiles para trazabilidad
                            d.metadata.setdefault("source", str(path))
                            d.metadata.setdefault("filename", filename)
                            chunks.append(d)
                    else:
                        docs_to_split = raw_docs

                        # 2) Split recursivo en chunks
                        rc_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            separators=["\n\n", "\n", ". ", ", ", " ", ""],
                            add_start_index=True,
                        )
                        chunks = []
                        for d in docs_to_split:
                            for c in rc_splitter.split_documents([d]):
                                # Añade metadatos útiles para trazabilidad
                                c.metadata.setdefault("source", str(path))
                                c.metadata.setdefault("filename", filename)
                                chunks.append(c)

                    # Indexa
                    for idx, c in enumerate(chunks):
                        c.metadata["chunk_id"] = idx
                    output.extend(chunks)

                except OSError:
                    # Skip files that cannot be opened/read
                    print(OSError)
                    continue

        return output
