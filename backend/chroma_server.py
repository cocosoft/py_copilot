"""
ChromaDB独立服务
通过HTTP API提供向量数据库功能，隔离PyTorch内存问题
"""
import os

# 必须在任何其他导入之前设置环境变量
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# 根据CPU核心数设置线程数，提升并行处理能力
import multiprocessing
cpu_count = multiprocessing.cpu_count()
# 使用CPU核心数的一半，避免占用过多资源
thread_count = max(2, cpu_count // 2)
os.environ['OMP_NUM_THREADS'] = str(thread_count)
os.environ['MKL_NUM_THREADS'] = str(thread_count)
os.environ['OPENBLAS_NUM_THREADS'] = str(thread_count)
os.environ['TORCH_NUM_THREADS'] = str(thread_count)
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
print(f"[ChromaDB] 使用 {thread_count} 线程进行并行处理")

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="ChromaDB独立服务")

# 全局变量
client = None
collections = {}
embedding_function = None

class AddDocumentRequest(BaseModel):
    collection_name: str
    document_id: str
    text: str
    metadata: Dict[str, Any]

class BatchAddDocumentsRequest(BaseModel):
    collection_name: str
    documents: List[Dict[str, Any]]  # 每个文档包含 id, text, metadata

class SearchRequest(BaseModel):
    collection_name: str
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

class DeleteRequest(BaseModel):
    collection_name: str
    document_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None

class GetDocumentsRequest(BaseModel):
    collection_name: str
    filters: Optional[Dict[str, Any]] = None

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化ChromaDB"""
    global client, embedding_function
    
    try:
        # 获取存储路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        storage_path = os.path.join(
            current_dir, 
            "..",
            "frontend",
            "public",
            "knowledges", 
            "chromadb"
        )
        storage_path = os.path.normpath(storage_path)
        
        logger.info(f"ChromaDB存储路径: {storage_path}")
        os.makedirs(storage_path, exist_ok=True)
        
        # 加载Embedding模型
        model_path = os.path.join(current_dir, "models", "BAAI", "bge-large-zh-v1.5")
        logger.info(f"加载Embedding模型: {model_path}")
        
        if os.path.exists(model_path):
            # 使用优化的Embedding配置，提升批处理性能
            embedding_function = SentenceTransformerEmbeddingFunction(
                model_name=model_path,
                device="cpu",
                normalize_embeddings=True
            )
            logger.info("Embedding模型加载成功（已启用归一化优化）")
        else:
            logger.warning("Embedding模型未找到")
            embedding_function = None
        
        # 初始化ChromaDB客户端
        client = chromadb.PersistentClient(path=storage_path)
        logger.info("ChromaDB客户端初始化成功")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "client_initialized": client is not None}

@app.post("/collections/{collection_name}/documents")
async def add_document(collection_name: str, request: AddDocumentRequest):
    """添加单个文档"""
    try:
        collection = client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
        )

        collection.add(
            ids=[request.document_id],
            documents=[request.text],
            metadatas=[request.metadata]
        )

        return {"message": "文档添加成功"}
    except Exception as e:
        logger.error(f"添加文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collections/{collection_name}/documents/batch")
async def batch_add_documents(collection_name: str, request: BatchAddDocumentsRequest):
    """批量添加文档 - 性能优化版"""
    try:
        collection = client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
        )

        # 批量提取数据
        ids = [doc["id"] for doc in request.documents]
        documents = [doc["text"] for doc in request.documents]
        metadatas = [doc["metadata"] for doc in request.documents]

        # 批量添加（ChromaDB内部会批量处理嵌入）
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"批量添加成功: {len(ids)} 个文档")
        return {
            "message": "批量添加成功",
            "count": len(ids)
        }
    except Exception as e:
        logger.error(f"批量添加文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collections/{collection_name}/search")
async def search(collection_name: str, request: SearchRequest):
    """搜索文档"""
    try:
        collection = client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
        )

        where_clause = None
        if request.filters and len(request.filters) > 0:
            where_clause = request.filters

        query_params = {
            "query_texts": [request.query],
            "n_results": request.top_k
        }
        if where_clause:
            query_params["where"] = where_clause

        results = collection.query(**query_params)
        
        # 格式化结果
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i] if results['documents'] else "",
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0
                })
        
        return {"results": formatted_results}
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/collections/{collection_name}/documents")
async def delete_documents(collection_name: str, request: DeleteRequest):
    """删除文档"""
    try:
        collection = client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
        )
        
        if request.document_ids:
            collection.delete(ids=request.document_ids)
        elif request.filters:
            collection.delete(where=request.filters)
        
        return {"message": "文档删除成功"}
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/{collection_name}/count")
async def count_documents(collection_name: str):
    """获取文档数量"""
    try:
        collection = client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
        )

        count = collection.count()
        return {"count": count}
    except Exception as e:
        logger.error(f"获取文档数量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/collections/{collection_name}/documents/get")
async def get_documents_by_metadata(collection_name: str, request: GetDocumentsRequest):
    """根据元数据获取文档"""
    try:
        collection = client.get_or_create_collection(
            collection_name,
            embedding_function=embedding_function
        )

        all_ids = []
        all_documents = []
        all_metadatas = []

        # 转换过滤器格式以适应 ChromaDB 的 where 语法
        # ChromaDB 支持 $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin 等操作符
        if request.filters:
            # 首先尝试使用原始值查询
            chroma_filters = {}
            for key, value in request.filters.items():
                chroma_filters[key] = {"$eq": value}

            logger.info(f"查询过滤器(原始值): {chroma_filters}")

            try:
                results = collection.get(where=chroma_filters)
                all_ids.extend(results.get("ids", []))
                all_documents.extend(results.get("documents", []))
                all_metadatas.extend(results.get("metadatas", []))
            except Exception as e:
                logger.warning(f"原始值查询失败: {e}")

            # 对于整数类型的值，同时尝试字符串格式查询
            # 因为 ChromaDB 可能会将整数存储为字符串
            string_filters = {}
            has_string_filter = False
            for key, value in request.filters.items():
                if isinstance(value, int):
                    string_filters[key] = {"$eq": str(value)}
                    has_string_filter = True
                elif isinstance(value, str):
                    # 如果值是字符串，尝试整数格式
                    try:
                        int_value = int(value)
                        string_filters[key] = {"$eq": int_value}
                        has_string_filter = True
                    except ValueError:
                        pass

            if has_string_filter and string_filters != chroma_filters:
                logger.info(f"查询过滤器(转换值): {string_filters}")
                try:
                    results = collection.get(where=string_filters)
                    # 合并结果，避免重复
                    existing_ids = set(all_ids)
                    for i, doc_id in enumerate(results.get("ids", [])):
                        if doc_id not in existing_ids:
                            all_ids.append(doc_id)
                            all_documents.append(results.get("documents", [])[i] if i < len(results.get("documents", [])) else "")
                            all_metadatas.append(results.get("metadatas", [])[i] if i < len(results.get("metadatas", [])) else {})
                except Exception as e:
                    logger.warning(f"转换值查询失败: {e}")
        else:
            # 没有过滤器，获取所有文档
            results = collection.get()
            all_ids = results.get("ids", [])
            all_documents = results.get("documents", [])
            all_metadatas = results.get("metadatas", [])

        logger.info(f"查询完成，找到 {len(all_ids)} 个结果")

        return {
            "ids": all_ids,
            "documents": all_documents,
            "metadatas": all_metadatas
        }
    except Exception as e:
        logger.error(f"根据元数据获取文档失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
