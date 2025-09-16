"""
Streamlit Web UI for College Recommendation System
"""
import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import pandas as pd

from ..models.college import StudentProfile, StreamType, RecommendationRequest
from ..services.college_recommendation_service import CollegeRecommendationService


def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="College Recommendation System",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .recommendation-card {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #fafafa;
    }
    .verification-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .verified {
        background-color: #d4edda;
        color: #155724;
    }
    .flagged {
        background-color: #f8d7da;
        color: #721c24;
    }
    .pending {
        background-color: #fff3cd;
        color: #856404;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🎓 College Recommendation System</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Government College Recommendations with Verification")
    
    # Initialize session state
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []
    if 'service' not in st.session_state:
        st.session_state.service = None
    
    # Sidebar for student profile
    with st.sidebar:
        st.header("📝 Student Profile")
        
        # Basic Information
        age = st.number_input("Age", min_value=16, max_value=30, value=18)
        board = st.selectbox("Education Board", ["CBSE", "ICSE", "State Board", "IB", "Other"])
        marks = st.slider("Marks Percentage", min_value=0.0, max_value=100.0, value=85.0, step=0.1)
        
        # Preferred Streams
        st.subheader("Preferred Streams")
        preferred_streams = []
        stream_options = [stream.value for stream in StreamType]
        selected_streams = st.multiselect(
            "Select preferred streams",
            stream_options,
            default=["engineering", "science"]
        )
        preferred_streams = [StreamType(stream) for stream in selected_streams]
        
        # Budget
        st.subheader("Budget Range")
        budget_min = st.number_input("Minimum Annual Fees (₹)", min_value=0, value=10000, step=1000)
        budget_max = st.number_input("Maximum Annual Fees (₹)", min_value=budget_min, value=500000, step=1000)
        
        # Location
        st.subheader("Location Preferences")
        location = st.text_input("Preferred Location (City/State)", value="Delhi")
        max_distance = st.slider("Maximum Distance (km)", min_value=10, max_value=500, value=100)
        
        # Additional Preferences
        st.subheader("Additional Preferences")
        language = st.selectbox("Preferred Language", ["English", "Hindi", "Regional Language", "Any"])
        interests = st.text_area("Interests (comma-separated)", value="Technology, Research, Innovation")
        career_goals = st.text_area("Career Goals (comma-separated)", value="Software Engineer, Data Scientist")
        
        # Preferences Weights
        st.subheader("🎛️ Preference Weights")
        st.markdown("Adjust the importance of different factors:")
        
        official_quality_weight = st.slider(
            "Official Quality (Accreditation, Ranking)", 
            min_value=0.0, max_value=1.0, value=0.3, step=0.1
        )
        mentor_trust_weight = st.slider(
            "Mentor Trust (Ratings, Reviews)", 
            min_value=0.0, max_value=1.0, value=0.2, step=0.1
        )
        relevance_weight = st.slider(
            "Relevance (Match to Preferences)", 
            min_value=0.0, max_value=1.0, value=0.3, step=0.1
        )
        proximity_weight = st.slider(
            "Proximity (Location Convenience)", 
            min_value=0.0, max_value=1.0, value=0.2, step=0.1
        )
        
        # Normalize weights
        total_weight = official_quality_weight + mentor_trust_weight + relevance_weight + proximity_weight
        if total_weight > 0:
            preferences = {
                "official_quality": official_quality_weight / total_weight,
                "mentor_trust": mentor_trust_weight / total_weight,
                "relevance": relevance_weight / total_weight,
                "proximity": proximity_weight / total_weight
            }
        else:
            preferences = {}
        
        # Generate Recommendations Button
        if st.button("🔍 Get Recommendations", type="primary"):
            with st.spinner("Generating recommendations..."):
                try:
                    # Create student profile
                    student_profile = StudentProfile(
                        age=age,
                        board=board,
                        marks_percentage=marks,
                        preferred_streams=preferred_streams,
                        budget_range=(budget_min, budget_max),
                        preferred_language=language,
                        max_distance_km=max_distance,
                        location=location,
                        interests=[interest.strip() for interest in interests.split(",") if interest.strip()],
                        career_goals=[goal.strip() for goal in career_goals.split(",") if goal.strip()]
                    )
                    
                    # Create recommendation request
                    request = RecommendationRequest(
                        student_profile=student_profile,
                        preferences=preferences,
                        max_recommendations=3,
                        include_verification=True
                    )
                    
                    # Initialize service if not already done
                    if st.session_state.service is None:
                        st.session_state.service = CollegeRecommendationService()
                    
                    # Get recommendations
                    recommendations = st.session_state.service.get_recommendations(request)
                    st.session_state.recommendations = recommendations
                    
                    st.success(f"✅ Generated {len(recommendations)} recommendations!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating recommendations: {str(e)}")
    
    # Main content area
    if st.session_state.recommendations:
        display_recommendations(st.session_state.recommendations)
    else:
        display_welcome_screen()


def display_welcome_screen():
    """Display welcome screen with instructions"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🎯 How It Works
        
        1. **Fill your profile** in the sidebar
        2. **Adjust preferences** using the sliders
        3. **Click Get Recommendations**
        4. **Review verified results**
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 What We Analyze
        
        - **Academic Performance** (Marks, Board)
        - **Stream Preferences** (Engineering, Science, etc.)
        - **Budget Constraints** (Fee range)
        - **Location Preferences** (Distance, City)
        - **Career Goals** (Future aspirations)
        """)
    
    with col3:
        st.markdown("""
        ### ✅ Verification Features
        
        - **Government Sources** (NIRF, UGC, AICTE)
        - **Placement Statistics** (Verified data)
        - **Accreditation Status** (Official records)
        - **Source Transparency** (All claims cited)
        """)


def display_recommendations(recommendations: List[Dict[str, Any]]):
    """Display college recommendations"""
    
    st.header("🎓 Your Top College Recommendations")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Recommendations", len(recommendations))
    
    with col2:
        verified_count = sum(1 for rec in recommendations if rec.verification_status == "verified")
        st.metric("Verified Claims", f"{verified_count}/{len(recommendations)}")
    
    with col3:
        avg_score = sum(rec.score.composite_score for rec in recommendations) / len(recommendations)
        st.metric("Average Score", f"{avg_score:.1f}/10")
    
    with col4:
        confidence = sum(rec.score.confidence for rec in recommendations) / len(recommendations)
        st.metric("Confidence", f"{confidence:.1%}")
    
    # Individual recommendations
    for i, recommendation in enumerate(recommendations, 1):
        display_recommendation_card(recommendation, i)
    
    # Visualization
    display_recommendation_charts(recommendations)


def display_recommendation_card(recommendation: Dict[str, Any], rank: int):
    """Display individual recommendation card"""
    
    with st.container():
        st.markdown(f"### #{rank} {recommendation.college.name}")
        
        # Verification badge
        verification_class = recommendation.verification_status
        st.markdown(f"""
        <span class="verification-badge {verification_class}">
            {recommendation.verification_status.upper()}
        </span>
        """, unsafe_allow_html=True)
        
        # Score breakdown
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Official Quality", f"{recommendation.score.official_quality:.1f}/10")
        with col2:
            st.metric("Mentor Trust", f"{recommendation.score.mentor_trust:.1f}/10")
        with col3:
            st.metric("Relevance", f"{recommendation.score.relevance:.1f}/10")
        with col4:
            st.metric("Proximity", f"{recommendation.score.proximity:.1f}/10")
        with col5:
            st.metric("Composite", f"{recommendation.score.composite_score:.1f}/10")
        
        # Rationale
        st.markdown(f"**Rationale:** {recommendation.rationale}")
        
        # Evidence citations
        if recommendation.evidence_citations:
            with st.expander("📚 Evidence & Sources"):
                for citation in recommendation.evidence_citations:
                    st.markdown(f"• {citation}")
        
        # Source links
        if recommendation.source_links:
            with st.expander("🔗 Official Sources"):
                for link in recommendation.source_links:
                    st.markdown(f"• [{link}]({link})")
        
        st.divider()


def display_recommendation_charts(recommendations: List[Dict[str, Any]]):
    """Display visualization charts for recommendations"""
    
    st.header("📊 Recommendation Analysis")
    
    # Prepare data for visualization
    data = []
    for rec in recommendations:
        data.append({
            "College": rec.college.name,
            "Official Quality": rec.score.official_quality,
            "Mentor Trust": rec.score.mentor_trust,
            "Relevance": rec.score.relevance,
            "Proximity": rec.score.proximity,
            "Composite": rec.score.composite_score
        })
    
    df = pd.DataFrame(data)
    
    # Radar chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Score Comparison")
        
        fig = go.Figure()
        
        for _, row in df.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row["Official Quality"], row["Mentor Trust"], 
                   row["Relevance"], row["Proximity"], row["Official Quality"]],
                theta=["Official Quality", "Mentor Trust", 
                       "Relevance", "Proximity", "Official Quality"],
                fill='toself',
                name=row["College"]
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title="Score Breakdown Comparison"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Composite Score Ranking")
        
        fig = px.bar(
            df, 
            x="Composite", 
            y="College",
            orientation='h',
            title="Composite Score Ranking",
            color="Composite",
            color_continuous_scale="Viridis"
        )
        
        fig.update_layout(
            xaxis_title="Composite Score",
            yaxis_title="College",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Verification status
    st.subheader("Verification Status")
    
    verification_counts = {}
    for rec in recommendations:
        status = rec.verification_status
        verification_counts[status] = verification_counts.get(status, 0) + 1
    
    fig = px.pie(
        values=list(verification_counts.values()),
        names=list(verification_counts.keys()),
        title="Verification Status Distribution",
        color_discrete_map={
            "verified": "#28a745",
            "flagged": "#dc3545",
            "pending": "#ffc107"
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
