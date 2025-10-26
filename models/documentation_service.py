"""Documentation service - handles RAG searches"""

class DocumentationService:
    """Service for searching company documentation"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
    
    def search_documentation(self, query):
        """Search company documentation"""
        try:
            print(f"📚 Searching documentation for: {query}", flush=True)
            
            docs = self.rag_service.search(query, top_k=3)
            
            if not docs:
                return {
                    "success": True,
                    "message": "No relevant documentation found for this query."
                }
            
            # Format results
            result = {
                "success": True,
                "results": []
            }
            
            for doc in docs:
                result["results"].append({
                    "source": doc['source'],
                    "content": doc['text'],
                    "relevance_score": doc['score']
                })
                print(f"  ✓ Found: {doc['source']} (score: {doc['score']:.3f})", flush=True)
            
            return result
            
        except Exception as e:
            print(f"❌ Documentation search error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }