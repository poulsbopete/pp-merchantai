#!/usr/bin/env python3
"""
Test AI Features Script
This script demonstrates the new LLM agent features for location resolution and insights.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

async def test_ai_features():
    """Test the AI features"""
    print("🤖 Testing AI Features")
    print("=" * 50)
    
    try:
        from app.llm_agent import llm_agent
        from app.elastic_client import ElasticClient
        from app.analytics import AnalyticsService
        
        # Initialize services
        elastic_client = ElasticClient()
        analytics_service = AnalyticsService(elastic_client)
        
        print(f"✅ LLM Agent Status: {'Available' if llm_agent.available else 'Unavailable'}")
        if llm_agent.available:
            print(f"   Provider: {llm_agent.provider}")
            print(f"   Model: {llm_agent.model}")
        else:
            print("   No API key configured - will use fallback methods")
        
        print("\n🔍 Testing Location Resolution...")
        
        # Get merchants with location issues
        location_issues = await elastic_client.get_location_issues()
        print(f"   Found {len(location_issues)} merchants with location issues")
        
        if location_issues:
            # Test AI location resolution
            resolutions = await analytics_service.resolve_location_issues_with_ai()
            print(f"   Resolved {len(resolutions)} locations using AI")
            
            for resolution in resolutions[:3]:  # Show first 3
                print(f"   - {resolution.merchant_name}: {resolution.original_location} → {resolution.resolved_location}")
                print(f"     Confidence: {resolution.confidence_score:.1%}, Method: {resolution.resolution_method}")
        
        print("\n💡 Testing AI Insights...")
        
        # Get a merchant for insights
        merchants = await elastic_client.get_merchants(size=1)
        if merchants:
            merchant_id = merchants[0]["merchant_id"]
            insights = await analytics_service.get_ai_insights(merchant_id)
            print(f"   AI Insights for {merchant_id}:")
            print(f"   {insights[:200]}...")
        
        print("\n🎉 AI Features Test Complete!")
        print("\nTo use these features in the web app:")
        print("1. Visit: http://localhost:8000")
        print("2. Click 'AI Location Resolution' to automatically fix missing locations")
        print("3. Click 'AI Insights' to get personalized recommendations")
        print("4. Click 'AI Status' to check the AI agent status")
        
    except Exception as e:
        print(f"❌ Error testing AI features: {e}")
        print("\nMake sure the application is running and Elastic Cloud is connected.")

if __name__ == "__main__":
    asyncio.run(test_ai_features()) 