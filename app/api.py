from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from typing import List, Optional
import logging
from datetime import datetime

from app.models import (
    Merchant, ConversionRateAnalysis, LocationIssue, MonthlyComparison,
    TroubleshootingRequest, TroubleshootingResponse, AnalyticsResponse, ErrorResponse
)
from app.llm_agent import LocationResolution
from app.elastic_client import ElasticClient
from app.analytics import AnalyticsService
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="PayPal Merchant Troubleshooting Application"
)

# Initialize services
elastic_client = ElasticClient()
analytics_service = AnalyticsService(elastic_client)

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        summary = await analytics_service.get_dashboard_summary()
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Failed to load dashboard"
        })

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        elastic_health = await elastic_client.health_check()
        return {
            "status": "healthy" if elastic_health else "unhealthy",
            "elasticsearch": "connected" if elastic_health else "disconnected",
            "version": settings.app_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/api/merchants", response_model=List[Merchant])
async def get_merchants(size: int = 100, from_: int = 0):
    """Get all merchants with pagination"""
    try:
        merchants_data = await elastic_client.get_merchants(size=size, from_=from_)
        return [Merchant(**merchant) for merchant in merchants_data]
    except Exception as e:
        logger.error(f"Failed to get merchants: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve merchants")

@app.get("/api/merchants/{merchant_id}", response_model=Merchant)
async def get_merchant(merchant_id: str):
    """Get specific merchant by ID"""
    try:
        merchant_data = await elastic_client.get_merchant_by_id(merchant_id)
        if not merchant_data:
            raise HTTPException(status_code=404, detail="Merchant not found")
        return Merchant(**merchant_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get merchant {merchant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve merchant")

@app.get("/api/analytics/conversion-rates", response_model=List[ConversionRateAnalysis])
async def get_conversion_rate_analysis():
    """Get conversion rate analysis"""
    try:
        return await analytics_service.analyze_conversion_rates()
    except Exception as e:
        logger.error(f"Failed to analyze conversion rates: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze conversion rates")

@app.get("/api/analytics/location-issues", response_model=List[LocationIssue])
async def get_location_issues():
    """Get location data issues"""
    try:
        return await analytics_service.analyze_location_issues()
    except Exception as e:
        logger.error(f"Failed to analyze location issues: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze location issues")

@app.get("/api/analytics/monthly-comparison", response_model=List[MonthlyComparison])
async def get_monthly_comparison(merchant_id: Optional[str] = None):
    """Get month-to-month comparison data"""
    try:
        return await analytics_service.get_monthly_comparisons(merchant_id)
    except Exception as e:
        logger.error(f"Failed to get monthly comparison: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monthly comparison")

@app.get("/api/analytics/error-rates")
async def get_error_rate_issues():
    """Get merchants with high error rates"""
    try:
        issues = await elastic_client.get_error_rate_issues()
        return AnalyticsResponse(
            total_merchants=len(issues),
            issues_found=len(issues),
            data=issues,
            summary={
                "high_severity": len([i for i in issues if i["severity"] == "high"]),
                "medium_severity": len([i for i in issues if i["severity"] == "medium"]),
                "avg_error_rate": sum(i["error_rate"] for i in issues) / len(issues) if issues else 0
            }
        )
    except Exception as e:
        logger.error(f"Failed to get error rate issues: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error rate issues")

@app.post("/api/troubleshoot", response_model=TroubleshootingResponse)
async def troubleshoot_merchant(request: TroubleshootingRequest):
    """AI-powered troubleshooting for merchant"""
    try:
        if not request.merchant_id:
            raise HTTPException(status_code=400, detail="Merchant ID is required")
        
        return await analytics_service.troubleshoot_merchant(request.merchant_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to troubleshoot merchant: {e}")
        raise HTTPException(status_code=500, detail="Failed to troubleshoot merchant")

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        return await analytics_service.get_dashboard_summary()
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard summary")

@app.get("/api/search/merchants")
async def search_merchants(q: str):
    """Search merchants by name or ID"""
    try:
        if not q or len(q) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        results = await elastic_client.search_merchants(q)
        return {
            "query": q,
            "results": results,
            "total": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search merchants: {e}")
        raise HTTPException(status_code=500, detail="Failed to search merchants")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Page not found"
    })

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    return templates.TemplateResponse("error.html", {
        "request": request,
        "error": "Internal server error"
    })

# LLM Agent Endpoints
@app.post("/api/ai/resolve-locations", response_model=List[LocationResolution])
async def resolve_location_issues_with_ai():
    """Use AI to automatically resolve missing location information"""
    try:
        resolutions = await analytics_service.resolve_location_issues_with_ai()
        return resolutions
    except Exception as e:
        logger.error(f"Failed to resolve locations with AI: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve locations with AI")

@app.get("/api/ai/insights/{merchant_id}")
async def get_ai_insights(merchant_id: str):
    """Get AI-powered insights for a specific merchant"""
    try:
        insights = await analytics_service.get_ai_insights(merchant_id)
        return {
            "merchant_id": merchant_id,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get AI insights for {merchant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI insights")

@app.get("/api/ai/status")
async def get_ai_status():
    """Get AI agent status and capabilities"""
    from app.llm_agent import llm_agent
    return {
        "available": llm_agent.available,
        "provider": llm_agent.provider if llm_agent.available else None,
        "model": llm_agent.model if llm_agent.available else None,
        "capabilities": [
            "location_resolution",
            "troubleshooting_insights",
            "merchant_analysis",
            "conversion_rate_optimization",
            "error_rate_reduction"
        ]
    }

@app.post("/api/ai/resolve-conversion-rates")
async def resolve_conversion_rate_issues_with_ai():
    """Use AI to analyze and provide recommendations for conversion rate issues"""
    try:
        recommendations = await analytics_service.resolve_conversion_rate_issues_with_ai()
        return recommendations
    except Exception as e:
        logger.error(f"Failed to resolve conversion rate issues with AI: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve conversion rate issues with AI")

@app.post("/api/ai/resolve-error-rates")
async def resolve_error_rate_issues_with_ai():
    """Use AI to analyze and provide recommendations for error rate issues"""
    try:
        recommendations = await analytics_service.resolve_error_rate_issues_with_ai()
        return recommendations
    except Exception as e:
        logger.error(f"Failed to resolve error rate issues with AI: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve error rate issues with AI") 