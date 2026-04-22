from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

CHROMA_PATH = "./chroma_db"


def get_rag_chain():
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template(
        """
        Answer the question based only on the following context.
        If the answer is not in the context, say "I don't know."

        Context: {context}
        Question: {question}
        """
    )

    def rag_chain(question: str) -> dict:
        # Retrieve
        docs = retriever.invoke(question)
        context = "\n\n".join([doc.page_content for doc in docs])

        # Generate
        response = llm.invoke(prompt.format(context=context, question=question))
        return {"answer": response.content, "context": context, "question": question}

    return rag_chain
