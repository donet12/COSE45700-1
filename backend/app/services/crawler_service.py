"""
웹 크롤링 서비스
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import time
import re


class CrawlerService:
    """웹 크롤링 서비스 클래스"""
    
    def __init__(self):
        """초기화"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # SSL 인증서 검증 경고 비활성화 (개발 환경용)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def crawl_url(self, url: str, max_length: int = 50000) -> str:
        """
        URL에서 텍스트 내용 크롤링 (GitHub 페이지 지원)
        
        Args:
            url: 크롤링할 URL
            max_length: 최대 텍스트 길이 (기본값: 50000자)
            
        Returns:
            크롤링된 텍스트 내용
        """
        try:
            # URL 유효성 검사
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"유효하지 않은 URL: {url}")
            
            # GitHub URL 처리
            if 'github.com' in parsed.netloc:
                return self._crawl_github(url, max_length)
            
            # 카카오 기술 블로그 URL 처리 (JavaScript 렌더링 필요)
            if 'tech.kakao.com' in parsed.netloc:
                return self._crawl_kakao_tech(url, max_length)
            
            # 네이버 블로그 URL 처리 (Selenium 필요)
            if 'blog.naver.com' in parsed.netloc:
                return self._crawl_naver_blog(url, max_length)
            
            # 티스토리 블로그 URL 처리 (Selenium 필요)
            if 'tistory.com' in parsed.netloc:
                return self._crawl_tistory(url, max_length)
            
            # 일반 URL 크롤링 (SSL 인증서 검증 비활성화 - 개발 환경용)
            response = self.session.get(url, timeout=10, verify=False)
            response.raise_for_status()
            
            # HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 불필요한 태그 제거 (더 많은 태그 추가)
            unwanted_tags = [
                'script', 'style', 'nav', 'footer', 'header', 'aside',
                'noscript', 'iframe', 'embed', 'object', 'form',
                'button', 'input', 'select', 'textarea', 'label'
            ]
            for tag in soup(unwanted_tags):
                tag.decompose()
            
            # aria-label이나 role로 네비게이션 요소 제거
            for tag in soup.find_all(attrs={'role': ['navigation', 'banner', 'complementary', 'search']}):
                tag.decompose()
            
            # aria-label에 "바로가기", "메뉴" 등이 포함된 요소 제거
            for tag in soup.find_all(attrs={'aria-label': True}):
                aria_label = tag.get('aria-label', '').lower()
                if any(keyword in aria_label for keyword in ['바로가기', '메뉴', 'navigation', 'menu', 'skip']):
                    tag.decompose()
            
            # class나 id에 nav, menu, header, footer가 포함된 요소 제거
            for tag in soup.find_all(class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['nav', 'menu', 'header', 'footer', 'sidebar', 'skip'])):
                tag.decompose()
            for tag in soup.find_all(id=lambda x: x and any(keyword in str(x).lower() for keyword in ['nav', 'menu', 'header', 'footer', 'sidebar', 'skip'])):
                tag.decompose()
            
            # 메인 콘텐츠 영역 우선 추출 시도
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '#content', '.main-content', '#main-content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # 메인 콘텐츠가 있으면 그것만 사용, 없으면 전체 사용
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # 텍스트 정리
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            # 너무 짧은 줄 제거 (1-2자만 있는 줄)
            lines = [line for line in lines if len(line) > 2]
            cleaned_text = '\n'.join(lines)
            
            # 길이 제한
            if len(cleaned_text) > max_length:
                cleaned_text = cleaned_text[:max_length] + "... (내용이 너무 길어 일부만 추출했습니다)"
            
            return cleaned_text
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"웹 크롤링 오류: {str(e)}")
        except Exception as e:
            raise Exception(f"크롤링 처리 중 오류: {str(e)}")
    
    def crawl_multiple_urls(self, urls: List[str]) -> List[dict]:
        """
        여러 URL을 크롤링
        
        Args:
            urls: 크롤링할 URL 리스트
            
        Returns:
            크롤링 결과 리스트
        """
        results = []
        
        for url in urls:
            try:
                text = self.crawl_url(url)
                results.append({
                    "url": url,
                    "status": "success",
                    "content": text,
                    "length": len(text)
                })
                # 요청 간격 조절 (서버 부하 방지)
                time.sleep(1)
            except Exception as e:
                results.append({
                    "url": url,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def extract_links(self, url: str, base_url: Optional[str] = None) -> List[str]:
        """
        페이지에서 링크 추출
        
        Args:
            url: 크롤링할 URL
            base_url: 기본 URL (상대 경로 해결용)
            
        Returns:
            링크 URL 리스트
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(url, href)
                links.append(absolute_url)
            
            return links
        
        except Exception as e:
            return []
    
    def _crawl_github(self, url: str, max_length: int = 50000) -> str:
        """
        GitHub 페이지 크롤링 (Selenium 사용)
        
        Args:
            url: GitHub URL
            max_length: 최대 텍스트 길이
            
        Returns:
            크롤링된 텍스트 내용
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            raise Exception("GitHub 크롤링을 위해 Selenium이 필요합니다. pip install selenium webdriver-manager")
        
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--ignore-certificate-errors')  # SSL 인증서 검증 비활성화
            chrome_options.add_argument('--ignore-ssl-errors')  # SSL 오류 무시
            chrome_options.add_experimental_option('acceptInsecureCerts', True)  # 안전하지 않은 인증서 허용
            
            # ChromeDriver 설정
            import os
            import subprocess
            
            driver_path = None
            
            # 방법 1: 시스템에 설치된 chromedriver 찾기
            try:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    driver_path = result.stdout.strip()
            except:
                pass
            
            # 방법 2: ChromeDriverManager 사용
            if not driver_path:
                try:
                    manager_path = ChromeDriverManager().install()
                    driver_dir = os.path.dirname(manager_path)
                    
                    # chromedriver 실행 파일 찾기 (재귀적으로)
                    for root, dirs, files in os.walk(driver_dir):
                        for file in files:
                            if file == 'chromedriver' or file.startswith('chromedriver') and not any(file.endswith(ext) for ext in ['.txt', '.md', '.zip', '.tar.gz']):
                                candidate_path = os.path.join(root, file)
                                # 실행 가능한 파일인지 확인
                                if os.path.isfile(candidate_path) and os.access(candidate_path, os.X_OK):
                                    # 파일 타입 확인 (실행 파일인지)
                                    try:
                                        result = subprocess.run(['file', candidate_path], capture_output=True, text=True)
                                        if 'executable' in result.stdout.lower() or 'binary' in result.stdout.lower():
                                            driver_path = candidate_path
                                            break
                                    except:
                                        # file 명령어가 없으면 그냥 사용
                                        driver_path = candidate_path
                                        break
                        if driver_path:
                            break
                except Exception as e:
                    pass
            
            # 방법 3: 직접 chromedriver 사용 시도
            if driver_path and os.path.exists(driver_path):
                try:
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    # Service 지정 실패 시 자동 탐지 시도
                    driver = webdriver.Chrome(options=chrome_options)
            else:
                # 모든 방법 실패 시 자동 탐지 시도
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    raise Exception(
                        f"ChromeDriver를 찾을 수 없습니다.\n"
                        f"다음 명령어로 설치하세요:\n"
                        f"Mac: brew install chromedriver\n"
                        f"또는 ChromeDriver 캐시를 삭제하세요: rm -rf ~/.wdm/drivers/chromedriver"
                    )
            
            try:
                # 페이지 로드
                driver.get(url)
                
                # 페이지가 완전히 로드될 때까지 대기 (최대 10초)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 추가 대기 (JavaScript 실행 완료)
                time.sleep(3)
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                
                # BeautifulSoup으로 파싱
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 불필요한 태그 제거
                unwanted_tags = [
                    'script', 'style', 'nav', 'footer', 'header', 'aside',
                    'noscript', 'iframe', 'embed', 'object', 'form',
                    'button', 'input', 'select', 'textarea', 'label'
                ]
                for tag in soup(unwanted_tags):
                    tag.decompose()
                
                # GitHub 특정 요소 제거
                for tag in soup.find_all(class_=lambda x: x and any(keyword in str(x).lower() for keyword in ['header', 'footer', 'sidebar', 'navigation', 'menu'])):
                    tag.decompose()
                
                # 메인 콘텐츠 영역 찾기
                main_content = None
                for selector in ['main', 'article', '[role="main"]', '.repository-content', '.Box', '.markdown-body']:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                # 메인 콘텐츠가 있으면 그것만 사용
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                else:
                    text = soup.get_text(separator='\n', strip=True)
                
                # 텍스트 정리
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                lines = [line for line in lines if len(line) > 2]
                cleaned_text = '\n'.join(lines)
                
                # 길이 제한
                if len(cleaned_text) > max_length:
                    cleaned_text = cleaned_text[:max_length] + "... (내용이 너무 길어 일부만 추출했습니다)"
                
                return cleaned_text
                
            finally:
                driver.quit()
        
        except Exception as e:
            raise Exception(f"GitHub 크롤링 중 오류: {str(e)}")
    
    def _crawl_kakao_tech(self, url: str, max_length: int = 50000) -> str:
        """
        카카오 기술 블로그 크롤링 (Selenium 사용)
        
        Args:
            url: 카카오 기술 블로그 URL
            max_length: 최대 텍스트 길이
            
        Returns:
            크롤링된 텍스트 내용
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            raise Exception("카카오 기술 블로그 크롤링을 위해 Selenium이 필요합니다. pip install selenium webdriver-manager")
        
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--ignore-certificate-errors')  # SSL 인증서 검증 비활성화
            chrome_options.add_argument('--ignore-ssl-errors')  # SSL 오류 무시
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option('acceptInsecureCerts', True)  # 안전하지 않은 인증서 허용
            
            # ChromeDriver 설정
            import os
            import subprocess
            
            driver_path = None
            
            # 방법 1: 시스템에 설치된 chromedriver 찾기
            try:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    driver_path = result.stdout.strip()
            except:
                pass
            
            # 방법 2: ChromeDriverManager 사용
            if not driver_path:
                try:
                    manager_path = ChromeDriverManager().install()
                    driver_dir = os.path.dirname(manager_path)
                    
                    # chromedriver 실행 파일 찾기
                    for root, dirs, files in os.walk(driver_dir):
                        for file in files:
                            if file == 'chromedriver' or (file.startswith('chromedriver') and not any(file.endswith(ext) for ext in ['.txt', '.md', '.zip', '.tar.gz'])):
                                candidate_path = os.path.join(root, file)
                                if os.path.isfile(candidate_path) and os.access(candidate_path, os.X_OK):
                                    try:
                                        result = subprocess.run(['file', candidate_path], capture_output=True, text=True)
                                        if 'executable' in result.stdout.lower() or 'binary' in result.stdout.lower():
                                            driver_path = candidate_path
                                            break
                                    except:
                                        driver_path = candidate_path
                                        break
                        if driver_path:
                            break
                except Exception as e:
                    pass
            
            # ChromeDriver 초기화
            if driver_path and os.path.exists(driver_path):
                try:
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    driver = webdriver.Chrome(options=chrome_options)
            else:
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    raise Exception(
                        f"ChromeDriver를 찾을 수 없습니다.\n"
                        f"다음 명령어로 설치하세요:\n"
                        f"Mac: brew install chromedriver\n"
                        f"또는 ChromeDriver 캐시를 삭제하세요: rm -rf ~/.wdm/drivers/chromedriver"
                    )
            
            try:
                # 페이지 로드
                driver.get(url)
                
                # 페이지가 완전히 로드될 때까지 대기
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 추가 대기 (JavaScript 실행 완료)
                time.sleep(3)
                
                # 스크롤 다운 (동적 콘텐츠 로딩을 위해)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                
                # BeautifulSoup으로 파싱
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 불필요한 태그 제거
                unwanted_tags = [
                    'script', 'style', 'nav', 'footer', 'header', 'aside',
                    'noscript', 'iframe', 'embed', 'object', 'form',
                    'button', 'input', 'select', 'textarea', 'label',
                    'meta', 'link', 'svg', 'path'
                ]
                for tag in soup(unwanted_tags):
                    tag.decompose()
                
                # 카카오 기술 블로그 특정 요소 제거
                for tag in soup.find_all(class_=lambda x: x and any(keyword in str(x).lower() for keyword in [
                    'header', 'footer', 'sidebar', 'navigation', 'menu', 'nav',
                    'comment', 'reply', 'ad', 'banner', 'widget', 'aside',
                    'site-header', 'site-footer', 'site-nav', 'site-menu'
                ])):
                    tag.decompose()
                
                # 카카오 기술 블로그 본문 영역 찾기
                main_content = None
                selectors = [
                    'article',  # HTML5 article 태그
                    'main',  # HTML5 main 태그
                    '[role="main"]',  # role="main"
                    '.post-content',  # post-content 클래스
                    '.article-content',  # article-content 클래스
                    '.content',  # content 클래스
                    '#content',  # content ID
                    '.post-body',  # post-body 클래스
                    '.entry-content'  # entry-content 클래스
                ]
                
                for selector in selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                # 메인 콘텐츠가 있으면 그것만 사용
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                else:
                    # 메인 콘텐츠를 찾지 못한 경우, body에서 불필요한 요소 제거 후 추출
                    for tag in soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in [
                        'header', 'footer', 'nav', 'menu', 'sidebar', 'comment', 'ad'
                    ])):
                        tag.decompose()
                    text = soup.get_text(separator='\n', strip=True)
                
                # 텍스트 정리
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                # 너무 짧은 줄 제거 (1-2자만 있는 줄)
                lines = [line for line in lines if len(line) > 2]
                # 중복된 빈 줄 제거
                cleaned_lines = []
                prev_empty = False
                for line in lines:
                    if line:
                        cleaned_lines.append(line)
                        prev_empty = False
                    elif not prev_empty:
                        cleaned_lines.append('')
                        prev_empty = True
                
                cleaned_text = '\n'.join(cleaned_lines)
                
                # 길이 제한
                if len(cleaned_text) > max_length:
                    cleaned_text = cleaned_text[:max_length] + "... (내용이 너무 길어 일부만 추출했습니다)"
                
                return cleaned_text
                
            finally:
                driver.quit()
        
        except Exception as e:
            raise Exception(f"카카오 기술 블로그 크롤링 중 오류: {str(e)}")
    
    def _crawl_naver_blog(self, url: str, max_length: int = 50000) -> str:
        """
        네이버 블로그 크롤링 (Selenium 사용)
        
        Args:
            url: 네이버 블로그 URL
            max_length: 최대 텍스트 길이
            
        Returns:
            크롤링된 텍스트 내용
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            raise Exception("네이버 블로그 크롤링을 위해 Selenium이 필요합니다. pip install selenium webdriver-manager")
        
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--ignore-certificate-errors')  # SSL 인증서 검증 비활성화
            chrome_options.add_argument('--ignore-ssl-errors')  # SSL 오류 무시
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option('acceptInsecureCerts', True)  # 안전하지 않은 인증서 허용
            
            # ChromeDriver 설정 (GitHub와 동일한 로직)
            import os
            import subprocess
            
            driver_path = None
            
            # 방법 1: 시스템에 설치된 chromedriver 찾기
            try:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    driver_path = result.stdout.strip()
            except:
                pass
            
            # 방법 2: ChromeDriverManager 사용
            if not driver_path:
                try:
                    manager_path = ChromeDriverManager().install()
                    driver_dir = os.path.dirname(manager_path)
                    
                    # chromedriver 실행 파일 찾기
                    for root, dirs, files in os.walk(driver_dir):
                        for file in files:
                            if file == 'chromedriver' or (file.startswith('chromedriver') and not any(file.endswith(ext) for ext in ['.txt', '.md', '.zip', '.tar.gz'])):
                                candidate_path = os.path.join(root, file)
                                if os.path.isfile(candidate_path) and os.access(candidate_path, os.X_OK):
                                    try:
                                        result = subprocess.run(['file', candidate_path], capture_output=True, text=True)
                                        if 'executable' in result.stdout.lower() or 'binary' in result.stdout.lower():
                                            driver_path = candidate_path
                                            break
                                    except:
                                        driver_path = candidate_path
                                        break
                        if driver_path:
                            break
                except Exception as e:
                    pass
            
            # ChromeDriver 초기화
            if driver_path and os.path.exists(driver_path):
                try:
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    driver = webdriver.Chrome(options=chrome_options)
            else:
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    raise Exception(
                        f"ChromeDriver를 찾을 수 없습니다.\n"
                        f"다음 명령어로 설치하세요:\n"
                        f"Mac: brew install chromedriver\n"
                        f"또는 ChromeDriver 캐시를 삭제하세요: rm -rf ~/.wdm/drivers/chromedriver"
                    )
            
            try:
                # 페이지 로드
                driver.get(url)
                
                # 페이지가 완전히 로드될 때까지 대기
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 추가 대기 (JavaScript 실행 완료, 네이버 블로그는 동적 콘텐츠가 많음)
                time.sleep(5)
                
                # 스크롤 다운 (동적 콘텐츠 로딩을 위해)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                
                # BeautifulSoup으로 파싱
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 불필요한 태그 제거
                unwanted_tags = [
                    'script', 'style', 'nav', 'footer', 'header', 'aside',
                    'noscript', 'iframe', 'embed', 'object', 'form',
                    'button', 'input', 'select', 'textarea', 'label',
                    'meta', 'link', 'svg', 'path'
                ]
                for tag in soup(unwanted_tags):
                    tag.decompose()
                
                # 네이버 블로그 특정 요소 제거
                # 네비게이션, 사이드바, 댓글 영역 등 제거
                for tag in soup.find_all(class_=lambda x: x and any(keyword in str(x).lower() for keyword in [
                    'header', 'footer', 'sidebar', 'navigation', 'menu', 'nav',
                    'comment', 'reply', 'ad', 'banner', 'widget', 'aside',
                    'blog_menu', 'blog_header', 'blog_footer', 'area_comment'
                ])):
                    tag.decompose()
                
                # 네이버 블로그 본문 영역 찾기 (여러 선택자 시도)
                main_content = None
                selectors = [
                    '#postViewArea',  # 네이버 블로그 본문 영역
                    '.se-main-container',  # 스마트에디터 본문
                    '.se-component-content',  # 스마트에디터 컴포넌트
                    '#postView',  # 포스트 뷰
                    '.post-view',  # 포스트 뷰 클래스
                    'main',  # HTML5 main 태그
                    'article',  # HTML5 article 태그
                    '[role="main"]',  # role="main"
                    '.content',  # content 클래스
                    '#content'  # content ID
                ]
                
                for selector in selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                # 메인 콘텐츠가 있으면 그것만 사용
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                else:
                    # 메인 콘텐츠를 찾지 못한 경우, body에서 불필요한 요소 제거 후 추출
                    # 네이버 블로그 특정 클래스/ID 제거
                    for tag in soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in [
                        'header', 'footer', 'nav', 'menu', 'sidebar', 'comment', 'ad'
                    ])):
                        tag.decompose()
                    text = soup.get_text(separator='\n', strip=True)
                
                # 텍스트 정리
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                # 너무 짧은 줄 제거 (1-2자만 있는 줄)
                lines = [line for line in lines if len(line) > 2]
                # 중복된 빈 줄 제거
                cleaned_lines = []
                prev_empty = False
                for line in lines:
                    if line:
                        cleaned_lines.append(line)
                        prev_empty = False
                    elif not prev_empty:
                        cleaned_lines.append('')
                        prev_empty = True
                
                cleaned_text = '\n'.join(cleaned_lines)
                
                # 길이 제한
                if len(cleaned_text) > max_length:
                    cleaned_text = cleaned_text[:max_length] + "... (내용이 너무 길어 일부만 추출했습니다)"
                
                return cleaned_text
                
            finally:
                driver.quit()
        
        except Exception as e:
            raise Exception(f"네이버 블로그 크롤링 중 오류: {str(e)}")
    
    def _crawl_tistory(self, url: str, max_length: int = 50000) -> str:
        """
        티스토리 블로그 크롤링 (Selenium 사용)
        
        Args:
            url: 티스토리 블로그 URL
            max_length: 최대 텍스트 길이
            
        Returns:
            크롤링된 텍스트 내용
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError:
            raise Exception("티스토리 크롤링을 위해 Selenium이 필요합니다. pip install selenium webdriver-manager")
        
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--ignore-certificate-errors')  # SSL 인증서 검증 비활성화
            chrome_options.add_argument('--ignore-ssl-errors')  # SSL 오류 무시
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option('acceptInsecureCerts', True)  # 안전하지 않은 인증서 허용
            
            # ChromeDriver 설정 (네이버 블로그와 동일한 로직)
            import os
            import subprocess
            
            driver_path = None
            
            # 방법 1: 시스템에 설치된 chromedriver 찾기
            try:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    driver_path = result.stdout.strip()
            except:
                pass
            
            # 방법 2: ChromeDriverManager 사용
            if not driver_path:
                try:
                    manager_path = ChromeDriverManager().install()
                    driver_dir = os.path.dirname(manager_path)
                    
                    # chromedriver 실행 파일 찾기
                    for root, dirs, files in os.walk(driver_dir):
                        for file in files:
                            if file == 'chromedriver' or (file.startswith('chromedriver') and not any(file.endswith(ext) for ext in ['.txt', '.md', '.zip', '.tar.gz'])):
                                candidate_path = os.path.join(root, file)
                                if os.path.isfile(candidate_path) and os.access(candidate_path, os.X_OK):
                                    try:
                                        result = subprocess.run(['file', candidate_path], capture_output=True, text=True)
                                        if 'executable' in result.stdout.lower() or 'binary' in result.stdout.lower():
                                            driver_path = candidate_path
                                            break
                                    except:
                                        driver_path = candidate_path
                                        break
                        if driver_path:
                            break
                except Exception as e:
                    pass
            
            # ChromeDriver 초기화
            if driver_path and os.path.exists(driver_path):
                try:
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception:
                    driver = webdriver.Chrome(options=chrome_options)
            else:
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e:
                    raise Exception(
                        f"ChromeDriver를 찾을 수 없습니다.\n"
                        f"다음 명령어로 설치하세요:\n"
                        f"Mac: brew install chromedriver\n"
                        f"또는 ChromeDriver 캐시를 삭제하세요: rm -rf ~/.wdm/drivers/chromedriver"
                    )
            
            try:
                # 페이지 로드
                driver.get(url)
                
                # 페이지가 완전히 로드될 때까지 대기
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 추가 대기 (JavaScript 실행 완료, 티스토리는 동적 콘텐츠가 많음)
                time.sleep(5)
                
                # 스크롤 다운 (동적 콘텐츠 로딩을 위해)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 페이지 소스 가져오기
                page_source = driver.page_source
                
                # BeautifulSoup으로 파싱
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # 불필요한 태그 제거
                unwanted_tags = [
                    'script', 'style', 'nav', 'footer', 'header', 'aside',
                    'noscript', 'iframe', 'embed', 'object', 'form',
                    'button', 'input', 'select', 'textarea', 'label',
                    'meta', 'link', 'svg', 'path'
                ]
                for tag in soup(unwanted_tags):
                    tag.decompose()
                
                # 티스토리 특정 요소 제거
                # 네비게이션, 사이드바, 댓글 영역 등 제거
                for tag in soup.find_all(class_=lambda x: x and any(keyword in str(x).lower() for keyword in [
                    'header', 'footer', 'sidebar', 'navigation', 'menu', 'nav',
                    'comment', 'reply', 'ad', 'banner', 'widget', 'aside',
                    'tistory', 'plugin', 'recent', 'category', 'tag'
                ])):
                    tag.decompose()
                
                # 티스토리 본문 영역 찾기 (여러 선택자 시도)
                main_content = None
                selectors = [
                    '#content',  # 티스토리 본문 영역
                    '.article',  # article 클래스
                    '.entry-content',  # entry-content 클래스
                    '.post-content',  # post-content 클래스
                    '.post-view',  # post-view 클래스
                    'article',  # HTML5 article 태그
                    'main',  # HTML5 main 태그
                    '[role="main"]',  # role="main"
                    '.content',  # content 클래스
                    '#post-view',  # post-view ID
                    '.tt_article_useless_p_margin'  # 티스토리 본문 영역
                ]
                
                for selector in selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                # 메인 콘텐츠가 있으면 그것만 사용
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                else:
                    # 메인 콘텐츠를 찾지 못한 경우, body에서 불필요한 요소 제거 후 추출
                    # 티스토리 특정 클래스/ID 제거
                    for tag in soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in str(x).lower() for keyword in [
                        'header', 'footer', 'nav', 'menu', 'sidebar', 'comment', 'ad', 'tistory'
                    ])):
                        tag.decompose()
                    text = soup.get_text(separator='\n', strip=True)
                
                # 텍스트 정리
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                # 너무 짧은 줄 제거 (1-2자만 있는 줄)
                lines = [line for line in lines if len(line) > 2]
                # 중복된 빈 줄 제거
                cleaned_lines = []
                prev_empty = False
                for line in lines:
                    if line:
                        cleaned_lines.append(line)
                        prev_empty = False
                    elif not prev_empty:
                        cleaned_lines.append('')
                        prev_empty = True
                
                cleaned_text = '\n'.join(cleaned_lines)
                
                # 길이 제한
                if len(cleaned_text) > max_length:
                    cleaned_text = cleaned_text[:max_length] + "... (내용이 너무 길어 일부만 추출했습니다)"
                
                return cleaned_text
                
            finally:
                driver.quit()
        
        except Exception as e:
            raise Exception(f"티스토리 크롤링 중 오류: {str(e)}")

