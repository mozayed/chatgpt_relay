"""RAG management routes"""
from flask import Blueprint, jsonify
from models.rag_service import RAGService
from models.document_loader import DocumentLoader
import os

rag_bp = Blueprint('rag', __name__)

_rag_service = None

def init_rag_routes(rag_service):
    """Initialize routes with RAG service"""
    global _rag_service
    _rag_service = rag_service
    print("✓ RAG routes initialized")

@rag_bp.route("/rag/status", methods=['GET'])
def rag_status():
    """Check RAG system status"""
    try:
        stats = _rag_service.index.describe_index_stats()
        return jsonify({
            "status": "ready",
            "vector_count": stats.get('total_vector_count', 0),
            "index_name": _rag_service.index_name
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@rag_bp.route("/rag/reload", methods=['POST'])
def reload_documents():
    """Manually reload documents (admin only)"""
    try:
        # Clear existing
        _rag_service.clear_index()
        
        # Reload
        loader = DocumentLoader(chunk_size=500, chunk_overlap=50)
        docs_folder = os.path.join(os.path.dirname(__file__), '..', 'documents')
        documents = loader.load_all_documents(docs_folder)
        _rag_service.store_documents(documents)
        
        return jsonify({
            "status": "success",
            "documents_loaded": len(documents)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500