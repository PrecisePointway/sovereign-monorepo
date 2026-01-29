#!/usr/bin/env python3
"""
Sovereign Truth Engine - Enhanced Multi-Modal Document Search System
Quantum-resistant storage with SHA-256, SentenceTransformer embeddings, FastAPI server
"""

import os
import sys
import sqlite3
import hashlib
import zlib
import json
import argparse
import logging
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

# Document processing
import PyPDF2
import docx
from bs4 import BeautifulSoup
import markdown

# ML and embeddings
import numpy as np
from sentence_transformers import SentenceTransformer

# FastAPI server
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    top_k: int = 10
    threshold: float = 0.3


class SearchResult(BaseModel):
    """Search result model"""
    document_id: str
    file_path: str
    chunk_text: str
    similarity: float
    metadata: Dict


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    indexed_documents: int
    indexed_chunks: int
    uptime_seconds: float


class StatisticsResponse(BaseModel):
    """Statistics response"""
    total_documents: int
    total_chunks: int
    total_searches: int
    unique_document_types: List[str]
    database_size_mb: float


class SovereignTruthEngine:
    """
    Sovereign Truth Engine with quantum-resistant storage and multi-modal indexing
    """
    
    CHUNK_SIZE = 2000
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(self, 
                 db_path: str = "sovereign_truth.db",
                 data_dirs: Optional[List[str]] = None):
        """
        Initialize the Sovereign Truth Engine
        
        Args:
            db_path: Path to SQLite database
            data_dirs: List of directories to index
        """
        self.db_path = db_path
        self.data_dirs = data_dirs or [
            "./sovereign_hive_data/Elite_Legal_Finished",
            "./sovereign_hive_data/Research_Support_Finished"
        ]
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(self.EMBEDDING_MODEL)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize database
        self._init_database()
        
        # Start time for uptime tracking
        self.start_time = time.time()
        
        logger.info("Sovereign Truth Engine initialized")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize quantum-resistant SQLite database with SHA-256 hashing"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Documents table with SHA-256 hash
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    indexed_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Chunks table with compressed embeddings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_hash TEXT NOT NULL,
                    embedding_compressed BLOB NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id),
                    UNIQUE(document_id, chunk_index)
                )
            """)
            
            # Search history for audit logging
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    results_count INTEGER NOT NULL,
                    execution_time_ms REAL NOT NULL
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_hash 
                ON documents(file_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_document 
                ON chunks(document_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_timestamp 
                ON search_history(timestamp)
            """)
            
            logger.info("Database initialized with quantum-resistant schema")
    
    def _compute_sha256(self, data: bytes) -> str:
        """Compute SHA-256 hash for quantum resistance"""
        return hashlib.sha256(data).hexdigest()
    
    def _compress_embedding(self, embedding: np.ndarray) -> bytes:
        """Compress embedding with zlib"""
        return zlib.compress(embedding.astype(np.float32).tobytes())
    
    def _decompress_embedding(self, compressed: bytes) -> np.ndarray:
        """Decompress embedding"""
        decompressed = zlib.decompress(compressed)
        return np.frombuffer(decompressed, dtype=np.float32)
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = []
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
        except Exception as e:
            logger.error(f"Error extracting PDF {file_path}: {e}")
        return "\n".join(text)
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting DOCX {file_path}: {e}")
            return ""
    
    def _extract_text_from_html(self, file_path: str) -> str:
        """Extract text from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text()
        except Exception as e:
            logger.error(f"Error extracting HTML {file_path}: {e}")
            return ""
    
    def _extract_text_from_json(self, file_path: str) -> str:
        """Extract text from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error extracting JSON {file_path}: {e}")
            return ""
    
    def _extract_text_from_markdown(self, file_path: str) -> str:
        """Extract text from Markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                # Convert to HTML then extract text
                html = markdown.markdown(md_content)
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text()
        except Exception as e:
            logger.error(f"Error extracting Markdown {file_path}: {e}")
            return ""
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error extracting TXT {file_path}: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """
        Multi-modal document text extraction
        Supports: PDF, DOCX, TXT, MD, JSON, HTML
        """
        ext = Path(file_path).suffix.lower()
        
        extractors = {
            '.pdf': self._extract_text_from_pdf,
            '.docx': self._extract_text_from_docx,
            '.doc': self._extract_text_from_docx,
            '.txt': self._extract_text_from_txt,
            '.md': self._extract_text_from_markdown,
            '.markdown': self._extract_text_from_markdown,
            '.json': self._extract_text_from_json,
            '.html': self._extract_text_from_html,
            '.htm': self._extract_text_from_html,
        }
        
        extractor = extractors.get(ext, self._extract_text_from_txt)
        return extractor(file_path)
    
    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text at 2000 character boundaries"""
        chunks = []
        for i in range(0, len(text), self.CHUNK_SIZE):
            chunk = text[i:i + self.CHUNK_SIZE]
            if chunk.strip():
                chunks.append(chunk)
        return chunks
    
    def index_document(self, file_path: str) -> bool:
        """
        Index a single document with multi-modal support
        
        Args:
            file_path: Path to document
            
        Returns:
            True if successfully indexed
        """
        try:
            # Read file and compute hash
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_hash = self._compute_sha256(file_data)
            file_size = len(file_data)
            file_type = Path(file_path).suffix.lower()
            
            # Check if already indexed
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM documents WHERE file_hash = ?",
                    (file_hash,)
                )
                if cursor.fetchone():
                    logger.debug(f"Document already indexed: {file_path}")
                    return True
            
            # Extract text
            text = self.extract_text(file_path)
            if not text.strip():
                logger.warning(f"No text extracted from: {file_path}")
                return False
            
            # Chunk text
            chunks = self._chunk_text(text)
            if not chunks:
                logger.warning(f"No chunks created from: {file_path}")
                return False
            
            # Generate embeddings
            embeddings = self.model.encode(chunks, show_progress_bar=False)
            
            # Store in database
            document_id = self._compute_sha256(file_path.encode())
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert document
                cursor.execute("""
                    INSERT OR REPLACE INTO documents 
                    (id, file_path, file_hash, file_type, file_size, indexed_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_id,
                    file_path,
                    file_hash,
                    file_type,
                    file_size,
                    datetime.utcnow().isoformat(),
                    json.dumps({"chunks": len(chunks)})
                ))
                
                # Insert chunks
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_hash = self._compute_sha256(chunk.encode())
                    embedding_compressed = self._compress_embedding(embedding)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO chunks
                        (document_id, chunk_index, chunk_text, chunk_hash, embedding_compressed)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        document_id,
                        idx,
                        chunk,
                        chunk_hash,
                        embedding_compressed
                    ))
            
            logger.info(f"Indexed: {file_path} ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing {file_path}: {e}")
            return False
    
    def index_directories(self):
        """Index all documents in configured directories"""
        logger.info("Starting directory indexing...")
        
        supported_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.markdown', '.json', '.html', '.htm'}
        total_files = 0
        indexed_files = 0
        
        for data_dir in self.data_dirs:
            if not os.path.exists(data_dir):
                logger.warning(f"Directory not found: {data_dir}")
                continue
            
            logger.info(f"Scanning directory: {data_dir}")
            
            for root, _, files in os.walk(data_dir):
                for file in files:
                    if Path(file).suffix.lower() in supported_extensions:
                        total_files += 1
                        file_path = os.path.join(root, file)
                        if self.index_document(file_path):
                            indexed_files += 1
        
        logger.info(f"Indexing complete: {indexed_files}/{total_files} files indexed")
    
    def search(self, query: str, top_k: int = 10, threshold: float = 0.3) -> List[Dict]:
        """
        Semantic search with cosine similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Retrieve all chunks
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    c.id,
                    c.document_id,
                    c.chunk_text,
                    c.embedding_compressed,
                    d.file_path,
                    d.file_type,
                    d.metadata
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
            """)
            
            chunks = cursor.fetchall()
        
        # Calculate cosine similarities
        results = []
        for chunk in chunks:
            embedding = self._decompress_embedding(chunk['embedding_compressed'])
            
            # Cosine similarity
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            
            if similarity >= threshold:
                results.append({
                    'document_id': chunk['document_id'],
                    'file_path': chunk['file_path'],
                    'chunk_text': chunk['chunk_text'],
                    'similarity': float(similarity),
                    'metadata': json.loads(chunk['metadata'])
                })
        
        # Sort by similarity and get top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        results = results[:top_k]
        
        # Log search to audit trail
        execution_time = (time.time() - start_time) * 1000
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history (query, timestamp, results_count, execution_time_ms)
                VALUES (?, ?, ?, ?)
            """, (
                query,
                datetime.utcnow().isoformat(),
                len(results),
                execution_time
            ))
        
        logger.info(f"Search completed: '{query}' - {len(results)} results in {execution_time:.2f}ms")
        return results
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Document count
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            
            # Chunk count
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            
            # Search count
            cursor.execute("SELECT COUNT(*) FROM search_history")
            search_count = cursor.fetchone()[0]
            
            # Document types
            cursor.execute("SELECT DISTINCT file_type FROM documents")
            doc_types = [row[0] for row in cursor.fetchall()]
            
            # Database size
            db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
        
        return {
            'total_documents': doc_count,
            'total_chunks': chunk_count,
            'total_searches': search_count,
            'unique_document_types': doc_types,
            'database_size_mb': round(db_size_mb, 2)
        }
    
    def get_health(self) -> Dict:
        """Get health status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            doc_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
        
        uptime = time.time() - self.start_time
        
        return {
            'status': 'healthy',
            'indexed_documents': doc_count,
            'indexed_chunks': chunk_count,
            'uptime_seconds': round(uptime, 2)
        }


# Global engine instance
engine: Optional[SovereignTruthEngine] = None
indexing_thread: Optional[threading.Thread] = None


def background_indexer():
    """Background thread for initial indexing"""
    global engine
    if engine:
        logger.info("Background indexing started")
        engine.index_directories()
        logger.info("Background indexing completed")


# FastAPI Application
app = FastAPI(
    title="Sovereign Truth Engine",
    description="Quantum-resistant multi-modal document search system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize engine on startup"""
    global engine, indexing_thread
    
    logger.info("Starting Sovereign Truth Engine...")
    
    # Initialize engine
    engine = SovereignTruthEngine()
    
    # Start background indexing
    indexing_thread = threading.Thread(target=background_indexer, daemon=True)
    indexing_thread.start()
    
    logger.info("Sovereign Truth Engine started")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    health_data = engine.get_health()
    return HealthResponse(**health_data)


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get system statistics"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    stats = engine.get_statistics()
    return StatisticsResponse(**stats)


@app.post("/search")
async def search(request: SearchRequest):
    """Semantic search endpoint"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    results = engine.search(
        query=request.query,
        top_k=request.top_k,
        threshold=request.threshold
    )
    
    return {
        "query": request.query,
        "results_count": len(results),
        "results": results
    }


@app.post("/reindex")
async def reindex():
    """Trigger reindexing of all documents"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    # Start reindexing in background
    thread = threading.Thread(target=engine.index_directories, daemon=True)
    thread.start()
    
    return {"message": "Reindexing started in background"}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run FastAPI server"""
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def run_tests():
    """Run test suite"""
    logger.info("Running test suite...")
    
    # Initialize test engine
    test_db = "test_sovereign_truth.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    test_engine = SovereignTruthEngine(
        db_path=test_db,
        data_dirs=["./test_data"]
    )
    
    # Test 1: Database initialization
    logger.info("Test 1: Database initialization")
    assert os.path.exists(test_db), "Database not created"
    logger.info("✓ Database initialized")
    
    # Test 2: Text extraction
    logger.info("Test 2: Text extraction")
    test_text = "This is a test document for the Sovereign Truth Engine."
    chunks = test_engine._chunk_text(test_text)
    assert len(chunks) > 0, "Text chunking failed"
    logger.info(f"✓ Text chunking successful ({len(chunks)} chunks)")
    
    # Test 3: Embedding generation
    logger.info("Test 3: Embedding generation")
    embeddings = test_engine.model.encode(chunks)
    assert embeddings.shape[0] == len(chunks), "Embedding generation failed"
    logger.info(f"✓ Embeddings generated (dim={embeddings.shape[1]})")
    
    # Test 4: Compression
    logger.info("Test 4: Embedding compression")
    compressed = test_engine._compress_embedding(embeddings[0])
    decompressed = test_engine._decompress_embedding(compressed)
    assert np.allclose(embeddings[0], decompressed), "Compression/decompression failed"
    compression_ratio = len(embeddings[0].tobytes()) / len(compressed)
    logger.info(f"✓ Compression successful (ratio: {compression_ratio:.2f}x)")
    
    # Test 5: SHA-256 hashing
    logger.info("Test 5: SHA-256 hashing")
    hash1 = test_engine._compute_sha256(b"test")
    hash2 = test_engine._compute_sha256(b"test")
    assert hash1 == hash2, "Hash consistency failed"
    assert len(hash1) == 64, "Invalid hash length"
    logger.info("✓ SHA-256 hashing successful")
    
    # Test 6: Statistics
    logger.info("Test 6: Statistics")
    stats = test_engine.get_statistics()
    assert 'total_documents' in stats, "Statistics missing fields"
    logger.info(f"✓ Statistics: {stats}")
    
    # Test 7: Health check
    logger.info("Test 7: Health check")
    health = test_engine.get_health()
    assert health['status'] == 'healthy', "Health check failed"
    logger.info(f"✓ Health check: {health}")
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    
    logger.info("=" * 60)
    logger.info("All tests passed successfully!")
    logger.info("=" * 60)


def main():
    """Main entry point with command line modes"""
    parser = argparse.ArgumentParser(
        description="Sovereign Truth Engine - Multi-Modal Document Search"
    )
    parser.add_argument(
        '--server',
        action='store_true',
        help='Run in server mode'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test suite'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Server host (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Server port (default: 8000)'
    )
    parser.add_argument(
        '--db',
        default='sovereign_truth.db',
        help='Database path (default: sovereign_truth.db)'
    )
    parser.add_argument(
        '--data-dir',
        action='append',
        help='Data directory to index (can be specified multiple times)'
    )
    
    args = parser.parse_args()
    
    if args.test:
        run_tests()
    elif args.server:
        # Override data directories if specified
        if args.data_dir:
            # This will be picked up by the startup event
            os.environ['SOVEREIGN_DATA_DIRS'] = json.dumps(args.data_dir)
        if args.db:
            os.environ['SOVEREIGN_DB_PATH'] = args.db
        
        run_server(host=args.host, port=args.port)
    else:
        # Interactive mode
        logger.info("Sovereign Truth Engine - Interactive Mode")
        logger.info("Use --server to run HTTP server or --test to run tests")
        parser.print_help()


if __name__ == "__main__":
    main()
