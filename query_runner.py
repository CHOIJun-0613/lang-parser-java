import os  
from dotenv import load_dotenv  
from neo4j import GraphDatabase  
import json  
  
load_dotenv()  
  
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")  
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")  
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "devpass01") 
