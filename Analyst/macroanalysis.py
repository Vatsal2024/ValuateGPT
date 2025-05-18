import fitz  # PyMuPDF
from tqdm.auto import tqdm
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

class MacroeconomicAnalyzer:
    def __init__(self, pdf_path, company, openai_api_key):
        self.pdf_path = pdf_path
        self.company = company
        self.openai_api_key = openai_api_key
        self.documents = []
        self.splits = []
        self.vectorstore = None
        self.retriever = None
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0,
            openai_api_key=self.openai_api_key
        )

    @staticmethod
    def text_formatter(text):
        return text.replace('\n', ' ').strip()

    def read_pdf(self):
        doc = fitz.open(self.pdf_path)
        pages_and_texts = []
        for page_number, page in tqdm(enumerate(doc), total=doc.page_count, desc="Reading PDF"):
            text = page.get_text()
            text = self.text_formatter(text)
            pages_and_texts.append({
                "page_number": page_number + 1,
                "page_char_count": len(text),
                "page_word_count": len(text.split(" ")),
                "page_sentence_count": len(text.split(". ")),
                "page_token_count": len(text) // 4,
                "text": text
            })
        return pages_and_texts

    def create_documents(self):
        data = self.read_pdf()
        for page in data:
            text = page['text'].strip()
            if text:
                doc = Document(
                    page_content=text,
                    metadata={
                        'page_number': page['page_number'],
                        'char_count': page['page_char_count'],
                    }
                )
                self.documents.append(doc)

    def split_text(self):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.splits = text_splitter.split_documents(self.documents)

    def build_vectorstore(self):
        # print("Starting vector store...")
        embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        self.vectorstore = FAISS.from_documents(self.splits, embeddings)
        self.retriever = self.vectorstore.as_retriever()
        # print("Vector store built.")

    def generate_questions(self):
        prompt_to_retrieve = ChatPromptTemplate.from_messages([('system', "You're the world's most renowned financial analyst, celebrated for your uncanny ability to decipher complex economic data and predict market trends with remarkable precision. One day, while perusing the latest Economic Survey, you notice subtle patterns and anomalies that others have overlooked. Embedded within the dense charts and statistics are hidden insights into the key economic factors affecting the growth of companies in various sectors. Global economic shifts, fiscal policies, consumer spending behaviors, inflation rates, technological advancements, and international trade dynamics—all these elements are interwoven in the data before you. You realize that by extracting and analyzing these factors, you could forecast which companies are poised for extraordinary growth and which might face impending decline. Time is of the essence. Investors, corporations, and even governments are making decisions without the critical insights you've uncovered. You decide to delve deep into the Economic Survey to extract these vital economic factors. Your goal is to construct a comprehensive analysis that can guide businesses and investors toward informed, strategic decisions that foster sustainable growth. Armed with your expertise, you set out on this mission to unlock insights about {company} and you have decided to ask 10 questions and get the data from economic analysis of the country to get the information you need, therefore it will be better to ask industry wide questions rather than asking company specific, otherwise you know better. List those 10 questions only , in para form separated by ********, no other information is needed.")])

        chain = prompt_to_retrieve | self.llm | StrOutputParser()
        questions_str = chain.invoke({"company": self.company})
        questions = questions_str.split("********")
        self.questions = [q.strip() for q in questions if q.strip()]
        # print(self.questions)

    def retrieve_context(self):
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever
        )

        context = ""
        for question in self.questions:
            context += question + "\n\n"
            answer = qa_chain.run(question)
            context += answer + "\n\n"
        self.context = context
        print(self.context)

    def generate_analysis(self):
        prompt_context = ChatPromptTemplate.from_messages([
            ('system', f"""
            You're a top financial analyst, providing macroeconomic insights on {self.company} based on economic data. 
            Write a comprehensive analysis and recommendation using the provided context: {{context}}.
            """)
        ])

        chain = prompt_context | self.llm | StrOutputParser()
        self.analysis = chain.invoke({"company": self.company, "context": self.context})

    def analyze(self):
        self.create_documents()
        # print("Splitting text...")
        self.split_text()
        # print("Building vector store...")
        self.build_vectorstore()
        # print("Generating questions...")
        self.generate_questions()
        # print("Retrieving context...")
        self.retrieve_context()
        # print("Generating analysis...")
        self.generate_analysis()

    def get_analysis(self):
        return self.analysis
