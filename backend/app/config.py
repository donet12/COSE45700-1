"""
애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # AWS 설정
    aws_region: str = "us-east-1"  # Bedrock 사용 가능한 리전
    aws_access_key_id: str = ""  # 선택사항 (환경변수나 IAM 역할 사용 가능)
    aws_secret_access_key: str = ""  # 선택사항
    
    # Database
    database_url: str = "sqlite:///./interview_coach.db"
    
    # ChromaDB
    chroma_persist_directory: str = "./chroma_db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Bedrock Model Settings
    # Claude 3.5 Sonnet (최신 버전, on-demand 지원)
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    # 또는 Claude 3 Sonnet (구버전, inference profile 필요 시)
    # bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    # Titan Embeddings (최신 버전)
    embedding_model: str = "amazon.titan-embed-text-v2:0"
    # 또는 구버전: "amazon.titan-embed-text-v1"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

