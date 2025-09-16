"""
Enhanced RAG Pipeline for College Recommendation System
"""
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from langchain_core.documents import Document
from langchain_community.document_loaders import JSONLoader, CSVLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document

from ..models.college import College, StudentProfile, StreamType


class CollegeRAGPipeline:
    """Enhanced RAG pipeline for college recommendations"""
    
    def __init__(self, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 persist_directory: str = "./data/chroma_db"):
        self.embedding_model = SentenceTransformerEmbeddings(model_name=embedding_model)
        self.persist_directory = persist_directory
        self.vectorstore = None
        self.colleges_data = []
        
    def load_college_data(self, data_path: str) -> List[College]:
        """Load college data from JSON file"""
        with open(data_path, 'r', encoding='utf-8') as f:
            colleges_json = json.load(f)
        
        colleges = []
        for college_data in colleges_json:
            # Convert datetime strings to datetime objects
            for rating in college_data.get('mentor_ratings', []):
                if 'review_date' in rating:
                    rating['review_date'] = datetime.fromisoformat(rating['review_date'].replace('Z', '+00:00'))
            
            college_data['last_updated'] = datetime.fromisoformat(
                college_data.get('last_updated', datetime.now().isoformat()).replace('Z', '+00:00')
            )
            
            colleges.append(College(**college_data))
        
        self.colleges_data = colleges
        return colleges
    
    def load_college_data_from_json(self, colleges_json: List[Dict[str, Any]]) -> List[College]:
        """Load college data from JSON list (for testing)"""
        colleges = []
        for college_data in colleges_json:
            # Convert datetime strings to datetime objects
            for rating in college_data.get('mentor_ratings', []):
                if 'review_date' in rating:
                    rating['review_date'] = datetime.fromisoformat(rating['review_date'].replace('Z', '+00:00'))
            
            college_data['last_updated'] = datetime.fromisoformat(
                college_data.get('last_updated', datetime.now().isoformat()).replace('Z', '+00:00')
            )
            
            colleges.append(College(**college_data))
        
        self.colleges_data = colleges
        return colleges
    
    def create_college_documents(self, colleges: List[College]) -> List[Document]:
        """Convert college data to LangChain documents"""
        documents = []
        
        for college in colleges:
            # Create comprehensive document for each college
            content = f"""
            College: {college.name}
            Type: {college.college_type.value}
            Location: {college.location}, {college.district}, {college.state}
            Established: {college.established_year}
            Accreditation: {', '.join(college.accreditation)}
            
            Programs:
            """
            
            for program in college.programs:
                content += f"""
                - {program.program_name} ({program.stream.value})
                  Duration: {program.duration_years} years
                  Annual Fees: ₹{program.fees_annual:,}
                  Total Seats: {program.seats_total}
                  Eligibility: {program.eligibility_criteria}
                  Entrance Exam: {program.entrance_exam or 'Not specified'}
                  Cutoff: {program.cutoff_percentage or 'Not available'}%
                """
            
            if college.placement_stats:
                latest_stats = college.placement_stats[-1]
                content += f"""
                
                Placement Statistics ({latest_stats.year}):
                - Total Students: {latest_stats.total_students}
                - Placed Students: {latest_stats.placed_students}
                - Placement Percentage: {latest_stats.placement_percentage}%
                - Average Salary: ₹{latest_stats.average_salary:,}
                - Highest Salary: ₹{latest_stats.highest_salary:,}
                - Top Recruiters: {', '.join(latest_stats.top_recruiters)}
                - Job Roles: {', '.join(latest_stats.job_roles)}
                """
            
            if college.mentor_ratings:
                avg_rating = sum(r.rating for r in college.mentor_ratings) / len(college.mentor_ratings)
                content += f"""
                
                Mentor Ratings:
                - Average Rating: {avg_rating:.1f}/5.0
                - Total Reviews: {len(college.mentor_ratings)}
                - Latest Review: {college.mentor_ratings[-1].review_text}
                """
            
            content += f"""
            
            Infrastructure:
            - Labs: {college.infrastructure.get('labs', 'N/A')}
            - Library Books: {college.infrastructure.get('library_books', 'N/A'):,}
            - Hostel Capacity: {college.infrastructure.get('hostel_capacity', 'N/A')}
            - Sports Facilities: {', '.join(college.infrastructure.get('sports_facilities', []))}
            - WiFi Campus: {college.infrastructure.get('wifi_campus', 'N/A')}
            
            Faculty:
            - Total Faculty: {college.faculty_info.get('total_faculty', 'N/A')}
            - PhD Faculty: {college.faculty_info.get('phd_faculty', 'N/A')}
            - Student-Faculty Ratio: {college.faculty_info.get('student_faculty_ratio', 'N/A')}
            
            Contact: {college.contact_info.get('phone', 'N/A')} | {college.contact_info.get('email', 'N/A')}
            Website: {college.official_website or 'N/A'}
            """
            
            # Create metadata for filtering
            metadata = {
                "college_id": college.college_id,
                "college_name": college.name,
                "college_type": college.college_type.value,
                "location": college.location,
                "district": college.district,
                "state": college.state,
                "streams": [program.stream.value for program in college.programs],
                "established_year": college.established_year,
                "accreditation": college.accreditation,
                "avg_rating": avg_rating if college.mentor_ratings else 0.0,
                "placement_percentage": latest_stats.placement_percentage if college.placement_stats else 0.0,
                "avg_salary": latest_stats.average_salary if college.placement_stats else 0.0,
                "min_fees": min(program.fees_annual for program in college.programs) if college.programs else 0,
                "max_fees": max(program.fees_annual for program in college.programs) if college.programs else 0,
                "source": "college_database",
                "last_updated": college.last_updated.isoformat(),
                "source_links": college.source_links
            }
            
            doc = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(doc)
        
        return documents
    
    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """Create and populate vector store"""
        # Filter complex metadata to avoid ChromaDB issues
        filtered_documents = []
        for doc in documents:
            filtered_doc, _ = filter_complex_metadata(doc)
            filtered_documents.append(filtered_doc)
        
        self.vectorstore = Chroma.from_documents(
            documents=filtered_documents,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory
        )
        return self.vectorstore
    
    def load_existing_vectorstore(self) -> Chroma:
        """Load existing vector store"""
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model
        )
        return self.vectorstore
    
    def get_retriever(self, 
                     k: int = 5,
                     filter_dict: Optional[Dict[str, Any]] = None) -> 'CollegeRetriever':
        """Get retriever with optional metadata filtering"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call create_vectorstore() first.")
        
        return CollegeRetriever(
            vectorstore=self.vectorstore,
            k=k,
            filter_dict=filter_dict
        )
    
    def search_colleges(self, 
                       query: str,
                       k: int = 5,
                       filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search for colleges based on query and filters"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized.")
        
        if filters:
            # Convert filters to ChromaDB format
            where_clause = {}
            for key, value in filters.items():
                if isinstance(value, list):
                    where_clause[key] = {"$in": value}
                else:
                    where_clause[key] = value
            
            results = self.vectorstore.similarity_search(
                query, 
                k=k, 
                filter=where_clause
            )
        else:
            results = self.vectorstore.similarity_search(query, k=k)
        
        return results


class CollegeRetriever(BaseRetriever):
    """Custom retriever for college recommendations"""
    
    def __init__(self, 
                 vectorstore: Chroma,
                 k: int = 5,
                 filter_dict: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.vectorstore = vectorstore
        self.k = k
        self.filter_dict = filter_dict or {}
    
    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Retrieve relevant documents based on query and filters"""
        
        # Convert filters to ChromaDB format
        where_clause = {}
        for key, value in self.filter_dict.items():
            if isinstance(value, list):
                where_clause[key] = {"$in": value}
            else:
                where_clause[key] = value
        
        if where_clause:
            results = self.vectorstore.similarity_search(
                query, 
                k=self.k, 
                filter=where_clause
            )
        else:
            results = self.vectorstore.similarity_search(query, k=self.k)
        
        return results


def create_student_query(student_profile: StudentProfile) -> str:
    """Create search query from student profile"""
    query_parts = []
    
    # Add stream preferences
    if student_profile.preferred_streams:
        streams = [stream.value for stream in student_profile.preferred_streams]
        query_parts.append(f"programs in {', '.join(streams)}")
    
    # Add budget constraint
    if student_profile.budget_range:
        min_budget, max_budget = student_profile.budget_range
        query_parts.append(f"fees between {min_budget} and {max_budget}")
    
    # Add location constraint
    if student_profile.location:
        query_parts.append(f"near {student_profile.location}")
    
    # Add academic performance
    if student_profile.marks_percentage:
        query_parts.append(f"cutoff around {student_profile.marks_percentage}%")
    
    # Add interests and career goals
    if student_profile.interests:
        query_parts.append(f"interests in {', '.join(student_profile.interests)}")
    
    if student_profile.career_goals:
        query_parts.append(f"career goals: {', '.join(student_profile.career_goals)}")
    
    return " ".join(query_parts)
