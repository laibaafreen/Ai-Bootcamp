import os
import sys
import types
import uuid
import urllib.request
from typing import List, Optional, Dict

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

PDF_URL = "https://www.planetebook.com/free-ebooks/crime-and-punishment.pdf"
PDF_PATH = "crime_and_punishment.pdf"
PERSIST_DIR = "chroma_db"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
TOP_K = 4


@st.cache_resource(show_spinner=False)
def get_vector_store():
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if os.path.isdir(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        return Chroma(persist_directory=PERSIST_DIR, embedding_function=embedding_model)

    if not os.path.exists(PDF_PATH):
        urllib.request.urlretrieve(PDF_URL, PDF_PATH)

    loader = PyPDFLoader(PDF_PATH)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(pages)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=PERSIST_DIR,
    )
    vectordb.persist()
    return vectordb


def retrieve_context(query: str, k: int = TOP_K) -> List[str]:
    vectordb = get_vector_store()
    docs = vectordb.similarity_search(query, k=k)
    return [d.page_content for d in docs]


@st.cache_resource(show_spinner=False)
def get_llm():
    import google.generativeai as genai

    if not GEMINI_API_KEY:
        st.error("GEMINI_API_KEY is missing. Add it to your .env file.")
        st.stop()
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(model_name="models/gemini-3.6-flash")


def build_prompt(question: str, contexts: List[str], history: Optional[List[Dict]] = None) -> str:
    context_block = "\n\n---\n\n".join(contexts)

    history_block = ""
    if history:
        turns = []
        for turn in history:
            speaker = "User" if turn["role"] == "user" else "Assistant"
            turns.append(f"{speaker}: {turn['message']}")
        history_block = "Conversation so far:\n" + "\n".join(turns) + "\n\n"

    return f"""You are a helpful assistant answering questions about the novel
"Crime and Punishment" by Fyodor Dostoevsky, using only the context passages
provided below. If the answer isn't contained in the context, say you don't
know instead of guessing.

{history_block}Context passages from the novel:
{context_block}

Question: {question}

Answer clearly and concisely, grounded only in the context above:"""


def generate_answer(question: str, history: Optional[List[Dict]] = None):
    contexts = retrieve_context(question)
    prompt = build_prompt(question, contexts, history)
    response = get_llm().generate_content(prompt)
    return response.text, contexts


def get_supabase_client():
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("SUPABASE_URL / SUPABASE_KEY missing. Add them to your .env file.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def load_history_from_db(session_id: str) -> List[Dict]:
    client = get_supabase_client()
    res = (
        client.table("chats")
        .select("role, message")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


def save_message_to_db(session_id: str, role: str, message: str) -> None:
    client = get_supabase_client()
    client.table("chats").insert(
        {"session_id": session_id, "role": role, "message": message}
    ).execute()


st.set_page_config(page_title="Crime & Punishment RAG", page_icon="📖", layout="wide")
st.title("📖 Crime and Punishment — RAG App")

mode = st.sidebar.radio(
    "Mode:",
    [
        "Single-turn chat",
        "Multi-turn chat (session memory)",
        "Multi-turn chat (saved history)",
        "Evaluate answers",
    ],
)

with st.spinner("Loading the book index..."):
    get_vector_store()


if mode == "Single-turn chat":
    st.caption("Each question is answered independently.")

    question = st.chat_input("Ask something about Crime and Punishment...")
    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving context and generating an answer..."):
                answer, contexts = generate_answer(question)
            st.write(answer)
            with st.expander("Retrieved context chunks"):
                for i, c in enumerate(contexts, start=1):
                    st.markdown(f"**Chunk {i}:**\n\n{c}")


elif mode == "Multi-turn chat (session memory)":
    st.caption("Remembers the conversation while the app is open.")

    if "chat_memory" not in st.session_state:
        st.session_state.chat_memory = []

    for turn in st.session_state.chat_memory:
        with st.chat_message("user" if turn["role"] == "user" else "assistant"):
            st.write(turn["message"])

    question = st.chat_input("Ask something about Crime and Punishment...")
    if question:
        st.session_state.chat_memory.append({"role": "user", "message": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer, contexts = generate_answer(
                    question, history=st.session_state.chat_memory[:-1]
                )
            st.write(answer)
            with st.expander("Retrieved context chunks"):
                for i, c in enumerate(contexts, start=1):
                    st.markdown(f"**Chunk {i}:**\n\n{c}")
        st.session_state.chat_memory.append({"role": "ai", "message": answer})

    if st.session_state.chat_memory:
        if st.button("Clear conversation", key="clear_memory"):
            st.session_state.chat_memory = []
            st.rerun()


elif mode == "Multi-turn chat (saved history)":
    st.caption("Conversation history is saved and survives app restarts.")

    if "session_id" not in st.session_state:
        st.session_state.session_id = st.query_params.get("session_id", str(uuid.uuid4()))
        st.query_params["session_id"] = st.session_state.session_id
    st.caption(f"Session ID: `{st.session_state.session_id}` — bookmark this URL to resume later.")

    if "chat_saved" not in st.session_state:
        st.session_state.chat_saved = load_history_from_db(st.session_state.session_id)

    for turn in st.session_state.chat_saved:
        with st.chat_message("user" if turn["role"] == "user" else "assistant"):
            st.write(turn["message"])

    question = st.chat_input("Ask something about Crime and Punishment...")
    if question:
        st.session_state.chat_saved.append({"role": "user", "message": question})
        save_message_to_db(st.session_state.session_id, "user", question)
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer, contexts = generate_answer(
                    question, history=st.session_state.chat_saved[:-1]
                )
            st.write(answer)
            with st.expander("Retrieved context chunks"):
                for i, c in enumerate(contexts, start=1):
                    st.markdown(f"**Chunk {i}:**\n\n{c}")
        st.session_state.chat_saved.append({"role": "ai", "message": answer})
        save_message_to_db(st.session_state.session_id, "ai", answer)


elif mode == "Evaluate answers":
    st.caption("Runs a small Q&A test set through the pipeline and scores the answers.")

    eval_set = [
        {
            "question": "Who is the protagonist of Crime and Punishment?",
            "ground_truth": "The protagonist is Rodion Romanovich Raskolnikov, a poor "
            "former student in St. Petersburg who murders a pawnbroker.",
        },
        {
            "question": "Why does Raskolnikov murder the pawnbroker?",
            "ground_truth": "Raskolnikov murders the old pawnbroker Alyona Ivanovna partly "
            "out of poverty and partly to test his theory that certain 'extraordinary' "
            "people are above conventional morality and may transgress the law for a "
            "greater purpose.",
        },
        {
            "question": "Who is Sonia and what role does she play in the novel?",
            "ground_truth": "Sonia Marmeladova is a young woman forced into prostitution to "
            "support her family; she becomes Raskolnikov's moral and spiritual guide, "
            "urging him toward confession and redemption.",
        },
        {
            "question": "Which investigator suspects Raskolnikov of the murders?",
            "ground_truth": "Porfiry Petrovich is the magistrate who suspects Raskolnikov "
            "and psychologically pressures him toward confession.",
        },
        {
            "question": "How does the novel end for Raskolnikov?",
            "ground_truth": "Raskolnikov confesses to the murders, is sent to a Siberian "
            "prison camp, and begins a path toward spiritual redemption with Sonia's support.",
        },
    ]

    st.write(f"Evaluation set has **{len(eval_set)}** questions.")
    for item in eval_set:
        st.markdown(f"- {item['question']}")

    if st.button("Run evaluation"):
        from datasets import Dataset

        # Some ragas builds try to import a VertexAI module that no longer
        # exists in newer langchain-community versions. This app never uses
        # VertexAI, so stub the module out to avoid the import crash.
        if "langchain_community.chat_models.vertexai" not in sys.modules:
            try:
                import langchain_community.chat_models.vertexai  # noqa: F401
            except ModuleNotFoundError:
                stub = types.ModuleType("langchain_community.chat_models.vertexai")

                class _DummyChatVertexAI:
                    def __init__(self, *args, **kwargs):
                        raise RuntimeError("VertexAI is not used in this app.")

                stub.ChatVertexAI = _DummyChatVertexAI
                sys.modules["langchain_community.chat_models.vertexai"] = stub

        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_huggingface import HuggingFaceEmbeddings

        rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

        progress = st.progress(0.0, text="Running questions through the pipeline...")
        for i, item in enumerate(eval_set):
            answer, contexts = generate_answer(item["question"])
            rows["question"].append(item["question"])
            rows["answer"].append(answer)
            rows["contexts"].append(contexts)
            rows["ground_truth"].append(item["ground_truth"])
            progress.progress((i + 1) / len(eval_set), text=f"Answered {i + 1}/{len(eval_set)}")

        dataset = Dataset.from_dict(rows)

        judge_llm = LangchainLLMWrapper(
            ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=GEMINI_API_KEY)
        )
        judge_embeddings = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        )

        with st.spinner("Scoring answers..."):
            result = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=judge_llm,
                embeddings=judge_embeddings,
            )

        st.success("Evaluation complete!")
        df = result.to_pandas()
        st.dataframe(df)

        df.to_csv("ragas_results.csv", index=False)
        st.download_button(
            "Download results as CSV",
            data=df.to_csv(index=False),
            file_name="ragas_results.csv",
            mime="text/csv",
        )
