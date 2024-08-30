import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


os.environ["OPENAI_API_KEY"] = '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'
C_DIR = os.path.dirname(__file__)

system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)


@csrf_exempt
# Create your views here.
def upload_files(request):
    '''
    POST api to upload PDF and JSON files
    '''
    if request.method == 'POST':
        if 'pdf_file' in request.FILES and 'json_file' in request.FILES:
            pdf_file = request.FILES['pdf_file']
            json_file = request.FILES['json_file']
            # Define upload paths
            pdf_path = os.path.join(C_DIR, 'uploads', 'context.pdf')
            json_path = os.path.join(C_DIR, 'uploads', 'Questions.json')

            # Save PDF file
            with open(pdf_path, 'wb+') as pdf_destination:
                for chunk in pdf_file.chunks():
                    pdf_destination.write(chunk)

            # Save JSON file
            with open(json_path, 'wb+') as json_destination:
                for chunk in json_file.chunks():
                    json_destination.write(chunk)

            return JsonResponse({'message': 'Files uploaded successfully.'}, status=201)
        return JsonResponse({'error': 'Both files must be uploaded.'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

def get_retriever():
    
    pdf_path = os.path.join(C_DIR, 'uploads', 'context.pdf')
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    return vectorstore.as_retriever()

def get_json_question():
    '''
    Return all the questions
    from json file
    '''
    json_path = os.path.join(C_DIR, 'uploads', 'Questions.json')
    with open(json_path, 'r') as file:
    # Load the content of the file into a Python dictionary
        data = json.load(file)
    return data

def generate_answers(request):
    '''
    View which will generate answers of each question
    present in question.json file and return the 
    JSON of answers
    '''

    # Step 1 - load the pdf and get the vector store
    retriever = get_retriever()
    # Step 2 - Read Questions File
    questions = get_json_question()

    llm = ChatOpenAI(model="gpt-3.5-turbo")

    prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    ques_ans = {}
    for question in questions:
        results = rag_chain.invoke({"input": question})
        ques_ans[question] = results['answer']
    return JsonResponse(ques_ans, status=201)
