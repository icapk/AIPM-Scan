"""
RAGFlow 服务
用于与 RAGFlow 知识库交互
"""
import httpx
from typing import List, Dict, Any, Optional
from config import settings

class RAGService:
    """RAGFlow 服务封装"""
    
    def __init__(self):
        self.api_key = settings.ragflow_api_key
        self.base_url = settings.ragflow_api_base
        self.dataset_id = settings.ragflow_dataset_id
        
    async def retrieve(self, query: str, top_k: int = 5, similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        从知识库检索相关内容
        
        Args:
            query: 检索关键词
            top_k: 返回数量
            similarity_threshold: 相似度阈值
            
        Returns:
            检索结果列表
        """
        if not self.api_key or not self.dataset_id:
            print("❌ RAGFlow 配置缺失: API Key 或 Dataset ID 未设置")
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # RAGFlow 检索 API 路径 (根据 RAGFlow 标准 API)
        # 注意: 具体路径可能根据版本不同有所差异，这里使用通用路径 /api/v1/retrieval
        url = f"{self.base_url}/api/v1/retrieval/{self.dataset_id}"
        
        payload = {
            "question": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code != 200:
                    print(f"❌ RAGFlow API 错误: {response.status_code} - {response.text}")
                    return []
                
                data = response.json()
                if data.get("code") != 0:
                    print(f"❌ RAGFlow 业务错误: {data.get('message')}")
                    return []
                
                # 解析返回结果
                # RAGFlow 返回结构通常为 data: { chunks: [...] }
                chunks = data.get("data", {}).get("chunks", [])
                return chunks
                
        except Exception as e:
            print(f"❌ RAGFlow 请求异常: {str(e)}")
            return []

rag_service = RAGService()
