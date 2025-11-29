"""
DDD 하이브리드 구조 마이그레이션: Import 경로 수정 스크립트
"""
import re
import os
from pathlib import Path

REPLACEMENTS = [
    # LangGraph
    (r'from app\.langgraph\.', 'from app.domain.langgraph.'),
    (r'import app\.langgraph\.', 'import app.domain.langgraph.'),
    (r'from app\.langgraph import', 'from app.domain.langgraph import'),
    (r'import app\.langgraph', 'import app.domain.langgraph'),
    
    # Services
    (r'from app\.services\.', 'from app.application.services.'),
    (r'import app\.services\.', 'import app.application.services.'),
    (r'from app\.services import', 'from app.application.services import'),
    (r'import app\.services', 'import app.application.services'),
    
    # DB → Infrastructure
    (r'from app\.db\.models\.', 'from app.infrastructure.persistence.models.'),
    (r'from app\.db\.repositories\.', 'from app.infrastructure.repositories.'),
    (r'from app\.db\.session import', 'from app.infrastructure.persistence.session import'),
    (r'from app\.db\.redis_client import', 'from app.infrastructure.cache.redis_client import'),
    (r'from app\.db import', 'from app.infrastructure.persistence import'),
    (r'import app\.db\.', 'import app.infrastructure.'),
    
    # API → Presentation
    (r'from app\.api\.routes\.', 'from app.presentation.api.routes.'),
    (r'from app\.api import', 'from app.presentation.api import'),
    (r'import app\.api\.', 'import app.presentation.api.'),
    
    # Schemas → Presentation
    (r'from app\.schemas\.', 'from app.presentation.schemas.'),
    (r'from app\.schemas import', 'from app.presentation.schemas import'),
    (r'import app\.schemas\.', 'import app.presentation.schemas.'),
    
    # Repository 파일명 (import 경로에서)
    (r'app\.infrastructure\.repositories\.(\w+)_repo', r'app.infrastructure.repositories.\1_repository'),
]

def fix_imports(file_path):
    """파일의 import 경로를 수정"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """모든 Python 파일의 import 경로 수정"""
    app_dir = Path('app')
    fixed_count = 0
    
    for root, dirs, files in os.walk(app_dir):
        # __pycache__ 제외
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if fix_imports(file_path):
                    fixed_count += 1
                    print(f"Fixed: {file_path}")
    
    print(f"\n총 {fixed_count}개 파일 수정 완료")

if __name__ == '__main__':
    main()

