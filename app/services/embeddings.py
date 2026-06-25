import faiss
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings 



embedding_model = GoogleGenerativeAIEmbeddings(
    model=settings.GEMINI_EMBEDDING_MODEL,
    google_api_key=settings.GEMINI_API_KEY
)