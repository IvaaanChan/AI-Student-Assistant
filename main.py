import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# Get your API keys from openai, you will need to create an account. 
os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"


def convert(document):
    text = ""
    for pdf in document:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def chunk(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap  = 24,
    )
    chunks = text_splitter.split_text(text)
    return chunks
    
def vectorstore(chunks):
    db = FAISS.from_texts(texts=chunks, embedding=OpenAIEmbeddings())
    return db

def qa_chain(vectorstore):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo")    #Choose the model you want to use, can also use gpt-4 if you have access to it

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return qa_chain


st.set_page_config(page_title="PDFchatbot", page_icon=":robot_face:")
st.header(":books: Ask me anything about your PDF:nerd_face::books:")

with st.sidebar:
    st.subheader("Your documents")
    document = st.file_uploader("Upload your PDFs here and click 'Submit', Then I will start to learn!", accept_multiple_files=True)

    if st.button("Submit"):
            with st.spinner("Processing"):
                raw_text = convert(document)
                text_chunks = chunk(raw_text)
                vectorstore = vectorstore(text_chunks)
                st.session_state.answer = qa_chain(vectorstore)
                st.write("Finish Loading!")


if "chat_history" not in st.session_state.keys(): 
    st.session_state.chat_history = [{"role": "assistant", "content": "Hello human!"}]
if "answer" not in st.session_state.keys():
    st.session_state.answer = None


for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Your question:")    
if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

if st.session_state.chat_history[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.answer({"question": prompt})
            st.write(response["answer"]) 

    message = {"role": "assistant", "content": response["answer"]}

    st.session_state.chat_history.append(message)

