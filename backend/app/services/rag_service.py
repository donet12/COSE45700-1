"""
RAG (Retrieval Augmented Generation) 서비스
"""
import uuid
from typing import List, Optional, AsyncGenerator, Dict
from langchain_aws import ChatBedrock
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from app.config import settings
from app.services.rate_limiter import rate_limiter
import boto3
import chromadb
from chromadb.config import Settings as ChromaSettings


class RAGService:
    """RAG 서비스 클래스"""
    
    def __init__(self):
        """초기화"""
        # AWS 세션 생성
        session_kwargs = {
            "region_name": settings.aws_region
        }
        
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key
            })
        
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            **session_kwargs
        )
        
        # Embeddings 초기화
        self.embeddings = BedrockEmbeddings(
            model_id=settings.embedding_model,
            client=self.bedrock_runtime
        )
        
        # LLM 초기화
        self.llm = ChatBedrock(
            model_id=settings.bedrock_model_id,
            client=self.bedrock_runtime,
            model_kwargs={
                "temperature": settings.temperature,
                "max_tokens": settings.max_tokens
            }
        )
        
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory
        )
        
        # Vector Store 초기화
        self.vectorstore = Chroma(
            client=self.client,
            collection_name="interview_documents",
            embedding_function=self.embeddings
        )
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # 세션별 메모리 관리 (Multi-turn 대화)
        self.memories: Dict[str, ConversationBufferMemory] = {}
    
    async def add_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        문서를 벡터 스토어에 추가
        
        Args:
            content: 문서 내용
            metadata: 문서 메타데이터 (url, source 등)
            
        Returns:
            문서 ID
        """
        try:
            doc_id = str(uuid.uuid4())
            
            # 텍스트를 청크로 분할
            chunks = self.text_splitter.split_text(content)
            
            # 문서 생성
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        **(metadata or {}),
                        "chunk_id": f"{doc_id}_{i}",
                        "doc_id": doc_id
                    }
                )
                for i, chunk in enumerate(chunks)
            ]
            
            # 벡터 스토어에 추가
            if not documents:
                raise Exception("분할된 문서가 없습니다. 내용이 너무 짧거나 비어있을 수 있습니다.")
            
            # Embedding 생성 및 저장
            self.vectorstore.add_documents(documents)
            
            # 저장 확인
            if len(documents) > 0:
                # 저장 성공 확인을 위해 간단한 검색 테스트
                try:
                    test_results = self.vectorstore.similarity_search(
                        documents[0].page_content[:50], 
                        k=1
                    )
                except:
                    pass  # 검색 테스트 실패는 무시
            
            return doc_id
        
        except Exception as e:
            raise Exception(f"문서 추가 중 오류: {str(e)}")
    
    async def search_documents(self, query: str, k: int = 10) -> List[Document]:
        """
        관련 문서 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 수 (기본값: 10개로 증가)
            
        Returns:
            관련 문서 리스트
        """
        try:
            # ChromaDB retriever는 search_kwargs에 k만 전달
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": k}
            )
            docs = retriever.get_relevant_documents(query)
            return docs
        except Exception as e:
            raise Exception(f"문서 검색 중 오류: {str(e)}")
    
    def _get_memory(self, session_id: Optional[str] = None) -> ConversationBufferMemory:
        """세션별 메모리 가져오기 (대화 히스토리 길이 제한)"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in self.memories:
            self.memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer",
                max_token_limit=2000  # 최대 토큰 수 제한
            )
        
        memory = self.memories[session_id]
        
        # 대화 히스토리 길이 제한 (최근 10개 대화만 유지)
        if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
            messages = memory.chat_memory.messages
            if len(messages) > 20:  # 10개 대화 (user + assistant = 20개 메시지)
                # 최근 20개만 유지
                memory.chat_memory.messages = messages[-20:]
        
        return memory
    
    async def generate_with_rag(
        self,
        question: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        RAG를 사용하여 답변 생성 (Multi-turn 대화 지원)
        
        Args:
            question: 질문
            context: 추가 컨텍스트 (선택사항)
            session_id: 세션 ID (대화 히스토리 유지용)
            conversation_history: 대화 히스토리 (선택사항)
            
        Returns:
            생성된 답변
        """
        try:
            import asyncio
            
            # 세션별 메모리 가져오기
            memory = self._get_memory(session_id)
            
            # 대화 히스토리 구성 (메모리에서 가져오기)
            chat_history_text = ""
            if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                messages = memory.chat_memory.messages
                # 최근 10개 메시지만 사용 (5개 대화)
                recent_messages = messages[-10:] if len(messages) > 10 else messages
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        role = "사용자" if msg.__class__.__name__ == "HumanMessage" else "어시스턴트"
                        chat_history_text += f"{role}: {msg.content}\n"
            
            # 관련 문서 검색
            relevant_docs = await self.search_documents(question, k=10)
            context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # 프롬프트 구성
            if chat_history_text:
                prompt = f"""다음 대화 히스토리와 컨텍스트를 참고하여 질문에 답변해주세요.

[대화 히스토리]
{chat_history_text}

[참고 컨텍스트]
{context_text}

[현재 질문]
{question}

답변:"""
            else:
                prompt = f"""다음 컨텍스트를 참고하여 질문에 답변해주세요.

[참고 컨텍스트]
{context_text}

[질문]
{question}

답변:"""
            
            # Rate Limiting: 첫 요청은 빠르게, 이후 요청만 간격 제어
            if session_id and session_id in self.memories:
                await rate_limiter.wait_if_needed(key=session_id)
            
            # LLM 호출 (재시도 로직 포함)
            max_retries = 3
            base_delay = 3
            
            for attempt in range(max_retries):
                try:
                    response = await self.llm.ainvoke(prompt)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    
                    # 메모리에 대화 추가
                    memory.chat_memory.add_user_message(question)
                    memory.chat_memory.add_ai_message(answer)
                    
                    return answer
                except Exception as e:
                    error_str = str(e)
                    if "ThrottlingException" in error_str or "Too many requests" in error_str:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            await asyncio.sleep(delay)
                            continue
                    raise Exception(f"RAG 생성 중 오류: {error_str}")
            
            raise Exception(f"RAG 생성 중 오류: 최대 재시도 횟수 초과")
        
        except Exception as e:
            raise Exception(f"RAG 생성 중 오류: {str(e)}")
    
    async def stream_generate_with_rag(
        self,
        question: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        RAG를 사용하여 스트리밍 방식으로 답변 생성 (Multi-turn 대화 지원)
        
        Args:
            question: 질문
            context: 추가 컨텍스트 (선택사항)
            session_id: 세션 ID (대화 히스토리 유지용)
            conversation_history: 대화 히스토리 (선택사항)
            
        Yields:
            생성된 답변 청크
        """
        try:
            import asyncio
            
            # 세션별 메모리 가져오기
            memory = self._get_memory(session_id)
            
            # 대화 히스토리 구성 (메모리에서 가져오기)
            chat_history_text = ""
            if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                messages = memory.chat_memory.messages
                # 최근 10개 메시지만 사용 (5개 대화)
                recent_messages = messages[-10:] if len(messages) > 10 else messages
                for msg in recent_messages:
                    if hasattr(msg, 'content'):
                        role = "사용자" if msg.__class__.__name__ == "HumanMessage" else "어시스턴트"
                        chat_history_text += f"{role}: {msg.content}\n"
            
            # 관련 문서 검색
            relevant_docs = await self.search_documents(question, k=10)
            context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # 프롬프트 구성
            if chat_history_text:
                prompt = f"""다음 대화 히스토리와 컨텍스트를 참고하여 질문에 답변해주세요.

[대화 히스토리]
{chat_history_text}

[참고 컨텍스트]
{context_text}

[현재 질문]
{question}

답변:"""
            else:
                prompt = f"""다음 컨텍스트를 참고하여 질문에 답변해주세요.

[참고 컨텍스트]
{context_text}

[질문]
{question}

답변:"""
            
            # Rate Limiting: 첫 요청은 빠르게, 이후 요청만 간격 제어
            if session_id and session_id in self.memories:
                await rate_limiter.wait_if_needed(key=session_id)
            
            # 스트리밍 실행 (재시도 로직 포함)
            max_retries = 3
            base_delay = 3
            
            full_answer = ""
            for attempt in range(max_retries):
                try:
                    async for chunk in self.llm.astream(prompt):
                        if hasattr(chunk, 'content'):
                            content = chunk.content
                            full_answer += content
                            yield content
                        else:
                            content = str(chunk)
                            full_answer += content
                            yield content
                    
                    # 메모리에 대화 추가
                    memory.chat_memory.add_user_message(question)
                    memory.chat_memory.add_ai_message(full_answer)
                    
                    return  # 성공 시 종료
                except Exception as e:
                    error_str = str(e)
                    if "ThrottlingException" in error_str or "Too many requests" in error_str:
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            await asyncio.sleep(delay)
                            continue
                    raise Exception(f"RAG 스트리밍 중 오류: {error_str}")
            
            raise Exception(f"RAG 스트리밍 중 오류: 최대 재시도 횟수 초과")
        
        except Exception as e:
            raise Exception(f"RAG 스트리밍 중 오류: {str(e)}")
    
    async def list_documents(self) -> List[dict]:
        """업로드된 문서 목록 조회"""
        try:
            collection = self.client.get_collection("interview_documents")
            results = collection.get()
            
            # 고유한 문서 ID 수집
            seen_doc_ids = set()
            documents = []
            
            for i, metadata in enumerate(results.get("metadatas", [])):
                doc_id = metadata.get("doc_id")
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    documents.append({
                        "id": doc_id,
                        "source": metadata.get("source", "unknown"),
                        "url": metadata.get("url", ""),
                        "type": metadata.get("type", "web")
                    })
            
            return documents
        except Exception as e:
            return []
    
    async def delete_document(self, document_id: str):
        """문서 삭제"""
        try:
            collection = self.client.get_collection("interview_documents")
            
            # 해당 문서의 모든 청크 찾기
            results = collection.get()
            ids_to_delete = []
            
            for i, metadata in enumerate(results.get("metadatas", [])):
                if metadata.get("doc_id") == document_id:
                    ids_to_delete.append(results["ids"][i])
            
            # 청크 삭제
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
        except Exception as e:
            raise Exception(f"문서 삭제 중 오류: {str(e)}")

