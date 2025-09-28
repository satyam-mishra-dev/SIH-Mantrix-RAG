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

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.college import (
    CollegeRecommendation, 
    RecommendationScore, 
    StudentProfile,
    College,
    CollegeType,
    CollegeProgram,
    PlacementStats,
    MentorRating
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
        print(f"🔧 Initializing LLM with API key: {api_key}")
        # For demo mode, use a mock LLM that returns structured responses
        if not api_key or api_key is None or api_key == "sk-or-v1-demo-key-replace-with-real-key":
            print("🔧 Using MockLLM for demo mode")
            return MockLLM()
        
        if "gpt" in self.model_name.lower():
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"  # OpenRouter endpoint
            )
        elif "claude" in self.model_name.lower():
            return ChatAnthropic(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"  # OpenRouter endpoint
            )
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
    
    def create_recommendation_prompt(self) -> PromptTemplate:
        """Create the main recommendation prompt template"""
        
        template = """
        You are an expert college counselor specializing in Jammu and Kashmir region. 
        You MUST use ONLY the retrieved college data provided below. 
        Do NOT make up or hallucinate any college information.

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

        RETRIEVED COLLEGE DATA (USE ONLY THESE):
        {retrieved_documents}

        CRITICAL INSTRUCTIONS:
        1. PRIORITIZE Jammu and Kashmir colleges - give them higher proximity scores (8-10)
        2. You MUST use ONLY the colleges from the retrieved data above or you might use your own knowledge to predict the colleges in J&K
        3. Do NOT create or invent any college information
        4. Do NOT assume entrance exam scores (JEE, NEET, etc.) unless explicitly provided in retrieved data
        5. Use ONLY the eligibility criteria mentioned in the retrieved data - do not add requirements
        6. If no colleges match the student's criteria, say so clearly
        7. You MUST return EXACTLY 3 recommendations in ranked order (rank 1, 2, 3)
        8. For each college from the retrieved data, provide:
           - Rank (1-3)
           - Use the actual college name from the retrieved data
           - Score breakdown based on the retrieved information:
             * Official Quality (0-10): Based on accreditation and reputation from retrieved data
             * Mentor Trust (0-10): Based on mentor ratings from retrieved data
             * Relevance (0-10): How well the college matches student's preferences
             * Proximity (0-10): Higher score for Jammu/Kashmir colleges, lower for distant ones
             * Composite Score (0-10): Weighted average of above scores
           - One-sentence rationale using actual college information
           - Evidence citations from the retrieved data

        OUTPUT FORMAT (Simple JSON):
        Return a JSON array with EXACTLY 3 recommendations in this exact structure:
        [
          {{
            "rank": 1,
            "college_name": "actual_name_from_retrieved_data",
            "college_id": "actual_id_from_retrieved_data",
            "location": "actual_location_from_retrieved_data",
            "college_type": "government",
            "established_year": 1961,
            "accreditation": ["NAAC A++", "NBA"],
            "programs": [
              {{
                "name": "actual_program_name",
                "stream": "engineering",
                "duration_years": 4,
                "fees_annual": 250000,
                "seats_total": 120,
                "eligibility_criteria": "Use ONLY what's in retrieved data - no assumptions"
              }}
            ],
            "placement_stats": [
              {{
                "year": 2023,
                "placement_percentage": 98.3,
                "average_salary": 1800000,
                "top_recruiters": ["Google", "Microsoft"]
              }}
            ],
            "mentor_ratings": [
              {{
                "mentor_name": "Dr. Rajesh Kumar",
                "rating": 4.8,
                "review_text": "Excellent faculty and infrastructure"
              }}
            ],
            "official_website": "https://www.iitd.ac.in",
            "source_links": ["https://www.nirf.ac.in"]
          }}
        ]

        CRITICAL: Return ONLY valid JSON. No text before or after. Ensure all brackets and quotes are properly closed.
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
        
        # Log the context being sent to LLM
        print("\n" + "="*80)
        print("🔍 DETAILED LOGGING - CONTEXT SENT TO LLM")
        print("="*80)
        print(f"📝 STUDENT PROFILE:")
        print(f"   Age: {student_profile.age}")
        print(f"   Board: {student_profile.board}")
        print(f"   Marks: {student_profile.marks_percentage}%")
        print(f"   Streams: {[s.value for s in student_profile.preferred_streams]}")
        print(f"   Budget: ₹{student_profile.budget_range[0]:,} - ₹{student_profile.budget_range[1]:,}")
        print(f"   Location: {student_profile.location}")
        print(f"   Interests: {student_profile.interests}")
        print(f"   Career Goals: {student_profile.career_goals}")
        
        print(f"\n📚 RETRIEVED DOCUMENTS ({len(retrieved_documents)}):")
        for i, doc in enumerate(retrieved_documents, 1):
            if isinstance(doc, dict):
                print(f"   Document {i}: {doc.get('metadata', {}).get('college_name', 'Unknown')}")
                print(f"   Content: {doc.get('page_content', '')[:200]}...")
                print(f"   Metadata: {doc.get('metadata', {})}")
            else:
                print(f"   Document {i}: {type(doc)} - {str(doc)[:200]}...")
            print()
        
        print(f"\n📝 FORMATTED DOCUMENTS FOR LLM:")
        print(f"Length: {len(formatted_docs)} characters")
        print(f"Preview: {formatted_docs[:500]}...")
        
        print(f"🤖 SENDING TO LLM...")
        print(f"Prompt length: {len(formatted_prompt)} characters")
        print("="*80)
        
        response = self.llm.invoke(formatted_prompt)
        
        # Log the LLM response
        print("\n" + "="*80)
        print("🤖 LLM RESPONSE")
        print("="*80)
        print(f"Response length: {len(response.content)} characters")
        print(f"Raw response:\n{response.content}")
        print("="*80)
        
        # Parse response
        try:
            # Try to parse as JSON first
            import json
            import re
            
            # Clean the response to extract JSON
            response_text = response.content.strip()
            
            # Try to find JSON array in the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
            
            response_json = json.loads(response_text)
            
            # Ensure it's a list
            if isinstance(response_json, dict):
                response_json = [response_json]
            
            # Convert to CollegeRecommendation objects
            recommendations = []
            for i, rec_data in enumerate(response_json):
                try:
                    print(f"Processing recommendation {i+1}: {rec_data.get('college_name', 'Unknown')}")
                    # Create a basic recommendation structure
                    # Imports already done at top of file
                    
                    # Parse simplified college data
                    programs = []
                    for prog_data in rec_data.get('programs', []):
                        mapped_program = {
                            'program_name': prog_data.get('name', 'Unknown Program'),
                            'stream': prog_data.get('stream', 'engineering'),
                            'duration_years': prog_data.get('duration_years', 4),
                            'fees_annual': prog_data.get('fees_annual', 100000),
                            'seats_total': prog_data.get('seats_total', 100),
                            'seats_general': prog_data.get('seats_general', 50),
                            'seats_reserved': prog_data.get('seats_reserved', 50),
                            'eligibility_criteria': prog_data.get('eligibility_criteria', 'Not specified')
                        }
                        programs.append(CollegeProgram(**mapped_program))
                    
                    placement_stats = []
                    for stat_data in rec_data.get('placement_stats', []):
                        mapped_stats = {
                            'year': stat_data.get('year', 2023),
                            'total_students': 100,
                            'placed_students': 90,
                            'placement_percentage': stat_data.get('placement_percentage', 90.0),
                            'average_salary': stat_data.get('average_salary', 500000),
                            'highest_salary': stat_data.get('average_salary', 500000) * 2,
                            'top_recruiters': stat_data.get('top_recruiters', []),
                            'job_roles': ['Software Engineer', 'Data Scientist']
                        }
                        placement_stats.append(PlacementStats(**mapped_stats))
                    
                    mentor_ratings = []
                    for rating_data in rec_data.get('mentor_ratings', []):
                        mapped_rating = {
                            'mentor_id': 'mentor_001',
                            'mentor_name': rating_data.get('mentor_name', 'Unknown Mentor'),
                            'rating': rating_data.get('rating', 4.0),
                            'review_text': rating_data.get('review_text', 'No review provided'),
                            'review_date': '2024-01-01T00:00:00Z',
                            'verified': True,
                            'categories': ['faculty', 'infrastructure']
                        }
                        mentor_ratings.append(MentorRating(**mapped_rating))
                    
                    # Create college object
                    # CollegeType already imported at top of file
                    college = College(
                        college_id=rec_data.get('college_id', 'unknown'),
                        name=rec_data.get('college_name', 'Unknown College'),
                        college_type=CollegeType(rec_data.get('college_type', 'government')),
                        location=rec_data.get('location', 'Unknown'),
                        district=rec_data.get('location', 'Unknown').split(',')[0],
                        state=rec_data.get('location', 'Unknown').split(',')[-1],
                        established_year=rec_data.get('established_year', 2000),
                        accreditation=rec_data.get('accreditation', []),
                        programs=programs,
                        placement_stats=placement_stats,
                        mentor_ratings=mentor_ratings,
                        official_website=rec_data.get('official_website'),
                        source_links=rec_data.get('source_links', [])
                    )
                    
                    # Create simple score
                    score = RecommendationScore(
                        official_quality=8.0,
                        mentor_trust=7.5,
                        relevance=8.5,
                        proximity=7.0,
                        composite_score=7.8,
                        confidence=0.8
                    )
                    
                    # Create meaningful rationale based on student profile and college
                    rationale_parts = []
                    
                    # Check stream match
                    if any(program.stream.value in ['engineering', 'science'] for program in programs):
                        rationale_parts.append(f"offers {[p.stream.value for p in programs][0]} programs")
                    
                    # Check location proximity
                    if 'Jammu' in rec_data.get('location', '') or 'Kashmir' in rec_data.get('location', ''):
                        rationale_parts.append("is located in Jammu & Kashmir region")
                    
                    # Check budget fit
                    if programs:
                        avg_fees = sum(p.fees_annual for p in programs) / len(programs)
                        if avg_fees <= 200000:
                            rationale_parts.append("has affordable fees")
                        elif avg_fees <= 300000:
                            rationale_parts.append("fits your budget range")
                    
                    # Check placement stats
                    if placement_stats:
                        latest_stats = placement_stats[-1]
                        if latest_stats.placement_percentage >= 80:
                            rationale_parts.append("has excellent placement record")
                        elif latest_stats.placement_percentage >= 60:
                            rationale_parts.append("has good placement opportunities")
                    
                    rationale = f"Recommended because {rec_data.get('college_name', 'this college')} " + ", ".join(rationale_parts) + "."
                    
                    # Create recommendation
                    # CollegeRecommendation already imported at top of file
                    recommendation = CollegeRecommendation(
                        rank=rec_data.get('rank', 1),
                        college=college,
                        score=score,
                        rationale=rationale,
                        evidence_citations=rec_data.get('source_links', []),
                        source_links=rec_data.get('source_links', []),
                        verification_status='pending'
                    )
                    
                    recommendations.append(recommendation)
                    print(f"Successfully processed recommendation {i+1}")
                except Exception as e:
                    print(f"Error processing recommendation {i+1}: {e}")
                    print(f"Rec data: {rec_data}")
                    continue
            
            return recommendations
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw LLM response: {response.content[:500]}...")
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


class MockLLM:
    """Mock LLM for demo mode that returns structured recommendations"""
    
    def invoke(self, prompt: str):
        """Return mock response for demo"""
        # Extract student profile info from prompt
        import re
        
        # Parse student preferences from prompt
        marks_match = re.search(r'Marks: ([\d.]+)%', prompt)
        location_match = re.search(r'Location: ([^\n]+)', prompt)
        streams_match = re.search(r'Preferred Streams: ([^\n]+)', prompt)
        budget_match = re.search(r'Budget Range: ₹([\d,]+) - ₹([\d,]+)', prompt)
        
        marks = float(marks_match.group(1)) if marks_match else 85.0
        location = location_match.group(1) if location_match else "Jammu"
        streams = streams_match.group(1) if streams_match else "engineering, science"
        budget_min = int(budget_match.group(1).replace(',', '')) if budget_match else 100000
        budget_max = int(budget_match.group(2).replace(',', '')) if budget_match else 500000
        
        # Create mock response with Top-3 recommendations
        mock_response = f"""
        [
          {{
            "rank": 1,
            "college_name": "National Institute of Technology Srinagar",
            "college_id": "nit_srinagar",
            "location": "Srinagar, Jammu and Kashmir",
            "college_type": "government",
            "established_year": 1960,
            "accreditation": ["NAAC A", "NBA", "AICTE"],
            "programs": [
              {{
                "name": "Bachelor of Technology in Computer Science and Engineering",
                "stream": "engineering",
                "duration_years": 4,
                "fees_annual": 150000,
                "seats_total": 60,
                "eligibility_criteria": "JEE Main qualified, 12th with 75% marks"
              }}
            ],
            "placement_stats": [
              {{
                "year": 2023,
                "placement_percentage": 90.0,
                "average_salary": 800000,
                "top_recruiters": ["TCS", "Infosys", "Wipro", "HCL", "Cognizant"]
              }}
            ],
            "mentor_ratings": [
              {{
                "mentor_name": "Dr. Ahmed Khan",
                "rating": 4.2,
                "review_text": "Good engineering college in Kashmir with decent infrastructure and faculty."
              }}
            ],
            "official_website": "https://www.nitsri.ac.in",
            "source_links": ["https://www.nitsri.ac.in", "https://www.nirf.ac.in"]
          }},
          {{
            "rank": 2,
            "college_name": "University of Jammu",
            "college_id": "university_of_jammu",
            "location": "Jammu, Jammu and Kashmir",
            "college_type": "government",
            "established_year": 1969,
            "accreditation": ["NAAC A", "UGC"],
            "programs": [
              {{
                "name": "Bachelor of Technology in Computer Science and Engineering",
                "stream": "engineering",
                "duration_years": 4,
                "fees_annual": 50000,
                "seats_total": 60,
                "eligibility_criteria": "12th with 50% marks in Physics, Chemistry, Mathematics"
              }}
            ],
            "placement_stats": [
              {{
                "year": 2023,
                "placement_percentage": 75.0,
                "average_salary": 400000,
                "top_recruiters": ["J&K Bank", "State Bank of India", "HDFC Bank", "TCS", "Infosys"]
              }}
            ],
            "mentor_ratings": [
              {{
                "mentor_name": "Prof. Sunita Sharma",
                "rating": 4.0,
                "review_text": "Good university in Jammu with decent infrastructure and local job opportunities."
              }}
            ],
            "official_website": "https://www.jammuuniversity.ac.in",
            "source_links": ["https://www.jammuuniversity.ac.in", "https://www.ugc.ac.in"]
          }},
          {{
            "rank": 3,
            "college_name": "University of Kashmir",
            "college_id": "university_of_kashmir",
            "location": "Srinagar, Jammu and Kashmir",
            "college_type": "government",
            "established_year": 1948,
            "accreditation": ["NAAC A", "UGC"],
            "programs": [
              {{
                "name": "Bachelor of Technology in Information Technology",
                "stream": "engineering",
                "duration_years": 4,
                "fees_annual": 45000,
                "seats_total": 40,
                "eligibility_criteria": "12th with 50% marks in Physics, Chemistry, Mathematics"
              }}
            ],
            "placement_stats": [
              {{
                "year": 2023,
                "placement_percentage": 66.7,
                "average_salary": 350000,
                "top_recruiters": ["J&K Bank", "State Bank of India", "Government of J&K", "Local IT companies"]
              }}
            ],
            "mentor_ratings": [
              {{
                "mentor_name": "Dr. Ahmed Mir",
                "rating": 3.8,
                "review_text": "Established university in Kashmir with good academic programs and local connections."
              }}
            ],
            "official_website": "https://www.kashmiruniversity.net",
            "source_links": ["https://www.kashmiruniversity.net", "https://www.ugc.ac.in"]
          }}
        ]
        """
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
        
        return MockResponse(mock_response)
