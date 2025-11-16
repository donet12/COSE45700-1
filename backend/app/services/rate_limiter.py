"""
Rate Limiter - 요청 간격 제어
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict
from collections import deque


class RateLimiter:
    """요청 간격 제어 클래스"""
    
    def __init__(self, min_interval: float = 2.0):
        """
        Args:
            min_interval: 최소 요청 간격 (초)
        """
        self.min_interval = min_interval
        self.last_request_time: Dict[str, datetime] = {}
        self.request_times: Dict[str, deque] = {}
    
    async def wait_if_needed(self, key: str = "default"):
        """
        요청 간격이 충분하지 않으면 대기
        
        Args:
            key: 요청 키 (세션별로 구분 가능)
        """
        now = datetime.now()
        
        if key not in self.last_request_time:
            self.last_request_time[key] = now
            self.request_times[key] = deque()
            return
        
        last_time = self.last_request_time[key]
        elapsed = (now - last_time).total_seconds()
        
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_request_time[key] = datetime.now()
        
        # 요청 시간 기록 (최근 10개만 유지)
        if key not in self.request_times:
            self.request_times[key] = deque(maxlen=10)
        self.request_times[key].append(datetime.now())
    
    def get_stats(self, key: str = "default") -> Dict:
        """요청 통계 반환"""
        if key not in self.request_times or len(self.request_times[key]) < 2:
            return {"total_requests": 0, "avg_interval": 0}
        
        times = list(self.request_times[key])
        intervals = [
            (times[i] - times[i-1]).total_seconds()
            for i in range(1, len(times))
        ]
        
        return {
            "total_requests": len(times),
            "avg_interval": sum(intervals) / len(intervals) if intervals else 0,
            "min_interval": min(intervals) if intervals else 0
        }


# 전역 Rate Limiter 인스턴스
rate_limiter = RateLimiter(min_interval=4.0)  # 최소 4초 간격 (Throttling 방지)

