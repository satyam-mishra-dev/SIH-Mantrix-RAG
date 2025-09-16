"""
Verification Service for College Claims
"""
import requests
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse

from ..models.college import VerificationResult, CollegeRecommendation


class CollegeVerificationService:
    """Service for verifying college-related claims against government sources"""
    
    def __init__(self):
        self.government_sources = {
            "nirf": "https://www.nirf.ac.in",
            "ugc": "https://www.ugc.ac.in",
            "aicte": "https://www.aicte-india.org",
            "digilocker": "https://www.digilocker.gov.in",
            "ncs": "https://www.ncs.gov.in"
        }
        self.verification_cache = {}
    
    def verify_college_claim(self, 
                           claim: str, 
                           college_name: str,
                           claim_type: str = "general") -> VerificationResult:
        """Verify a specific claim about a college"""
        
        # Check cache first
        cache_key = f"{college_name}_{claim}_{claim_type}"
        if cache_key in self.verification_cache:
            cached_result = self.verification_cache[cache_key]
            if self._is_cache_valid(cached_result):
                return cached_result
        
        # Perform verification
        verification_result = self._perform_verification(claim, college_name, claim_type)
        
        # Cache the result
        self.verification_cache[cache_key] = verification_result
        
        return verification_result
    
    def verify_recommendations(self, 
                             recommendations: List[CollegeRecommendation]) -> List[CollegeRecommendation]:
        """Verify all claims in a list of recommendations"""
        verified_recommendations = []
        
        for recommendation in recommendations:
            # Verify key claims about the college
            verification_results = []
            
            # Verify placement statistics
            if recommendation.college.placement_stats:
                latest_stats = recommendation.college.placement_stats[-1]
                placement_claim = f"Placement percentage: {latest_stats.placement_percentage}%"
                verification_results.append(
                    self.verify_college_claim(placement_claim, recommendation.college.name, "placement")
                )
            
            # Verify accreditation
            if recommendation.college.accreditation:
                acc_claim = f"Accredited by: {', '.join(recommendation.college.accreditation)}"
                verification_results.append(
                    self.verify_college_claim(acc_claim, recommendation.college.name, "accreditation")
                )
            
            # Verify program information
            if recommendation.college.programs:
                program = recommendation.college.programs[0]
                program_claim = f"Offers {program.program_name} with {program.seats_total} seats"
                verification_results.append(
                    self.verify_college_claim(program_claim, recommendation.college.name, "program")
                )
            
            # Determine overall verification status
            verified_count = sum(1 for result in verification_results if result.verified)
            total_count = len(verification_results)
            
            if total_count == 0:
                verification_status = "no_claims"
            elif verified_count == total_count:
                verification_status = "verified"
            elif verified_count > total_count // 2:
                verification_status = "partially_verified"
            else:
                verification_status = "flagged"
            
            # Update recommendation with verification status
            recommendation.verification_status = verification_status
            recommendation.evidence_citations.extend([
                f"Verification: {result.verified} (Confidence: {result.confidence:.2f})"
                for result in verification_results
            ])
            
            verified_recommendations.append(recommendation)
        
        return verified_recommendations
    
    def _perform_verification(self, 
                            claim: str, 
                            college_name: str, 
                            claim_type: str) -> VerificationResult:
        """Perform the actual verification against government sources"""
        
        verification_attempts = []
        
        # Try different verification methods based on claim type
        if claim_type == "placement":
            verification_attempts.append(
                self._verify_placement_claim(claim, college_name)
            )
        elif claim_type == "accreditation":
            verification_attempts.append(
                self._verify_accreditation_claim(claim, college_name)
            )
        elif claim_type == "program":
            verification_attempts.append(
                self._verify_program_claim(claim, college_name)
            )
        else:
            # General verification
            verification_attempts.extend([
                self._verify_nirf_data(claim, college_name),
                self._verify_ugc_data(claim, college_name),
                self._verify_aicte_data(claim, college_name)
            ])
        
        # Combine verification results
        verified_results = [r for r in verification_attempts if r.verified]
        
        if verified_results:
            # Use the result with highest confidence
            best_result = max(verified_results, key=lambda x: x.confidence)
            return best_result
        else:
            # Return unverified result
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.0,
                source="verification_failed",
                verification_date=datetime.now(),
                notes="Could not verify claim against government sources"
            )
    
    def _verify_placement_claim(self, claim: str, college_name: str) -> VerificationResult:
        """Verify placement-related claims"""
        try:
            # In a real implementation, you would query NIRF or other official sources
            # For now, we'll simulate verification
            nirf_data = self._fetch_nirf_data(college_name)
            
            if nirf_data and "placement" in nirf_data:
                # Extract placement percentage from claim
                import re
                placement_match = re.search(r"(\d+(?:\.\d+)?)%", claim)
                if placement_match:
                    claimed_percentage = float(placement_match.group(1))
                    official_percentage = nirf_data["placement"]
                    
                    # Check if within reasonable range (allow 5% variance)
                    if abs(claimed_percentage - official_percentage) <= 5.0:
                        return VerificationResult(
                            claim=claim,
                            verified=True,
                            confidence=0.9,
                            source="NIRF",
                            verification_date=datetime.now(),
                            notes=f"Verified against NIRF data: {official_percentage}%"
                        )
            
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.3,
                source="NIRF",
                verification_date=datetime.now(),
                notes="Placement data not found in NIRF records"
            )
            
        except Exception as e:
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.0,
                source="verification_error",
                verification_date=datetime.now(),
                notes=f"Error during verification: {str(e)}"
            )
    
    def _verify_accreditation_claim(self, claim: str, college_name: str) -> VerificationResult:
        """Verify accreditation claims"""
        try:
            # Check UGC and AICTE databases
            ugc_data = self._fetch_ugc_data(college_name)
            aicte_data = self._fetch_aicte_data(college_name)
            
            # Extract accreditation from claim
            accreditations = []
            for acc in ["NAAC", "NBA", "AICTE", "UGC"]:
                if acc in claim:
                    accreditations.append(acc)
            
            verified_accreditations = []
            if ugc_data and "accreditation" in ugc_data:
                verified_accreditations.extend(ugc_data["accreditation"])
            if aicte_data and "accreditation" in aicte_data:
                verified_accreditations.extend(aicte_data["accreditation"])
            
            # Check if claimed accreditations match verified ones
            verified_count = sum(1 for acc in accreditations if acc in verified_accreditations)
            
            if verified_count == len(accreditations):
                return VerificationResult(
                    claim=claim,
                    verified=True,
                    confidence=0.95,
                    source="UGC/AICTE",
                    verification_date=datetime.now(),
                    notes=f"All accreditations verified: {', '.join(verified_accreditations)}"
                )
            elif verified_count > 0:
                return VerificationResult(
                    claim=claim,
                    verified=True,
                    confidence=0.7,
                    source="UGC/AICTE",
                    verification_date=datetime.now(),
                    notes=f"Partially verified: {verified_count}/{len(accreditations)} accreditations found"
                )
            else:
                return VerificationResult(
                    claim=claim,
                    verified=False,
                    confidence=0.8,
                    source="UGC/AICTE",
                    verification_date=datetime.now(),
                    notes="No matching accreditations found in official records"
                )
                
        except Exception as e:
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.0,
                source="verification_error",
                verification_date=datetime.now(),
                notes=f"Error during accreditation verification: {str(e)}"
            )
    
    def _verify_program_claim(self, claim: str, college_name: str) -> VerificationResult:
        """Verify program-related claims"""
        try:
            # Check AICTE and UGC program databases
            program_data = self._fetch_program_data(college_name)
            
            if program_data:
                # Extract program name and seats from claim
                import re
                program_match = re.search(r"Offers (.+?) with (\d+) seats", claim)
                if program_match:
                    program_name = program_match.group(1)
                    claimed_seats = int(program_match.group(2))
                    
                    # Check if program exists in official data
                    for program in program_data.get("programs", []):
                        if program_name.lower() in program.get("name", "").lower():
                            official_seats = program.get("seats", 0)
                            
                            # Allow some variance in seat numbers
                            if abs(claimed_seats - official_seats) <= 10:
                                return VerificationResult(
                                    claim=claim,
                                    verified=True,
                                    confidence=0.9,
                                    source="AICTE/UGC",
                                    verification_date=datetime.now(),
                                    notes=f"Program verified: {program_name} with {official_seats} seats"
                                )
            
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.6,
                source="AICTE/UGC",
                verification_date=datetime.now(),
                notes="Program not found in official records or seat count mismatch"
            )
            
        except Exception as e:
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.0,
                source="verification_error",
                verification_date=datetime.now(),
                notes=f"Error during program verification: {str(e)}"
            )
    
    def _verify_nirf_data(self, claim: str, college_name: str) -> VerificationResult:
        """Verify against NIRF data"""
        try:
            nirf_data = self._fetch_nirf_data(college_name)
            if nirf_data:
                return VerificationResult(
                    claim=claim,
                    verified=True,
                    confidence=0.8,
                    source="NIRF",
                    verification_date=datetime.now(),
                    notes="Data found in NIRF records"
                )
        except Exception:
            pass
        
        return VerificationResult(
            claim=claim,
            verified=False,
            confidence=0.0,
            source="NIRF",
            verification_date=datetime.now(),
            notes="Data not found in NIRF records"
        )
    
    def _verify_ugc_data(self, claim: str, college_name: str) -> VerificationResult:
        """Verify against UGC data"""
        try:
            ugc_data = self._fetch_ugc_data(college_name)
            if ugc_data:
                return VerificationResult(
                    claim=claim,
                    verified=True,
                    confidence=0.7,
                    source="UGC",
                    verification_date=datetime.now(),
                    notes="Data found in UGC records"
                )
        except Exception:
            pass
        
        return VerificationResult(
            claim=claim,
            verified=False,
            confidence=0.0,
            source="UGC",
            verification_date=datetime.now(),
            notes="Data not found in UGC records"
        )
    
    def _verify_aicte_data(self, claim: str, college_name: str) -> VerificationResult:
        """Verify against AICTE data"""
        try:
            aicte_data = self._fetch_aicte_data(college_name)
            if aicte_data:
                return VerificationResult(
                    claim=claim,
                    verified=True,
                    confidence=0.7,
                    source="AICTE",
                    verification_date=datetime.now(),
                    notes="Data found in AICTE records"
                )
        except Exception:
            pass
        
        return VerificationResult(
            claim=claim,
            verified=False,
            confidence=0.0,
            source="AICTE",
            verification_date=datetime.now(),
            notes="Data not found in AICTE records"
        )
    
    def _fetch_nirf_data(self, college_name: str) -> Optional[Dict[str, Any]]:
        """Fetch NIRF data for a college (simulated)"""
        # In a real implementation, you would make API calls to NIRF
        # For now, we'll return simulated data
        nirf_database = {
            "Indian Institute of Technology Delhi": {
                "ranking": 2,
                "placement": 98.3,
                "accreditation": ["NAAC A++", "NBA"]
            },
            "University of Delhi": {
                "ranking": 15,
                "placement": 84.0,
                "accreditation": ["NAAC A++"]
            },
            "Indian Institute of Science Bangalore": {
                "ranking": 1,
                "placement": 95.0,
                "accreditation": ["NAAC A++", "NBA"]
            }
        }
        
        return nirf_database.get(college_name)
    
    def _fetch_ugc_data(self, college_name: str) -> Optional[Dict[str, Any]]:
        """Fetch UGC data for a college (simulated)"""
        # Simulated UGC data
        ugc_database = {
            "Indian Institute of Technology Delhi": {
                "accreditation": ["NAAC A++"],
                "status": "recognized"
            },
            "University of Delhi": {
                "accreditation": ["NAAC A++"],
                "status": "recognized"
            },
            "Indian Institute of Science Bangalore": {
                "accreditation": ["NAAC A++"],
                "status": "recognized"
            }
        }
        
        return ugc_database.get(college_name)
    
    def _fetch_aicte_data(self, college_name: str) -> Optional[Dict[str, Any]]:
        """Fetch AICTE data for a college (simulated)"""
        # Simulated AICTE data
        aicte_database = {
            "Indian Institute of Technology Delhi": {
                "accreditation": ["NBA"],
                "programs": [
                    {"name": "Computer Science", "seats": 120},
                    {"name": "Electrical Engineering", "seats": 100}
                ]
            },
            "University of Delhi": {
                "accreditation": [],
                "programs": [
                    {"name": "Computer Science", "seats": 200},
                    {"name": "Commerce", "seats": 300}
                ]
            },
            "Indian Institute of Science Bangalore": {
                "accreditation": ["NBA"],
                "programs": [
                    {"name": "Research", "seats": 80}
                ]
            }
        }
        
        return aicte_database.get(college_name)
    
    def _fetch_program_data(self, college_name: str) -> Optional[Dict[str, Any]]:
        """Fetch program data for a college"""
        # Combine AICTE and UGC data
        aicte_data = self._fetch_aicte_data(college_name)
        ugc_data = self._fetch_ugc_data(college_name)
        
        if aicte_data or ugc_data:
            return {
                "programs": (aicte_data or {}).get("programs", []) + (ugc_data or {}).get("programs", []),
                "accreditation": (aicte_data or {}).get("accreditation", []) + (ugc_data or {}).get("accreditation", [])
            }
        
        return None
    
    def _is_cache_valid(self, cached_result: VerificationResult) -> bool:
        """Check if cached verification result is still valid"""
        # Cache valid for 24 hours
        cache_duration = 24 * 60 * 60  # 24 hours in seconds
        age = (datetime.now() - cached_result.verification_date).total_seconds()
        return age < cache_duration
