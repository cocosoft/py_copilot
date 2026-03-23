import requests
import sys

def check_api():
    try:
        print("Testing backend API...")
        r = requests.get('http://localhost:8009/api/v1/health', timeout=5)
        print(f'Status: {r.status_code}')
        print(f'Response: {r.text[:200]}')
        
        # Test new endpoints
        endpoints = [
            ("POST", "/api/v1/knowledge/documents/1/extract-chunk-entities", "片段级实体识别"),
            ("POST", "/api/v1/knowledge/documents/1/aggregate-entities", "文档级实体聚合"),
            ("POST", "/api/v1/knowledge/knowledge-bases/1/align-entities", "知识库级实体对齐"),
        ]
        
        print("\nTesting new API endpoints:")
        for method, url, desc in endpoints:
            try:
                if method == "POST":
                    r = requests.post(f'http://localhost:8009{url}', timeout=5)
                else:
                    r = requests.get(f'http://localhost:8009{url}', timeout=5)
                
                if r.status_code == 404:
                    print(f"❌ {desc}: 404 Not Found")
                else:
                    print(f"✅ {desc}: {r.status_code}")
            except Exception as e:
                print(f"❌ {desc}: {e}")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = check_api()
    sys.exit(0 if success else 1)
