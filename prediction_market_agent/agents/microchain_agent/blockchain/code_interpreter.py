from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from prediction_market_agent.utils import APIKeys


class FunctionSummary(BaseModel):
    function_name: str = Field(..., description="Name of the function or property")
    summary: str = Field(..., description="The summary assigned to this function.")


class Summaries(BaseModel):
    """Identifying information about functions/properties of the source code."""

    summaries: list[FunctionSummary]


class CodeInterpreter:
    summarization_model: str
    source_code: str
    keys: APIKeys
    retriever: VectorStoreRetriever
    rag_chain: RunnableSerializable[Any, Any]

    def __init__(self, source_code: str, summarization_model: str = "gpt-4") -> None:
        self.summarization_model = summarization_model
        self.source_code = source_code
        self.keys = APIKeys()
        self.build_retriever()
        self.build_rag_chain()

    def build_retriever(self) -> None:
        sol_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.SOL, chunk_size=128, chunk_overlap=0
        )
        docs = sol_splitter.create_documents([self.source_code])
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            api_key=self.keys.openai_api_key_secretstr_v1,
        )
        db = Chroma.from_documents(docs, embeddings)
        self.retriever = db.as_retriever(
            search_kwargs={"k": 20},
        )

    def build_rag_chain(self) -> None:
        if not self.retriever:
            self.build_retriever()

        parser_sol = PydanticOutputParser(pydantic_object=Summaries)
        template = """Answer the question based only on the following context:

        {context}

        Question: {question}

        {format_instructions}
        """
        prompt = ChatPromptTemplate.from_template(template)

        def format_docs(docs: list[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        self.rag_chain = (
            {
                "context": self.retriever | format_docs,
                "format_instructions": lambda x: parser_sol.get_format_instructions(),
                "question": RunnablePassthrough(),
            }
            | prompt
            | ChatOpenAI(
                model=self.summarization_model,
                temperature=0.0,
                api_key=APIKeys().openai_api_key_secretstr_v1,
            )
            | parser_sol
        )

    def generate_summary(self, function_names: list[str]) -> Summaries:
        function_names_formatted = "\n".join(
            ["- " + substr for substr in function_names]
        )
        result: Summaries = self.rag_chain.invoke(
            f"Create a summary for the function names listed below. Summarize, for each function, its purpose and what it does. You must produce a summary for all the functions listed below. \n  {function_names_formatted}."
        )
        return result
