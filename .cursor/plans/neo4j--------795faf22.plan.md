<!-- 795faf22-1393-417c-8091-60eaf1d77f6f 378e462b-4509-4278-9304-0afe97f20c39 -->
# Neo4j Connection Pool 완전 구현

## 개요

Connection Pool을 제대로 구현하여 미리 설정된 개수만큼 DB 연결을 생성하고, 요청/반납 방식으로 관리합니다. 멀티스레드 병렬 작업을 고려한 thread-safe 구현입니다.

## 1. 환경 설정 파일 수정

### `env.example` 수정

```
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_INSTANCE=CSADB
NEO4J_DATABASE=csadb01
NEO4J_USER=csauser
NEO4J_PASSWORD=csauser123
NEO4J_POOL_SIZE=10  # Connection Pool 크기
```

## 2. Connection Pool Manager 구현

### **신규 파일**: `csa/services/neo4j_connection_pool.py`

#### 핵심 기능:

1. **초기화 시 연결 생성**: `NEO4J_POOL_SIZE`만큼 driver 생성하여 Queue에 저장
2. **연결 획득**: `acquire()` - Queue에서 사용 가능한 연결 가져오기 (blocking)
3. **연결 반납**: `release(connection)` - 사용 완료된 연결을 Queue에 반환
4. **컨텍스트 매니저**: `with pool.acquire() as conn:` 패턴 지원
5. **Thread-safe**: `queue.Queue` 사용으로 멀티스레드 안전
6. **Pool 종료**: `close_all()` - 모든 연결 종료
```python
import queue
import threading
from neo4j import GraphDatabase

class ConnectionWrapper:
    """연결과 세션을 래핑하는 클래스"""
    def __init__(self, driver, database):
        self.driver = driver
        self.database = database
    
    def session(self):
        return self.driver.session(database=self.database)

class Neo4jConnectionPool:
    """Neo4j Connection Pool (Singleton)"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._pool = queue.Queue()
        self._all_connections = []
        self._config = {}
        self.logger = get_logger(__name__)
    
    def initialize(self, uri, user, password, database, pool_size=10):
        """Pool 초기화 - 설정된 개수만큼 연결 생성"""
        self._config = {
            'uri': uri,
            'user': user,
            'password': password,
            'database': database,
            'pool_size': pool_size
        }
        
        self.logger.info(f"Initializing connection pool: {pool_size} connections")
        
        for i in range(pool_size):
            driver = GraphDatabase.driver(uri, auth=(user, password))
            conn = ConnectionWrapper(driver, database)
            self._pool.put(conn)
            self._all_connections.append(conn)
            self.logger.debug(f"Created connection {i+1}/{pool_size}")
        
        self.logger.info(f"Connection pool initialized successfully")
    
    def acquire(self, timeout=30):
        """연결 획득 (blocking, timeout 지원)"""
        try:
            conn = self._pool.get(timeout=timeout)
            self.logger.debug(f"Connection acquired. Pool size: {self._pool.qsize()}")
            return conn
        except queue.Empty:
            raise TimeoutError("Could not acquire connection from pool")
    
    def release(self, conn):
        """연결 반납"""
        self._pool.put(conn)
        self.logger.debug(f"Connection released. Pool size: {self._pool.qsize()}")
    
    def get_database(self):
        """데이터베이스 이름 반환"""
        return self._config.get('database', 'neo4j')
    
    def close_all(self):
        """모든 연결 종료"""
        self.logger.info("Closing all connections in pool...")
        for conn in self._all_connections:
            try:
                conn.driver.close()
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
        self._all_connections.clear()
        
        # Queue 비우기
        while not self._pool.empty():
            try:
                self._pool.get_nowait()
            except queue.Empty:
                break
        
        self.logger.info("All connections closed")
```


## 3. GraphDB 클래스 수정

### `csa/services/graph_db.py` 수정

- Pool에서 연결을 획득하여 사용하고 반납하는 방식으로 변경
- 모든 메서드에서 `with pool.acquire() as conn:` 패턴 사용
```python
class GraphDB:
    def __init__(self):
        """Connection Pool 사용"""
        self.pool = Neo4jConnectionPool()
        self.database = self.pool.get_database()
        self.logger = get_logger(__name__)
    
    def add_project(self, project: Project):
        """Pool에서 연결 획득하여 작업 수행"""
        conn = self.pool.acquire()
        try:
            with conn.session() as session:
                session.execute_write(self._create_project_node_tx, project)
        finally:
            self.pool.release(conn)
    
    # 모든 메서드를 acquire/release 패턴으로 변경 (약 25개 메서드)
```


## 4. CLI 수정

### `csa/cli/main.py` 수정

#### 4.1 애플리케이션 시작 시 Pool 초기화

```python
@cli.command()
def analyze(...):
    # Pool 초기화 (최초 1회)
    pool = Neo4jConnectionPool()
    if not hasattr(pool, '_initialized') or not pool._initialized:
        pool_size = int(os.getenv('NEO4J_POOL_SIZE', 10))
        pool.initialize(neo4j_uri, neo4j_user, neo4j_password, neo4j_database, pool_size)
    
    try:
        db = GraphDB()  # Pool 사용
        # ... 작업 수행
    finally:
        # 개별 close 불필요 - Pool이 관리
        pass
```

#### 4.2 모든 명령어에 `--neo4j-database` 옵션 추가

- 기본값: `os.getenv("NEO4J_DATABASE", "neo4j")`

#### 4.3 애플리케이션 종료 시 Pool 정리

```python
# main() 또는 cli() 종료 시
try:
    # 작업 수행
finally:
    pool = Neo4jConnectionPool()
    pool.close_all()
```

## 5. 멀티스레드 병렬 처리 지원

### 병렬 처리 시나리오 (향후 구현 대비)

```python
from concurrent.futures import ThreadPoolExecutor

def process_java_file(java_file):
    """각 스레드에서 독립적으로 Pool에서 연결 획득"""
    db = GraphDB()  # Pool에서 자동 획득
    db.add_class(...)  # 작업 수행
    # 자동 반납

# 병렬 실행
with ThreadPoolExecutor(max_workers=pool_size) as executor:
    executor.map(process_java_file, java_files)
```

## 구현 순서

1. `env.example`에 `NEO4J_POOL_SIZE=10` 추가
2. `neo4j_connection_pool.py` 신규 생성 (Connection Pool 구현)
3. `graph_db.py` 수정 (모든 메서드를 acquire/release 패턴으로 변경)
4. `main.py` 수정:

   - Pool 초기화 로직 추가
   - 모든 명령어에 database 옵션 추가
   - 종료 시 cleanup 추가

5. 테스트 코드 실행 및 검증

## 주요 특징

✅ **진정한 Connection Pool**: 미리 연결 생성하여 재사용

✅ **Thread-safe**: `queue.Queue` 사용으로 멀티스레드 안전

✅ **Timeout 지원**: 연결 대기 시 타임아웃 설정 가능

✅ **자동 관리**: Pool이 모든 연결의 생명주기 관리

✅ **확장성**: 멀티스레드 병렬 처리 준비 완료

✅ **리소스 효율**: 연결 재사용으로 성능 향상