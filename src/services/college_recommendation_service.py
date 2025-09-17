"""
Main College Recommendation Service
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.college import (
    StudentProfile, 
    CollegeRecommendation, 
    RecommendationRequest,
    StreamType
)
from services.rag_pipeline import CollegeRAGPipeline, create_student_query
from services.llm_service import CollegeRecommendationLLM
from services.verification_service import CollegeVerificationService


class CollegeRecommendationService:
    """Main service for college recommendations"""
    
    def __init__(self, 
                 llm_model: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        
        # Initialize components
        self.rag_pipeline = CollegeRAGPipeline(embedding_model=embedding_model)
        self.llm_service = CollegeRecommendationLLM(
            model_name=llm_model,
            api_key=api_key
        )
        self.verification_service = CollegeVerificationService()
        
        # Load college data
        self._load_college_data()
    
    def _load_college_data(self):
        """Load and process college data"""
        try:
            # Check if vector store already exists
            import os
            if os.path.exists(self.rag_pipeline.persist_directory) and os.listdir(self.rag_pipeline.persist_directory):
                # Load existing vector store
                self.rag_pipeline.load_existing_vectorstore()
                print(f"✅ Loaded existing vector store from {self.rag_pipeline.persist_directory}")
            else:
                # Create new vector store
                colleges = self.rag_pipeline.load_college_data("./data/colleges_sample.json")
                documents = self.rag_pipeline.create_college_documents(colleges)
                self.rag_pipeline.create_vectorstore(documents)
                print(f"✅ Created new vector store with {len(colleges)} colleges")
            
        except Exception as e:
            print(f"❌ Error loading college data: {e}")
            raise
    
    def get_recommendations(self, 
                          request: RecommendationRequest) -> List[CollegeRecommendation]:
        """Get college recommendations for a student"""
        
        # Create search query from student profile
        query = create_student_query(request.student_profile)
        
        # Apply filters based on student preferences
        filters = self._create_filters(request.student_profile)
        
        # Retrieve relevant documents
        retrieved_docs = self.rag_pipeline.search_colleges(
            query=query,
            k=5,  # Limit to 5 documents for better performance
            filters=filters
        )
        
        # Apply budget filtering in post-processing
        if request.student_profile.budget_range:
            min_budget, max_budget = request.student_profile.budget_range
            budget_filtered_docs = []
            for doc in retrieved_docs:
                min_fees = doc.metadata.get('min_fees', 0)
                max_fees = doc.metadata.get('max_fees', 0)
                
                # Check if any program is within budget
                if min_fees <= max_budget and max_fees >= min_budget:
                    budget_filtered_docs.append(doc)
            
            retrieved_docs = budget_filtered_docs[:5]  # Take top 5 after filtering
        
        # Convert documents to format expected by LLM
        formatted_docs = []
        for doc in retrieved_docs:
            formatted_docs.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata
            })
        
        # Generate recommendations using LLM
        recommendations = self.llm_service.generate_recommendations(
            student_profile=request.student_profile,
            retrieved_documents=formatted_docs,
            preferences=request.preferences
        )
        
        # Apply user preferences to scoring
        if request.preferences:
            recommendations = self._apply_preferences(recommendations, request.preferences)
        
        # Verify recommendations if requested
        if request.include_verification:
            recommendations = self.verification_service.verify_recommendations(recommendations)
        
        # Limit to requested number of recommendations
        return recommendations[:request.max_recommendations]
    
    def _create_filters(self, student_profile: StudentProfile) -> Dict[str, Any]:
        """Create metadata filters based on student profile"""
        # For now, don't use filters to avoid ChromaDB issues
        # We'll do all filtering in post-processing
        return {}
    
    def _apply_preferences(self, 
                          recommendations: List[CollegeRecommendation],
                          preferences: Dict[str, float]) -> List[CollegeRecommendation]:
        """Apply user preferences to reweight scores"""
        
        # Default weights
        default_weights = {
            "official_quality": 0.3,
            "mentor_trust": 0.2,
            "relevance": 0.3,
            "proximity": 0.2
        }
        
        # Apply user preferences
        weights = {**default_weights, **preferences}
        
        # Normalize weights
        total_weight = sum(weights.values())
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        
        # Recalculate composite scores
        for recommendation in recommendations:
            score = recommendation.score
            new_composite = (
                score.official_quality * normalized_weights["official_quality"] +
                score.mentor_trust * normalized_weights["mentor_trust"] +
                score.relevance * normalized_weights["relevance"] +
                score.proximity * normalized_weights["proximity"]
            )
            score.composite_score = new_composite
        
        # Re-sort by composite score
        recommendations.sort(key=lambda x: x.score.composite_score, reverse=True)
        
        # Update ranks
        for i, recommendation in enumerate(recommendations, 1):
            recommendation.rank = i
        
        return recommendations
    
    def get_recommendation_explanation(self, 
                                     recommendation: CollegeRecommendation) -> Dict[str, Any]:
        """Get detailed explanation for a recommendation"""
        
        explanation = {
            "college_name": recommendation.college.name,
            "rank": recommendation.rank,
            "scores": {
                "official_quality": {
                    "score": recommendation.score.official_quality,
                    "description": "Based on accreditation, NIRF ranking, and institutional reputation"
                },
                "mentor_trust": {
                    "score": recommendation.score.mentor_trust,
                    "description": "Based on mentor ratings and verified reviews"
                },
                "relevance": {
                    "score": recommendation.score.relevance,
                    "description": "How well the college matches your preferences and goals"
                },
                "proximity": {
                    "score": recommendation.score.proximity,
                    "description": "Location convenience and distance from your preferred location"
                },
                "composite": {
                    "score": recommendation.score.composite_score,
                    "description": "Weighted average of all factors"
                }
            },
            "rationale": recommendation.rationale,
            "evidence": recommendation.evidence_citations,
            "verification_status": recommendation.verification_status,
            "source_links": recommendation.source_links,
            "confidence": recommendation.score.confidence
        }
        
        return explanation
    
    def get_college_details(self, college_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific college"""
        
        # Search for college in vector store
        results = self.rag_pipeline.search_colleges(
            query=college_id,
            k=1,
            filters={"college_id": college_id}
        )
        
        if not results:
            return None
        
        doc = results[0]
        metadata = doc.metadata
        
        return {
            "college_id": metadata.get("college_id"),
            "name": metadata.get("college_name"),
            "type": metadata.get("college_type"),
            "location": metadata.get("location"),
            "district": metadata.get("district"),
            "state": metadata.get("state"),
            "established_year": metadata.get("established_year"),
            "accreditation": metadata.get("accreditation", []),
            "streams": metadata.get("streams", []),
            "avg_rating": metadata.get("avg_rating", 0.0),
            "placement_percentage": metadata.get("placement_percentage", 0.0),
            "avg_salary": metadata.get("avg_salary", 0.0),
            "min_fees": metadata.get("min_fees", 0),
            "max_fees": metadata.get("max_fees", 0),
            "source_links": metadata.get("source_links", []),
            "last_updated": metadata.get("last_updated"),
            "full_content": doc.page_content
        }
    
    def search_colleges_by_criteria(self, 
                                  criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search colleges by specific criteria"""
        
        # Build search query from criteria
        query_parts = []
        
        if "stream" in criteria:
            query_parts.append(f"programs in {criteria['stream']}")
        
        if "location" in criteria:
            query_parts.append(f"in {criteria['location']}")
        
        if "budget_max" in criteria:
            query_parts.append(f"fees under {criteria['budget_max']}")
        
        if "min_rating" in criteria:
            query_parts.append(f"rating above {criteria['min_rating']}")
        
        query = " ".join(query_parts) if query_parts else "government colleges"
        
        # Apply filters
        filters = {}
        if "streams" in criteria:
            filters["streams"] = criteria["streams"]
        if "college_type" in criteria:
            filters["college_type"] = criteria["college_type"]
        if "state" in criteria:
            filters["state"] = criteria["state"]
        
        # Search
        results = self.rag_pipeline.search_colleges(
            query=query,
            k=criteria.get("limit", 10),
            filters=filters
        )
        
        # Format results
        colleges = []
        for doc in results:
            metadata = doc.metadata
            colleges.append({
                "college_id": metadata.get("college_id"),
                "name": metadata.get("college_name"),
                "type": metadata.get("college_type"),
                "location": metadata.get("location"),
                "district": metadata.get("district"),
                "state": metadata.get("state"),
                "streams": metadata.get("streams", []),
                "avg_rating": metadata.get("avg_rating", 0.0),
                "placement_percentage": metadata.get("placement_percentage", 0.0),
                "avg_salary": metadata.get("avg_salary", 0.0),
                "min_fees": metadata.get("min_fees", 0),
                "max_fees": metadata.get("max_fees", 0),
                "source_links": metadata.get("source_links", [])
            })
        
        return colleges
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        
        # Get collection info from vector store
        collection_info = self.rag_pipeline.vectorstore._collection.count()
        
        return {
            "total_colleges": collection_info,
            "embedding_model": self.rag_pipeline.embedding_model.model_name,
            "llm_model": self.llm_service.model_name,
            "last_updated": datetime.now().isoformat(),
            "verification_enabled": True
        }
