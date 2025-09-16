"""
Data models for college recommendation system
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StreamType(str, Enum):
    """Academic stream types"""
    ENGINEERING = "engineering"
    MEDICAL = "medical"
    COMMERCE = "commerce"
    ARTS = "arts"
    SCIENCE = "science"
    MANAGEMENT = "management"
    LAW = "law"
    AGRICULTURE = "agriculture"


class CollegeType(str, Enum):
    """College types"""
    GOVERNMENT = "government"
    PRIVATE = "private"
    DEEMED = "deemed"
    AUTONOMOUS = "autonomous"


class StudentProfile(BaseModel):
    """Student profile for recommendations"""
    age: int = Field(..., ge=16, le=30, description="Student age")
    board: str = Field(..., description="Education board (CBSE, ICSE, State, etc.)")
    marks_percentage: float = Field(..., ge=0, le=100, description="Marks percentage")
    preferred_streams: List[StreamType] = Field(..., description="Preferred academic streams")
    budget_range: tuple[int, int] = Field(..., description="Budget range (min, max) in INR")
    preferred_language: str = Field(default="English", description="Preferred language of instruction")
    max_distance_km: int = Field(default=100, description="Maximum distance from home in km")
    location: Optional[str] = Field(None, description="Student's location/address")
    interests: List[str] = Field(default_factory=list, description="Student interests")
    career_goals: List[str] = Field(default_factory=list, description="Career goals")


class CollegeProgram(BaseModel):
    """College program information"""
    program_name: str
    stream: StreamType
    duration_years: int
    fees_annual: int
    seats_total: int
    seats_general: int
    seats_reserved: int
    eligibility_criteria: str
    entrance_exam: Optional[str] = None
    cutoff_percentage: Optional[float] = None


class PlacementStats(BaseModel):
    """Placement statistics"""
    year: int
    total_students: int
    placed_students: int
    placement_percentage: float
    average_salary: float
    highest_salary: float
    top_recruiters: List[str]
    job_roles: List[str]


class MentorRating(BaseModel):
    """Mentor rating and feedback"""
    mentor_id: str
    mentor_name: str
    rating: float = Field(..., ge=1, le=5)
    review_text: str
    review_date: datetime
    verified: bool = False
    categories: List[str] = Field(default_factory=list)  # e.g., ["faculty", "infrastructure", "placement"]


class College(BaseModel):
    """Complete college information"""
    college_id: str
    name: str
    college_type: CollegeType
    location: str
    district: str
    state: str
    established_year: int
    accreditation: List[str] = Field(default_factory=list)
    programs: List[CollegeProgram]
    placement_stats: List[PlacementStats]
    mentor_ratings: List[MentorRating]
    infrastructure: Dict[str, Any] = Field(default_factory=dict)
    faculty_info: Dict[str, Any] = Field(default_factory=dict)
    official_website: Optional[str] = None
    contact_info: Dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    source_links: List[str] = Field(default_factory=list)


class RecommendationScore(BaseModel):
    """Breakdown of recommendation scoring"""
    official_quality: float = Field(..., ge=0, le=10)
    mentor_trust: float = Field(..., ge=0, le=10)
    relevance: float = Field(..., ge=0, le=10)
    proximity: float = Field(..., ge=0, le=10)
    composite_score: float = Field(..., ge=0, le=10)
    confidence: float = Field(..., ge=0, le=1)


class CollegeRecommendation(BaseModel):
    """Final college recommendation"""
    rank: int
    college: College
    score: RecommendationScore
    rationale: str
    evidence_citations: List[str]
    source_links: List[str]
    verification_status: str = "pending"  # pending, verified, flagged


class RecommendationRequest(BaseModel):
    """Request for college recommendations"""
    student_profile: StudentProfile
    preferences: Dict[str, float] = Field(default_factory=dict)  # Weight adjustments
    max_recommendations: int = Field(default=3, ge=1, le=10)
    include_verification: bool = True


class VerificationResult(BaseModel):
    """Result of claim verification"""
    claim: str
    verified: bool
    confidence: float
    source: str
    verification_date: datetime
    notes: Optional[str] = None
