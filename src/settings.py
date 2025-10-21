from os import getenv

from dotenv import load_dotenv

load_dotenv()

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI

    OPENAI_EMBEDDINGS = OpenAIEmbeddings(model="text-embedding-3-large")

except ImportError as exception:
    OPENAI_EMBEDDINGS = None

try:
    from langchain_huggingface import HuggingFaceEmbeddings

    HUGGING_FACE_EMBEDDINGS = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True},
    )

except ImportError as exception:
    HUGGING_FACE_EMBEDDINGS = None


EMBEDDING_FUNCTIONS = dict(
    HUGGING_FACE=HUGGING_FACE_EMBEDDINGS,
    OPENAI=OPENAI_EMBEDDINGS,
)
EMBEDDING_PROVIDER = getenv("EMBEDDING_PROVIDER", "HUGGING_FACE")
EMBEDDING_FUNCTION = EMBEDDING_FUNCTIONS[EMBEDDING_PROVIDER]
SYSTEM_PROMPT = "Eres un asistente de QA." + (
    " Usa SÓLO el contexto recuperado para responder. "
    "Si no hay suficiente contexto o no estás seguro, di explícitamente que no lo sabes. "
    "Cita las fuentes con el campo 'source' de cada fragmento.\n"
    "Contexto:\n{context}"
)
