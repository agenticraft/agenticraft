"""SEO Specialist Agent - Simplified for AgentiCraft.

A specialized agent for search engine optimization focused on
practical SEO analysis and recommendations.
"""

from typing import Dict, List, Optional, Any
from agenticraft.core.agent import Agent, AgentConfig
from agenticraft.core.reasoning import ReasoningTrace, SimpleReasoning


class SEOSpecialist(Agent):
    """
    SEO specialist agent for content optimization and search visibility.
    
    Focuses on:
    - Keyword research and analysis
    - On-page SEO optimization
    - Content optimization for search
    - Technical SEO recommendations
    - Competitor analysis
    """
    
    def __init__(self, name: str = "SEO Specialist", **kwargs):
        config = AgentConfig(
            name=name,
            role="seo_specialist",
            specialty="search engine optimization",
            personality_traits={
                "analytical": 0.9,
                "detail_oriented": 0.9,
                "strategic": 0.8,
                "data_driven": 0.9,
                "creative": 0.6
            },
            **kwargs
        )
        super().__init__(config)
        
        # SEO knowledge base
        self.keyword_intent_patterns = {
            "informational": ["what", "how", "why", "when", "guide", "tutorial"],
            "transactional": ["buy", "purchase", "order", "price", "cost"],
            "navigational": ["login", "website", "contact", "location"],
            "commercial": ["best", "review", "comparison", "vs", "alternative"]
        }
    
    async def analyze_content(self, content: str, target_keywords: List[str]) -> Dict[str, Any]:
        """Analyze content for SEO optimization."""
        # Show reasoning process
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(f"Analyzing content for SEO with target keywords: {target_keywords}")
        
        # Basic content analysis
        word_count = len(content.split())
        trace.add_step("analysis", {"metric": "content_length", "value": f"{word_count} words"})
        
        # Keyword density analysis
        keyword_density = {}
        content_lower = content.lower()
        for keyword in target_keywords:
            count = content_lower.count(keyword.lower())
            density = (count / word_count) * 100 if word_count > 0 else 0
            keyword_density[keyword] = {
                "count": count,
                "density": round(density, 2)
            }
            trace.add_step("keyword_analysis", {
                "keyword": keyword,
                "count": count,
                "density": f"{density:.1f}%"
            })
        
        # Readability analysis (simplified)
        sentences = content.split('.')
        avg_sentence_length = word_count / len(sentences) if sentences else 0
        readability_score = 100 - (avg_sentence_length * 2)  # Simplified score
        
        trace.add_step("readability_analysis", {
            "score": f"{readability_score:.1f}/100"
        })
        
        # SEO recommendations
        recommendations = []
        
        # Keyword density recommendations
        for keyword, data in keyword_density.items():
            if data["density"] < 0.5:
                recommendations.append(f"Increase usage of '{keyword}' - currently too low at {data['density']}%")
            elif data["density"] > 3:
                recommendations.append(f"Reduce usage of '{keyword}' - currently too high at {data['density']}%")
        
        # Content length recommendations
        if word_count < 300:
            recommendations.append("Content is too short. Aim for at least 300 words for better SEO.")
        elif word_count < 600:
            recommendations.append("Consider expanding content to 600+ words for comprehensive coverage.")
        
        # Readability recommendations
        if readability_score < 60:
            recommendations.append("Improve readability by using shorter sentences and simpler words.")
        
        trace.complete({"result": "SEO analysis complete with actionable recommendations"})
        self.last_reasoning = trace
        
        return {
            "word_count": word_count,
            "keyword_density": keyword_density,
            "readability_score": round(readability_score, 1),
            "recommendations": recommendations,
            "seo_score": self._calculate_seo_score(keyword_density, word_count, readability_score),
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def suggest_keywords(self, topic: str, intent: str = "informational") -> Dict[str, Any]:
        """Suggest keywords based on topic and search intent."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(f"Generating keyword suggestions for topic: {topic}")
        
        # Identify search intent patterns
        patterns = self.keyword_intent_patterns.get(intent, [])
        trace.add_step("intent_analysis", {
            "intent": intent,
            "patterns": patterns
        })
        
        # Generate keyword suggestions
        primary_keywords = []
        long_tail_keywords = []
        questions = []
        
        # Primary keywords (simplified simulation)
        primary_keywords = [
            topic.lower(),
            f"{topic.lower()} guide",
            f"best {topic.lower()}",
            f"{topic.lower()} tips"
        ]
        
        # Long-tail keywords based on intent
        for pattern in patterns[:3]:
            long_tail_keywords.append(f"{pattern} {topic.lower()}")
            if pattern in ["what", "how", "why"]:
                questions.append(f"{pattern} is {topic}?")
        
        # Related keywords (simplified)
        related_keywords = [
            f"{topic} tools",
            f"{topic} strategies",
            f"{topic} examples",
            f"{topic} benefits"
        ]
        
        trace.add_step("keyword_generation", {
            "primary_count": len(primary_keywords),
            "long_tail_count": len(long_tail_keywords)
        })
        trace.complete({"result": "Keyword research complete with targeted suggestions"})
        
        self.last_reasoning = trace
        
        return {
            "primary_keywords": primary_keywords,
            "long_tail_keywords": long_tail_keywords,
            "questions": questions,
            "related_keywords": related_keywords,
            "search_intent": intent,
            "total_suggestions": len(primary_keywords) + len(long_tail_keywords) + len(related_keywords),
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def optimize_meta_tags(self, title: str, description: str, keywords: List[str]) -> Dict[str, Any]:
        """Optimize meta title and description for SEO."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace("Optimizing meta tags for search engines")
        
        optimized = {
            "title": title,
            "description": description,
            "issues": [],
            "suggestions": []
        }
        
        # Title optimization
        title_length = len(title)
        trace.add_step("title_analysis", {
            "length": f"{title_length} characters"
        })
        
        if title_length < 30:
            optimized["issues"].append("Title too short")
            optimized["suggestions"].append("Expand title to 30-60 characters")
        elif title_length > 60:
            optimized["issues"].append("Title too long")
            optimized["suggestions"].append("Shorten title to under 60 characters")
            optimized["title"] = title[:57] + "..."
        
        # Check keyword presence in title
        title_lower = title.lower()
        keywords_in_title = [kw for kw in keywords if kw.lower() in title_lower]
        if not keywords_in_title and keywords:
            optimized["suggestions"].append(f"Include primary keyword '{keywords[0]}' in title")
            optimized["title"] = f"{keywords[0].title()} - {title}"
        
        # Description optimization
        desc_length = len(description)
        trace.add_step("description_analysis", {
            "length": f"{desc_length} characters"
        })
        
        if desc_length < 120:
            optimized["issues"].append("Description too short")
            optimized["suggestions"].append("Expand description to 120-160 characters")
        elif desc_length > 160:
            optimized["issues"].append("Description too long")
            optimized["suggestions"].append("Shorten description to under 160 characters")
            optimized["description"] = description[:157] + "..."
        
        # Check keyword presence in description
        desc_lower = description.lower()
        keywords_in_desc = [kw for kw in keywords if kw.lower() in desc_lower]
        if not keywords_in_desc and keywords:
            optimized["suggestions"].append(f"Include keywords in description")
        
        trace.complete({"result": f"Meta tags optimized with {len(optimized['suggestions'])} suggestions"})
        self.last_reasoning = trace
        
        return {
            "optimized": optimized,
            "seo_score": self._calculate_meta_score(optimized),
            "reasoning": reasoning.format_trace(trace)
        }
    
    async def analyze_competitors(self, topic: str, competitors: List[str]) -> Dict[str, Any]:
        """Analyze competitor SEO strategies (simplified)."""
        reasoning = SimpleReasoning()
        trace = reasoning.start_trace(f"Analyzing {len(competitors)} competitors for topic: {topic}")
        
        # Simulated competitor analysis
        analysis = {}
        opportunities = []
        
        for competitor in competitors:
            trace.add_step("competitor_analysis", {
                "competitor": competitor
            })
            
            # Simulated metrics
            analysis[competitor] = {
                "estimated_traffic": len(competitor) * 1000,  # Simplified
                "content_count": len(competitor) * 10,
                "avg_content_length": 800 + (len(competitor) * 50),
                "strengths": [
                    "Regular content updates",
                    "Strong keyword targeting",
                    "Good site structure"
                ][:len(competitor) % 3 + 1],
                "weaknesses": [
                    "Limited long-form content",
                    "Poor mobile optimization",
                    "Slow page speed"
                ][:len(competitor) % 3 + 1]
            }
        
        # Identify opportunities
        avg_content_length = sum(a["avg_content_length"] for a in analysis.values()) / len(analysis)
        if avg_content_length < 1000:
            opportunities.append("Create comprehensive long-form content (1500+ words)")
        
        opportunities.extend([
            "Target underserved long-tail keywords",
            "Improve page load speed for better rankings",
            "Build high-quality backlinks from relevant sites"
        ])
        
        trace.complete({"result": f"Competitor analysis complete with {len(opportunities)} opportunities identified"})
        self.last_reasoning = trace
        
        return {
            "competitor_analysis": analysis,
            "opportunities": opportunities,
            "recommendations": [
                "Focus on content gaps not covered by competitors",
                "Improve technical SEO to gain competitive advantage",
                "Create more comprehensive content than competitors"
            ],
            "reasoning": reasoning.format_trace(trace)
        }
    
    def _calculate_seo_score(self, keyword_density: Dict, word_count: int, readability: float) -> float:
        """Calculate overall SEO score."""
        score = 50.0  # Base score
        
        # Word count score (max 20 points)
        if word_count >= 600:
            score += 20
        elif word_count >= 300:
            score += 10
        
        # Keyword density score (max 20 points)
        optimal_densities = [d["density"] for d in keyword_density.values() if 0.5 <= d["density"] <= 2.5]
        if optimal_densities:
            score += (len(optimal_densities) / len(keyword_density)) * 20
        
        # Readability score (max 10 points)
        score += (readability / 100) * 10
        
        return min(100, round(score, 1))
    
    def _calculate_meta_score(self, optimized: Dict) -> float:
        """Calculate meta tags SEO score."""
        score = 100.0
        
        # Deduct points for issues
        score -= len(optimized["issues"]) * 15
        
        # Deduct points for missing optimizations
        score -= len(optimized["suggestions"]) * 10
        
        return max(0, round(score, 1))
