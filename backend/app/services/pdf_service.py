"""
PDF 처리 서비스
"""
import pdfplumber
from typing import Optional, Dict
import io


class PDFService:
    """PDF 처리 서비스 클래스"""
    
    async def extract_text(self, file_content: bytes, filename: str) -> str:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            file_content: PDF 파일의 바이트 내용
            filename: 파일명
            
        Returns:
            추출된 텍스트
        """
        try:
            text_content = []
            
            # PDF 파싱
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"=== 페이지 {page_num} ===\n{text}\n")
            
            if not text_content:
                raise Exception("PDF에서 텍스트를 추출할 수 없습니다. 이미지 기반 PDF일 수 있습니다.")
            
            return "\n".join(text_content)
        
        except Exception as e:
            raise Exception(f"PDF 처리 중 오류 발생: {str(e)}")
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        텍스트에서 섹션별로 분리
        (이력서/자기소개서의 구조화된 정보 추출)
        
        Args:
            text: 추출된 텍스트
            
        Returns:
            섹션별로 분리된 딕셔너리
        """
        sections = {
            "personal_info": "",
            "education": "",
            "experience": "",
            "projects": "",
            "skills": "",
            "other": ""
        }
        
        lines = text.split("\n")
        current_section = "other"
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # 섹션 키워드 감지
            if any(keyword in line_lower for keyword in ["이름", "연락처", "이메일", "주소", "전화번호", "phone", "email"]):
                current_section = "personal_info"
            elif any(keyword in line_lower for keyword in ["학력", "교육", "education", "학위", "학교"]):
                current_section = "education"
            elif any(keyword in line_lower for keyword in ["경력", "경험", "experience", "근무", "회사", "work"]):
                current_section = "experience"
            elif any(keyword in line_lower for keyword in ["프로젝트", "project", "작업"]):
                current_section = "projects"
            elif any(keyword in line_lower for keyword in ["기술", "스킬", "skill", "능력", "보유기술"]):
                current_section = "skills"
            
            # 빈 줄이 아닌 경우 현재 섹션에 추가
            if line.strip():
                if sections[current_section]:
                    sections[current_section] += "\n"
                sections[current_section] += line
        
        return sections
    
    def get_summary(self, text: str) -> Dict[str, any]:
        """
        PDF 텍스트 요약 정보 추출
        
        Args:
            text: 추출된 텍스트
            
        Returns:
            요약 정보 딕셔너리
        """
        sections = self.extract_sections(text)
        
        # 기본 통계
        total_chars = len(text)
        total_lines = len(text.split("\n"))
        non_empty_lines = len([line for line in text.split("\n") if line.strip()])
        
        return {
            "total_characters": total_chars,
            "total_lines": total_lines,
            "non_empty_lines": non_empty_lines,
            "sections_found": {
                "personal_info": bool(sections["personal_info"]),
                "education": bool(sections["education"]),
                "experience": bool(sections["experience"]),
                "projects": bool(sections["projects"]),
                "skills": bool(sections["skills"])
            },
            "sections": sections
        }

