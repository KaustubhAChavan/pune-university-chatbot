import os
from typing import List, Optional
from langchain.schema.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VectorStoreManager:
    """Class to manage vector store operations"""
    
    def __init__(self, index_name: str = "pune_university"):
        """Initialize the vector store manager"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.index_name = index_name
        self.embeddings = OpenAIEmbeddings(api_key=self.api_key)
        self.vector_store = None
    
    def create_vector_store(self, documents: List[Document]) -> None:
        """Create a new vector store from documents"""
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        # Save the index
        self._save_vector_store()
    
    def load_or_create_vector_store(self, documents: Optional[List[Document]] = None) -> FAISS:
        """Load existing vector store or create a new one"""
        # Check if index already exists
        try:
            self.vector_store = FAISS.load_local(
                folder_path=f"vector_stores/{self.index_name}",
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True  # Added parameter to fix deserialization error
            )
            print(f"Loaded existing vector store: {self.index_name}")
        except Exception as e:
            # If no index exists or loading fails, create a new one
            print(f"Error loading vector store: {e}")
            if documents:
                print(f"Creating new vector store: {self.index_name}")
                self.create_vector_store(documents)
            else:
                raise ValueError("No documents provided to create a new vector store")
        
        return self.vector_store
    
    def update_vector_store(self, new_documents: List[Document]) -> None:
        """Update the vector store with new documents"""
        # Ensure vector store is loaded
        if self.vector_store is None:
            self.load_or_create_vector_store(new_documents)
            return
        
        # Add new documents
        self.vector_store.add_documents(new_documents)
        # Save the updated index
        self._save_vector_store()
    
    def _save_vector_store(self) -> None:
        """Save the vector store to disk"""
        # Create directory if it doesn't exist
        os.makedirs(f"vector_stores/{self.index_name}", exist_ok=True)
        # Save the index
        self.vector_store.save_local(f"vector_stores/{self.index_name}")
    
    def get_retriever(self, k: int = 3):
        """Get a retriever from the vector store"""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call load_or_create_vector_store first.")
        
        return self.vector_store.as_retriever(search_kwargs={"k": k})