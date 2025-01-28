from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
import uuid
import os

from mykeys import apiKey
os.environ['OPENAI_API_KEY'] = apiKey

class QdrantManager:
    def __init__(self):
        self.qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.collection_name = "rag_jobs"
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

        try:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        except Exception as e:
            #collection already exists
            print(e)
        self.top_k = 2

    def addVectors(self,documents,metadata):
        embeddings = self.embedding_model.embed_documents(documents)

        points = [
            PointStruct(id=str(uuid.uuid4()), vector=embedding, payload={"company":company,"position":position,"text": doc})
            for (company, position), embedding, doc in zip(metadata, embeddings, documents)
        ]

        self.qdrant_client.upsert(collection_name=self.collection_name, points=points)

    def searchVector(self,query_text):
        query_embedding = self.embedding_model.embed_query(query_text)

        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=self.top_k
        )
        return results



