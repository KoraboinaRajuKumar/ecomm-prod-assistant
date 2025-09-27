import sys
import os
from pathlib import Path
# Add project root to sys.path for direct script run
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from prod_assistant.prompt_library.prompts import PROMPT_REGISTRY, PromptType
from prod_assistant.retriever.retrieval import Retriever
from prod_assistant.utils.model_loader import ModelLoader

retriever_obj = Retriever()
model_loader = ModelLoader()


def format_docs(docs) -> str:
    """Format retrieved documents into a structured text block for the prompt."""
    if not docs:
        return "No relevant documents found."

    formatted_chunks = []
    for d in docs:
        meta = d.metadata or {}
        formatted = (
            f"Title: {meta.get('product_title', 'N/A')}\n"
            f"Price: {meta.get('price', 'N/A')}\n"
            f"Rating: {meta.get('rating', 'N/A')}\n"
            f"Reviews:\n{d.page_content.strip()}"
        )
        formatted_chunks.append(formatted)

    return "\n\n---\n\n".join(formatted_chunks)


def build_chain():
    """Build the RAG pipeline chain with retriever, prompt, LLM, and parser."""
    retriever = retriever_obj.load_retriever()
    llm = model_loader.load_llm()
    prompt = ChatPromptTemplate.from_template(
        PROMPT_REGISTRY[PromptType.PRODUCT_BOT].template
    )

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def invoke_chain(query: str, debug: bool = False) -> str:
    """Run the chain with a user query."""
    chain = build_chain()

    if debug:
        # For debugging: show docs retrieved before passing to LLM
        docs = retriever_obj.load_retriever().invoke(query)
        print("\nRetrieved Documents:")
        print(format_docs(docs))
        print("\n---\n")

    return chain.invoke(query)

class AgenticRAG:
    """Agentic RAG workflow wrapper for FastAPI and other integrations."""
    def run(self, query: str) -> str:
        return invoke_chain(query)

if __name__ == "__main__":
    try:
        answer = invoke_chain("can you tell me the price of the iPhone 16 pro?")
        print("\n Assistant Answer:\n", answer)
    except Exception as e:
        print("Exception occurred:", str(e))
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass
