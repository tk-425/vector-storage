"""
Vector Storage API - Direct FastAPI service for vector operations
Calls Ollama for embeddings and ChromaDB for storage
"""

import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel

app = FastAPI(title="Vector Storage API", version="1.0.0")

# Configuration from environment
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://192.168.1.154:11434")
CHROMA_URL = os.getenv("CHROMA_URL", "http://chroma:8000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
CHROMA_API_BASE = f"{CHROMA_URL}/api/v2/tenants/default_tenant/databases/default_database"


# --- Models ---

class WriteGlobalRequest(BaseModel):
    text: str
    metadata: Optional[dict] = {}


class WriteProjectRequest(BaseModel):
    project_id: str
    text: str
    metadata: Optional[dict] = {}


class QueryGlobalRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class QueryProjectRequest(BaseModel):
    project_id: str
    query: str
    top_k: Optional[int] = 5


class ListGlobalRequest(BaseModel):
    limit: Optional[int] = 20
    offset: Optional[int] = 0


class ListProjectRequest(BaseModel):
    project_id: str
    limit: Optional[int] = 20
    offset: Optional[int] = 0


class DeleteRequest(BaseModel):
    collection: str
    ids: list[str]


class UninitProjectRequest(BaseModel):
    project_id: str


# --- Auth ---

async def verify_token(authorization: str = Header(None)):
    if not AUTH_TOKEN:
        return True  # No auth required if token not set
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    token = authorization[7:]
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return True


# --- Helper Functions ---

async def get_embeddings(text: str) -> list:
    """Get embeddings from Ollama"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama error: {response.text}")
        return response.json()["embedding"]


async def get_or_create_collection(name: str) -> str:
    """Create collection if not exists, return collection UUID"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try to create collection
        try:
            create_response = await client.post(
                f"{CHROMA_API_BASE}/collections",
                json={"name": name, "metadata": {"auto_created": True}}
            )
            # Log non-success responses (except 409 Conflict = already exists)
            if create_response.status_code not in [200, 201, 409]:
                print(f"[WARN] Collection create for '{name}' returned {create_response.status_code}: {create_response.text}", flush=True)
        except Exception as e:
            # Log error but continue - collection may already exist
            print(f"[WARN] Collection create for '{name}' failed: {e}", flush=True)
        
        # Get collection to get UUID
        response = await client.get(f"{CHROMA_API_BASE}/collections")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"ChromaDB error: {response.text}")
        
        data = response.json()
        # Find the collection by name
        if isinstance(data, list):
            for collection in data:
                if collection.get("name") == name:
                    return collection["id"]
            # If not found after create, something went wrong
            raise HTTPException(status_code=500, detail=f"Collection '{name}' not found after creation")
        # Single collection response (shouldn't happen but handle it)
        if data.get("name") == name:
            return data["id"]
        raise HTTPException(status_code=500, detail=f"Collection '{name}' not found")


async def add_document(collection_id: str, doc_id: str, text: str, embeddings: list, metadata: dict):
    """Add document to ChromaDB collection"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{CHROMA_API_BASE}/collections/{collection_id}/add",
            json={
                "ids": [doc_id],
                "documents": [text],
                "embeddings": [embeddings],
                "metadatas": [metadata]
            }
        )
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"ChromaDB add error: {response.text}")


async def query_collection(collection_id: str, embeddings: list, top_k: int):
    """Query ChromaDB collection"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{CHROMA_API_BASE}/collections/{collection_id}/query",
            json={
                "query_embeddings": [embeddings],
                "n_results": top_k
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"ChromaDB query error: {response.text}")
        return response.json()


async def list_documents(collection_id: str, limit: int, offset: int = 0):
    """List documents from ChromaDB collection with pagination"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{CHROMA_API_BASE}/collections/{collection_id}/get",
            json={
                "limit": limit,
                "offset": offset,
                "include": ["documents", "metadatas"]
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"ChromaDB list error: {response.text}")
        return response.json()


# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/write/global")
async def write_global(request: WriteGlobalRequest, _: bool = Depends(verify_token)):
    doc_id = f"{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:9]}"
    
    metadata = request.metadata.copy()
    metadata["visibility"] = "global"
    metadata["created_at"] = datetime.utcnow().isoformat() + "Z"
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    embeddings = await get_embeddings(request.text)
    collection_id = await get_or_create_collection("global")
    await add_document(collection_id, doc_id, request.text, embeddings, metadata)
    
    return {"status": "success", "collection": "global", "id": doc_id}


@app.post("/write/project")
async def write_project(request: WriteProjectRequest, _: bool = Depends(verify_token)):
    collection_name = f"project_{request.project_id.lower().replace(' ', '-')}"
    doc_id = f"{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:9]}"
    
    metadata = request.metadata.copy()
    metadata["project_slug"] = request.project_id
    metadata["visibility"] = "project"
    metadata["created_at"] = datetime.utcnow().isoformat() + "Z"
    metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
    
    embeddings = await get_embeddings(request.text)
    collection_id = await get_or_create_collection(collection_name)
    await add_document(collection_id, doc_id, request.text, embeddings, metadata)
    
    return {"status": "success", "collection": collection_name, "id": doc_id}


@app.post("/query/global")
async def query_global(request: QueryGlobalRequest, _: bool = Depends(verify_token)):
    embeddings = await get_embeddings(request.query)
    collection_id = await get_or_create_collection("global")
    result = await query_collection(collection_id, embeddings, request.top_k)
    
    matches = []
    if result.get("ids") and result["ids"][0]:
        for i, doc_id in enumerate(result["ids"][0]):
            matches.append({
                "id": doc_id,
                "text": result["documents"][0][i] if result.get("documents") else None,
                "metadata": result["metadatas"][0][i] if result.get("metadatas") else {},
                "distance": result["distances"][0][i] if result.get("distances") else None,
                "similarity": 1 / (1 + result["distances"][0][i]) if result.get("distances") else None
            })
    
    return {"query": request.query, "collection": "global", "count": len(matches), "matches": matches}


@app.post("/query/project")
async def query_project(request: QueryProjectRequest, _: bool = Depends(verify_token)):
    collection_name = f"project_{request.project_id.lower().replace(' ', '-')}"
    
    embeddings = await get_embeddings(request.query)
    collection_id = await get_or_create_collection(collection_name)
    result = await query_collection(collection_id, embeddings, request.top_k)
    
    matches = []
    if result.get("ids") and result["ids"][0]:
        for i, doc_id in enumerate(result["ids"][0]):
            matches.append({
                "id": doc_id,
                "text": result["documents"][0][i] if result.get("documents") else None,
                "metadata": result["metadatas"][0][i] if result.get("metadatas") else {},
                "distance": result["distances"][0][i] if result.get("distances") else None,
                "similarity": 1 / (1 + result["distances"][0][i]) if result.get("distances") else None
            })
    
    return {"query": request.query, "collection": collection_name, "count": len(matches), "matches": matches}


@app.post("/list/global")
async def list_global(request: ListGlobalRequest, _: bool = Depends(verify_token)):
    collection_id = await get_or_create_collection("global")
    result = await list_documents(collection_id, request.limit, request.offset)
    
    documents = []
    if result.get("ids"):
        for i, doc_id in enumerate(result["ids"]):
            doc = {
                "id": doc_id,
                "text": result["documents"][i] if result.get("documents") else None,
                "metadata": result["metadatas"][i] if result.get("metadatas") else {}
            }
            documents.append(doc)
    
    # Sort by created_at descending
    documents.sort(key=lambda d: d.get("metadata", {}).get("created_at", ""), reverse=True)
    
    return {"collection": "global", "count": len(documents), "documents": documents}


@app.post("/list/project")
async def list_project(request: ListProjectRequest, _: bool = Depends(verify_token)):
    collection_name = f"project_{request.project_id.lower().replace(' ', '-')}"
    
    collection_id = await get_or_create_collection(collection_name)
    result = await list_documents(collection_id, request.limit, request.offset)
    
    documents = []
    if result.get("ids"):
        for i, doc_id in enumerate(result["ids"]):
            doc = {
                "id": doc_id,
                "text": result["documents"][i] if result.get("documents") else None,
                "metadata": result["metadatas"][i] if result.get("metadatas") else {}
            }
            documents.append(doc)
    
    # Sort by created_at descending
    documents.sort(key=lambda d: d.get("metadata", {}).get("created_at", ""), reverse=True)
    
    return {"collection": collection_name, "count": len(documents), "documents": documents}


async def delete_documents(collection_id: str, ids: list[str]):
    """Delete documents from ChromaDB collection"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{CHROMA_API_BASE}/collections/{collection_id}/delete",
            json={"ids": ids}
        )
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail=f"ChromaDB delete error: {response.text}")
        return True


@app.post("/delete/document")
async def delete_document(request: DeleteRequest, _: bool = Depends(verify_token)):
    # Get or create collection to get UUID
    collection_id = await get_or_create_collection(request.collection)
    
    await delete_documents(collection_id, request.ids)
    
    return {
        "status": "success",
        "collection": request.collection,
        "deleted_count": len(request.ids),
        "deleted_ids": request.ids
    }


@app.post("/delete/project")
async def delete_project(request: UninitProjectRequest, _: bool = Depends(verify_token)):
    """Drop the entire project collection"""
    collection_name = f"project_{request.project_id}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # ChromaDB Delete Collection endpoint: DELETE /collections/{name}
        response = await client.delete(f"{CHROMA_API_BASE}/collections/{collection_name}")
        
        if response.status_code == 404:
            # If it doesn't exist, we consider it a success (idempotent)
            return {"status": "success", "message": f"Project collection '{collection_name}' not found, nothing to delete"}
            
        if response.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail=f"ChromaDB delete error: {response.text}")
            
        return {"status": "success", "message": f"Project collection '{collection_name}' deleted"}
