"""
Tests for data models
"""
import pytest
from datetime import datetime
from src.models.college import (
    StudentProfile, 
    StreamType, 
    College, 
    CollegeProgram,
    PlacementStats,
    MentorRating,
    RecommendationScore,
    CollegeRecommendation
)


class TestStudentProfile:
    """Test StudentProfile model"""
    
    def test_valid_student_profile(self):
        """Test creating a valid student profile"""
        profile = StudentProfile(
            age=18,
            board="CBSE",
            marks_percentage=85.5,
            preferred_streams=[StreamType.ENGINEERING],
            budget_range=(100000, 300000),
            location="Delhi"
        )
        
        assert profile.age == 18
        assert profile.board == "CBSE"
        assert profile.marks_percentage == 85.5
        assert profile.preferred_streams == [StreamType.ENGINEERING]
        assert profile.budget_range == (100000, 300000)
        assert profile.location == "Delhi"
    
    def test_age_validation(self):
        """Test age validation"""
        with pytest.raises(ValueError):
            StudentProfile(
                age=15,  # Too young
                board="CBSE",
                marks_percentage=85.5,
                preferred_streams=[StreamType.ENGINEERING],
                budget_range=(100000, 300000)
            )
        
        with pytest.raises(ValueError):
            StudentProfile(
                age=31,  # Too old
                board="CBSE",
                marks_percentage=85.5,
                preferred_streams=[StreamType.ENGINEERING],
                budget_range=(100000, 300000)
            )
    
    def test_marks_validation(self):
        """Test marks percentage validation"""
        with pytest.raises(ValueError):
            StudentProfile(
                age=18,
                board="CBSE",
                marks_percentage=105.0,  # Too high
                preferred_streams=[StreamType.ENGINEERING],
                budget_range=(100000, 300000)
            )
        
        with pytest.raises(ValueError):
            StudentProfile(
                age=18,
                board="CBSE",
                marks_percentage=-5.0,  # Too low
                preferred_streams=[StreamType.ENGINEERING],
                budget_range=(100000, 300000)
            )


class TestCollege:
    """Test College model"""
    
    def test_valid_college(self):
        """Test creating a valid college"""
        program = CollegeProgram(
            program_name="Computer Science",
            stream=StreamType.ENGINEERING,
            duration_years=4,
            fees_annual=250000,
            seats_total=120,
            seats_general=60,
            seats_reserved=60,
            eligibility_criteria="JEE Advanced qualified"
        )
        
        placement = PlacementStats(
            year=2023,
            total_students=1200,
            placed_students=1180,
            placement_percentage=98.3,
            average_salary=1800000,
            highest_salary=4500000,
            top_recruiters=["Google", "Microsoft"],
            job_roles=["Software Engineer", "Data Scientist"]
        )
        
        rating = MentorRating(
            mentor_id="mentor_001",
            mentor_name="Dr. Rajesh Kumar",
            rating=4.8,
            review_text="Excellent faculty",
            review_date=datetime.now(),
            verified=True
        )
        
        college = College(
            college_id="iit_delhi",
            name="IIT Delhi",
            college_type="government",
            location="New Delhi",
            district="New Delhi",
            state="Delhi",
            established_year=1961,
            programs=[program],
            placement_stats=[placement],
            mentor_ratings=[rating]
        )
        
        assert college.college_id == "iit_delhi"
        assert college.name == "IIT Delhi"
        assert len(college.programs) == 1
        assert len(college.placement_stats) == 1
        assert len(college.mentor_ratings) == 1


class TestRecommendationScore:
    """Test RecommendationScore model"""
    
    def test_valid_score(self):
        """Test creating a valid recommendation score"""
        score = RecommendationScore(
            official_quality=8.5,
            mentor_trust=7.2,
            relevance=9.0,
            proximity=6.8,
            composite_score=7.9,
            confidence=0.85
        )
        
        assert score.official_quality == 8.5
        assert score.mentor_trust == 7.2
        assert score.relevance == 9.0
        assert score.proximity == 6.8
        assert score.composite_score == 7.9
        assert score.confidence == 0.85
    
    def test_score_validation(self):
        """Test score validation"""
        with pytest.raises(ValueError):
            RecommendationScore(
                official_quality=11.0,  # Too high
                mentor_trust=7.2,
                relevance=9.0,
                proximity=6.8,
                composite_score=7.9,
                confidence=0.85
            )
        
        with pytest.raises(ValueError):
            RecommendationScore(
                official_quality=8.5,
                mentor_trust=7.2,
                relevance=9.0,
                proximity=6.8,
                composite_score=7.9,
                confidence=1.5  # Too high
            )
