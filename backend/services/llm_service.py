"""
LLM 服务层 - 使用 OpenAI 兼容 API 调用（支持 DeepSeek 等）
"""
import json
from typing import Optional, Dict, Any
from openai import OpenAI
from config import settings


class LLMService:
    """OpenAI 兼容 LLM 服务封装"""
    
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.model_name = settings.llm_model
        self._client = None
        
    def _get_client(self) -> OpenAI:
        """获取 OpenAI 客户端"""
        if self._client is None:
            if not self.api_key:
                raise ValueError("LLM API Key 未配置，请在 .env 文件中设置 LLM_API_KEY")
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
        
    async def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """
        调用 LLM 完成对话
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大输出 token 数
            
        Returns:
            LLM 响应文本
        """
        try:
            client = self._get_client()
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM API 调用异常: {str(e)}")
            raise
    
    async def chat_completion_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> Optional[Dict[str, Any]]:
        """
        调用 LLM 并解析 JSON 响应
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数（JSON 输出建议用较低温度）
            
        Returns:
            解析后的 JSON 对象
        """
        response = await self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature
        )
        
        if not response:
            return None
        
        # 尝试提取 JSON
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试从 markdown 代码块中提取
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                # 尝试找到 JSON 对象的开始和结束
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end > start:
                    return json.loads(response[start:end])
                raise ValueError(f"无法解析 LLM 响应为 JSON: {response[:200]}")


# 全局 LLM 服务实例
llm_service = LLMService()
