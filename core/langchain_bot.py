from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.memory import ConversationBufferMemory
from utils.document_loader import load_knowledge_base, load_documents_from_directory, split_documents
from utils.vector_store import VectorStoreManager
import os
from typing import Dict, List, Tuple, Any  # Add this import for the type hints
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PuneUniversityChatbot:
    """Pune University Chatbot with knowledge base integration"""
    
    def __init__(self):
        """Initialize the chatbot with necessary components"""
        # Load OpenAI API Key
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=self.api_key
        )
        
        # Initialize vector store
        self._initialize_knowledge_base()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for Pune University students. Answer the question based on the provided context.
If the context doesn't contain relevant information, acknowledge what you know and what you don't.
Be polite, professional, and concise.

Previous conversation for context (do not repeat this in your answer):
{chat_history}

Context information (use this to answer):
{context}

Question: {input}

Provide your answer directly without prefixes like "User:" or "Assistant:" or restating the question.
""")
        
        # Create retrieval chain
        self._create_retrieval_chain()
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(return_messages=True, output_key="answer", input_key="input")
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base and vector store"""
        # Load knowledge base
        kb_documents = load_knowledge_base("knowledge/knowledge_base.json")
        
        # Load additional documents if they exist
        additional_docs = []
        if os.path.exists("knowledge/documents"):
            additional_docs = load_documents_from_directory("knowledge/documents")
        
        # Combine all documents and split into chunks
        all_documents = kb_documents + additional_docs
        split_docs = split_documents(all_documents)
        
        # Initialize vector store
        self.vector_store_manager = VectorStoreManager()
        self.vector_store = self.vector_store_manager.load_or_create_vector_store(split_docs)
        self.retriever = self.vector_store_manager.get_retriever(k=3)
    
    def _create_retrieval_chain(self):
        """Create the retrieval chain for answering questions"""
        # Create document chain
        self.document_chain = create_stuff_documents_chain(self.llm, self.prompt)
        
        # Create retrieval chain
        self.retrieval_chain = create_retrieval_chain(self.retriever, self.document_chain)
    
    def process_query(self, query: str, conversation_history: List[Dict] = None) -> Tuple[str, List[Dict]]:
        """Process a query through LangChain and return response with conversation history"""
        if conversation_history is None:
            conversation_history = []
        
        # Convert conversation history to chat history format for context
        # BUT don't include it in a way that it appears in the response
        chat_history = ""
        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                chat_history += f"Previous User Query: {content}\n"
            elif role == "assistant":
                chat_history += f"Previous Response: {content}\n"
        
        try:
            # Call the retrieval chain
            response = self.retrieval_chain.invoke({
                "input": query,
                "chat_history": chat_history
            })
            
            # Extract the response
            bot_response = response.get("answer", "")
            
            # Clean up any remaining formatting artifacts
            bot_response = self._clean_response(bot_response)
            
        except Exception as e:
            print(f"Error in processing query: {str(e)}")
            bot_response = "I'm sorry, I encountered an error while processing your request. Please try again."
        
        # Update conversation history
        updated_conversation = conversation_history + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": bot_response}
        ]
        
        return bot_response, updated_conversation
    
    def _clean_response(self, text: str) -> str:
        """Clean up any formatting artifacts from the response"""
        # Remove any "Assistant:" prefix
        if "Assistant:" in text:
            text = text.split("Assistant:", 1)[1].strip()
        
        # Remove any "User:" prefix and everything before it
        if "User:" in text:
            text = text.split("User:", 1)[1]
            if "Assistant:" in text:
                text = text.split("Assistant:", 1)[1].strip()
        
        return text

# Initialize a global instance
chatbot = PuneUniversityChatbot()

# Export the process_query function for app.py to use
def process_query(query: str, conversation_history: List[Dict] = None) -> Tuple[str, List[Dict]]:
    """Wrapper function for chatbot.process_query"""
    return chatbot.process_query(query, conversation_history)