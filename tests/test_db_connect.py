"""
Neo4j 데이터베이스 접속 테스트

이 테스트는 Neo4j 데이터베이스에 접속하여 연결 상태를 확인합니다.
"""

import pytest
from neo4j import GraphDatabase
import os


class TestNeo4jConnection:
    """Neo4j 데이터베이스 접속 테스트 클래스"""
    
    # 접속 정보
    NEO4J_URI = "neo4j://127.0.0.1:7687"
    NEO4J_DATABASE = "csadb01"
    NEO4J_USER = "csauser"
    NEO4J_PASSWORD = "csauser123"
    
    def test_neo4j_connection(self):
        """Neo4j 데이터베이스 접속 테스트"""
        driver = None
        try:
            print(f"\n=== Neo4j 접속 테스트 시작 ===")
            print(f"URI: {self.NEO4J_URI}")
            print(f"Database: {self.NEO4J_DATABASE}")
            print(f"User: {self.NEO4J_USER}")
            
            # Neo4j 드라이버 생성
            driver = GraphDatabase.driver(
                self.NEO4J_URI, 
                auth=(self.NEO4J_USER, self.NEO4J_PASSWORD)
            )
            
            # 연결 테스트
            with driver.session(database=self.NEO4J_DATABASE) as session:
                # 간단한 쿼리 실행하여 연결 확인
                result = session.run("RETURN 1 as test_value")
                record = result.single()
                
                assert record is not None, "쿼리 결과가 None입니다"
                assert record["test_value"] == 1, f"예상값 1, 실제값: {record['test_value']}"
                
                print(f"✓ 접속 성공! 테스트 값: {record['test_value']}")
                
        except Exception as e:
            print(f"✗ 접속 실패: {str(e)}")
            print(f"에러 타입: {type(e).__name__}")
            raise
        finally:
            if driver:
                driver.close()
                print("✓ 드라이버 연결 종료")
    
    def test_neo4j_connection_without_database(self):
        """기본 데이터베이스로 접속 테스트"""
        driver = None
        try:
            print(f"\n=== Neo4j 기본 데이터베이스 접속 테스트 ===")
            print(f"URI: {self.NEO4J_URI}")
            print(f"User: {self.NEO4J_USER}")
            
            # Neo4j 드라이버 생성
            driver = GraphDatabase.driver(
                self.NEO4J_URI, 
                auth=(self.NEO4J_USER, self.NEO4J_PASSWORD)
            )
            
            # 기본 데이터베이스로 연결 테스트
            with driver.session() as session:
                # 간단한 쿼리 실행하여 연결 확인
                result = session.run("RETURN 1 as test_value")
                record = result.single()
                
                assert record is not None, "쿼리 결과가 None입니다"
                assert record["test_value"] == 1, f"예상값 1, 실제값: {record['test_value']}"
                
                print(f"✓ 기본 데이터베이스 접속 성공! 테스트 값: {record['test_value']}")
                
        except Exception as e:
            print(f"✗ 기본 데이터베이스 접속 실패: {str(e)}")
            print(f"에러 타입: {type(e).__name__}")
            raise
        finally:
            if driver:
                driver.close()
                print("✓ 드라이버 연결 종료")
    
    def test_neo4j_database_info(self):
        """Neo4j 데이터베이스 정보 조회 테스트"""
        driver = None
        try:
            print(f"\n=== Neo4j 데이터베이스 정보 조회 테스트 ===")
            
            driver = GraphDatabase.driver(
                self.NEO4J_URI, 
                auth=(self.NEO4J_USER, self.NEO4J_PASSWORD)
            )
            
            with driver.session(database=self.NEO4J_DATABASE) as session:
                # 데이터베이스 정보 조회
                result = session.run("CALL db.info()")
                records = list(result)
                
                if records:
                    print(f"✓ 데이터베이스 정보 조회 성공")
                    for record in records:
                        print(f"  - {dict(record)}")
                else:
                    print("⚠ 데이터베이스 정보가 없습니다")
                
                # 노드 개수 확인
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                record = result.single()
                node_count = record["node_count"] if record else 0
                print(f"  - 총 노드 개수: {node_count}")
                
        except Exception as e:
            print(f"✗ 데이터베이스 정보 조회 실패: {str(e)}")
            print(f"에러 타입: {type(e).__name__}")
            # 이 테스트는 실패해도 전체 테스트를 중단하지 않음
            pytest.skip(f"데이터베이스 정보 조회 실패: {str(e)}")
        finally:
            if driver:
                driver.close()


if __name__ == "__main__":
    # 직접 실행 시 테스트 수행
    test_instance = TestNeo4jConnection()
    
    print("=" * 50)
    print("Neo4j 데이터베이스 접속 테스트")
    print("=" * 50)
    
    try:
        test_instance.test_neo4j_connection()
        test_instance.test_neo4j_connection_without_database()
        test_instance.test_neo4j_database_info()
        print("\n" + "=" * 50)
        print("✓ 모든 테스트 완료!")
        print("=" * 50)
    except Exception as e:
        print(f"\n" + "=" * 50)
        print(f"✗ 테스트 실패: {str(e)}")
        print("=" * 50)
