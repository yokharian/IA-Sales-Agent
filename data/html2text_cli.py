#!/usr/bin/env python3
import os

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
import argparse
from pathlib import Path

from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import MarkdownifyTransformer


def html_to_text(url: str) -> str:
    # 1) Load HTML from the web
    loader = AsyncHtmlLoader(url, header_template=None, verify_ssl=True)
    docs = loader.load()

    # 2) Transform HTML → Markdown text using MarkdownifyTransformer
    md = MarkdownifyTransformer()
    converted_docs = md.transform_documents(docs)

    # 3) Join the content (in case the loader returns multiple documents)
    raw_text = "\n\n".join(d.page_content for d in converted_docs)
    return raw_text


def main():
    parser = argparse.ArgumentParser(
        description="Download an HTML page and convert it to plain text using LangChain MarkdownifyTransformer."
    )
    parser.add_argument("url", help="URL to download (e.g., https://example.com)")
    parser.add_argument(
        "-o",
        "--output",
        help="Output .md file (if not specified, prints to stdout)",
        default=None,
    )
    args = parser.parse_args()

    text = html_to_text(args.url)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(text, encoding="utf-8")
        print(f"✅ Text saved at: {out_path.resolve()}")
    else:
        print(text)


if __name__ == "__main__":
    main()
