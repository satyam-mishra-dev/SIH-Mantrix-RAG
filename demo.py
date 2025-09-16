"""
Demo script for College Recommendation System
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def run_demo():
    """Run a simple demo of the system"""
    print("🎓 College Recommendation System - Demo")
    print("=" * 50)
    
    try:
        # Test imports
        print("Testing imports...")
        from src.models.college import StudentProfile, StreamType, RecommendationRequest
        from src.services.rag_pipeline import CollegeRAGPipeline
        from src.services.verification_service import CollegeVerificationService
        print("✅ All imports successful")
        
        # Test data models
        print("\nTesting data models...")
        student = StudentProfile(
            age=18,
            board="CBSE",
            marks_percentage=85.5,
            preferred_streams=[StreamType.ENGINEERING],
            budget_range=(100000, 300000),
            location="Delhi"
        )
        print(f"✅ Student profile created: {student.board}, {student.marks_percentage}%")
        
        # Test RAG pipeline initialization
        print("\nTesting RAG pipeline...")
        pipeline = CollegeRAGPipeline()
        print("✅ RAG pipeline initialized")
        
        # Test verification service
        print("\nTesting verification service...")
        verification_service = CollegeVerificationService()
        print("✅ Verification service initialized")
        
        # Test college data loading
        print("\nTesting college data loading...")
        colleges = pipeline.load_college_data("./data/colleges_sample.json")
        print(f"✅ Loaded {len(colleges)} colleges")
        
        # Test document creation
        print("\nTesting document creation...")
        documents = pipeline.create_college_documents(colleges)
        print(f"✅ Created {len(documents)} documents")
        
        # Test verification
        print("\nTesting verification...")
        result = verification_service.verify_college_claim(
            claim="Placement percentage: 98.3%",
            college_name="Indian Institute of Technology Delhi",
            claim_type="placement"
        )
        print(f"✅ Verification result: {result.verified} (confidence: {result.confidence:.2f})")
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo run the full system:")
        print("  python main.py streamlit  # Web interface")
        print("  python main.py evaluate   # Evaluation framework")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1)
