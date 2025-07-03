"""Response Analyzer for AI Service.

This module analyzes AI responses for quality, relevance, and usefulness,
providing feedback for continuous improvement of the AI service.
"""

import re
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from .base_service import AIRequest, AIResponse, ResponseQuality


class AnalysisMetric(Enum):
    """Metrics for response analysis."""
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    ACCURACY = "accuracy"
    USEFULNESS = "usefulness"
    COHERENCE = "coherence"
    SPECIFICITY = "specificity"
    ACTIONABILITY = "actionability"


class QualityIssue(Enum):
    """Types of quality issues that can be detected."""
    TOO_GENERIC = "too_generic"
    INCOMPLETE_RESPONSE = "incomplete_response"
    OFF_TOPIC = "off_topic"
    UNCLEAR_LANGUAGE = "unclear_language"
    MISSING_CONTEXT = "missing_context"
    INCONSISTENT_TONE = "inconsistent_tone"
    POOR_STRUCTURE = "poor_structure"
    INSUFFICIENT_DETAIL = "insufficient_detail"
    EXCESSIVE_LENGTH = "excessive_length"
    FACTUAL_CONCERNS = "factual_concerns"


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment of an AI response."""
    overall_score: float  # 0.0 to 1.0
    quality: ResponseQuality
    confidence: float
    metric_scores: Dict[AnalysisMetric, float]
    detected_issues: List[QualityIssue]
    strengths: List[str]
    improvement_suggestions: List[str]
    analysis_notes: List[str]
    processing_time: float
    

@dataclass
class ResponsePattern:
    """Pattern detected in responses for learning."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    quality_impact: float
    examples: List[str]
    first_seen: datetime
    last_seen: datetime


@dataclass
class ImprovementRecommendation:
    """Recommendation for improving response quality."""
    recommendation_id: str
    category: str
    priority: int  # 1-5, 1 being highest
    description: str
    expected_impact: float
    implementation_effort: str  # low, medium, high
    related_metrics: List[AnalysisMetric]
    examples: List[str]


class ResponseAnalyzer:
    """Analyzes AI responses for quality and provides improvement feedback."""
    
    def __init__(self):
        """Initialize the response analyzer."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Analysis configuration
        self.quality_thresholds = {
            ResponseQuality.EXCELLENT: 0.9,
            ResponseQuality.GOOD: 0.7,
            ResponseQuality.ACCEPTABLE: 0.5,
            ResponseQuality.POOR: 0.0
        }
        
        # Metric weights for overall score calculation
        self.metric_weights = {
            AnalysisMetric.RELEVANCE: 0.25,
            AnalysisMetric.COMPLETENESS: 0.20,
            AnalysisMetric.CLARITY: 0.15,
            AnalysisMetric.USEFULNESS: 0.15,
            AnalysisMetric.ACCURACY: 0.10,
            AnalysisMetric.COHERENCE: 0.08,
            AnalysisMetric.SPECIFICITY: 0.04,
            AnalysisMetric.ACTIONABILITY: 0.03
        }
        
        # Pattern detection
        self.detected_patterns: Dict[str, ResponsePattern] = {}
        self.pattern_detection_rules = self._load_pattern_rules()
        
        # Quality analysis rules
        self.quality_rules = self._load_quality_rules()
        
        # Performance tracking
        self.analysis_history: List[QualityAssessment] = []
        self.improvement_recommendations: List[ImprovementRecommendation] = []
        
        # Statistics
        self.analysis_stats = {
            "total_analyses": 0,
            "average_quality_score": 0.0,
            "quality_distribution": {q.value: 0 for q in ResponseQuality},
            "common_issues": {issue.value: 0 for issue in QualityIssue},
            "metric_averages": {metric.value: 0.0 for metric in AnalysisMetric}
        }
    
    def _load_pattern_rules(self) -> Dict[str, Any]:
        """Load pattern detection rules.
        
        Returns:
            Dict[str, Any]: Pattern detection rules
        """
        return {
            "generic_responses": {
                "patterns": [
                    r"\b(generally|usually|typically|often|sometimes)\b",
                    r"\b(it depends|varies|may vary)\b",
                    r"\b(consider|might want to|could try)\b"
                ],
                "threshold": 3,
                "quality_impact": -0.2
            },
            "incomplete_responses": {
                "patterns": [
                    r"\.\.\.$",
                    r"\b(etc|and so on|among others)\b",
                    r"\b(more details|further information)\b"
                ],
                "threshold": 2,
                "quality_impact": -0.3
            },
            "excellent_structure": {
                "patterns": [
                    r"^\d+\.",  # Numbered lists
                    r"^[•\-\*]",  # Bullet points
                    r"\*\*[^\*]+\*\*",  # Bold headers
                    r"#{1,6}\s",  # Markdown headers
                ],
                "threshold": 2,
                "quality_impact": 0.1
            },
            "actionable_content": {
                "patterns": [
                    r"\b(start by|first step|begin with)\b",
                    r"\b(next|then|after that|following)\b",
                    r"\b(action|task|step|do|implement)\b"
                ],
                "threshold": 3,
                "quality_impact": 0.15
            }
        }
    
    def _load_quality_rules(self) -> Dict[str, Any]:
        """Load quality analysis rules.
        
        Returns:
            Dict[str, Any]: Quality analysis rules
        """
        return {
            "length_analysis": {
                "too_short_threshold": 50,  # characters
                "too_long_threshold": 5000,  # characters
                "optimal_range": (200, 2000)
            },
            "structure_indicators": {
                "good_structure": [
                    r"\n\n",  # Paragraph breaks
                    r"^\d+\.",  # Numbered items
                    r"^[•\-\*]",  # Bullet points
                    r"\*\*[^\*]+\*\*"  # Bold text
                ],
                "poor_structure": [
                    r"^.{500,}$",  # Very long single line
                    r"[.!?]{3,}"  # Multiple punctuation
                ]
            },
            "clarity_indicators": {
                "clear_language": [
                    r"\b(specifically|exactly|precisely)\b",
                    r"\b(for example|such as|including)\b",
                    r"\b(first|second|third|finally)\b"
                ],
                "unclear_language": [
                    r"\b(somewhat|rather|quite|fairly)\b",
                    r"\b(thing|stuff|things|items)\b",
                    r"\b(maybe|perhaps|possibly)\b"
                ]
            },
            "completeness_indicators": {
                "complete_response": [
                    r"\b(in summary|to conclude|in conclusion)\b",
                    r"\b(steps?|process|method|approach)\b",
                    r"\b(result|outcome|solution)\b"
                ],
                "incomplete_response": [
                    r"\b(more research|additional information)\b",
                    r"\b(depends on|varies by)\b",
                    r"\.\.\.$"
                ]
            }
        }
    
    async def analyze(
        self,
        response: AIResponse,
        request: AIRequest
    ) -> QualityAssessment:
        """Analyze an AI response for quality and provide assessment.
        
        Args:
            response: The AI response to analyze
            request: The original request for context
            
        Returns:
            QualityAssessment: Comprehensive quality assessment
        """
        start_time = datetime.now()
        
        try:
            # Analyze individual metrics
            metric_scores = await self._analyze_metrics(response, request)
            
            # Detect quality issues
            detected_issues = self._detect_quality_issues(response, request)
            
            # Identify strengths
            strengths = self._identify_strengths(response, metric_scores)
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                response, detected_issues, metric_scores
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(metric_scores)
            
            # Determine quality level
            quality = self._determine_quality_level(overall_score)
            
            # Calculate confidence in assessment
            confidence = self._calculate_assessment_confidence(
                response, metric_scores, detected_issues
            )
            
            # Detect patterns
            await self._detect_and_update_patterns(response, quality)
            
            # Create assessment
            assessment = QualityAssessment(
                overall_score=overall_score,
                quality=quality,
                confidence=confidence,
                metric_scores=metric_scores,
                detected_issues=detected_issues,
                strengths=strengths,
                improvement_suggestions=improvement_suggestions,
                analysis_notes=self._generate_analysis_notes(response, request),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
            
            # Update statistics
            self._update_analysis_stats(assessment)
            
            # Store in history (keep last 1000)
            self.analysis_history.append(assessment)
            if len(self.analysis_history) > 1000:
                self.analysis_history = self.analysis_history[-1000:]
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error analyzing response: {e}")
            
            # Return basic assessment on error
            return QualityAssessment(
                overall_score=0.5,
                quality=ResponseQuality.ACCEPTABLE,
                confidence=0.3,
                metric_scores={metric: 0.5 for metric in AnalysisMetric},
                detected_issues=[QualityIssue.FACTUAL_CONCERNS],
                strengths=[],
                improvement_suggestions=["Analysis failed - manual review recommended"],
                analysis_notes=[f"Analysis error: {str(e)}"],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _analyze_metrics(
        self,
        response: AIResponse,
        request: AIRequest
    ) -> Dict[AnalysisMetric, float]:
        """Analyze individual quality metrics.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            Dict[AnalysisMetric, float]: Metric scores
        """
        scores = {}
        
        # Relevance analysis
        scores[AnalysisMetric.RELEVANCE] = self._analyze_relevance(response, request)
        
        # Completeness analysis
        scores[AnalysisMetric.COMPLETENESS] = self._analyze_completeness(response, request)
        
        # Clarity analysis
        scores[AnalysisMetric.CLARITY] = self._analyze_clarity(response)
        
        # Accuracy analysis (basic heuristics)
        scores[AnalysisMetric.ACCURACY] = self._analyze_accuracy(response)
        
        # Usefulness analysis
        scores[AnalysisMetric.USEFULNESS] = self._analyze_usefulness(response, request)
        
        # Coherence analysis
        scores[AnalysisMetric.COHERENCE] = self._analyze_coherence(response)
        
        # Specificity analysis
        scores[AnalysisMetric.SPECIFICITY] = self._analyze_specificity(response)
        
        # Actionability analysis
        scores[AnalysisMetric.ACTIONABILITY] = self._analyze_actionability(response, request)
        
        return scores
    
    def _analyze_relevance(self, response: AIResponse, request: AIRequest) -> float:
        """Analyze how relevant the response is to the request.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        # Extract key terms from request
        request_terms = set(re.findall(r'\b\w{3,}\b', request.prompt.lower()))
        response_terms = set(re.findall(r'\b\w{3,}\b', response.content.lower()))
        
        # Calculate term overlap
        if not request_terms:
            return 0.5  # Neutral if no terms to compare
        
        overlap = len(request_terms.intersection(response_terms))
        relevance_score = min(1.0, overlap / len(request_terms))
        
        # Boost score if response addresses the tool/operation specifically
        if request.tool_name.lower() in response.content.lower():
            relevance_score = min(1.0, relevance_score + 0.1)
        
        if request.operation.lower() in response.content.lower():
            relevance_score = min(1.0, relevance_score + 0.1)
        
        return relevance_score
    
    def _analyze_completeness(self, response: AIResponse, request: AIRequest) -> float:
        """Analyze how complete the response is.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            float: Completeness score (0.0 to 1.0)
        """
        content = response.content
        score = 0.5  # Base score
        
        # Check for completion indicators
        complete_patterns = self.quality_rules["completeness_indicators"]["complete_response"]
        incomplete_patterns = self.quality_rules["completeness_indicators"]["incomplete_response"]
        
        complete_matches = sum(1 for pattern in complete_patterns if re.search(pattern, content, re.IGNORECASE))
        incomplete_matches = sum(1 for pattern in incomplete_patterns if re.search(pattern, content, re.IGNORECASE))
        
        # Adjust score based on patterns
        score += complete_matches * 0.1
        score -= incomplete_matches * 0.15
        
        # Length-based assessment
        length = len(content)
        optimal_min, optimal_max = self.quality_rules["length_analysis"]["optimal_range"]
        
        if optimal_min <= length <= optimal_max:
            score += 0.1
        elif length < optimal_min:
            score -= 0.2
        elif length > optimal_max * 2:
            score -= 0.1
        
        # Check if response ends abruptly
        if content.endswith("...") or content.endswith("etc."):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _analyze_clarity(self, response: AIResponse) -> float:
        """Analyze how clear and understandable the response is.
        
        Args:
            response: AI response
            
        Returns:
            float: Clarity score (0.0 to 1.0)
        """
        content = response.content
        score = 0.5  # Base score
        
        # Check for clear language indicators
        clear_patterns = self.quality_rules["clarity_indicators"]["clear_language"]
        unclear_patterns = self.quality_rules["clarity_indicators"]["unclear_language"]
        
        clear_matches = sum(1 for pattern in clear_patterns if re.search(pattern, content, re.IGNORECASE))
        unclear_matches = sum(1 for pattern in unclear_patterns if re.search(pattern, content, re.IGNORECASE))
        
        score += clear_matches * 0.05
        score -= unclear_matches * 0.1
        
        # Sentence length analysis
        sentences = re.split(r'[.!?]+', content)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            
            # Optimal sentence length is 15-25 words
            if 15 <= avg_sentence_length <= 25:
                score += 0.1
            elif avg_sentence_length > 40:
                score -= 0.2
            elif avg_sentence_length < 5:
                score -= 0.1
        
        # Structure analysis
        good_structure = self.quality_rules["structure_indicators"]["good_structure"]
        structure_matches = sum(1 for pattern in good_structure if re.search(pattern, content, re.MULTILINE))
        
        if structure_matches >= 2:
            score += 0.15
        
        return max(0.0, min(1.0, score))
    
    def _analyze_accuracy(self, response: AIResponse) -> float:
        """Analyze potential accuracy issues (basic heuristics).
        
        Args:
            response: AI response
            
        Returns:
            float: Accuracy score (0.0 to 1.0)
        """
        content = response.content
        score = 0.8  # Start with high confidence
        
        # Check for uncertainty indicators
        uncertainty_patterns = [
            r"\b(I think|I believe|I assume|probably|likely)\b",
            r"\b(not sure|uncertain|unclear|might be wrong)\b",
            r"\b(disclaimer|may not be accurate)\b"
        ]
        
        uncertainty_matches = sum(1 for pattern in uncertainty_patterns if re.search(pattern, content, re.IGNORECASE))
        score -= uncertainty_matches * 0.1
        
        # Check for contradictions (simple detection)
        contradiction_patterns = [
            r"\b(however|but|although|despite)\b.*\b(however|but|although|despite)\b",
            r"\b(yes|true|correct)\b.*\b(no|false|incorrect)\b",
            r"\b(always|never)\b.*\b(sometimes|occasionally)\b"
        ]
        
        contradiction_matches = sum(1 for pattern in contradiction_patterns if re.search(pattern, content, re.IGNORECASE))
        score -= contradiction_matches * 0.2
        
        # Boost score for confident, specific statements
        confidence_patterns = [
            r"\b(specifically|exactly|precisely|definitely)\b",
            r"\b(research shows|studies indicate|proven)\b",
            r"\b(according to|based on|evidence suggests)\b"
        ]
        
        confidence_matches = sum(1 for pattern in confidence_patterns if re.search(pattern, content, re.IGNORECASE))
        score += confidence_matches * 0.05
        
        return max(0.0, min(1.0, score))
    
    def _analyze_usefulness(self, response: AIResponse, request: AIRequest) -> float:
        """Analyze how useful the response is for the user.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            float: Usefulness score (0.0 to 1.0)
        """
        content = response.content
        score = 0.5  # Base score
        
        # Check for practical elements
        practical_patterns = [
            r"\b(step|steps|process|method|technique)\b",
            r"\b(example|instance|case|scenario)\b",
            r"\b(tip|advice|recommendation|suggestion)\b",
            r"\b(tool|resource|link|reference)\b"
        ]
        
        practical_matches = sum(1 for pattern in practical_patterns if re.search(pattern, content, re.IGNORECASE))
        score += practical_matches * 0.08
        
        # Check for actionable content
        actionable_patterns = self.pattern_detection_rules["actionable_content"]["patterns"]
        actionable_matches = sum(1 for pattern in actionable_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if actionable_matches >= 3:
            score += 0.2
        
        # Penalize overly generic responses
        generic_patterns = self.pattern_detection_rules["generic_responses"]["patterns"]
        generic_matches = sum(1 for pattern in generic_patterns if re.search(pattern, content, re.IGNORECASE))
        
        if generic_matches >= 3:
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _analyze_coherence(self, response: AIResponse) -> float:
        """Analyze logical flow and coherence of the response.
        
        Args:
            response: AI response
            
        Returns:
            float: Coherence score (0.0 to 1.0)
        """
        content = response.content
        score = 0.7  # Start with good assumption
        
        # Check for transition words and logical flow
        transition_patterns = [
            r"\b(first|second|third|next|then|finally)\b",
            r"\b(however|therefore|consequently|as a result)\b",
            r"\b(furthermore|additionally|moreover|also)\b",
            r"\b(in contrast|on the other hand|alternatively)\b"
        ]
        
        transition_matches = sum(1 for pattern in transition_patterns if re.search(pattern, content, re.IGNORECASE))
        score += min(0.2, transition_matches * 0.05)
        
        # Check for topic consistency
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) > 3:
            # Simple coherence check: look for repeated key terms
            all_words = re.findall(r'\b\w{4,}\b', content.lower())
            word_freq = {}
            for word in all_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # If top words appear throughout, it suggests coherence
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            if top_words and top_words[0][1] >= len(sentences) * 0.3:
                score += 0.1
        
        # Penalize abrupt topic changes (heuristic)
        if re.search(r'\b(by the way|incidentally|unrelated)\b', content, re.IGNORECASE):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _analyze_specificity(self, response: AIResponse) -> float:
        """Analyze how specific and detailed the response is.
        
        Args:
            response: AI response
            
        Returns:
            float: Specificity score (0.0 to 1.0)
        """
        content = response.content
        score = 0.5  # Base score
        
        # Check for specific indicators
        specific_patterns = [
            r"\b\d+\b",  # Numbers
            r"\b(exactly|specifically|precisely)\b",
            r"\b(for example|such as|including)\b",
            r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  # Proper nouns
            r"\b\w+\.\w+\b"  # Technical terms or URLs
        ]
        
        specific_matches = sum(1 for pattern in specific_patterns if re.search(pattern, content))
        score += min(0.3, specific_matches * 0.05)
        
        # Penalize vague language
        vague_patterns = [
            r"\b(thing|stuff|something|anything)\b",
            r"\b(some|many|few|several)\b",
            r"\b(generally|usually|often|sometimes)\b"
        ]
        
        vague_matches = sum(1 for pattern in vague_patterns if re.search(pattern, content, re.IGNORECASE))
        score -= vague_matches * 0.08
        
        return max(0.0, min(1.0, score))
    
    def _analyze_actionability(self, response: AIResponse, request: AIRequest) -> float:
        """Analyze how actionable the response is.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            float: Actionability score (0.0 to 1.0)
        """
        content = response.content
        score = 0.3  # Low base score
        
        # Check for action-oriented language
        action_patterns = [
            r"\b(start|begin|create|make|do|implement|execute)\b",
            r"\b(step \d+|first step|next step)\b",
            r"\b(action|task|activity|exercise)\b",
            r"\b(click|select|choose|enter|type)\b"
        ]
        
        action_matches = sum(1 for pattern in action_patterns if re.search(pattern, content, re.IGNORECASE))
        score += min(0.5, action_matches * 0.1)
        
        # Check for imperative mood (commands)
        imperative_patterns = [
            r"^[A-Z][a-z]+ (the|your|a)\b",  # "Start the...", "Create a..."
            r"\n[A-Z][a-z]+ (the|your|a)\b"   # Same at line start
        ]
        
        imperative_matches = sum(1 for pattern in imperative_patterns if re.search(pattern, content, re.MULTILINE))
        score += min(0.3, imperative_matches * 0.1)
        
        # Boost for numbered steps or bullet points
        if re.search(r'^\d+\.', content, re.MULTILINE) or re.search(r'^[•\-\*]', content, re.MULTILINE):
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _detect_quality_issues(self, response: AIResponse, request: AIRequest) -> List[QualityIssue]:
        """Detect specific quality issues in the response.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            List[QualityIssue]: Detected quality issues
        """
        issues = []
        content = response.content
        
        # Check length issues
        length = len(content)
        if length < self.quality_rules["length_analysis"]["too_short_threshold"]:
            issues.append(QualityIssue.INCOMPLETE_RESPONSE)
        elif length > self.quality_rules["length_analysis"]["too_long_threshold"]:
            issues.append(QualityIssue.EXCESSIVE_LENGTH)
        
        # Check for generic responses
        generic_patterns = self.pattern_detection_rules["generic_responses"]["patterns"]
        generic_count = sum(1 for pattern in generic_patterns if re.search(pattern, content, re.IGNORECASE))
        if generic_count >= self.pattern_detection_rules["generic_responses"]["threshold"]:
            issues.append(QualityIssue.TOO_GENERIC)
        
        # Check for incomplete responses
        incomplete_patterns = self.pattern_detection_rules["incomplete_responses"]["patterns"]
        incomplete_count = sum(1 for pattern in incomplete_patterns if re.search(pattern, content, re.IGNORECASE))
        if incomplete_count >= self.pattern_detection_rules["incomplete_responses"]["threshold"]:
            issues.append(QualityIssue.INCOMPLETE_RESPONSE)
        
        # Check for poor structure
        poor_structure = self.quality_rules["structure_indicators"]["poor_structure"]
        if any(re.search(pattern, content, re.MULTILINE) for pattern in poor_structure):
            issues.append(QualityIssue.POOR_STRUCTURE)
        
        # Check for unclear language
        unclear_patterns = self.quality_rules["clarity_indicators"]["unclear_language"]
        unclear_count = sum(1 for pattern in unclear_patterns if re.search(pattern, content, re.IGNORECASE))
        if unclear_count >= 5:
            issues.append(QualityIssue.UNCLEAR_LANGUAGE)
        
        # Check relevance to request
        request_terms = set(re.findall(r'\b\w{3,}\b', request.prompt.lower()))
        response_terms = set(re.findall(r'\b\w{3,}\b', content.lower()))
        if request_terms and len(request_terms.intersection(response_terms)) / len(request_terms) < 0.2:
            issues.append(QualityIssue.OFF_TOPIC)
        
        return issues
    
    def _identify_strengths(self, response: AIResponse, metric_scores: Dict[AnalysisMetric, float]) -> List[str]:
        """Identify strengths in the response.
        
        Args:
            response: AI response
            metric_scores: Calculated metric scores
            
        Returns:
            List[str]: Identified strengths
        """
        strengths = []
        
        # Check high-scoring metrics
        for metric, score in metric_scores.items():
            if score >= 0.8:
                if metric == AnalysisMetric.RELEVANCE:
                    strengths.append("Highly relevant to the request")
                elif metric == AnalysisMetric.CLARITY:
                    strengths.append("Clear and easy to understand")
                elif metric == AnalysisMetric.COMPLETENESS:
                    strengths.append("Comprehensive and complete response")
                elif metric == AnalysisMetric.ACTIONABILITY:
                    strengths.append("Provides actionable steps and guidance")
                elif metric == AnalysisMetric.SPECIFICITY:
                    strengths.append("Specific and detailed information")
        
        # Check for good structure
        content = response.content
        if re.search(r'^\d+\.', content, re.MULTILINE):
            strengths.append("Well-structured with numbered points")
        elif re.search(r'^[•\-\*]', content, re.MULTILINE):
            strengths.append("Well-organized with bullet points")
        
        # Check for examples
        if re.search(r'\b(for example|such as|instance)\b', content, re.IGNORECASE):
            strengths.append("Includes helpful examples")
        
        return strengths
    
    def _generate_improvement_suggestions(
        self,
        response: AIResponse,
        issues: List[QualityIssue],
        metric_scores: Dict[AnalysisMetric, float]
    ) -> List[str]:
        """Generate specific improvement suggestions.
        
        Args:
            response: AI response
            issues: Detected quality issues
            metric_scores: Metric scores
            
        Returns:
            List[str]: Improvement suggestions
        """
        suggestions = []
        
        # Address specific issues
        for issue in issues:
            if issue == QualityIssue.TOO_GENERIC:
                suggestions.append("Provide more specific, concrete examples and details")
            elif issue == QualityIssue.INCOMPLETE_RESPONSE:
                suggestions.append("Expand the response to fully address all aspects of the request")
            elif issue == QualityIssue.UNCLEAR_LANGUAGE:
                suggestions.append("Use clearer, more direct language and avoid ambiguous terms")
            elif issue == QualityIssue.POOR_STRUCTURE:
                suggestions.append("Improve organization with clear headings, bullet points, or numbered lists")
            elif issue == QualityIssue.OFF_TOPIC:
                suggestions.append("Focus more directly on the specific request and requirements")
        
        # Address low-scoring metrics
        for metric, score in metric_scores.items():
            if score < 0.5:
                if metric == AnalysisMetric.ACTIONABILITY:
                    suggestions.append("Include more specific, actionable steps and instructions")
                elif metric == AnalysisMetric.SPECIFICITY:
                    suggestions.append("Add more specific details, examples, and concrete information")
                elif metric == AnalysisMetric.COMPLETENESS:
                    suggestions.append("Ensure all aspects of the request are thoroughly addressed")
        
        return list(set(suggestions))  # Remove duplicates
    
    def _generate_analysis_notes(self, response: AIResponse, request: AIRequest) -> List[str]:
        """Generate analysis notes for debugging and improvement.
        
        Args:
            response: AI response
            request: Original request
            
        Returns:
            List[str]: Analysis notes
        """
        notes = []
        
        # Basic statistics
        notes.append(f"Response length: {len(response.content)} characters")
        notes.append(f"Word count: {len(response.content.split())}")
        notes.append(f"Sentence count: {len(re.split(r'[.!?]+', response.content))}")
        
        # Provider information
        notes.append(f"AI Provider: {response.provider.value}")
        notes.append(f"Tokens used: {response.tokens_used}")
        
        # Request context
        notes.append(f"Tool: {request.tool_name}")
        notes.append(f"Operation: {request.operation}")
        
        return notes
    
    def _calculate_overall_score(self, metric_scores: Dict[AnalysisMetric, float]) -> float:
        """Calculate overall quality score from individual metrics.
        
        Args:
            metric_scores: Individual metric scores
            
        Returns:
            float: Overall quality score
        """
        weighted_sum = sum(
            score * self.metric_weights[metric]
            for metric, score in metric_scores.items()
        )
        
        return min(1.0, max(0.0, weighted_sum))
    
    def _determine_quality_level(self, overall_score: float) -> ResponseQuality:
        """Determine quality level from overall score.
        
        Args:
            overall_score: Overall quality score
            
        Returns:
            ResponseQuality: Quality level
        """
        for quality, threshold in sorted(self.quality_thresholds.items(), key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                return quality
        
        return ResponseQuality.POOR
    
    def _calculate_assessment_confidence(self, response: AIResponse, metric_scores: Dict[AnalysisMetric, float], issues: List[QualityIssue]) -> float:
        """Calculate confidence in the quality assessment.
        
        Args:
            response: AI response
            metric_scores: Metric scores
            issues: Detected issues
            
        Returns:
            float: Confidence score
        """
        base_confidence = 0.7
        
        # Higher confidence for longer responses (more data to analyze)
        length_factor = min(0.2, len(response.content) / 1000)
        
        # Lower confidence if metrics vary widely
        score_variance = statistics.variance(metric_scores.values()) if len(metric_scores) > 1 else 0
        variance_penalty = min(0.3, score_variance * 2)
        
        # Higher confidence if clear issues are detected
        issue_bonus = min(0.1, len(issues) * 0.02)
        
        confidence = base_confidence + length_factor - variance_penalty + issue_bonus
        return max(0.1, min(1.0, confidence))
    
    async def _detect_and_update_patterns(self, response: AIResponse, quality: ResponseQuality):
        """Detect patterns in responses and update pattern database.
        
        Args:
            response: AI response
            quality: Response quality
        """
        # This is a simplified pattern detection
        # In a full implementation, this would use more sophisticated NLP
        
        content = response.content.lower()
        
        # Check for known patterns
        for pattern_name, rule in self.pattern_detection_rules.items():
            pattern_count = sum(1 for pattern in rule["patterns"] if re.search(pattern, content, re.IGNORECASE))
            
            if pattern_count >= rule.get("threshold", 1):
                pattern_id = f"{pattern_name}_{response.provider.value}"
                
                if pattern_id in self.detected_patterns:
                    # Update existing pattern
                    pattern = self.detected_patterns[pattern_id]
                    pattern.frequency += 1
                    pattern.last_seen = datetime.now()
                    
                    # Update quality impact based on recent observations
                    if quality in [ResponseQuality.EXCELLENT, ResponseQuality.GOOD]:
                        pattern.quality_impact = (pattern.quality_impact + 0.1) / 2
                    else:
                        pattern.quality_impact = (pattern.quality_impact - 0.1) / 2
                else:
                    # Create new pattern
                    self.detected_patterns[pattern_id] = ResponsePattern(
                        pattern_id=pattern_id,
                        pattern_type=pattern_name,
                        description=f"Pattern: {pattern_name} detected in {response.provider.value} responses",
                        frequency=1,
                        quality_impact=rule.get("quality_impact", 0.0),
                        examples=[content[:200]],
                        first_seen=datetime.now(),
                        last_seen=datetime.now()
                    )
    
    def _update_analysis_stats(self, assessment: QualityAssessment):
        """Update analysis statistics.
        
        Args:
            assessment: Quality assessment
        """
        self.analysis_stats["total_analyses"] += 1
        
        # Update quality distribution
        self.analysis_stats["quality_distribution"][assessment.quality.value] += 1
        
        # Update average quality score
        total = self.analysis_stats["total_analyses"]
        current_avg = self.analysis_stats["average_quality_score"]
        new_avg = ((current_avg * (total - 1)) + assessment.overall_score) / total
        self.analysis_stats["average_quality_score"] = new_avg
        
        # Update issue counts
        for issue in assessment.detected_issues:
            self.analysis_stats["common_issues"][issue.value] += 1
        
        # Update metric averages
        for metric, score in assessment.metric_scores.items():
            current_avg = self.analysis_stats["metric_averages"][metric.value]
            new_avg = ((current_avg * (total - 1)) + score) / total
            self.analysis_stats["metric_averages"][metric.value] = new_avg
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis statistics.
        
        Returns:
            Dict[str, Any]: Analysis statistics
        """
        return self.analysis_stats.copy()
    
    def get_detected_patterns(self) -> List[ResponsePattern]:
        """Get detected response patterns.
        
        Returns:
            List[ResponsePattern]: Detected patterns
        """
        return list(self.detected_patterns.values())
    
    def get_improvement_recommendations(self) -> List[ImprovementRecommendation]:
        """Get improvement recommendations based on analysis history.
        
        Returns:
            List[ImprovementRecommendation]: Improvement recommendations
        """
        # This would generate recommendations based on patterns and statistics
        # For now, return basic recommendations
        recommendations = []
        
        # Analyze common issues
        total_analyses = self.analysis_stats["total_analyses"]
        if total_analyses > 10:
            for issue, count in self.analysis_stats["common_issues"].items():
                if count / total_analyses > 0.3:  # Issue appears in >30% of responses
                    rec_id = f"improve_{issue}"
                    recommendations.append(ImprovementRecommendation(
                        recommendation_id=rec_id,
                        category="quality_improvement",
                        priority=1 if count / total_analyses > 0.5 else 2,
                        description=f"Address frequent {issue.replace('_', ' ')} issues",
                        expected_impact=0.2,
                        implementation_effort="medium",
                        related_metrics=[AnalysisMetric.COMPLETENESS, AnalysisMetric.CLARITY],
                        examples=[]
                    ))
        
        return recommendations