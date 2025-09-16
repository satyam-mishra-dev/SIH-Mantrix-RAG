"""
Tests for services
"""
import pytest
import json
from unittest.mock import Mock, patch
from src.services.rag_pipeline import CollegeRAGPipeline
from src.services.verification_service import CollegeVerificationService
from src.models.college import StudentProfile, StreamType, College


class TestCollegeRAGPipeline:
    """Test RAG pipeline functionality"""
    
    def test_initialization(self):
        """Test pipeline initialization"""
        pipeline = CollegeRAGPipeline()
        assert pipeline.embedding_model is not None
        assert pipeline.persist_directory == "./data/chroma_db"
    
    def test_create_student_query(self):
        """Test student query creation"""
        from src.services.rag_pipeline import create_student_query
        
        student = StudentProfile(
            age=18,
            board="CBSE",
            marks_percentage=85.5,
            preferred_streams=[StreamType.ENGINEERING, StreamType.SCIENCE],
            budget_range=(100000, 300000),
            location="Delhi",
            interests=["Technology", "Programming"],
            career_goals=["Software Engineer"]
        )
        
        query = create_student_query(student)
        
        assert "engineering" in query.lower()
        assert "science" in query.lower()
        assert "100000" in query
        assert "300000" in query
        assert "delhi" in query.lower()
        assert "technology" in query.lower()
    
    @patch('src.services.rag_pipeline.Chroma')
    def test_create_vectorstore(self, mock_chroma):
        """Test vector store creation"""
        pipeline = CollegeRAGPipeline()
        
        # Mock documents
        mock_docs = [Mock(page_content="test content", metadata={"test": "data"})]
        
        # Mock Chroma.from_documents
        mock_chroma.from_documents.return_value = Mock()
        
        result = pipeline.create_vectorstore(mock_docs)
        
        mock_chroma.from_documents.assert_called_once()
        assert result is not None


class TestCollegeVerificationService:
    """Test verification service functionality"""
    
    def test_initialization(self):
        """Test verification service initialization"""
        service = CollegeVerificationService()
        assert service.government_sources is not None
        assert "nirf" in service.government_sources
        assert "ugc" in service.government_sources
        assert "aicte" in service.government_sources
    
    def test_verify_college_claim(self):
        """Test college claim verification"""
        service = CollegeVerificationService()
        
        # Test with a simple claim
        result = service.verify_college_claim(
            claim="Placement percentage: 95%",
            college_name="IIT Delhi",
            claim_type="placement"
        )
        
        assert result.claim == "Placement percentage: 95%"
        assert isinstance(result.verified, bool)
        assert 0.0 <= result.confidence <= 1.0
        assert result.source is not None
        assert result.verification_date is not None
    
    def test_cache_functionality(self):
        """Test verification caching"""
        service = CollegeVerificationService()
        
        # First verification
        result1 = service.verify_college_claim(
            claim="Test claim",
            college_name="Test College",
            claim_type="general"
        )
        
        # Second verification (should use cache)
        result2 = service.verify_college_claim(
            claim="Test claim",
            college_name="Test College",
            claim_type="general"
        )
        
        # Should be the same result (cached)
        assert result1.claim == result2.claim
        assert result1.verified == result2.verified
        assert result1.confidence == result2.confidence


class TestDataProcessing:
    """Test data processing functionality"""
    
    def test_college_data_loading(self):
        """Test loading college data from JSON"""
        # Create sample college data
        sample_data = [
            {
                "college_id": "test_college",
                "name": "Test College",
                "college_type": "government",
                "location": "Test City",
                "district": "Test District",
                "state": "Test State",
                "established_year": 2000,
                "accreditation": ["NAAC A"],
                "programs": [
                    {
                        "program_name": "Test Program",
                        "stream": "engineering",
                        "duration_years": 4,
                        "fees_annual": 100000,
                        "seats_total": 100,
                        "seats_general": 50,
                        "seats_reserved": 50,
                        "eligibility_criteria": "Test criteria"
                    }
                ],
                "placement_stats": [
                    {
                        "year": 2023,
                        "total_students": 100,
                        "placed_students": 95,
                        "placement_percentage": 95.0,
                        "average_salary": 500000,
                        "highest_salary": 1000000,
                        "top_recruiters": ["Company A"],
                        "job_roles": ["Engineer"]
                    }
                ],
                "mentor_ratings": [
                    {
                        "mentor_id": "mentor_001",
                        "mentor_name": "Test Mentor",
                        "rating": 4.5,
                        "review_text": "Good college",
                        "review_date": "2024-01-01T00:00:00Z",
                        "verified": True
                    }
                ]
            }
        ]
        
        # Test loading
        pipeline = CollegeRAGPipeline()
        colleges = pipeline.load_college_data_from_json(sample_data)
        
        assert len(colleges) == 1
        assert colleges[0].college_id == "test_college"
        assert colleges[0].name == "Test College"
        assert len(colleges[0].programs) == 1
        assert len(colleges[0].placement_stats) == 1
        assert len(colleges[0].mentor_ratings) == 1
