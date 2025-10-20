import os
from typing import List, Iterable, Tuple

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


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

    def load_documents(self, chunk_size=500, chunk_overlap=100) -> List[Document]:
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
                    documents: List[Document] = TextLoader(
                        file_path=path, encoding=self.encoding
                    ).load()
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=chunk_size, chunk_overlap=chunk_overlap
                    )
                    texts = text_splitter.split_documents(documents)
                    for idx, text in enumerate(texts):
                        text.metadata["id"] = idx
                    output.extend(texts)
                except OSError:
                    # Skip files that cannot be opened/read
                    print(OSError)
                    continue

        return output
