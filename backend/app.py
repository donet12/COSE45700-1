"""
Streamlit 메인 애플리케이션
기술 면접 준비 도우미
"""
import streamlit as st
import asyncio
import json
import boto3
from app.services.bedrock_service import BedrockService
from app.services.pdf_service import PDFService
from app.services.crawler_service import CrawlerService
from app.services.rag_service import RAGService
from app.config import settings

# 페이지 설정
st.set_page_config(
    page_title="면접 준비 도우미",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바 - 페이지 선택
with st.sidebar:
    st.header("📋 메뉴")
    
    # 개발자 모드 토글
    developer_mode = st.checkbox(
        "🔧 개발자 모드",
        value=st.session_state.get('developer_mode', False),
        help="개발자용 기능(크롤링, PDF 업로드 등)을 표시합니다",
        key='developer_mode'
    )
    # key를 지정하면 자동으로 st.session_state.developer_mode에 저장됨
    
    st.markdown("---")
    
    # 일반 사용자용 메뉴 (기본)
    user_pages = ["🏠 홈", "❓ 질문 생성"]
    
    # 개발자용 메뉴
    if developer_mode:
        developer_pages = ["🔗 Bedrock 연결 테스트", "💬 간단한 채팅", "📄 PDF 업로드", "🕷️ 웹 크롤링"]
        all_pages = user_pages + developer_pages
    else:
        all_pages = user_pages
    
    page = st.radio(
        "페이지 선택",
        all_pages,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if not developer_mode:
        st.info("💡 질문 생성 챗봇을 사용하여 면접 질문을 생성하세요!")
    else:
        st.info("💡 개발자 모드: 모든 기능이 활성화되었습니다.")

# 메인 콘텐츠
st.title("🎯 기술 면접 준비 도우미")
st.markdown("---")

# 페이지별 콘텐츠
if page == "🏠 홈":
    st.success("✅ Streamlit 앱이 정상적으로 실행되었습니다!")
    
    st.markdown("""
    ## 🚀 시작하기
    
    이 앱은 **기술 면접 준비**를 도와주는 AI 서비스입니다.
    
    ### 주요 기능
    1. **PDF 업로드**: 자기소개서/이력서 업로드
    2. **웹 크롤링**: 회사별 기술 스택 정보 수집
    3. **질문 생성**: 맞춤형 면접 질문 생성
    4. **피드백**: STAR 기법 기반 답변 피드백
    5. **히스토리**: 면접 기록 및 약점 분석
    
    ### 다음 단계
    각 기능은 단계별로 구현됩니다. 사이드바의 메뉴를 따라 진행하세요!
    """)

elif page == "🔗 Bedrock 연결 테스트":
    st.header("🔗 AWS Bedrock 연결 테스트")
    st.markdown("AWS Bedrock과의 연결을 테스트합니다.")
    
    # 설정 가이드 표시
    with st.expander("📖 AWS Bedrock 설정 가이드", expanded=False):
        st.markdown("""
        ### 1️⃣ AWS 자격 증명 설정
        
        **방법 1: AWS CLI 사용 (권장)**
        ```bash
        aws configure
        ```
        - AWS Access Key ID 입력
        - AWS Secret Access Key 입력
        - Default region: `us-east-1` (또는 Bedrock 사용 가능한 리전)
        - Default output format: `json`
        
        **방법 2: 환경 변수 사용**
        ```bash
        export AWS_ACCESS_KEY_ID=your_access_key_id
        export AWS_SECRET_ACCESS_KEY=your_secret_access_key
        export AWS_DEFAULT_REGION=us-east-1
        ```
        
        **방법 3: .env 파일 사용**
        `backend/.env` 파일을 생성하고:
        ```
        AWS_ACCESS_KEY_ID=your_access_key_id
        AWS_SECRET_ACCESS_KEY=your_secret_access_key
        AWS_REGION=us-east-1
        ```
        
        ### 2️⃣ Bedrock 모델 접근 권한 설정
        
        1. AWS 콘솔 → **Bedrock** 서비스로 이동
        2. 왼쪽 메뉴에서 **"Model access"** 클릭
        3. 사용할 모델 선택:
           - ✅ **Claude 3.5 Sonnet** (`anthropic.claude-3-5-sonnet-20240620-v1:0`)
           - ✅ **Amazon Titan Embeddings** (`amazon.titan-embed-text-v2:0`)
        4. **"Request model access"** 클릭
        5. Anthropic Use Case Form 작성 (Claude 모델의 경우)
        6. 승인 대기 (보통 몇 분 ~ 몇 시간)
        
        ### 3️⃣ 리전 확인
        
        Bedrock을 사용할 수 있는 리전:
        - `us-east-1` (N. Virginia) ✅
        - `us-west-2` (Oregon) ✅
        - `ap-northeast-2` (Seoul) ✅
        - `eu-west-1` (Ireland) ✅
        
        ### 4️⃣ 자격 증명 확인
        
        현재 자격 증명 확인:
        ```bash
        aws sts get-caller-identity
        ```
        """)
    
    # 현재 설정 표시
    with st.expander("📋 현재 설정 확인"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**리전**: {settings.aws_region}")
            st.write(f"**모델**: {settings.bedrock_model_id}")
        with col2:
            st.write(f"**Embedding 모델**: {settings.embedding_model}")
            st.write(f"**Temperature**: {settings.temperature}")
        
        # 자격 증명 상태 확인
        import os
        has_env_key = bool(os.getenv("AWS_ACCESS_KEY_ID") or settings.aws_access_key_id)
        has_env_secret = bool(os.getenv("AWS_SECRET_ACCESS_KEY") or settings.aws_secret_access_key)
        has_aws_config = os.path.exists(os.path.expanduser("~/.aws/credentials"))
        
        st.markdown("---")
        st.markdown("**자격 증명 상태:**")
        if has_env_key and has_env_secret:
            st.success("✅ 환경 변수에서 자격 증명 발견")
        elif has_aws_config:
            st.info("ℹ️ AWS CLI 설정 파일에서 자격 증명 사용 중")
        else:
            st.warning("⚠️ 자격 증명이 설정되지 않았습니다. 위 가이드를 참고하세요.")
    
    # 연결 테스트 버튼
    if st.button("🔍 연결 테스트", type="primary", use_container_width=True):
        with st.spinner("Bedrock 연결 중..."):
            try:
                # BedrockService 인스턴스 생성
                bedrock_service = BedrockService()
                
                # 비동기 함수 실행
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(bedrock_service.test_connection())
                loop.close()
                
                # 결과 표시
                if result["status"] == "success":
                    st.success("✅ " + result["message"])
                    st.json({
                        "모델": result["model"],
                        "리전": result["region"],
                        "응답": result["response"]
                    })
                else:
                    st.error("❌ " + result["message"])
                    st.json({
                        "모델": result["model"],
                        "리전": result["region"],
                        "오류": result["message"]
                    })
                    
                    # 일반적인 오류 해결 방법 제시
                    error_msg = result.get("message", "").lower()
                    if "credentials" in error_msg or "unauthorized" in error_msg:
                        st.warning("💡 **해결 방법**: AWS 자격 증명을 설정하세요. 위의 'AWS Bedrock 설정 가이드'를 참고하세요.")
                    elif "model access" in error_msg or "use case" in error_msg:
                        st.warning("💡 **해결 방법**: AWS Bedrock 콘솔에서 모델 접근 권한을 요청하세요.")
                    elif "region" in error_msg or "invalid" in error_msg:
                        st.warning("💡 **해결 방법**: 올바른 리전을 설정하세요. (예: us-east-1)")
                    
            except Exception as e:
                st.error(f"❌ 오류 발생: {str(e)}")
                st.exception(e)
                
                # 오류 타입별 해결 방법 제시
                error_str = str(e).lower()
                if "credentials" in error_str or "no credentials" in error_str:
                    st.warning("💡 **해결 방법**: AWS 자격 증명을 설정하세요.")
                    st.code("aws configure", language="bash")
                elif "throttling" in error_str:
                    st.info("ℹ️ 요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
                elif "model" in error_str and "access" in error_str:
                    st.warning("💡 **해결 방법**: AWS Bedrock 콘솔에서 모델 접근 권한을 요청하세요.")

elif page == "💬 간단한 채팅":
    st.header("💬 간단한 채팅 테스트")
    st.markdown("Bedrock과 간단한 대화를 나눠보세요. (Multi-turn 지원, 스트리밍)")
    
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # 채팅 히스토리 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    def chunk_handler_simple(chunk):
        """스트리밍 청크 처리"""
        text = ""
        chunk_type = chunk.get("type")
        
        if chunk_type == "content_block_delta":
            text = chunk.get("delta", {}).get("text", "")
        elif chunk_type == "content_block_start":
            text = chunk.get("content_block", {}).get("text", "")
        
        return text
    
    def get_simple_streaming_response(user_prompt):
        """간단한 스트리밍 응답 생성 (Rate Limiting & Retry 포함)"""
        import time
        from app.services.rate_limiter import rate_limiter
        
        # Bedrock 클라이언트 초기화
        session_kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key
            })
        bedrock_runtime_local = boto3.client("bedrock-runtime", **session_kwargs)
        
        # Retry 설정
        max_retries = 5
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Rate Limiting
                loop_rate = asyncio.new_event_loop()
                asyncio.set_event_loop(loop_rate)
                loop_rate.run_until_complete(rate_limiter.wait_if_needed(key="bedrock_simple_chat"))
                loop_rate.close()
                
                # 메시지 히스토리 구성 (최근 6개)
                history = []
                recent_messages = st.session_state.messages[-6:]
                for msg in recent_messages:
                    if msg["role"] in ["user", "assistant"]:
                        content = msg["content"][:500] if len(msg["content"]) > 500 else msg["content"]
                        history.append({
                            "role": msg["role"],
                            "content": [{"type": "text", "text": content}]
                        })
                
                # 현재 사용자 메시지 추가
                history.append({
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                })
                
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "messages": history,
                })
                
                # 스트리밍 응답
                response = bedrock_runtime_local.invoke_model_with_response_stream(
                    modelId=settings.bedrock_model_id,
                    body=body,
                )
                
                stream = response.get("body")
                if stream:
                    for event in stream:
                        chunk = event.get("chunk")
                        if chunk:
                            chunk_json = json.loads(chunk.get("bytes").decode())
                            text = chunk_handler_simple(chunk_json)
                            if text:
                                yield text
                return
                                
            except Exception as e:
                error_str = str(e)
                
                if "ThrottlingException" in error_str or "Too many requests" in error_str or "throttl" in error_str.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        yield f"\n\n⏳ {delay}초 대기 후 재시도합니다...\n\n"
                        time.sleep(delay)
                        continue
                    else:
                        yield f"\n\n❌ 서버 과부하. 5분 후 다시 시도해주세요.\n\n"
                        return
                else:
                    yield f"\n\n❌ 오류: {str(e)}\n\n"
                    return
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성 (스트리밍)
        with st.chat_message("assistant"):
            model_output = st.write_stream(get_simple_streaming_response(prompt))
        
        # 보조 응답 세션 상태에 추가
        st.session_state.messages.append({"role": "assistant", "content": model_output})

elif page == "📄 PDF 업로드":
    st.header("📄 PDF 업로드 및 텍스트 추출")
    st.markdown("자기소개서나 이력서 PDF를 업로드하여 텍스트를 추출합니다.")
    
    # PDF 파일 업로드
    uploaded_file = st.file_uploader(
        "PDF 파일을 선택하세요",
        type=["pdf"],
        help="이력서나 자기소개서 PDF 파일을 업로드하세요"
    )
    
    if uploaded_file is not None:
        # 파일 정보 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("파일명", uploaded_file.name)
        with col2:
            st.metric("파일 크기", f"{uploaded_file.size / 1024:.2f} KB")
        with col3:
            st.metric("파일 타입", uploaded_file.type)
        
        # 텍스트 추출 버튼
        if st.button("📝 텍스트 추출", type="primary", use_container_width=True):
            with st.spinner("PDF에서 텍스트를 추출하는 중..."):
                try:
                    # 파일 읽기
                    file_content = uploaded_file.read()
                    
                    # PDFService를 사용하여 텍스트 추출
                    pdf_service = PDFService()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    extracted_text = loop.run_until_complete(
                        pdf_service.extract_text(file_content, uploaded_file.name)
                    )
                    loop.close()
                    
                    # 세션 상태에 저장
                    st.session_state.pdf_text = extracted_text
                    st.session_state.pdf_filename = uploaded_file.name
                    
                    st.success("✅ 텍스트 추출 완료!")
                    
                    # 요약 정보 표시
                    summary = pdf_service.get_summary(extracted_text)
                    
                    st.subheader("📊 문서 요약")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 문자 수", f"{summary['total_characters']:,}")
                    with col2:
                        st.metric("총 줄 수", f"{summary['total_lines']:,}")
                    with col3:
                        st.metric("비어있지 않은 줄", f"{summary['non_empty_lines']:,}")
                    
                    # 섹션별 정보
                    st.subheader("📑 섹션별 정보")
                    sections_found = summary['sections_found']
                    cols = st.columns(5)
                    section_names = {
                        "personal_info": "개인정보",
                        "education": "학력",
                        "experience": "경력",
                        "projects": "프로젝트",
                        "skills": "기술"
                    }
                    
                    for idx, (key, name) in enumerate(section_names.items()):
                        with cols[idx]:
                            if sections_found[key]:
                                st.success(f"✅ {name}")
                            else:
                                st.info(f"ℹ️ {name}")
                    
                    # 섹션별 상세 내용
                    st.subheader("📄 섹션별 상세 내용")
                    sections = summary['sections']
                    for key, name in section_names.items():
                        if sections[key]:
                            with st.expander(f"📌 {name}"):
                                st.text(sections[key])
                    
                    # 전체 텍스트 미리보기
                    st.subheader("📖 전체 텍스트 미리보기")
                    with st.expander("전체 텍스트 보기", expanded=False):
                        st.text_area(
                            "추출된 텍스트",
                            extracted_text,
                            height=400,
                            label_visibility="collapsed"
                        )
                    
                    # 다운로드 버튼
                    st.download_button(
                        label="💾 텍스트 파일로 다운로드",
                        data=extracted_text,
                        file_name=f"{uploaded_file.name.replace('.pdf', '')}_extracted.txt",
                        mime="text/plain"
                    )
                    
                except Exception as e:
                    st.error(f"❌ 오류 발생: {str(e)}")
                    st.exception(e)
        
        # 이전에 추출한 텍스트가 있으면 표시
        if "pdf_text" in st.session_state and st.session_state.pdf_filename == uploaded_file.name:
            st.info("ℹ️ 이전에 추출한 텍스트가 있습니다. 위의 '텍스트 추출' 버튼을 다시 클릭하면 최신 내용으로 업데이트됩니다.")
    
    else:
        st.info("👆 위에서 PDF 파일을 업로드하세요.")

elif page == "🕷️ 웹 크롤링":
    st.header("🕷️ 웹 크롤링")
    st.markdown("웹페이지에서 정보를 크롤링하여 면접 준비에 활용합니다.")
    
    # 크롤링 가능한 사이트 예시
    with st.expander("💡 크롤링 가능한 사이트 예시", expanded=False):
        st.markdown("""
        ### ✅ 크롤링 잘 되는 사이트
        
        **기술 블로그 (특정 포스트):**
        - https://tech.kakao.com/2024/01/01/example (카카오 기술 블로그)
        - https://d2.naver.com/news/1234567 (네이버 D2)
        - https://toss.tech/slash/example (토스 기술 블로그)
        - https://techblog.woowahan.com/1234 (우아한형제들)
        
        **기술 문서/위키:**
        - https://ko.wikipedia.org/wiki/Java (위키백과)
        - https://velog.io/@username/post-title (벨로그)
        - https://brunch.co.kr/@username/post-title (브런치)
        
        **GitHub:**
        - https://github.com/owner/repo (GitHub 저장소)
        - https://github.com/owner/repo/blob/main/README.md (GitHub 파일)
        
        ### ⚠️ 크롤링 어려운 사이트
        
        - 네이버 메인 페이지 (동적 콘텐츠)
        - 카카오톡, 인스타그램 (로그인 필요)
        - JavaScript로만 렌더링되는 SPA 사이트
        
        ### 💡 팁
        
        - **특정 포스트 URL**을 사용하세요 (메인 페이지보다 상세 페이지가 잘 됩니다)
        - GitHub README나 문서 파일은 크롤링이 잘 됩니다
        - 위키백과, 기술 블로그 포스트는 추천합니다
        """)
    st.info("💡 웹페이지를 PDF로 변환하려면 브라우저에서 직접 변환하세요. (Cmd+P 또는 Ctrl+P → PDF로 저장)")
    
    # 크롤링 모드 선택
    crawl_mode = st.radio(
        "크롤링 모드",
        ["단일 URL", "여러 URL"],
        horizontal=True
    )
    
    if crawl_mode == "단일 URL":
        # 단일 URL 크롤링
        url = st.text_input(
            "크롤링할 URL을 입력하세요",
            placeholder="https://example.com",
            help="크롤링할 웹페이지의 URL을 입력하세요"
        )
        
        # 자동 RAG 저장 옵션
        auto_rag = st.checkbox(
            "📚 크롤링 후 자동으로 RAG에 추가",
            value=True,
            help="체크하면 크롤링 성공 시 자동으로 벡터 DB에 저장됩니다"
        )
        
        if url:
            if st.button("🕷️ 크롤링 시작", type="primary", use_container_width=True):
                with st.spinner("웹페이지를 크롤링하는 중..."):
                    try:
                        crawler_service = CrawlerService()
                        content = crawler_service.crawl_url(url)
                        
                        # 세션 상태에 저장
                        if "crawled_data" not in st.session_state:
                            st.session_state.crawled_data = []
                        
                        crawled_item = {
                            "url": url,
                            "content": content,
                            "length": len(content)
                        }
                        st.session_state.crawled_data.append(crawled_item)
                        
                        st.success(f"✅ 크롤링 완료! ({len(content):,}자)")
                        
                        # 자동 RAG 저장
                        if auto_rag and content and len(content.strip()) > 0:
                            with st.spinner("📚 RAG 벡터 DB에 저장 중..."):
                                try:
                                    from app.services.rag_service import RAGService
                                    rag_service = RAGService()
                                    
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    doc_id = loop.run_until_complete(
                                        rag_service.add_document(
                                            content,
                                            {"source": "crawler", "url": url}
                                        )
                                    )
                                    loop.close()
                                    
                                    st.success(f"📚 RAG에 자동 저장 완료! (문서 ID: {doc_id[:8]}...)")
                                except Exception as rag_error:
                                    st.warning(f"⚠️ RAG 저장 실패: {str(rag_error)} (크롤링 데이터는 세션에 저장되었습니다)")
                        
                        # 결과 표시
                        st.subheader("📄 크롤링 결과")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("URL", url)
                        with col2:
                            st.metric("추출된 텍스트 길이", f"{len(content):,}자")
                        
                        # 내용 미리보기
                        st.subheader("📖 내용 미리보기")
                        with st.expander("크롤링된 내용 보기", expanded=True):
                            st.text_area(
                                "크롤링된 텍스트",
                                content,
                                height=400,
                                label_visibility="collapsed"
                            )
                        
                        # 다운로드 버튼
                        st.download_button(
                            label="💾 텍스트 파일로 다운로드",
                            data=content,
                            file_name=f"crawled_{url.split('//')[-1].replace('/', '_')}.txt",
                            mime="text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ 크롤링 실패: {str(e)}")
                        st.exception(e)
    
    else:
        # 여러 URL 크롤링
        st.markdown("### 여러 URL 크롤링")
        urls_text = st.text_area(
            "크롤링할 URL들을 입력하세요 (한 줄에 하나씩)",
            height=150,
            help="각 URL을 새 줄에 입력하세요"
        )
        
        if urls_text:
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            
            if urls:
                st.info(f"📋 총 {len(urls)}개의 URL이 입력되었습니다.")
                
                # 자동 RAG 저장 옵션
                auto_rag_multi = st.checkbox(
                    "📚 크롤링 후 자동으로 RAG에 추가",
                    value=True,
                    key="auto_rag_multi",
                    help="체크하면 크롤링 성공 시 자동으로 벡터 DB에 저장됩니다"
                )
                
                if st.button("🕷️ 일괄 크롤링 시작", type="primary", use_container_width=True):
                    # 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results = []
                    crawler_service = CrawlerService()
                    rag_added_count = 0
                    
                    # RAG 서비스 초기화 (자동 저장용)
                    rag_service = None
                    if auto_rag_multi:
                        try:
                            from app.services.rag_service import RAGService
                            rag_service = RAGService()
                        except:
                            pass
                    
                    for idx, url in enumerate(urls):
                        status_text.text(f"크롤링 중: {url} ({idx + 1}/{len(urls)})")
                        progress_bar.progress((idx + 1) / len(urls))
                        
                        try:
                            content = crawler_service.crawl_url(url)
                            results.append({
                                "url": url,
                                "status": "success",
                                "content": content,
                                "length": len(content)
                            })
                            
                            # 자동 RAG 저장
                            if auto_rag_multi and rag_service and content and len(content.strip()) > 0:
                                try:
                                    loop_rag = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop_rag)
                                    loop_rag.run_until_complete(
                                        rag_service.add_document(
                                            content,
                                            {"source": "crawler", "url": url}
                                        )
                                    )
                                    loop_rag.close()
                                    rag_added_count += 1
                                except Exception as rag_err:
                                    pass  # RAG 저장 실패는 무시하고 계속
                            
                        except Exception as e:
                            results.append({
                                "url": url,
                                "status": "error",
                                "error": str(e)
                            })
                    
                    progress_bar.empty()
                    status_text.empty()
                    
                    # 결과 요약
                    success_count = sum(1 for r in results if r["status"] == "success")
                    error_count = len(results) - success_count
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.success(f"✅ 크롤링 성공: {success_count}개")
                    with col2:
                        if error_count > 0:
                            st.error(f"❌ 크롤링 실패: {error_count}개")
                    with col3:
                        if auto_rag_multi and rag_added_count > 0:
                            st.success(f"📚 RAG 저장: {rag_added_count}개")
                    
                    # 결과 상세 표시
                    st.subheader("📊 크롤링 결과 상세")
                    
                    for idx, result in enumerate(results):
                        with st.expander(f"{'✅' if result['status'] == 'success' else '❌'} {result['url']}", expanded=False):
                            if result["status"] == "success":
                                st.metric("텍스트 길이", f"{result['length']:,}자")
                                st.text_area(
                                    "내용",
                                    result["content"],
                                    height=200,
                                    key=f"content_{idx}",
                                    label_visibility="collapsed"
                                )
                            else:
                                st.error(f"오류: {result['error']}")
                    
                    # 세션 상태에 저장
                    if "crawled_data" not in st.session_state:
                        st.session_state.crawled_data = []
                    
                    for result in results:
                        if result["status"] == "success":
                            st.session_state.crawled_data.append({
                                "url": result["url"],
                                "content": result["content"],
                                "length": result["length"]
                            })
    
    # 크롤링된 데이터 요약
    if "crawled_data" in st.session_state and st.session_state.crawled_data:
        st.markdown("---")
        st.subheader("📚 크롤링된 데이터 요약")
        st.info(f"총 {len(st.session_state.crawled_data)}개의 페이지가 크롤링되었습니다.")
        
        # 데이터 목록
        for idx, item in enumerate(st.session_state.crawled_data):
            with st.expander(f"📄 {item['url']} ({item['length']:,}자)", expanded=False):
                st.text_area(
                    "내용",
                    item["content"],
                    height=200,
                    key=f"summary_{idx}",
                    label_visibility="collapsed"
                )
        
        # 전체 데이터 초기화 버튼
        if st.button("🗑️ 모든 크롤링 데이터 초기화", type="secondary"):
            st.session_state.crawled_data = []
            st.rerun()

elif page == "❓ 질문 생성":
    st.header("❓ 면접 질문 생성 챗봇")
    st.markdown("자연스러운 대화로 맞춤형 면접 질문을 생성합니다. 크롤링한 데이터나 PDF를 기반으로 답변합니다.")
    
    # RAG 서비스 초기화
    rag_service = RAGService()
    
    # Bedrock 클라이언트 초기화
    session_kwargs = {"region_name": settings.aws_region}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        session_kwargs.update({
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key
        })
    bedrock_runtime = boto3.client("bedrock-runtime", **session_kwargs)
    
    # 세션 상태 초기화
    if "question_messages" not in st.session_state:
        st.session_state.question_messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! 면접 질문 생성 챗봇입니다. 🎯\n\n예를 들어:\n- \"카카오 백엔드 개발자 면접 질문 5개 알려줘\"\n- \"네이버 프론트엔드 기술 질문 생성해줘\"\n- \"Java, Spring 기반 면접 질문 만들어줘\"\n\n어떤 질문을 생성해드릴까요?"
            }
        ]
    
    # 채팅 히스토리 표시
    for message in st.session_state.question_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    def chunk_handler(chunk):
        """스트리밍 청크 처리"""
        text = ""
        chunk_type = chunk.get("type")
        
        if chunk_type == "content_block_delta":
            # 스트리밍 중인 응답 텍스트의 일부
            text = chunk.get("delta", {}).get("text", "")
        elif chunk_type == "content_block_start":
            # 응답 텍스트 시작
            text = chunk.get("content_block", {}).get("text", "")
        
        return text
    
    def get_streaming_response_with_rag(user_prompt):
        """RAG를 사용한 스트리밍 응답 생성 (Rate Limiting & Retry 포함)"""
        import time
        from app.services.rate_limiter import rate_limiter
        
        # Retry 설정
        max_retries = 5
        base_delay = 5  # 기본 대기 시간 5초로 증가
        
        for attempt in range(max_retries):
            try:
                # Rate Limiting: 요청 전 대기 (매 시도마다)
                loop_rate = asyncio.new_event_loop()
                asyncio.set_event_loop(loop_rate)
                loop_rate.run_until_complete(rate_limiter.wait_if_needed(key="bedrock_stream"))
                loop_rate.close()
                
                # 회사명 추출 (회사 특화 문서 검색용)
                import re
                company_keywords = ["카카오", "네이버", "라인", "토스", "당근", "쿠팡", "배달의민족", "우아한형제들", 
                                   "삼성", "LG", "SK", "현대", "기아", "한화", "롯데", "CJ", "GS",
                                   "당근마켓", "무신사", "야놀자", "직방", "왓챠", "브랜디", "마켓컬리",
                                   "Apple", "Google", "Microsoft", "Amazon", "Meta", "Netflix", "Tesla",
                                   "애플", "구글", "마이크로소프트", "아마존", "메타", "넷플릭스", "테슬라"]
                
                extracted_companies = []
                user_prompt_lower = user_prompt.lower()
                for keyword in company_keywords:
                    if keyword.lower() in user_prompt_lower or keyword in user_prompt:
                        extracted_companies.append(keyword)
                
                # 검색 쿼리 개선: 회사명이 있으면 검색 쿼리에 포함
                search_query = user_prompt
                if extracted_companies:
                    # 회사명을 명시적으로 검색 쿼리에 추가
                    company_query = " ".join(extracted_companies)
                    search_query = f"{user_prompt} {company_query}"
                
                # RAG를 사용하여 관련 문서 검색
                relevant_docs = []
                rag_status = "❌ RAG 미사용 (일반 LLM 모드)"
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    # 검색 범위를 넓게 설정 (회사 특화 문서를 더 찾기 위해)
                    relevant_docs = loop.run_until_complete(
                        rag_service.search_documents(search_query, k=15)  # 검색 범위 확대: 10개 → 15개
                    )
                    loop.close()
                    
                    # 중복 제거: 같은 문서의 여러 청크 중 가장 긴 것만 유지
                    # url 또는 doc_id를 기준으로 중복 제거 (url 우선, 같은 URL = 같은 문서)
                    seen_documents = {}  # key: identifier, value: doc
                    
                    for doc in relevant_docs:
                        # 문서 식별자 생성 (url 우선, 없으면 doc_id, 없으면 source 사용)
                        doc_url = doc.metadata.get('url', '')
                        doc_id = doc.metadata.get('doc_id', '')
                        doc_source = doc.metadata.get('source', '')
                        
                        # URL이 있으면 URL을 식별자로, 없으면 doc_id, 없으면 source 사용
                        doc_identifier = doc_url if doc_url else (doc_id if doc_id else doc_source)
                        
                        if doc_identifier:
                            # 같은 문서를 아직 보지 않았으면 추가
                            if doc_identifier not in seen_documents:
                                seen_documents[doc_identifier] = doc
                            else:
                                # 이미 있는 문서의 청크보다 더 긴 청크면 교체 (더 많은 정보 포함)
                                existing_doc = seen_documents[doc_identifier]
                                if len(doc.page_content) > len(existing_doc.page_content):
                                    seen_documents[doc_identifier] = doc
                        else:
                            # 식별자가 없으면 그대로 추가 (중복 가능하지만 일단 포함)
                            # 고유 키 생성 (내용의 일부 사용)
                            unique_key = doc.page_content[:50] if doc.page_content else str(len(seen_documents))
                            if unique_key not in seen_documents:
                                seen_documents[unique_key] = doc
                    
                    # 중복 제거된 문서 리스트 생성
                    relevant_docs = list(seen_documents.values())
                    
                    # 회사명이 추출된 경우, 회사 관련 문서를 우선순위로 필터링
                    if extracted_companies and relevant_docs:
                        company_docs = []
                        other_docs = []
                        for doc in relevant_docs:
                            doc_content = doc.page_content.lower()
                            doc_url = doc.metadata.get('url', '').lower()
                            doc_source = str(doc.metadata.get('source', '')).lower()
                            
                            # 회사명이 문서 내용이나 메타데이터에 포함되어 있는지 확인
                            is_company_doc = any(
                                company.lower() in doc_content or 
                                company.lower() in doc_url or 
                                company.lower() in doc_source
                                for company in extracted_companies
                            )
                            
                            if is_company_doc:
                                company_docs.append(doc)
                            else:
                                other_docs.append(doc)
                        
                        # 회사 관련 문서를 먼저, 그 다음 일반 문서 (각각 중복 제거된 상태)
                        relevant_docs = company_docs[:10] + other_docs[:5]
                    
                    if relevant_docs:
                        company_info = f" (회사: {', '.join(extracted_companies)})" if extracted_companies else ""
                        rag_status = f"✅ RAG 사용 중 (관련 문서 {len(relevant_docs)}개 발견{company_info})"
                    else:
                        rag_status = "⚠️ RAG 검색됐지만 관련 문서 없음 (일반 LLM 모드)"
                except Exception as rag_error:
                    # RAG 검색 실패 시 무시하고 계속 진행
                    rag_status = f"❌ RAG 검색 실패: {str(rag_error)[:50]}... (일반 LLM 모드)"
                
                # 컨텍스트 구성 (검색 범위 확대에 맞춰 길이도 증가)
                context = "\n\n".join([doc.page_content[:500] for doc in relevant_docs]) if relevant_docs else ""
                
                # RAG 상태 정보를 yield로 전달 (개발자 모드에서만 표시)
                # 일반 사용자 모드에서는 절대 표시하지 않음
                developer_mode_debug = st.session_state.get('developer_mode', False)
                if developer_mode_debug:
                    # 개발자 모드일 때만 디버깅 정보 표시
                    yield f"🔍 **{rag_status}**\n\n"
                    if relevant_docs:
                        yield f"📚 **검색된 문서 미리보기:**\n"
                        for i, doc in enumerate(relevant_docs, 1):
                            preview = doc.page_content[:100].replace('\n', ' ')
                            source = doc.metadata.get('url', doc.metadata.get('source', 'unknown'))
                            yield f"{i}. [{source}] {preview}...\n"
                        yield "\n---\n\n"
                # 일반 사용자 모드일 때는 아무것도 표시하지 않고 바로 LLM 응답으로 넘어감
                
                # 시스템 프롬프트 구성
                system_message = """당신은 면접 준비를 도와주는 전문 챗봇입니다. 
사용자의 요청에 따라 맞춤형 면접 질문을 생성해주세요.

**중요: 대화 맥락 이해**
- 이전 대화 내용을 반드시 참고하여 답변하세요
- 사용자가 "1번", "2번", "그 질문", "위 질문" 등으로 참조할 때는 이전에 생성한 질문을 의미합니다
- 사용자가 "그것", "이것", "그건" 등으로 참조할 때는 이전 대화에서 언급된 내용을 의미합니다
- 대화 히스토리를 꼼꼼히 확인하여 사용자의 의도를 정확히 파악하세요

**참고 자료 활용 (가장 중요)**
- 참고 자료가 제공된 경우, 반드시 참고 자료의 내용을 우선적으로 사용하세요
- 참고 자료에 포함된 구체적인 정보, 용어, 기술 스택, 회사 특성 등을 정확히 반영하여 질문을 생성하세요
- 참고 자료의 내용이 일반적인 지식과 다를 경우, 참고 자료의 내용을 기준으로 질문하세요
- 참고 자료에 특정 회사명, 서비스명, 기술명이 나오면 그것을 반드시 포함하여 질문하세요
- 참고 자료의 세부 내용(예: 특정 알고리즘, 아키텍처, 경험 사례)을 그대로 반영하세요

다음 정보를 참고하여 답변하세요:
- 회사명, 직무, 기술 스택이 언급되면 그것을 반영한 질문 생성
- 질문 개수가 명시되지 않으면 5개 정도 생성
- 기술 질문, 행동 질문, 상황 질문 등 다양한 유형 제공
- 실제 면접에서 나올 수 있는 수준의 질문 생성
- 이전에 생성한 질문에 대한 후속 질문(답변 예시, 설명 등)도 제공하세요

**절대 하지 말아야 할 것:**
- 참고 자료, RAG 검색, 벡터 검색, 문서 검색 등 기술적 정보를 답변에 포함하지 마세요
- 검색된 문서의 출처나 URL을 답변에 표시하지 마세요
- "참고 자료를 기반으로", "검색 결과", "벡터 RAG", "VECTOR 검색" 등의 표현을 사용하지 마세요
- 참고 자료의 내용을 자연스럽게 활용하되, 기술적 용어는 언급하지 마세요

답변은 친근하고 도움이 되는 톤으로 작성해주세요."""
                
                # 메시지 히스토리 구성 (시스템 메시지 + 대화 히스토리)
                history = []
                
                # 시스템 메시지 추가 (참고 자료 포함)
                if context:
                    system_content = f"""{system_message}

[참고 자료]
{context[:1000]}"""  # 참고 자료도 길이 제한
                else:
                    system_content = f"""{system_message}

[참고 자료]
참고 자료가 없습니다. 일반적인 면접 질문을 생성해주세요."""
                
                # 대화 히스토리 추가 (최근 4개 메시지만 - 토큰 절약 & Throttling 방지)
                # 초기 환영 메시지 제외: 첫 번째 메시지가 assistant이고 실제 대화가 없는 경우
                all_messages = st.session_state.question_messages
                
                # 실제 대화 메시지만 필터링 (초기 환영 메시지 제외)
                # 첫 번째 메시지가 assistant인 경우 제외
                actual_conversation = []
                if len(all_messages) > 1:
                    # 첫 번째 메시지가 assistant인 경우 제외하고 나머지만
                    actual_conversation = all_messages[1:]  # 초기 환영 메시지 제외
                elif len(all_messages) == 1 and all_messages[0]["role"] == "user":
                    # 첫 메시지가 user인 경우 (초기 메시지 없음)
                    actual_conversation = all_messages
                
                # 현재 질문(user_prompt)은 히스토리에 포함하지 않음
                # 마지막 메시지가 user이고 현재 질문과 같으면 제외
                if actual_conversation and actual_conversation[-1]["role"] == "user":
                    # 마지막 user 메시지가 현재 질문이므로 제외
                    actual_conversation = actual_conversation[:-1]
                
                # 최근 4개만 선택 (실제 대화 메시지 중, 현재 질문 제외)
                recent_messages = actual_conversation[-4:] if len(actual_conversation) > 0 else []
                
                history_count = 0
                for msg in recent_messages:
                    if msg["role"] in ["user", "assistant"]:
                        # 메시지 내용 길이 제한 완화 (500자 → 1500자) - Multi-turn을 위해 더 많은 컨텍스트 필요
                        content = msg["content"][:1500] if len(msg["content"]) > 1500 else msg["content"]
                        history.append({
                            "role": msg["role"],
                            "content": [{"type": "text", "text": content}]
                        })
                        history_count += 1
                
                # 시스템 메시지를 히스토리 앞에 추가 (컨텍스트를 먼저 제공)
                history.insert(0, {
                    "role": "user",
                    "content": [{"type": "text", "text": system_content}]
                })
                
                # 현재 사용자 메시지 추가
                history.append({
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                })
                
                # 디버깅 정보 (개발자 모드에서만 표시)
                developer_mode_debug = st.session_state.get('developer_mode', False)
                if developer_mode_debug:
                    yield f"\n🔧 **디버깅 정보:**\n"
                    yield f"- 전체 대화 메시지 수: {len(st.session_state.question_messages)}개\n"
                    yield f"- 히스토리에 포함된 메시지: {history_count}개 (최근 4개 중)\n"
                    yield f"- LLM에 전달될 총 메시지 수: {len(history)}개\n"
                    yield f"\n---\n\n"
                
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,  # 토큰 수 감소 (2000 → 1500)
                    "messages": history,
                })
                
                # 스트리밍 응답 (성공 시 yield하고 return으로 종료)
                response = bedrock_runtime.invoke_model_with_response_stream(
                    modelId=settings.bedrock_model_id,
                    body=body,
                )
                
                stream = response.get("body")
                if stream:
                    for event in stream:
                        chunk = event.get("chunk")
                        if chunk:
                            chunk_json = json.loads(chunk.get("bytes").decode())
                            text = chunk_handler(chunk_json)
                            if text:
                                yield text
                
                # 성공적으로 완료되면 함수 종료
                return
                                
            except Exception as e:
                error_str = str(e)
                
                # ThrottlingException인 경우 재시도
                if "ThrottlingException" in error_str or "Too many requests" in error_str or "throttl" in error_str.lower():
                    if attempt < max_retries - 1:
                        # 지수 백오프: 5초, 10초, 20초, 40초, 80초
                        delay = base_delay * (2 ** attempt)
                        yield f"\n\n⏳ 요청이 많아 {delay}초 대기 후 재시도합니다... (시도 {attempt + 1}/{max_retries})\n\n"
                        time.sleep(delay)
                        continue
                    else:
                        yield f"\n\n❌ 오류: 서버가 과부하 상태입니다. 5분 정도 기다린 후 다시 시도해주세요.\n\n"
                        return
                else:
                    # 다른 오류는 즉시 반환
                    yield f"\n\n❌ 오류 발생: {str(e)}\n\n"
                    return
    
    # 사용자 입력
    if prompt := st.chat_input("면접 질문에 대해 물어보세요..."):
        # 사용자 메시지 추가
        st.session_state.question_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI 응답 생성 (스트리밍)
        with st.chat_message("assistant"):
            model_output = st.write_stream(get_streaming_response_with_rag(prompt))
        
        # 보조 응답 세션 상태에 추가
        st.session_state.question_messages.append({"role": "assistant", "content": model_output})
    
    # 사이드바에 RAG 문서 관리 추가 (개발자 모드에서만 표시)
    developer_mode_rag = st.session_state.get('developer_mode', False)
    
    if developer_mode_rag:
        with st.sidebar:
            st.markdown("---")
            st.subheader("📚 RAG 문서 관리 (개발자)")
            
            # RAG 문서 개수 확인
            try:
                loop_count = asyncio.new_event_loop()
                asyncio.set_event_loop(loop_count)
                doc_list = loop_count.run_until_complete(rag_service.list_documents())
                loop_count.close()
                
                if doc_list:
                    st.success(f"✅ 저장된 문서: {len(doc_list)}개")
                    
                    with st.expander("📋 문서 목록 및 삭제", expanded=False):
                        for doc in doc_list:
                            doc_id = doc.get('id', '')
                            source = doc.get('url', doc.get('source', 'unknown'))
                            source_display = source[:60] + "..." if len(source) > 60 else source
                            
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"• {source_display}")
                            with col2:
                                if st.button("🗑️ 삭제", key=f"delete_{doc_id}", use_container_width=True):
                                    try:
                                        loop_delete = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop_delete)
                                        loop_delete.run_until_complete(
                                            rag_service.delete_document(doc_id)
                                        )
                                        loop_delete.close()
                                        st.success(f"✅ 삭제 완료: {source_display}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ 삭제 실패: {str(e)}")
                        
                        # 전체 삭제 버튼
                        st.markdown("---")
                        if st.button("🗑️ 모든 문서 삭제", type="secondary", use_container_width=True):
                            try:
                                loop_delete_all = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop_delete_all)
                                
                                deleted_count = 0
                                for doc in doc_list:
                                    try:
                                        loop_delete_all.run_until_complete(
                                            rag_service.delete_document(doc.get('id', ''))
                                        )
                                        deleted_count += 1
                                    except:
                                        pass
                                
                                loop_delete_all.close()
                                st.success(f"✅ {deleted_count}개 문서 삭제 완료!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 삭제 실패: {str(e)}")
                else:
                    st.warning("⚠️ RAG에 저장된 문서가 없습니다.")
                    st.info("💡 크롤링 데이터나 PDF를 추가하면 맞춤형 질문을 생성할 수 있습니다.")
            except Exception as e:
                st.info("ℹ️ RAG 문서 목록 확인 중...")
            
            # 문서 추가 섹션
            add_mode = st.radio(
                "추가할 문서",
                ["크롤링 데이터", "PDF 텍스트", "직접 입력"],
                key="rag_add_mode"
            )
        
            if add_mode == "크롤링 데이터":
                if "crawled_data" in st.session_state and st.session_state.crawled_data:
                    selected_urls = st.multiselect(
                        "선택",
                        options=[item["url"] for item in st.session_state.crawled_data],
                        format_func=lambda x: x[:50] + "..." if len(x) > 50 else x,
                        key="rag_crawler_select"
                    )
                    
                    if st.button("📥 RAG에 추가", key="rag_add_crawler"):
                        with st.spinner("추가 중..."):
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                                added_count = 0
                                errors = []
                                
                                for url in selected_urls:
                                    try:
                                        for item in st.session_state.crawled_data:
                                            if item["url"] == url:
                                                # 내용 확인
                                                content = item.get("content", "")
                                                if not content or len(content.strip()) == 0:
                                                    errors.append(f"{url}: 내용이 비어있습니다")
                                                    continue
                                                
                                                # RAG에 추가
                                                doc_id = loop.run_until_complete(
                                                    rag_service.add_document(
                                                        content,
                                                        {"source": "crawler", "url": url}
                                                    )
                                                )
                                                added_count += 1
                                                st.info(f"✅ {url[:50]}... 추가됨 (ID: {doc_id[:8]}...)")
                                                break
                                    except Exception as e:
                                        errors.append(f"{url}: {str(e)}")
                                
                                loop.close()
                                
                                if added_count > 0:
                                    st.success(f"✅ {added_count}개 추가됨!")
                                    if errors:
                                        st.warning(f"⚠️ {len(errors)}개 실패: {', '.join(errors[:3])}")
                                else:
                                    st.error(f"❌ 추가 실패: {', '.join(errors) if errors else '알 수 없는 오류'}")
                                
                                # 저장 후 문서 목록 새로고침
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 실패: {str(e)}")
                                st.exception(e)
                else:
                    st.info("크롤링 데이터 없음")
            
            elif add_mode == "PDF 텍스트":
                if "pdf_text" in st.session_state:
                    if st.button("📥 PDF 텍스트 RAG에 추가", key="rag_add_pdf"):
                        with st.spinner("추가 중..."):
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(
                                    rag_service.add_document(
                                        st.session_state.pdf_text,
                                        {"source": "pdf", "filename": st.session_state.get("pdf_filename", "unknown")}
                                    )
                                )
                                loop.close()
                                st.success("✅ 추가됨!")
                            except Exception as e:
                                st.error(f"❌ 실패: {str(e)}")
                else:
                    st.info("PDF 텍스트 없음")
            
            elif add_mode == "직접 입력":
                manual_text = st.text_area("텍스트 입력", height=100, key="rag_manual_text")
                if st.button("📥 추가", key="rag_add_manual"):
                    if manual_text:
                        with st.spinner("추가 중..."):
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(
                                    rag_service.add_document(manual_text, {"source": "manual"})
                                )
                                loop.close()
                                st.success("✅ 추가됨!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ 실패: {str(e)}")
            
            # Multi-turn 디버깅 섹션
            st.markdown("---")
            st.subheader("🔧 Multi-turn 디버깅")
            
            # 대화 히스토리 통계
            total_messages = len(st.session_state.question_messages)
            user_messages = [m for m in st.session_state.question_messages if m["role"] == "user"]
            assistant_messages = [m for m in st.session_state.question_messages if m["role"] == "assistant"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("전체 메시지", total_messages)
            with col2:
                st.metric("사용자 메시지", len(user_messages))
            with col3:
                st.metric("AI 메시지", len(assistant_messages))
            
            # 최근 대화 히스토리 확인 (LLM에 전달되는 메시지)
            with st.expander("📋 최근 대화 히스토리 (LLM에 전달)", expanded=False):
                # 실제 대화 메시지만 필터링 (초기 환영 메시지 제외)
                all_messages = st.session_state.question_messages
                if len(all_messages) > 1:
                    # 첫 번째 메시지가 assistant인 경우 제외
                    actual_conversation = all_messages[1:]
                elif len(all_messages) == 1 and all_messages[0]["role"] == "user":
                    actual_conversation = all_messages
                else:
                    actual_conversation = []
                
                recent_for_llm = actual_conversation[-4:] if len(actual_conversation) > 0 else []
                if recent_for_llm:
                    st.info(f"💡 최근 {len(recent_for_llm)}개 메시지가 다음 질문에 포함됩니다:")
                    for i, msg in enumerate(recent_for_llm, 1):
                        role_emoji = "👤" if msg["role"] == "user" else "🤖"
                        content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                        st.write(f"{i}. {role_emoji} **{msg['role']}**: {content_preview}")
                else:
                    st.info("아직 대화 히스토리가 없습니다. (초기 환영 메시지는 제외됨)")
            
            # 전체 대화 히스토리 확인
            with st.expander("📜 전체 대화 히스토리", expanded=False):
                if st.session_state.question_messages:
                    for i, msg in enumerate(st.session_state.question_messages, 1):
                        role_emoji = "👤" if msg["role"] == "user" else "🤖"
                        st.write(f"{i}. {role_emoji} **{msg['role']}**")
                        st.text_area(
                            "내용",
                            msg["content"],
                            height=100,
                            key=f"debug_msg_{i}",
                            label_visibility="collapsed"
                        )
                else:
                    st.info("대화 히스토리가 없습니다.")
            
            # 대화 초기화 버튼
            if st.button("🗑️ 대화 초기화", type="secondary"):
                st.session_state.question_messages = [
                    {
                        "role": "assistant",
                        "content": "대화가 초기화되었습니다. 새로운 질문을 해주세요! 🎯"
                    }
                ]
                st.rerun()

