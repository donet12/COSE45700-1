"""
AWS Bedrock 서비스
"""
from typing import Optional, AsyncGenerator
from langchain_aws import ChatBedrock
from langchain_community.embeddings import BedrockEmbeddings
from app.config import settings
import boto3


class BedrockService:
    """AWS Bedrock 서비스 클래스"""
    
    def __init__(self):
        """초기화"""
        # AWS 세션 생성
        session_kwargs = {
            "region_name": settings.aws_region
        }
        
        # 자격증명이 .env에 있으면 사용
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key
            })
        
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            **session_kwargs
        )
        
        # LLM 초기화 (Claude 3 Sonnet)
        self.llm = ChatBedrock(
            model_id=settings.bedrock_model_id,
            client=self.bedrock_runtime,
            model_kwargs={
                "temperature": settings.temperature,
                "max_tokens": settings.max_tokens
            }
        )
        
        # Embeddings 초기화 (Titan Embeddings)
        self.embeddings = BedrockEmbeddings(
            model_id=settings.embedding_model,
            client=self.bedrock_runtime
        )
    
    async def chat(self, message: str) -> str:
        """
        일반 채팅 (스트리밍 없음, 재시도 로직 포함)
        
        Args:
            message: 사용자 메시지
            
        Returns:
            LLM 응답
        """
        import asyncio
        from app.services.rate_limiter import rate_limiter
        
        # Rate Limiting 적용
        await rate_limiter.wait_if_needed(key="bedrock_chat")
        
        max_retries = 5
        base_delay = 3
        
        for attempt in range(max_retries):
            try:
                response = await self.llm.ainvoke(message)
                return response.content
            except Exception as e:
                error_str = str(e)
                # ThrottlingException인 경우 재시도
                if "ThrottlingException" in error_str or "Too many requests" in error_str:
                    if attempt < max_retries - 1:
                        # 지수 백오프: 3초, 6초, 12초, 24초, 48초
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                raise Exception(f"Bedrock 호출 오류: {str(e)}")
        
        raise Exception(f"Bedrock 호출 실패: 최대 재시도 횟수 초과")
    
    async def stream_chat(self, message: str) -> AsyncGenerator[str, None]:
        """
        스트리밍 채팅
        
        Args:
            message: 사용자 메시지
            
        Yields:
            LLM 응답 청크
        """
        try:
            async for chunk in self.llm.astream(message):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
        except Exception as e:
            raise Exception(f"Bedrock 스트리밍 오류: {str(e)}")
    
    async def test_connection(self) -> dict:
        """
        Bedrock 연결 테스트
        
        Returns:
            테스트 결과
        """
        try:
            # 간단한 테스트 메시지
            test_message = "안녕하세요! 연결 테스트입니다. '테스트 성공'이라고만 답변해주세요."
            response = await self.chat(test_message)
            
            return {
                "status": "success",
                "message": "Bedrock 연결 성공",
                "response": response,
                "model": settings.bedrock_model_id,
                "region": settings.aws_region
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Bedrock 연결 실패: {str(e)}",
                "model": settings.bedrock_model_id,
                "region": settings.aws_region
            }

