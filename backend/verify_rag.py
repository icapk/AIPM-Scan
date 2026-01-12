import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import rag_service
from services.question_generator import generate_questions

async def main():
    print("🚀 Starting RAG Verification...")
    
    # 1. Test RAG Retrieval
    print("\n🔍 Testing RAG Retrieval...")
    query = "AI产品经理面试题"
    try:
        chunks = await rag_service.retrieve(query, top_k=2)
        print(f"✅ RAG Retrieval Success. Got {len(chunks)} chunks.")
        for i, chunk in enumerate(chunks):
            content = chunk.get("content_with_weight", "")[:100]
            print(f"   Chunk {i+1}: {content}...")
    except Exception as e:
        print(f"❌ RAG Retrieval Failed: {str(e)}")
        return

    # 2. Test Question Generation (Mock)
    print("\n📝 Testing Question Generation...")
    weights = {"business_decomposition": 1.0} # Only test one dimension
    try:
        questions = await generate_questions(weights, count=1)
        print(f"✅ Question Generation Success. Generated {len(questions)} questions.")
        for q in questions:
            print(f"   Q: {q['text']}")
            print(f"   Context Length: {len(q.get('reference_context', ''))}")
    except Exception as e:
        print(f"❌ Question Generation Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
