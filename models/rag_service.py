"""RAG Service - handles document storage and retrieval"""
import os
from openai import OpenAI
from pinecone import Pinecone

class RAGService:
    """Retrieval Augmented Generation service"""
    
    def __init__(self, auto_setup=True):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "network-docs")
        
        # Connect to existing index
        self.index = pc.Index(self.index_name)
        print(f"✓ Connected to Pinecone index: {self.index_name}")
        
        # Auto-setup on first run
        if auto_setup:
            self._check_and_setup()
    
    def _check_and_setup(self):
        """Check if index has documents, setup if empty"""
        try:
            stats = self.index.describe_index_stats()
            vector_count = stats.get('total_vector_count', 0)
            
            if vector_count == 0:
                print("⚠️  RAG index is empty - loading documents...")
                self._auto_load_documents()
            else:
                print(f"✓ RAG index ready with {vector_count} documents")
                
        except Exception as e:
            print(f"⚠️  Could not check RAG status: {e}")
    
    def _auto_load_documents(self):
        """Automatically load documents from documents folder"""
        try:
            from models.document_loader import DocumentLoader
            
            docs_folder = os.path.join(os.path.dirname(__file__), '..', 'documents')
            
            if not os.path.exists(docs_folder):
                print(f"⚠️  Documents folder not found: {docs_folder}")
                return
            
            loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
            documents = loader.load_all_documents(docs_folder)
            
            if documents:
                self.store_documents(documents)
                print("✅ RAG system auto-setup completed!")
            else:
                print("⚠️  No documents found to load")
                
        except Exception as e:
            print(f"❌ Auto-setup failed: {e}")
            import traceback
            traceback.print_exc()
    
    def create_embedding(self, text):
        """Convert text to embedding using OpenAI"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            dimensions=512
        )
        return response.data[0].embedding
    
    def store_documents(self, documents):
        """Store documents in Pinecone"""
        print(f"Storing {len(documents)} documents in Pinecone...")
        
        vectors = []
        for doc in documents:
            embedding = self.create_embedding(doc['text'])
            
            vector = {
                'id': doc['id'],
                'values': embedding,
                'metadata': {
                    'text': doc['text'][:1000],
                    'source': doc['metadata']['source'],
                    'chunk_index': doc['metadata']['chunk_index']
                }
            }
            vectors.append(vector)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            print(f"  Batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
        
        print(f"✓ Stored {len(documents)} documents!")
    
    def search(self, query, top_k=3):
        """Search for relevant documents"""
        print(f"Searching for: {query}")
        
        query_embedding = self.create_embedding(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        documents = []
        for match in results['matches']:
            documents.append({
                'text': match['metadata']['text'],
                'source': match['metadata']['source'],
                'score': match['score']
            })
        
        print(f"✓ Found {len(documents)} documents")
        return documents
    
    def clear_index(self):
        """Clear all vectors from index"""
        print("⚠️  Clearing index...")
        self.index.delete(delete_all=True)
        print("✓ Index cleared")