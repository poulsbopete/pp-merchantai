"""
LLM Agent for PayPal Merchant Location Resolution
This module provides an AI agent that can automatically resolve missing city/country information
for merchants based on available data and context.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import hashlib
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

class LocationResolution(BaseModel):
    """Model for location resolution results"""
    merchant_id: str
    merchant_name: str
    original_location: Dict[str, str]
    resolved_location: Dict[str, str]
    confidence_score: float
    resolution_method: str
    reasoning: str
    timestamp: datetime

class LLMAgent:
    """AI Agent for resolving merchant location issues"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
        
        # Cache for responses to reduce API calls
        self.response_cache = {}
        
        # Demo mode - use cached responses to avoid throttling
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        
        if not self.api_key:
            logger.warning("No LLM API key found. Using demo mode with cached responses.")
            self.available = False
        else:
            self.available = True
            self._setup_llm()
    
    def _setup_llm(self):
        """Setup the LLM client"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            elif self.provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"LLM client initialized with {self.provider}")
        except Exception as e:
            logger.error(f"Failed to setup LLM client: {e}")
            self.available = False
    
    def _get_cache_key(self, prompt: str, method: str) -> str:
        """Generate a cache key for a prompt and method"""
        content = f"{method}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, prompt: str, method: str) -> Optional[str]:
        """Get cached response if available"""
        cache_key = self._get_cache_key(prompt, method)
        return self.response_cache.get(cache_key)
    
    def _cache_response(self, prompt: str, method: str, response: str):
        """Cache a response"""
        cache_key = self._get_cache_key(prompt, method)
        self.response_cache[cache_key] = response
    
    def _get_demo_conversion_recommendation(self, merchant_name: str, conversion_rate: float) -> str:
        """Get a demo conversion rate recommendation"""
        recommendations = [
            f"Optimize checkout flow for {merchant_name} by reducing form fields and implementing guest checkout. Current {conversion_rate:.1%} rate indicates friction in payment process.",
            f"Implement mobile-first design for {merchant_name}. With {conversion_rate:.1%} conversion, mobile optimization could boost rates by 25-40%.",
            f"Add trust signals (SSL badges, security logos) to {merchant_name}'s checkout. Low {conversion_rate:.1%} rate suggests customer confidence issues.",
            f"Implement A/B testing for {merchant_name}'s payment buttons and form layout. Current {conversion_rate:.1%} rate needs systematic optimization.",
            f"Review fraud detection settings for {merchant_name}. Overly strict rules may be blocking legitimate transactions at {conversion_rate:.1%} rate."
        ]
        return recommendations[hash(merchant_name) % len(recommendations)]
    
    def _get_demo_error_recommendation(self, merchant_name: str, error_rate: float) -> str:
        """Get a demo error rate recommendation"""
        recommendations = [
            f"Review API integration for {merchant_name}. {error_rate:.1%} error rate suggests connection timeouts or malformed requests.",
            f"Implement retry logic with exponential backoff for {merchant_name}. Current {error_rate:.1%} rate indicates transient failures.",
            f"Add comprehensive error logging for {merchant_name} to identify root causes of {error_rate:.1%} error rate.",
            f"Optimize database queries for {merchant_name}. High {error_rate:.1%} rate may indicate performance bottlenecks.",
            f"Implement circuit breaker pattern for {merchant_name}'s external service calls. {error_rate:.1%} error rate suggests service degradation."
        ]
        return recommendations[hash(merchant_name) % len(recommendations)]
    
    def _get_demo_location_resolution(self, merchant_name: str) -> Dict[str, str]:
        """Get a demo location resolution"""
        # Simple rule-based location mapping for demo
        location_map = {
            "techcorp": {"city": "San Francisco", "country": "United States"},
            "global": {"city": "London", "country": "United Kingdom"},
            "digital": {"city": "Berlin", "country": "Germany"},
            "e-commerce": {"city": "New York", "country": "United States"},
            "online": {"city": "Toronto", "country": "Canada"},
            "webshop": {"city": "Amsterdam", "country": "Netherlands"},
            "web": {"city": "Sydney", "country": "Australia"},
            "tech": {"city": "Singapore", "country": "Singapore"},
            "e-business": {"city": "Tokyo", "country": "Japan"},
            "e-retail": {"city": "Paris", "country": "France"}
        }
        
        merchant_lower = merchant_name.lower()
        for key, location in location_map.items():
            if key in merchant_lower:
                return location
        
        # Default fallback
        return {"city": "Unknown City", "country": "Unknown Country"}
    
    def resolve_location_issues(self, merchants_with_issues: List[Dict]) -> List[LocationResolution]:
        """Resolve missing city/country information for merchants"""
        resolutions = []
        
        for merchant in merchants_with_issues:
            try:
                resolution = self._resolve_single_merchant(merchant)
                if resolution:
                    resolutions.append(resolution)
            except Exception as e:
                logger.error(f"Failed to resolve location for merchant {merchant.get('merchant_id')}: {e}")
        
        return resolutions
    
    def _resolve_single_merchant(self, merchant: Dict) -> Optional[LocationResolution]:
        """Resolve location for a single merchant"""
        merchant_id = merchant.get('merchant_id', '')
        merchant_name = merchant.get('merchant_name', '')
        current_location = merchant.get('location', {})
        
        # Check if location is actually missing
        city = current_location.get('city', '')
        country = current_location.get('country', '')
        
        if city and country:
            return None  # No resolution needed
        
        # Try to resolve using LLM (unless in demo mode)
        if self.available and not self.demo_mode:
            resolved_location = self._resolve_with_llm(merchant_name, current_location)
            if resolved_location:
                return LocationResolution(
                    merchant_id=merchant_id,
                    merchant_name=merchant_name,
                    original_location=current_location,
                    resolved_location=resolved_location,
                    confidence_score=0.85,
                    resolution_method="llm_analysis",
                    reasoning="Resolved using AI analysis of merchant name and context",
                    timestamp=datetime.now()
                )
        
        # Use demo mode or fallback to rule-based resolution
        if self.demo_mode:
            resolved_location = self._get_demo_location_resolution(merchant_name)
            return LocationResolution(
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                original_location=current_location,
                resolved_location=resolved_location,
                confidence_score=0.75,
                resolution_method="demo_analysis",
                reasoning="Resolved using demo location mapping based on merchant name patterns",
                timestamp=datetime.now()
            )
        else:
            # Fallback to rule-based resolution
            resolved_location = self._resolve_with_rules(merchant_name, current_location)
        if resolved_location:
            return LocationResolution(
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                original_location=current_location,
                resolved_location=resolved_location,
                confidence_score=0.6,
                resolution_method="rule_based",
                reasoning="Resolved using business name analysis and common patterns",
                timestamp=datetime.now()
            )
        
        return None
    
    def _resolve_with_llm(self, merchant_name: str, current_location: Dict) -> Optional[Dict]:
        """Use LLM to resolve location information"""
        try:
            prompt = self._build_location_prompt(merchant_name, current_location)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that resolves missing location information for businesses. Return only valid JSON with city and country fields."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                result = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    temperature=0.1,
                    system="You are a helpful assistant that resolves missing location information for businesses. Return only valid JSON with city and country fields.",
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            
            # Parse the JSON response
            try:
                resolved = json.loads(result)
                if isinstance(resolved, dict) and 'city' in resolved and 'country' in resolved:
                    return {
                        'city': resolved['city'],
                        'country': resolved['country']
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {result}")
                
        except Exception as e:
            logger.error(f"LLM resolution failed: {e}")
        
        return None
    
    def _build_location_prompt(self, merchant_name: str, current_location: Dict) -> str:
        """Build the prompt for location resolution"""
        city = current_location.get('city', '')
        country = current_location.get('country', '')
        
        prompt = f"""
        Analyze this business name and resolve any missing location information:
        
        Business Name: {merchant_name}
        Current City: {city if city else 'MISSING'}
        Current Country: {country if country else 'MISSING'}
        
        Based on the business name, common business patterns, and typical locations for this type of business, provide the most likely city and country.
        
        Return your response as JSON only:
        {{
            "city": "resolved_city_name",
            "country": "resolved_country_code"
        }}
        
        Use standard country codes (US, CA, UK, DE, etc.) and realistic city names.
        """
        
        return prompt
    
    def _resolve_with_rules(self, merchant_name: str, current_location: Dict) -> Optional[Dict]:
        """Fallback rule-based location resolution"""
        city = current_location.get('city', '')
        country = current_location.get('country', '')
        
        # Common business name patterns and their likely locations
        name_lower = merchant_name.lower()
        
        # Tech companies often in major tech hubs
        if any(word in name_lower for word in ['tech', 'digital', 'software', 'ai', 'data']):
            if not city:
                city = 'San Francisco'
            if not country:
                country = 'US'
        
        # Retail companies often in major cities
        elif any(word in name_lower for word in ['retail', 'store', 'shop', 'market']):
            if not city:
                city = 'New York'
            if not country:
                country = 'US'
        
        # E-commerce companies often in major business centers
        elif any(word in name_lower for word in ['ecommerce', 'e-commerce', 'online', 'web']):
            if not city:
                city = 'Los Angeles'
            if not country:
                country = 'US'
        
        # International companies
        elif any(word in name_lower for word in ['global', 'international', 'world']):
            if not city:
                city = 'London'
            if not country:
                country = 'UK'
        
        # Default to US if no pattern matches
        else:
            if not city:
                city = 'Chicago'
            if not country:
                country = 'US'
        
        return {
            'city': city,
            'country': country
        }
    
    def generate_troubleshooting_insights(self, merchant_data: Dict) -> str:
        """Generate AI-powered troubleshooting insights for a merchant"""
        if not self.available:
            return "LLM not available for insights generation."
        
        try:
            prompt = f"""
            Analyze this PayPal merchant's performance data and provide actionable troubleshooting insights:
            
            Merchant: {merchant_data.get('merchant_name', 'Unknown')}
            Conversion Rate: {merchant_data.get('conversion_rate', 0):.2%}
            Error Rate: {merchant_data.get('error_rate', 0):.2%}
            Transaction Count: {merchant_data.get('transaction_count', 0)}
            Location: {merchant_data.get('location', {})}
            
            Provide specific, actionable recommendations to improve their performance.
            Focus on:
            1. Conversion rate optimization
            2. Error rate reduction
            3. Location-based insights
            4. Best practices for their business type
            
            Keep the response concise and practical.
            """
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a PayPal merchant success specialist with expertise in e-commerce optimization."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                return response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    temperature=0.3,
                    system="You are a PayPal merchant success specialist with expertise in e-commerce optimization.",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return "Unable to generate AI insights at this time."

    def generate_conversion_rate_recommendation(self, merchant_data: Dict, issue: Dict) -> str:
        """Generate AI-powered recommendations for conversion rate issues"""
        merchant_name = merchant_data.get('merchant_name', 'Unknown')
        conversion_rate = issue.get('conversion_rate', 0)
        
        # Check cache first
        cache_key = f"conversion_{merchant_name}_{conversion_rate:.3f}"
        cached_response = self._get_cached_response(cache_key, "conversion_rate")
        if cached_response:
            logger.info(f"Using cached conversion rate recommendation for {merchant_name}")
            return cached_response
        
        # Use demo mode if enabled or no API key
        if self.demo_mode or not self.available:
            demo_response = self._get_demo_conversion_recommendation(merchant_name, conversion_rate)
            self._cache_response(cache_key, "conversion_rate", demo_response)
            logger.info(f"Using demo conversion rate recommendation for {merchant_name}")
            return demo_response
        
        try:
            prompt = f"""
            Analyze this PayPal merchant's conversion rate issue and provide specific recommendations:
            
            Merchant: {merchant_name}
            Current Conversion Rate: {conversion_rate:.2%}
            Issue Severity: {issue.get('severity', 'medium')}
            Transaction Count: {merchant_data.get('transaction_count', 0)}
            
            Provide specific, actionable recommendations to improve conversion rate.
            Focus on:
            1. Payment flow optimization
            2. User experience improvements
            3. Fraud detection settings
            4. Mobile optimization
            5. A/B testing strategies
            
            Keep the response concise and practical.
            """
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a PayPal conversion optimization specialist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=250
                )
                result = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=250,
                    temperature=0.3,
                    system="You are a PayPal conversion optimization specialist.",
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            
            # Cache the response
            self._cache_response(cache_key, "conversion_rate", result)
            return result
                
        except Exception as e:
            logger.error(f"Failed to generate conversion rate recommendation: {e}")
            # Fallback to demo response
            demo_response = self._get_demo_conversion_recommendation(merchant_name, conversion_rate)
            self._cache_response(cache_key, "conversion_rate", demo_response)
            return demo_response

    def generate_error_rate_recommendation(self, merchant_data: Dict, issue: Dict) -> str:
        """Generate AI-powered recommendations for error rate issues"""
        merchant_name = merchant_data.get('merchant_name', 'Unknown')
        error_rate = issue.get('error_rate', 0)
        
        # Check cache first
        cache_key = f"error_{merchant_name}_{error_rate:.3f}"
        cached_response = self._get_cached_response(cache_key, "error_rate")
        if cached_response:
            logger.info(f"Using cached error rate recommendation for {merchant_name}")
            return cached_response
        
        # Use demo mode if enabled or no API key
        if self.demo_mode or not self.available:
            demo_response = self._get_demo_error_recommendation(merchant_name, error_rate)
            self._cache_response(cache_key, "error_rate", demo_response)
            logger.info(f"Using demo error rate recommendation for {merchant_name}")
            return demo_response
        
        try:
            prompt = f"""
            Analyze this PayPal merchant's error rate issue and provide specific recommendations:
            
            Merchant: {merchant_name}
            Current Error Rate: {error_rate:.2%}
            Issue Severity: {issue.get('severity', 'medium')}
            Transaction Count: {merchant_data.get('transaction_count', 0)}
            
            Provide specific, actionable recommendations to reduce error rates.
            Focus on:
            1. Payment processing optimization
            2. API integration improvements
            3. Error handling and retry logic
            4. System monitoring and alerts
            5. Technical debt reduction
            
            Keep the response concise and practical.
            """
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a PayPal technical support specialist."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=250
                )
                result = response.choices[0].message.content
            else:  # anthropic
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=250,
                    temperature=0.3,
                    system="You are a PayPal technical support specialist.",
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            
            # Cache the response
            self._cache_response(cache_key, "error_rate", result)
            return result
                
        except Exception as e:
            logger.error(f"Failed to generate error rate recommendation: {e}")
            # Fallback to demo response
            demo_response = self._get_demo_error_recommendation(merchant_name, error_rate)
            self._cache_response(cache_key, "error_rate", demo_response)
            return demo_response

# Global instance
llm_agent = LLMAgent() 