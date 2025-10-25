"""Document loader - reads and chunks documents for RAG"""
import os

class DocumentLoader:
    """Loads and chunks documents for embedding"""
    
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_document(self, file_path):
        """Load a single document"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    def chunk_text(self, text):
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            if chunk.strip():  # Only add non-empty chunks
                chunks.append({
                    'text': chunk,
                    'start': start,
                    'end': end
                })
            
            start += (self.chunk_size - self.chunk_overlap)
        
        return chunks
    
    def load_all_documents(self, folder_path):
        """Load all .txt files from folder"""
        documents = []
        
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                print(f"Loading: {filename}")
                
                content = self.load_document(file_path)
                chunks = self.chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    documents.append({
                        'id': f"{filename}_{i}",
                        'text': chunk['text'],
                        'metadata': {
                            'source': filename,
                            'chunk_index': i
                        }
                    })
        
        print(f"✓ Loaded {len(documents)} chunks from {folder_path}")
        return documents