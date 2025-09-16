"""
LLM Integration Service for College Recommendations
"""
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from ..models.college import (
    CollegeRecommendation, 
    RecommendationScore, 
    StudentProfile,
    College
)


class CollegeRecommendationLLM:
    """LLM service for generating college recommendations"""
    
    def __init__(self, 
                 model_name: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None,
                 temperature: float = 0.3):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = self._initialize_llm(api_key)
        self.parser = PydanticOutputParser(pydantic_object=CollegeRecommendation)
        
    def _initialize_llm(self, api_key: Optional[str]) -> BaseLanguageModel:
        """Initialize the language model"""
        if "gpt" in self.model_name.lower():
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=api_key
            )
        elif "claude" in self.model_name.lower():
            return ChatAnthropic(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=api_key
            )
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
    
    def create_recommendation_prompt(self) -> PromptTemplate:
        """Create the main recommendation prompt template"""
        
        template = """
        You are an expert college counselor with access to comprehensive data about Indian government colleges. 
        Your task is to provide top-3 college recommendations based on a student's profile and retrieved college information.

        STUDENT PROFILE:
        Age: {age}
        Board: {board}
        Marks: {marks_percentage}%
        Preferred Streams: {preferred_streams}
        Budget Range: ₹{budget_min:,} - ₹{budget_max:,}
        Preferred Language: {preferred_language}
        Max Distance: {max_distance_km} km
        Location: {location}
        Interests: {interests}
        Career Goals: {career_goals}

        RETRIEVED COLLEGE DATA:
        {retrieved_documents}

        INSTRUCTIONS:
        1. Analyze the student profile and match it with the retrieved college information
        2. For each recommended college, provide:
           - Rank (1-3)
           - Composite score breakdown:
             * Official Quality (0-10): Based on accreditation, NIRF ranking, reputation
             * Mentor Trust (0-10): Based on mentor ratings and reviews
             * Relevance (0-10): How well the college matches student's preferences
             * Proximity (0-10): Distance and location convenience
             * Composite Score (0-10): Weighted average of above scores
           - One-sentence rationale explaining why this college is recommended
           - 2-3 evidence citations with source and timestamp
        3. Ensure recommendations are realistic and achievable
        4. Prioritize government colleges as specified
        5. Consider budget constraints and location preferences
        6. Provide source links for transparency

        OUTPUT FORMAT:
        For each recommendation, provide:
        - Rank: [1-3]
        - College Name: [Full name]
        - Official Quality Score: [0-10]
        - Mentor Trust Score: [0-10] 
        - Relevance Score: [0-10]
        - Proximity Score: [0-10]
        - Composite Score: [0-10]
        - Rationale: [One sentence explanation]
        - Evidence Citations: [2-3 citations with source and timestamp]
        - Source Links: [Official links for verification]

        {format_instructions}
        """
        
        return PromptTemplate(
            template=template,
            input_variables=[
                "age", "board", "marks_percentage", "preferred_streams", 
                "budget_min", "budget_max", "preferred_language", 
                "max_distance_km", "location", "interests", "career_goals",
                "retrieved_documents"
            ],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def create_verification_prompt(self) -> PromptTemplate:
        """Create prompt for claim verification"""
        
        template = """
        You are a fact-checker for college information. Verify the following claim against the provided evidence.

        CLAIM TO VERIFY:
        {claim}

        EVIDENCE:
        {evidence}

        INSTRUCTIONS:
        1. Check if the claim is supported by the evidence
        2. Identify any discrepancies or missing information
        3. Rate confidence level (0-1) in the verification
        4. Provide source information and timestamp
        5. Flag any unverifiable claims

        OUTPUT FORMAT:
        - Verified: [True/False]
        - Confidence: [0.0-1.0]
        - Source: [Source name and type]
        - Verification Date: [Current date]
        - Notes: [Any additional observations or flags]
        """
        
        return PromptTemplate(
            template=template,
            input_variables=["claim", "evidence"]
        )
    
    def generate_recommendations(self, 
                               student_profile: StudentProfile,
                               retrieved_documents: List[Dict[str, Any]],
                               preferences: Optional[Dict[str, float]] = None) -> List[CollegeRecommendation]:
        """Generate college recommendations using LLM"""
        
        # Create search query from student profile
        query = self._create_student_query(student_profile)
        
        # Format retrieved documents
        formatted_docs = self._format_retrieved_documents(retrieved_documents)
        
        # Create prompt
        prompt = self.create_recommendation_prompt()
        
        # Format input
        input_data = {
            "age": student_profile.age,
            "board": student_profile.board,
            "marks_percentage": student_profile.marks_percentage,
            "preferred_streams": ", ".join([s.value for s in student_profile.preferred_streams]),
            "budget_min": student_profile.budget_range[0],
            "budget_max": student_profile.budget_range[1],
            "preferred_language": student_profile.preferred_language,
            "max_distance_km": student_profile.max_distance_km,
            "location": student_profile.location or "Not specified",
            "interests": ", ".join(student_profile.interests) or "Not specified",
            "career_goals": ", ".join(student_profile.career_goals) or "Not specified",
            "retrieved_documents": formatted_docs
        }
        
        # Generate response
        formatted_prompt = prompt.format(**input_data)
        response = self.llm.invoke(formatted_prompt)
        
        # Parse response
        try:
            recommendations = self.parser.parse(response.content)
            return recommendations if isinstance(recommendations, list) else [recommendations]
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Fallback: extract recommendations manually
            return self._extract_recommendations_manual(response.content)
    
    def verify_claim(self, claim: str, evidence: str) -> Dict[str, Any]:
        """Verify a specific claim against evidence"""
        
        prompt = self.create_verification_prompt()
        formatted_prompt = prompt.format(claim=claim, evidence=evidence)
        
        response = self.llm.invoke(formatted_prompt)
        
        # Parse verification result
        return self._parse_verification_response(response.content)
    
    def _create_student_query(self, student_profile: StudentProfile) -> str:
        """Create search query from student profile"""
        query_parts = []
        
        if student_profile.preferred_streams:
            streams = [stream.value for stream in student_profile.preferred_streams]
            query_parts.append(f"programs in {', '.join(streams)}")
        
        if student_profile.budget_range:
            min_budget, max_budget = student_profile.budget_range
            query_parts.append(f"fees between {min_budget} and {max_budget}")
        
        if student_profile.location:
            query_parts.append(f"near {student_profile.location}")
        
        if student_profile.marks_percentage:
            query_parts.append(f"cutoff around {student_profile.marks_percentage}%")
        
        return " ".join(query_parts)
    
    def _format_retrieved_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents for LLM input"""
        formatted_docs = []
        
        for i, doc in enumerate(documents, 1):
            formatted_doc = f"""
            Document {i}:
            {doc.get('page_content', '')}
            
            Metadata:
            - College: {doc.get('metadata', {}).get('college_name', 'Unknown')}
            - Location: {doc.get('metadata', {}).get('location', 'Unknown')}
            - Streams: {', '.join(doc.get('metadata', {}).get('streams', []))}
            - Rating: {doc.get('metadata', {}).get('avg_rating', 'N/A')}
            - Placement: {doc.get('metadata', {}).get('placement_percentage', 'N/A')}%
            - Fees: ₹{doc.get('metadata', {}).get('min_fees', 'N/A')} - ₹{doc.get('metadata', {}).get('max_fees', 'N/A')}
            - Source: {doc.get('metadata', {}).get('source', 'Unknown')}
            - Last Updated: {doc.get('metadata', {}).get('last_updated', 'Unknown')}
            """
            formatted_docs.append(formatted_doc)
        
        return "\n".join(formatted_docs)
    
    def _extract_recommendations_manual(self, response_content: str) -> List[CollegeRecommendation]:
        """Manually extract recommendations from LLM response"""
        # This is a fallback method if JSON parsing fails
        # In practice, you'd implement more robust extraction logic
        recommendations = []
        
        # Simple regex-based extraction (this is a basic implementation)
        rank_pattern = r"Rank:\s*(\d+)"
        college_pattern = r"College Name:\s*([^\n]+)"
        
        ranks = re.findall(rank_pattern, response_content)
        colleges = re.findall(college_pattern, response_content)
        
        for i, (rank, college) in enumerate(zip(ranks, colleges)):
            # Create a basic recommendation structure
            # This would need to be enhanced based on actual response format
            recommendation = CollegeRecommendation(
                rank=int(rank),
                college=College(college_id=f"college_{i}", name=college),
                score=RecommendationScore(
                    official_quality=7.0,
                    mentor_trust=7.0,
                    relevance=7.0,
                    proximity=7.0,
                    composite_score=7.0,
                    confidence=0.7
                ),
                rationale="Recommended based on student profile match",
                evidence_citations=["Source verification pending"],
                source_links=["https://example.com"],
                verification_status="pending"
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _parse_verification_response(self, response_content: str) -> Dict[str, Any]:
        """Parse verification response from LLM"""
        # Extract verification details using regex
        verified_match = re.search(r"Verified:\s*(True|False)", response_content)
        confidence_match = re.search(r"Confidence:\s*([\d.]+)", response_content)
        source_match = re.search(r"Source:\s*([^\n]+)", response_content)
        notes_match = re.search(r"Notes:\s*([^\n]+)", response_content)
        
        return {
            "verified": verified_match.group(1) == "True" if verified_match else False,
            "confidence": float(confidence_match.group(1)) if confidence_match else 0.0,
            "source": source_match.group(1) if source_match else "Unknown",
            "verification_date": datetime.now().isoformat(),
            "notes": notes_match.group(1) if notes_match else ""
        }
