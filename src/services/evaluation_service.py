"""
Evaluation Service for College Recommendation System
"""
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from ..models.college import StudentProfile, StreamType, CollegeRecommendation


class EvaluationService:
    """Service for evaluating recommendation quality"""
    
    def __init__(self):
        self.test_cases = []
        self.mentor_feedback = {}
        self.evaluation_metrics = {}
    
    def generate_test_cases(self, num_cases: int = 20) -> List[Dict[str, Any]]:
        """Generate realistic student test cases"""
        
        # Define realistic test case templates
        test_case_templates = [
            {
                "name": "High Performer - Engineering",
                "age": 18,
                "board": "CBSE",
                "marks_percentage": 95.5,
                "preferred_streams": [StreamType.ENGINEERING],
                "budget_range": (200000, 500000),
                "location": "Delhi",
                "interests": ["Technology", "Programming", "Robotics"],
                "career_goals": ["Software Engineer", "Tech Entrepreneur"]
            },
            {
                "name": "Average Performer - Science",
                "age": 19,
                "board": "State Board",
                "marks_percentage": 78.0,
                "preferred_streams": [StreamType.SCIENCE],
                "budget_range": (50000, 150000),
                "location": "Bangalore",
                "interests": ["Research", "Biology", "Chemistry"],
                "career_goals": ["Research Scientist", "Lab Technician"]
            },
            {
                "name": "Commerce Student",
                "age": 18,
                "board": "ICSE",
                "marks_percentage": 82.0,
                "preferred_streams": [StreamType.COMMERCE],
                "budget_range": (30000, 100000),
                "location": "Mumbai",
                "interests": ["Business", "Finance", "Economics"],
                "career_goals": ["Chartered Accountant", "Investment Banker"]
            },
            {
                "name": "Arts Student",
                "age": 20,
                "board": "CBSE",
                "marks_percentage": 75.0,
                "preferred_streams": [StreamType.ARTS],
                "budget_range": (20000, 80000),
                "location": "Kolkata",
                "interests": ["Literature", "History", "Psychology"],
                "career_goals": ["Writer", "Teacher", "Counselor"]
            },
            {
                "name": "Medical Aspirant",
                "age": 18,
                "board": "CBSE",
                "marks_percentage": 92.0,
                "preferred_streams": [StreamType.MEDICAL],
                "budget_range": (100000, 300000),
                "location": "Chennai",
                "interests": ["Medicine", "Biology", "Healthcare"],
                "career_goals": ["Doctor", "Medical Researcher"]
            }
        ]
        
        # Generate variations of each template
        test_cases = []
        for i in range(num_cases):
            template = random.choice(test_case_templates)
            
            # Add variations
            variation = template.copy()
            variation["test_case_id"] = f"test_{i+1:03d}"
            variation["name"] = f"{template['name']} - Variation {i+1}"
            
            # Vary some parameters
            variation["age"] = random.randint(17, 22)
            variation["marks_percentage"] = max(60.0, min(100.0, 
                variation["marks_percentage"] + random.uniform(-5, 5)))
            
            # Vary budget
            min_budget, max_budget = variation["budget_range"]
            variation["budget_range"] = (
                int(min_budget * random.uniform(0.8, 1.2)),
                int(max_budget * random.uniform(0.8, 1.2))
            )
            
            # Add some additional interests
            additional_interests = [
                "Sports", "Music", "Art", "Volunteering", "Debate", 
                "Photography", "Dance", "Theater", "Gaming", "Reading"
            ]
            variation["interests"].extend(random.sample(additional_interests, 2))
            
            test_cases.append(variation)
        
        self.test_cases = test_cases
        return test_cases
    
    def save_test_cases(self, filepath: str = "./data/test_cases.json"):
        """Save test cases to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_cases, f, indent=2, default=str)
    
    def load_test_cases(self, filepath: str = "./data/test_cases.json") -> List[Dict[str, Any]]:
        """Load test cases from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.test_cases = json.load(f)
            return self.test_cases
        except FileNotFoundError:
            return []
    
    def create_mentor_annotation_ui(self) -> str:
        """Create HTML for mentor annotation UI"""
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Mentor Annotation Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .test-case { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }
                .recommendation { background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .rating { margin: 10px 0; }
                .rating label { display: inline-block; width: 150px; }
                .rating input[type="range"] { width: 200px; }
                .rating span { margin-left: 10px; font-weight: bold; }
                .feedback { margin: 10px 0; }
                .feedback textarea { width: 100%; height: 80px; }
                .submit-btn { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
                .submit-btn:hover { background-color: #0056b3; }
                .header { text-align: center; margin-bottom: 30px; }
                .stats { background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 College Recommendation Evaluation</h1>
                    <p>Mentor Annotation Interface</p>
                </div>
                
                <div class="stats">
                    <h3>Evaluation Progress</h3>
                    <p>Test Cases: <span id="total-cases">0</span> | 
                       Completed: <span id="completed-cases">0</span> | 
                       Remaining: <span id="remaining-cases">0</span></p>
                </div>
                
                <div id="test-cases-container">
                    <!-- Test cases will be populated here -->
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <button class="submit-btn" onclick="submitAllFeedback()">Submit All Feedback</button>
                </div>
            </div>
            
            <script>
                // This would be populated with actual test case data
                const testCases = [];
                const mentorFeedback = {};
                
                function renderTestCases() {
                    const container = document.getElementById('test-cases-container');
                    container.innerHTML = '';
                    
                    testCases.forEach((testCase, index) => {
                        const testCaseDiv = document.createElement('div');
                        testCaseDiv.className = 'test-case';
                        testCaseDiv.innerHTML = `
                            <h3>Test Case ${index + 1}: ${testCase.name}</h3>
                            <div class="student-profile">
                                <h4>Student Profile:</h4>
                                <p><strong>Age:</strong> ${testCase.age} | 
                                   <strong>Board:</strong> ${testCase.board} | 
                                   <strong>Marks:</strong> ${testCase.marks_percentage}%</p>
                                <p><strong>Preferred Streams:</strong> ${testCase.preferred_streams.join(', ')}</p>
                                <p><strong>Budget:</strong> ₹${testCase.budget_range[0].toLocaleString()} - ₹${testCase.budget_range[1].toLocaleString()}</p>
                                <p><strong>Location:</strong> ${testCase.location}</p>
                                <p><strong>Interests:</strong> ${testCase.interests.join(', ')}</p>
                                <p><strong>Career Goals:</strong> ${testCase.career_goals.join(', ')}</p>
                            </div>
                            
                            <div class="recommendations">
                                <h4>AI Recommendations:</h4>
                                ${testCase.recommendations ? testCase.recommendations.map((rec, recIndex) => `
                                    <div class="recommendation">
                                        <h5>#${recIndex + 1} ${rec.college_name}</h5>
                                        <p><strong>Rationale:</strong> ${rec.rationale}</p>
                                        <p><strong>Scores:</strong> 
                                           Official: ${rec.scores.official_quality}/10 | 
                                           Mentor: ${rec.scores.mentor_trust}/10 | 
                                           Relevance: ${rec.scores.relevance}/10 | 
                                           Proximity: ${rec.scores.proximity}/10</p>
                                        
                                        <div class="rating">
                                            <label>Overall Quality:</label>
                                            <input type="range" min="1" max="5" value="3" 
                                                   onchange="updateRating(${index}, ${recIndex}, 'overall', this.value)">
                                            <span id="rating-${index}-${recIndex}-overall">3</span>
                                        </div>
                                        
                                        <div class="rating">
                                            <label>Relevance to Student:</label>
                                            <input type="range" min="1" max="5" value="3" 
                                                   onchange="updateRating(${index}, ${recIndex}, 'relevance', this.value)">
                                            <span id="rating-${index}-${recIndex}-relevance">3</span>
                                        </div>
                                        
                                        <div class="rating">
                                            <label>Accuracy of Information:</label>
                                            <input type="range" min="1" max="5" value="3" 
                                                   onchange="updateRating(${index}, ${recIndex}, 'accuracy', this.value)">
                                            <span id="rating-${index}-${recIndex}-accuracy">3</span>
                                        </div>
                                        
                                        <div class="feedback">
                                            <label>Additional Feedback:</label>
                                            <textarea placeholder="Any additional comments or suggestions..." 
                                                      onchange="updateFeedback(${index}, ${recIndex}, this.value)"></textarea>
                                        </div>
                                    </div>
                                `).join('') : '<p>No recommendations available</p>'}
                            </div>
                        `;
                        container.appendChild(testCaseDiv);
                    });
                    
                    updateStats();
                }
                
                function updateRating(testCaseIndex, recIndex, ratingType, value) {
                    if (!mentorFeedback[testCaseIndex]) {
                        mentorFeedback[testCaseIndex] = {};
                    }
                    if (!mentorFeedback[testCaseIndex][recIndex]) {
                        mentorFeedback[testCaseIndex][recIndex] = {};
                    }
                    mentorFeedback[testCaseIndex][recIndex][ratingType] = parseInt(value);
                    
                    // Update display
                    document.getElementById(`rating-${testCaseIndex}-${recIndex}-${ratingType}`).textContent = value;
                }
                
                function updateFeedback(testCaseIndex, recIndex, feedback) {
                    if (!mentorFeedback[testCaseIndex]) {
                        mentorFeedback[testCaseIndex] = {};
                    }
                    if (!mentorFeedback[testCaseIndex][recIndex]) {
                        mentorFeedback[testCaseIndex][recIndex] = {};
                    }
                    mentorFeedback[testCaseIndex][recIndex].feedback = feedback;
                }
                
                function updateStats() {
                    const totalCases = testCases.length;
                    const completedCases = Object.keys(mentorFeedback).length;
                    const remainingCases = totalCases - completedCases;
                    
                    document.getElementById('total-cases').textContent = totalCases;
                    document.getElementById('completed-cases').textContent = completedCases;
                    document.getElementById('remaining-cases').textContent = remainingCases;
                }
                
                function submitAllFeedback() {
                    const feedbackData = {
                        mentor_id: 'mentor_' + Date.now(),
                        submission_date: new Date().toISOString(),
                        test_cases: testCases,
                        feedback: mentorFeedback
                    };
                    
                    // In a real implementation, this would send data to a server
                    console.log('Submitting feedback:', feedbackData);
                    alert('Feedback submitted successfully!');
                }
                
                // Initialize the interface
                renderTestCases();
            </script>
        </body>
        </html>
        """
        
        return html_template
    
    def evaluate_recommendations(self, 
                               test_cases: List[Dict[str, Any]],
                               recommendations: Dict[str, List[CollegeRecommendation]]) -> Dict[str, Any]:
        """Evaluate recommendation quality using various metrics"""
        
        evaluation_results = {
            "overall_metrics": {},
            "per_test_case": {},
            "recommendation_quality": {},
            "verification_accuracy": {},
            "mentor_feedback": {}
        }
        
        # Calculate overall metrics
        total_test_cases = len(test_cases)
        total_recommendations = sum(len(recs) for recs in recommendations.values())
        
        evaluation_results["overall_metrics"] = {
            "total_test_cases": total_test_cases,
            "total_recommendations": total_recommendations,
            "avg_recommendations_per_case": total_recommendations / total_test_cases if total_test_cases > 0 else 0
        }
        
        # Evaluate each test case
        for test_case in test_cases:
            test_case_id = test_case["test_case_id"]
            case_recommendations = recommendations.get(test_case_id, [])
            
            case_evaluation = self._evaluate_single_case(test_case, case_recommendations)
            evaluation_results["per_test_case"][test_case_id] = case_evaluation
        
        # Calculate aggregate metrics
        evaluation_results["recommendation_quality"] = self._calculate_quality_metrics(evaluation_results["per_test_case"])
        evaluation_results["verification_accuracy"] = self._calculate_verification_metrics(evaluation_results["per_test_case"])
        
        return evaluation_results
    
    def _evaluate_single_case(self, 
                            test_case: Dict[str, Any], 
                            recommendations: List[CollegeRecommendation]) -> Dict[str, Any]:
        """Evaluate recommendations for a single test case"""
        
        evaluation = {
            "test_case_id": test_case["test_case_id"],
            "num_recommendations": len(recommendations),
            "score_analysis": {},
            "relevance_analysis": {},
            "verification_analysis": {},
            "budget_compliance": {},
            "stream_alignment": {}
        }
        
        if not recommendations:
            return evaluation
        
        # Score analysis
        scores = [rec.score.composite_score for rec in recommendations]
        evaluation["score_analysis"] = {
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "score_variance": self._calculate_variance(scores)
        }
        
        # Relevance analysis
        evaluation["relevance_analysis"] = self._analyze_relevance(test_case, recommendations)
        
        # Verification analysis
        verification_statuses = [rec.verification_status for rec in recommendations]
        evaluation["verification_analysis"] = {
            "verified_count": verification_statuses.count("verified"),
            "flagged_count": verification_statuses.count("flagged"),
            "pending_count": verification_statuses.count("pending"),
            "verification_rate": verification_statuses.count("verified") / len(verification_statuses)
        }
        
        # Budget compliance
        evaluation["budget_compliance"] = self._analyze_budget_compliance(test_case, recommendations)
        
        # Stream alignment
        evaluation["stream_alignment"] = self._analyze_stream_alignment(test_case, recommendations)
        
        return evaluation
    
    def _analyze_relevance(self, 
                          test_case: Dict[str, Any], 
                          recommendations: List[CollegeRecommendation]) -> Dict[str, Any]:
        """Analyze how relevant recommendations are to the test case"""
        
        student_streams = test_case["preferred_streams"]
        student_interests = test_case["interests"]
        student_goals = test_case["career_goals"]
        
        relevance_scores = []
        stream_matches = 0
        
        for rec in recommendations:
            # Check stream alignment
            college_streams = [program.stream.value for program in rec.college.programs]
            stream_match = any(stream in college_streams for stream in student_streams)
            if stream_match:
                stream_matches += 1
            
            # Use the relevance score from the recommendation
            relevance_scores.append(rec.score.relevance)
        
        return {
            "avg_relevance_score": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
            "stream_match_rate": stream_matches / len(recommendations) if recommendations else 0,
            "high_relevance_count": sum(1 for score in relevance_scores if score >= 7.0)
        }
    
    def _analyze_budget_compliance(self, 
                                 test_case: Dict[str, Any], 
                                 recommendations: List[CollegeRecommendation]) -> Dict[str, Any]:
        """Analyze budget compliance of recommendations"""
        
        min_budget, max_budget = test_case["budget_range"]
        compliant_count = 0
        budget_scores = []
        
        for rec in recommendations:
            if rec.college.programs:
                min_fees = min(program.fees_annual for program in rec.college.programs)
                max_fees = max(program.fees_annual for program in rec.college.programs)
                
                # Check if any program is within budget
                if min_fees <= max_budget and max_fees >= min_budget:
                    compliant_count += 1
                
                # Calculate budget score (closer to student's preferred range is better)
                avg_fees = (min_fees + max_fees) / 2
                student_preferred = (min_budget + max_budget) / 2
                
                if avg_fees <= student_preferred:
                    budget_score = 10.0
                else:
                    # Penalize for being over budget
                    overage = avg_fees - student_preferred
                    budget_score = max(0, 10.0 - (overage / student_preferred) * 5)
                
                budget_scores.append(budget_score)
        
        return {
            "compliant_count": compliant_count,
            "compliance_rate": compliant_count / len(recommendations) if recommendations else 0,
            "avg_budget_score": sum(budget_scores) / len(budget_scores) if budget_scores else 0
        }
    
    def _analyze_stream_alignment(self, 
                                test_case: Dict[str, Any], 
                                recommendations: List[CollegeRecommendation]) -> Dict[str, Any]:
        """Analyze how well recommendations align with student's preferred streams"""
        
        student_streams = test_case["preferred_streams"]
        stream_counts = {}
        
        for rec in recommendations:
            for program in rec.college.programs:
                stream = program.stream.value
                stream_counts[stream] = stream_counts.get(stream, 0) + 1
        
        # Calculate alignment score
        total_programs = sum(stream_counts.values())
        alignment_score = 0
        
        for student_stream in student_streams:
            if student_stream in stream_counts:
                alignment_score += stream_counts[student_stream] / total_programs
        
        return {
            "stream_distribution": stream_counts,
            "alignment_score": alignment_score,
            "preferred_stream_coverage": len([s for s in student_streams if s in stream_counts]) / len(student_streams)
        }
    
    def _calculate_quality_metrics(self, per_test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregate quality metrics"""
        
        all_scores = []
        all_relevance = []
        all_verification_rates = []
        
        for case_data in per_test_case.values():
            if case_data["score_analysis"]:
                all_scores.append(case_data["score_analysis"]["avg_score"])
            if case_data["relevance_analysis"]:
                all_relevance.append(case_data["relevance_analysis"]["avg_relevance_score"])
            if case_data["verification_analysis"]:
                all_verification_rates.append(case_data["verification_analysis"]["verification_rate"])
        
        return {
            "avg_composite_score": sum(all_scores) / len(all_scores) if all_scores else 0,
            "avg_relevance_score": sum(all_relevance) / len(all_relevance) if all_relevance else 0,
            "avg_verification_rate": sum(all_verification_rates) / len(all_verification_rates) if all_verification_rates else 0,
            "score_consistency": 1 - self._calculate_variance(all_scores) if all_scores else 0
        }
    
    def _calculate_verification_metrics(self, per_test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate verification-related metrics"""
        
        total_verified = 0
        total_flagged = 0
        total_pending = 0
        total_recommendations = 0
        
        for case_data in per_test_case.values():
            if case_data["verification_analysis"]:
                total_verified += case_data["verification_analysis"]["verified_count"]
                total_flagged += case_data["verification_analysis"]["flagged_count"]
                total_pending += case_data["verification_analysis"]["pending_count"]
                total_recommendations += case_data["num_recommendations"]
        
        return {
            "total_verified": total_verified,
            "total_flagged": total_flagged,
            "total_pending": total_pending,
            "verification_rate": total_verified / total_recommendations if total_recommendations > 0 else 0,
            "flag_rate": total_flagged / total_recommendations if total_recommendations > 0 else 0
        }
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def save_evaluation_results(self, 
                              results: Dict[str, Any], 
                              filepath: str = "./data/evaluation_results.json"):
        """Save evaluation results to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
    
    def load_evaluation_results(self, 
                              filepath: str = "./data/evaluation_results.json") -> Dict[str, Any]:
        """Load evaluation results from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
