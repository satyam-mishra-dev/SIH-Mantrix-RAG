"""
College Recommendation RAG System - Main Entry Point
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.services.college_recommendation_service import CollegeRecommendationService
from src.models.college import StudentProfile, StreamType, RecommendationRequest
from src.services.evaluation_service import EvaluationService
import config


def main():
    """Main application entry point"""
    print("🎓 College Recommendation RAG System")
    print("=" * 50)
    
    # Check if running in Streamlit mode
    if len(sys.argv) > 1 and sys.argv[1] == "streamlit":
        run_streamlit_app()
    elif len(sys.argv) > 1 and sys.argv[1] == "evaluate":
        run_evaluation()
    else:
        run_demo()


def run_streamlit_app():
    """Run the Streamlit web application"""
    import subprocess
    import sys
    
    app_path = Path(__file__).parent / "src" / "ui" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


def run_evaluation():
    """Run the evaluation framework"""
    print("🔍 Running Evaluation Framework")
    print("-" * 30)
    
    # Initialize evaluation service
    eval_service = EvaluationService()
    
    # Generate test cases
    print("Generating test cases...")
    test_cases = eval_service.generate_test_cases(num_cases=20)
    print(f"✅ Generated {len(test_cases)} test cases")
    
    # Save test cases
    eval_service.save_test_cases()
    print("✅ Test cases saved to ./data/test_cases.json")
    
    # Create mentor annotation UI
    print("Creating mentor annotation UI...")
    ui_html = eval_service.create_mentor_annotation_ui()
    
    ui_path = Path("./data/mentor_annotation_ui.html")
    ui_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ui_path, 'w', encoding='utf-8') as f:
        f.write(ui_html)
    
    print(f"✅ Mentor annotation UI saved to {ui_path}")
    print(f"🌐 Open {ui_path} in your browser to start annotation")


def run_demo():
    """Run a demonstration of the system"""
    print("🚀 Running Demo")
    print("-" * 20)
    
    try:
        # Initialize the service
        print("Initializing College Recommendation Service...")
        service = CollegeRecommendationService(
            llm_model=config.DEFAULT_LLM_MODEL,
            api_key=config.DEMO_API_KEY  # Force demo mode
        )
        print("✅ Service initialized successfully")
        
        # Create a sample student profile
        print("\nCreating sample student profile...")
        student_profile = StudentProfile(
            age=18,
            board="CBSE",
            marks_percentage=85.5,
            preferred_streams=[StreamType.ENGINEERING, StreamType.SCIENCE],
            budget_range=(100000, 300000),
            preferred_language="English",
            max_distance_km=100,
            location="Jammu, Jammu and Kashmir",
            interests=["Technology", "Programming", "Research"],
            career_goals=["Software Engineer", "Data Scientist"]
        )
        
        # Create recommendation request
        request = RecommendationRequest(
            student_profile=student_profile,
            preferences={
                "official_quality": 0.3,
                "mentor_trust": 0.2,
                "relevance": 0.3,
                "proximity": 0.2
            },
            max_recommendations=3,
            include_verification=True
        )
        
        print("✅ Student profile created")
        print(f"   Age: {student_profile.age}")
        print(f"   Board: {student_profile.board}")
        print(f"   Marks: {student_profile.marks_percentage}%")
        print(f"   Streams: {[s.value for s in student_profile.preferred_streams]}")
        print(f"   Budget: ₹{student_profile.budget_range[0]:,} - ₹{student_profile.budget_range[1]:,}")
        
        # Get recommendations
        print("\n🔍 Generating recommendations...")
        recommendations = service.get_recommendations(request)
        
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        # Display recommendations
        print("\n📋 Recommendations:")
        print("=" * 50)
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n#{i} {rec.college.name}")
            print(f"   Type: {rec.college.college_type.value}")
            print(f"   Location: {rec.college.location}, {rec.college.state}")
            print(f"   Composite Score: {rec.score.composite_score:.1f}/10")
            print(f"   Verification: {rec.verification_status}")
            print(f"   Rationale: {rec.rationale}")
            
            if rec.evidence_citations:
                print("   Evidence:")
                for citation in rec.evidence_citations:
                    print(f"     • {citation}")
        
        # Display system stats
        print("\n📊 System Statistics:")
        print("=" * 30)
        stats = service.get_system_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo run the full web interface, use: python main.py streamlit")
        print("To run evaluation, use: python main.py evaluate")
        
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        print("\nMake sure you have:")
        print("1. Installed all dependencies: pip install -r requirements.txt")
        print("2. Set up your API keys in environment variables")
        print("3. The college data file exists at ./data/colleges_sample.json")


if __name__ == "__main__":
    main()
