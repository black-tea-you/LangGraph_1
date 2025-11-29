# Vertex AI 전환 가이드

## 📋 목차
1. [Vertex AI vs Gemini API 차이](#1-vertex-ai-vs-gemini-api-차이)
2. [인증 방식 비교](#2-인증-방식-비교)
3. [LangGraph에서 Vertex AI 사용 방법](#3-langgraph에서-vertex-ai-사용-방법)
4. [코드 변경 가이드](#4-코드-변경-가이드)
5. [환경 변수 설정](#5-환경-변수-설정)
6. [마이그레이션 체크리스트](#6-마이그레이션-체크리스트)

---

## 1. Vertex AI vs Gemini API 차이

### 🔄 **현재 구조 (Gemini API)**

```python
# 현재 사용 중
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,  # API Key 사용
    temperature=0.7,
)
```

**특징:**
- ✅ Consumer API (무료 티어 제공)
- ✅ API Key로 간단한 인증
- ⚠️ Rate Limit: 15 RPM (무료 티어)
- ⚠️ 프로덕션 환경에 제한적

### 🆕 **Vertex AI 구조**

```python
# Vertex AI로 전환
from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(
    model_name="gemini-2.0-flash-exp",
    project="your-gcp-project-id",
    location="us-central1",
    credentials=credentials,  # Service Account 또는 ADC
    temperature=0.7,
)
```

**특징:**
- ✅ Enterprise급 서비스
- ✅ 높은 Rate Limit (프로젝트별 설정)
- ✅ GCP 통합 (로깅, 모니터링, 비용 관리)
- ⚠️ GCP 프로젝트 필요
- ⚠️ 인증 설정 복잡도 증가

---

## 2. 인증 방식 비교

### 🔑 **방식 1: API Key (제한적 지원)**

**가능 여부:** ⚠️ **부분적으로 가능하지만 권장하지 않음**

**이유:**
- Vertex AI는 주로 Service Account 기반 인증 설계
- API Key는 일부 기능만 지원
- 프로덕션 환경에서 보안상 권장하지 않음

**사용 가능한 경우:**
- 개발/테스트 환경
- 제한된 기능만 사용하는 경우

### 🔐 **방식 2: Service Account (권장)**

**가능 여부:** ✅ **완전 지원, 프로덕션 권장**

**장점:**
- 모든 Vertex AI 기능 사용 가능
- 세밀한 권한 제어
- GCP 통합 (로깅, 모니터링)
- 보안성 높음

**단점:**
- GCP 프로젝트 설정 필요
- 서비스 계정 키 파일 관리 필요

### 🔄 **방식 3: Application Default Credentials (ADC)**

**가능 여부:** ✅ **로컬 개발 권장**

**장점:**
- 로컬 개발 환경에서 간편
- `gcloud auth application-default login` 한 번만 실행
- 키 파일 관리 불필요

**단점:**
- 프로덕션 환경에서는 Service Account 권장

---

## 3. LangGraph에서 Vertex AI 사용 방법

### 📦 **필요 패키지 설치**

```bash
# 기존 패키지 제거 (선택)
pip uninstall langchain-google-genai

# Vertex AI 패키지 설치
pip install langchain-google-vertexai
```

### 🔧 **기본 사용법**

#### **방법 A: Service Account (권장)**

```python
from langchain_google_vertexai import ChatVertexAI
from google.oauth2 import service_account
import os

# Service Account 키 파일 경로
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Credentials 로드
credentials = service_account.Credentials.from_service_account_file(
    credentials_path
)

# Vertex AI LLM 생성
llm = ChatVertexAI(
    model_name="gemini-2.0-flash-exp",  # 또는 "gemini-1.5-pro"
    project="your-gcp-project-id",
    location="us-central1",  # 또는 "asia-northeast3" (서울)
    credentials=credentials,
    temperature=0.7,
    max_tokens=4096,
)
```

#### **방법 B: Application Default Credentials (ADC)**

```python
from langchain_google_vertexai import ChatVertexAI

# ADC 사용 (환경 변수 GOOGLE_APPLICATION_CREDENTIALS 설정 또는 gcloud auth)
llm = ChatVertexAI(
    model_name="gemini-2.0-flash-exp",
    project="your-gcp-project-id",
    location="us-central1",
    # credentials 생략 시 ADC 자동 사용
    temperature=0.7,
    max_tokens=4096,
)
```

#### **방법 C: API Key (제한적, 비권장)**

```python
from langchain_google_vertexai import ChatVertexAI
from google.auth import credentials

# ⚠️ API Key는 Vertex AI에서 직접 지원하지 않음
# 대신 Gemini API를 계속 사용하거나 Service Account로 전환 권장

# 만약 API Key를 사용해야 한다면, Gemini API 유지:
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
)
```

---

## 4. 코드 변경 가이드

### 🔄 **Step 1: Config 설정 추가**

```python
# app/core/config.py
class Settings(BaseSettings):
    # ... 기존 설정 ...
    
    # Vertex AI 설정 (새로 추가)
    GCP_PROJECT_ID: Optional[str] = None
    GCP_LOCATION: str = "us-central1"  # 또는 "asia-northeast3" (서울)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None  # Service Account 키 파일 경로
    
    # 기존 Gemini API 설정 (호환성 유지)
    GEMINI_API_KEY: Optional[str] = None
    
    # LLM Provider 선택
    LLM_PROVIDER: str = "vertex_ai"  # "vertex_ai" | "gemini_api"
    
    # Vertex AI 모델명
    VERTEX_AI_MODEL: str = "gemini-2.0-flash-exp"  # 또는 "gemini-1.5-pro"
```

### 🔄 **Step 2: LLM 유틸리티 함수 수정**

```python
# app/langgraph/nodes/utils.py (새로 생성 또는 기존 파일 수정)
import os
from typing import Optional
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI
from google.oauth2 import service_account

from app.core.config import settings


def get_llm(provider: Optional[str] = None):
    """
    LLM 인스턴스 생성 (Vertex AI 또는 Gemini API)
    
    Args:
        provider: "vertex_ai" | "gemini_api" | None (설정에서 읽음)
    
    Returns:
        ChatVertexAI 또는 ChatGoogleGenerativeAI 인스턴스
    """
    provider = provider or settings.LLM_PROVIDER
    
    if provider == "vertex_ai":
        return _get_vertex_ai_llm()
    else:
        return _get_gemini_api_llm()


def _get_vertex_ai_llm() -> ChatVertexAI:
    """Vertex AI LLM 생성"""
    # Credentials 설정
    credentials = None
    
    # 방법 1: Service Account 키 파일 사용
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        else:
            raise FileNotFoundError(
                f"Service Account 키 파일을 찾을 수 없습니다: {credentials_path}"
            )
    
    # 방법 2: ADC 사용 (GOOGLE_APPLICATION_CREDENTIALS 환경 변수 또는 gcloud auth)
    # credentials가 None이면 ADC 자동 사용
    
    if not settings.GCP_PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID가 설정되지 않았습니다.")
    
    return ChatVertexAI(
        model_name=settings.VERTEX_AI_MODEL,
        project=settings.GCP_PROJECT_ID,
        location=settings.GCP_LOCATION,
        credentials=credentials,  # None이면 ADC 사용
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )


def _get_gemini_api_llm() -> ChatGoogleGenerativeAI:
    """Gemini API LLM 생성 (기존 방식)"""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
    
    return ChatGoogleGenerativeAI(
        model=settings.DEFAULT_LLM_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
```

### 🔄 **Step 3: 기존 get_llm() 함수 교체**

**변경 전:**
```python
# app/langgraph/nodes/writer.py
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_llm():
    return ChatGoogleGenerativeAI(
        model=settings.DEFAULT_LLM_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )
```

**변경 후:**
```python
# app/langgraph/nodes/writer.py
from app.langgraph.nodes.utils import get_llm  # 중앙화된 유틸리티 사용

# get_llm() 함수는 이미 utils.py에 정의되어 있으므로 import만 하면 됨
```

**적용할 파일들:**
- `app/langgraph/nodes/writer.py`
- `app/langgraph/nodes/intent_analyzer.py`
- `app/langgraph/nodes/system_nodes.py`
- `app/langgraph/nodes/turn_evaluator/utils.py`
- `app/langgraph/nodes/holistic_evaluator/utils.py`

### 🔄 **Step 4: 모델명 매핑**

```python
# Vertex AI 모델명 매핑
VERTEX_AI_MODELS = {
    "gemini-2.5-flash": "gemini-2.0-flash-exp",  # 또는 "gemini-1.5-flash"
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-1.5-flash": "gemini-1.5-flash",
}

# 설정에서 모델명 변환
def get_vertex_ai_model_name(gemini_model: str) -> str:
    """Gemini API 모델명을 Vertex AI 모델명으로 변환"""
    return VERTEX_AI_MODELS.get(gemini_model, "gemini-2.0-flash-exp")
```

---

## 5. 환경 변수 설정

### 📝 **.env 파일 예시**

```bash
# LLM Provider 선택
LLM_PROVIDER=vertex_ai  # 또는 "gemini_api"

# Vertex AI 설정 (LLM_PROVIDER=vertex_ai일 때)
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1  # 또는 asia-northeast3 (서울)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Gemini API 설정 (LLM_PROVIDER=gemini_api일 때, 호환성 유지)
GEMINI_API_KEY=your-api-key-here

# 공통 설정
DEFAULT_LLM_MODEL=gemini-2.5-flash
VERTEX_AI_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### 🔐 **Service Account 키 파일 생성**

1. **GCP 콘솔에서 서비스 계정 생성:**
   ```
   GCP Console → IAM & Admin → Service Accounts
   → Create Service Account
   → 이름: "langgraph-vertex-ai"
   → 역할: "Vertex AI User"
   ```

2. **키 파일 다운로드:**
   ```
   Service Account → Keys → Add Key → Create new key
   → JSON 형식 선택 → Download
   ```

3. **키 파일 저장:**
   ```bash
   # 프로젝트 루트에 저장 (gitignore에 추가!)
   mv ~/Downloads/your-project-key.json ./service-account-key.json
   
   # .gitignore에 추가
   echo "service-account-key.json" >> .gitignore
   ```

4. **환경 변수 설정:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="./service-account-key.json"
   ```

### 🔄 **ADC 설정 (로컬 개발용)**

```bash
# gcloud CLI 설치 후
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project your-project-id
```

---

## 6. 마이그레이션 체크리스트

### ✅ **준비 단계**

- [ ] GCP 프로젝트 생성 및 Vertex AI API 활성화
- [ ] Service Account 생성 및 키 파일 다운로드
- [ ] `langchain-google-vertexai` 패키지 설치
- [ ] 환경 변수 설정 (.env 파일)

### ✅ **코드 변경**

- [ ] `app/core/config.py`에 Vertex AI 설정 추가
- [ ] `app/langgraph/nodes/utils.py`에 `get_llm()` 함수 중앙화
- [ ] 모든 `get_llm()` 호출을 중앙화된 함수로 변경
- [ ] 모델명 매핑 로직 추가 (필요 시)

### ✅ **테스트**

- [ ] 단일 노드 테스트 (Intent Analyzer)
- [ ] Writer LLM 테스트
- [ ] 평가 노드 테스트
- [ ] 전체 플로우 통합 테스트

### ✅ **배포**

- [ ] 프로덕션 환경에 Service Account 키 파일 배포 (보안 주의!)
- [ ] 환경 변수 설정 확인
- [ ] Rate Limit 모니터링
- [ ] 비용 모니터링 (GCP Console)

---

## 📊 **비교표**

| 항목 | Gemini API | Vertex AI |
|------|-----------|-----------|
| **인증** | API Key | Service Account / ADC |
| **Rate Limit** | 15 RPM (무료) | 프로젝트별 설정 |
| **비용** | 무료 티어 있음 | 사용량 기반 |
| **GCP 통합** | ❌ | ✅ |
| **로깅/모니터링** | 제한적 | 완전 지원 |
| **프로덕션 적합성** | ⚠️ 제한적 | ✅ 권장 |
| **설정 복잡도** | 낮음 | 중간 |

---

## ⚠️ **주의사항**

### 🔴 **API Key로 Vertex AI 사용 불가**

**중요:** Vertex AI는 **API Key 방식으로 직접 인증할 수 없습니다**. 

**대안:**
1. **Service Account 사용 (권장)**
2. **ADC 사용 (로컬 개발)**
3. **Gemini API 유지** (API Key 사용 가능)

### 🔐 **보안 주의사항**

- Service Account 키 파일은 **절대 Git에 커밋하지 마세요**
- `.gitignore`에 키 파일 경로 추가
- 프로덕션 환경에서는 환경 변수 또는 Secret Manager 사용

### 💰 **비용 관리**

- Vertex AI는 사용량 기반 과금
- GCP Console에서 비용 알림 설정 권장
- 무료 할당량 확인 (프로젝트별로 다름)

---

## 🎯 **권장사항**

### **개발 환경:**
- ADC 사용 (`gcloud auth application-default login`)
- 간편한 설정, 키 파일 관리 불필요

### **프로덕션 환경:**
- Service Account 사용
- Secret Manager 또는 환경 변수로 키 관리
- GCP 통합 기능 활용 (로깅, 모니터링)

### **하이브리드 접근:**
- 개발: Gemini API (API Key)
- 프로덕션: Vertex AI (Service Account)
- `LLM_PROVIDER` 환경 변수로 전환

---

**작성일**: 2024-01-01  
**버전**: 1.0  
**참고**: LangChain Vertex AI 통합 문서

