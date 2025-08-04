from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from app.elastic_client import ElasticClient
from app.models import ConversionRateAnalysis, LocationIssue, MonthlyComparison, TroubleshootingResponse
from app.config import settings
from app.llm_agent import llm_agent, LocationResolution

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Analytics service for merchant troubleshooting"""
    
    def __init__(self, elastic_client: ElasticClient):
        self.elastic = elastic_client
    
    async def analyze_conversion_rates(self) -> List[ConversionRateAnalysis]:
        """Analyze conversion rate issues"""
        try:
            issues = await self.elastic.get_conversion_rate_issues()
            analyses = []
            
            for issue in issues:
                merchant_data = await self.elastic.get_merchant_by_id(issue["merchant_id"])
                if not merchant_data:
                    continue
                
                # Get historical data for comparison
                monthly_data = await self.elastic.get_monthly_comparison(issue["merchant_id"])
                previous_rate = 0.5  # Default assumption
                
                if monthly_data:
                    previous_rate = monthly_data[0]["previous_month"]["conversion_rate"]
                
                change_percentage = ((issue["conversion_rate"] - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0
                
                # Determine severity and recommendation
                severity = "high" if issue["conversion_rate"] < 0.2 else "medium"
                
                if issue["conversion_rate"] < 0.2:
                    recommendation = "Critical: Immediate intervention required. Review payment flow and fraud settings."
                elif issue["conversion_rate"] < 0.3:
                    recommendation = "High priority: Investigate payment processing issues and user experience."
                else:
                    recommendation = "Monitor: Track trends and consider optimization strategies."
                
                analyses.append(ConversionRateAnalysis(
                    merchant_id=issue["merchant_id"],
                    merchant_name=merchant_data.get("merchant_name", "Unknown"),
                    current_rate=issue["conversion_rate"],
                    previous_rate=previous_rate,
                    change_percentage=change_percentage,
                    is_issue=True,
                    severity=severity,
                    recommendation=recommendation
                ))
            
            return analyses
        except Exception as e:
            logger.error(f"Failed to analyze conversion rates: {e}")
            return []
    
    async def analyze_location_issues(self) -> List[LocationIssue]:
        """Analyze missing location data issues"""
        try:
            issues = await self.elastic.get_location_issues()
            location_issues = []
            
            for issue in issues:
                # Determine impact level and recommendation
                if len(issue["missing_fields"]) == 2:
                    impact_level = "high"
                    recommendation = "Critical: Both city and country missing. Update merchant profile immediately."
                elif "country" in issue["missing_fields"]:
                    impact_level = "high"
                    recommendation = "High priority: Country information required for compliance and fraud prevention."
                else:
                    impact_level = "medium"
                    recommendation = "Medium priority: City information helps with local fraud detection."
                
                location_issues.append(LocationIssue(
                    merchant_id=issue["merchant_id"],
                    merchant_name=issue["merchant_name"],
                    missing_fields=issue["missing_fields"],
                    impact_level=impact_level,
                    recommendation=recommendation
                ))
            
            return location_issues
        except Exception as e:
            logger.error(f"Failed to analyze location issues: {e}")
            return []
    
    async def get_monthly_comparisons(self, merchant_id: Optional[str] = None) -> List[MonthlyComparison]:
        """Get month-to-month comparison analysis"""
        try:
            comparisons_data = await self.elastic.get_monthly_comparison(merchant_id)
            comparisons = []
            
            for comp in comparisons_data:
                merchant_data = await self.elastic.get_merchant_by_id(comp["merchant_id"])
                
                comparisons.append(MonthlyComparison(
                    merchant_id=comp["merchant_id"],
                    merchant_name=merchant_data.get("merchant_name", "Unknown") if merchant_data else "Unknown",
                    current_month=comp["current_month"],
                    previous_month=comp["previous_month"],
                    changes={
                        "conversion_rate_change": comp["change_percentage"],
                        "error_rate_change": comp["current_month"]["error_rate"] - comp["previous_month"]["error_rate"],
                        "transaction_change": comp["current_month"]["transactions"] - comp["previous_month"]["transactions"]
                    },
                    trend=comp["trend"]
                ))
            
            return comparisons
        except Exception as e:
            logger.error(f"Failed to get monthly comparisons: {e}")
            return []
    
    async def troubleshoot_merchant(self, merchant_id: str) -> TroubleshootingResponse:
        """AI-powered troubleshooting for specific merchant"""
        try:
            issues_found = []
            recommendations = []
            priority_actions = []
            risk_score = 0.0
            
            # Get merchant data
            merchant_data = await self.elastic.get_merchant_by_id(merchant_id)
            if not merchant_data:
                # Try to find merchant by searching
                search_results = await self.elastic.search_merchants(merchant_id)
                if search_results:
                    merchant_data = search_results[0]
                else:
                    return TroubleshootingResponse(
                        issues_found=[],
                        recommendations=["Merchant not found"],
                        priority_actions=[],
                        risk_score=0.0,
                        next_steps=["Verify merchant ID"]
                    )
            
            # Check conversion rate issues
            conversion_issues = await self.elastic.get_conversion_rate_issues()
            merchant_conversion_issue = next((issue for issue in conversion_issues if issue["merchant_id"] == merchant_id), None)
            
            if merchant_conversion_issue:
                issues_found.append({
                    "type": "conversion_rate_drop",
                    "severity": merchant_conversion_issue["severity"],
                    "details": f"Conversion rate: {merchant_conversion_issue['conversion_rate']:.2%}"
                })
                risk_score += 0.4
                recommendations.append("Review payment flow and checkout process")
                priority_actions.append("Analyze failed transaction patterns")
            
            # Check location issues - both from location issues list and direct merchant data
            location_issues = await self.elastic.get_location_issues()
            merchant_location_issue = next((issue for issue in location_issues if issue["merchant_id"] == merchant_id), None)
            
            # Also check the merchant's current data directly for missing location
            missing_fields = []
            if not merchant_data.get("country") or merchant_data.get("country") == "":
                missing_fields.append("country")
            if not merchant_data.get("city") or merchant_data.get("city") == "":
                missing_fields.append("city")
            
            if merchant_location_issue or missing_fields:
                # Use the location issue if available, otherwise use direct check
                if merchant_location_issue:
                    missing_fields = merchant_location_issue["missing_fields"]
                
                issues_found.append({
                    "type": "missing_location",
                    "severity": "high" if len(missing_fields) == 2 else "medium",
                    "details": f"Missing: {', '.join(missing_fields)}"
                })
                risk_score += 0.3
                recommendations.append("Update merchant profile with location information")
                priority_actions.append("Contact merchant for missing data")
            
            # Check error rate issues
            error_issues = await self.elastic.get_error_rate_issues()
            merchant_error_issue = next((issue for issue in error_issues if issue["merchant_id"] == merchant_id), None)
            
            if merchant_error_issue:
                issues_found.append({
                    "type": "high_error_rate",
                    "severity": merchant_error_issue["severity"],
                    "details": f"Error rate: {merchant_error_issue['error_rate']:.2%}"
                })
                risk_score += 0.3
                recommendations.append("Investigate error patterns and system issues")
                priority_actions.append("Review error logs and transaction failures")
            
            # Generate next steps based on risk score
            if risk_score > 0.7:
                next_steps = [
                    "Immediate merchant contact required",
                    "Review fraud detection settings",
                    "Consider temporary account restrictions"
                ]
            elif risk_score > 0.4:
                next_steps = [
                    "Schedule merchant review call",
                    "Monitor transaction patterns closely",
                    "Prepare optimization recommendations"
                ]
            else:
                next_steps = [
                    "Continue monitoring",
                    "Regular health check in 30 days"
                ]
            
            return TroubleshootingResponse(
                issues_found=issues_found,
                recommendations=recommendations,
                priority_actions=priority_actions,
                risk_score=min(risk_score, 1.0),
                next_steps=next_steps
            )
            
        except Exception as e:
            logger.error(f"Failed to troubleshoot merchant {merchant_id}: {e}")
            return TroubleshootingResponse(
                issues_found=[],
                recommendations=["Error occurred during analysis"],
                priority_actions=[],
                risk_score=0.0,
                next_steps=["Retry analysis or contact support"]
            )
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary statistics"""
        try:
            # Get comprehensive issue statistics including resolved vs unresolved
            issue_stats = await self.elastic.get_issue_statistics()
            
            # Get total merchants
            all_merchants = await self.elastic.get_merchants(size=1000)
            total_merchants = len(all_merchants)
            
            # Calculate high severity issues (unresolved only)
            conversion_issues = await self.elastic.get_conversion_rate_issues()
            error_issues = await self.elastic.get_error_rate_issues()
            high_severity_issues = len([i for i in conversion_issues if i["severity"] == "high"]) + \
                                 len([i for i in error_issues if i["severity"] == "high"])
            
            return {
                "total_merchants": total_merchants,
                "total_issues": issue_stats["unresolved"]["total"],
                "high_severity_issues": high_severity_issues,
                "conversion_rate_issues": issue_stats["unresolved"]["conversion_rate"],
                "location_issues": issue_stats["unresolved"]["location"],
                "error_rate_issues": issue_stats["unresolved"]["error_rate"],
                "issue_distribution": {
                    "conversion_rate": issue_stats["unresolved"]["conversion_rate"],
                    "missing_location": issue_stats["unresolved"]["location"],
                    "high_error_rate": issue_stats["unresolved"]["error_rate"]
                },
                "risk_levels": {
                    "high": high_severity_issues,
                    "medium": issue_stats["unresolved"]["total"] - high_severity_issues,
                    "low": 0
                },
                "resolution_stats": {
                    "total_resolved": issue_stats["total_resolved"],
                    "resolved_by_type": issue_stats["resolved"],
                    "resolution_rate": (issue_stats["total_resolved"] / (issue_stats["total_resolved"] + issue_stats["unresolved"]["total"])) * 100 if (issue_stats["total_resolved"] + issue_stats["unresolved"]["total"]) > 0 else 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {
                "total_merchants": 0,
                "total_issues": 0,
                "high_severity_issues": 0,
                "conversion_rate_issues": 0,
                "location_issues": 0,
                "error_rate_issues": 0,
                "issue_distribution": {},
                "risk_levels": {"high": 0, "medium": 0, "low": 0},
                "resolution_stats": {
                    "total_resolved": 0,
                    "resolved_by_type": {"location": 0, "conversion_rate": 0, "error_rate": 0},
                    "resolution_rate": 0
                }
            }
    
    async def resolve_location_issues_with_ai(self) -> List[LocationResolution]:
        """Use AI to automatically resolve location issues"""
        try:
            # Get merchants with location issues
            location_issues = await self.elastic.get_location_issues()
            
            # Convert to merchant data format for LLM agent
            merchants_with_issues = []
            for issue in location_issues:
                # Try to get merchant data, with fallback to search
                merchant_data = await self.elastic.get_merchant_by_id(issue["merchant_id"])
                if not merchant_data:
                    # Try searching by merchant name as fallback
                    search_results = await self.elastic.search_merchants(issue["merchant_name"])
                    if search_results:
                        merchant_data = search_results[0]
                
                if merchant_data:
                    # Add missing fields information to the merchant data
                    merchant_data["missing_fields"] = issue["missing_fields"]
                    merchants_with_issues.append(merchant_data)
            
            # Use LLM agent to resolve issues
            resolutions = llm_agent.resolve_location_issues(merchants_with_issues)
            
            # Update Elasticsearch with resolved locations
            for resolution in resolutions:
                await self._update_merchant_location(resolution)
            
            return resolutions
        except Exception as e:
            logger.error(f"Failed to resolve location issues with AI: {e}")
            return []
    
    async def _update_merchant_location(self, resolution: LocationResolution):
        """Update merchant location in Elasticsearch"""
        try:
            # Update the merchant's location data
            update_body = {
                "doc": {
                    "location": resolution.resolved_location,
                    "country": resolution.resolved_location.get("country"),
                    "city": resolution.resolved_location.get("city"),
                    "location_resolved": True,
                    "location_resolution_date": datetime.now().isoformat(),
                    "location_resolution_method": "ai_automated",
                    "location_resolution_confidence": resolution.confidence_score
                }
            }
            
            # Find and update all documents for this merchant
            search_response = await self.elastic.client.search(
                index=self.elastic.index,
                body={
                    "query": {"term": {"merchant_id": resolution.merchant_id}},
                    "size": 1000
                }
            )
            
            for hit in search_response["hits"]["hits"]:
                doc_id = hit["_id"]
                await self.elastic.client.update(
                    index=self.elastic.index,
                    id=doc_id,
                    body=update_body
                )
            
            logger.info(f"Updated location for merchant {resolution.merchant_id}")
        except Exception as e:
            logger.error(f"Failed to update merchant location: {e}")

    async def _update_conversion_rate_resolution(self, merchant_id: str, recommendation: str, confidence_score: float):
        """Update merchant conversion rate resolution in Elasticsearch"""
        try:
            update_body = {
                "doc": {
                    "conversion_rate_resolved": True,
                    "conversion_rate_resolution_date": datetime.now().isoformat(),
                    "conversion_rate_resolution_method": "ai_analysis",
                    "conversion_rate_resolution_confidence": confidence_score,
                    "conversion_rate_ai_recommendation": recommendation,
                    "conversion_rate_status": "under_review"
                }
            }
            
            # Find and update all documents for this merchant
            search_response = await self.elastic.client.search(
                index=self.elastic.index,
                body={
                    "query": {"term": {"merchant_id": merchant_id}},
                    "size": 1000
                }
            )
            
            for hit in search_response["hits"]["hits"]:
                doc_id = hit["_id"]
                await self.elastic.client.update(
                    index=self.elastic.index,
                    id=doc_id,
                    body=update_body
                )
            
            logger.info(f"Updated conversion rate resolution for merchant {merchant_id}")
        except Exception as e:
            logger.error(f"Failed to update conversion rate resolution: {e}")

    async def _update_error_rate_resolution(self, merchant_id: str, recommendation: str, confidence_score: float):
        """Update merchant error rate resolution in Elasticsearch"""
        try:
            update_body = {
                "doc": {
                    "error_rate_resolved": True,
                    "error_rate_resolution_date": datetime.now().isoformat(),
                    "error_rate_resolution_method": "ai_analysis",
                    "error_rate_resolution_confidence": confidence_score,
                    "error_rate_ai_recommendation": recommendation,
                    "error_rate_status": "under_review"
                }
            }
            
            # Find and update all documents for this merchant
            search_response = await self.elastic.client.search(
                index=self.elastic.index,
                body={
                    "query": {"term": {"merchant_id": merchant_id}},
                    "size": 1000
                }
            )
            
            for hit in search_response["hits"]["hits"]:
                doc_id = hit["_id"]
                await self.elastic.client.update(
                    index=self.elastic.index,
                    id=doc_id,
                    body=update_body
                )
            
            logger.info(f"Updated error rate resolution for merchant {merchant_id}")
        except Exception as e:
            logger.error(f"Failed to update error rate resolution: {e}")

    async def _mark_issue_resolved(self, merchant_id: str, issue_type: str, resolution_data: dict):
        """Generic method to mark any issue as resolved"""
        try:
            update_body = {
                "doc": {
                    f"{issue_type}_resolved": True,
                    f"{issue_type}_resolution_date": datetime.now().isoformat(),
                    f"{issue_type}_resolution_method": resolution_data.get("method", "ai_analysis"),
                    f"{issue_type}_resolution_confidence": resolution_data.get("confidence", 0.8),
                    f"{issue_type}_ai_recommendation": resolution_data.get("recommendation", ""),
                    f"{issue_type}_status": "resolved"
                }
            }
            
            # Find and update all documents for this merchant
            search_response = await self.elastic.client.search(
                index=self.elastic.index,
                body={
                    "query": {"term": {"merchant_id": merchant_id}},
                    "size": 1000
                }
            )
            
            for hit in search_response["hits"]["hits"]:
                doc_id = hit["_id"]
                await self.elastic.client.update(
                    index=self.elastic.index,
                    id=doc_id,
                    body=update_body
                )
            
            logger.info(f"Marked {issue_type} as resolved for merchant {merchant_id}")
        except Exception as e:
            logger.error(f"Failed to mark {issue_type} as resolved: {e}")
    
    async def get_ai_insights(self, merchant_id: str) -> str:
        """Get AI-powered insights for a specific merchant"""
        try:
            merchant_data = await self.elastic.get_merchant_by_id(merchant_id)
            if not merchant_data:
                return "Merchant not found."
            
            # Get recent performance data
            recent_data = await self.elastic.client.search(
                index=self.elastic.index,
                body={
                    "query": {"term": {"merchant_id": merchant_id}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 1
                }
            )
            
            if recent_data["hits"]["hits"]:
                latest_data = recent_data["hits"]["hits"][0]["_source"]
                return llm_agent.generate_troubleshooting_insights(latest_data)
            else:
                return "No recent data available for analysis."
                
        except Exception as e:
            logger.error(f"Failed to get AI insights: {e}")
            return "Unable to generate insights at this time."

    async def resolve_conversion_rate_issues_with_ai(self) -> List[Dict[str, Any]]:
        """Use AI to analyze and provide recommendations for conversion rate issues"""
        try:
            # Get merchants with conversion rate issues
            conversion_issues = await self.elastic.get_conversion_rate_issues()
            
            ai_recommendations = []
            for issue in conversion_issues[:5]:  # Limit to 5 for demo
                # Get merchant data
                merchant_data = await self.elastic.get_merchant_by_id(issue["merchant_id"])
                if not merchant_data:
                    search_results = await self.elastic.search_merchants(issue["merchant_id"])
                    if search_results:
                        merchant_data = search_results[0]
                
                if merchant_data:
                    # Generate AI recommendation
                    recommendation = llm_agent.generate_conversion_rate_recommendation(merchant_data, issue)
                    confidence_score = 0.85
                    
                    # Update Elasticsearch to mark this issue as resolved
                    await self._update_conversion_rate_resolution(
                        issue["merchant_id"], 
                        recommendation, 
                        confidence_score
                    )
                    
                    ai_recommendations.append({
                        "merchant_id": issue["merchant_id"],
                        "merchant_name": merchant_data.get("merchant_name", "Unknown"),
                        "current_conversion_rate": issue["conversion_rate"],
                        "issue_severity": issue["severity"],
                        "ai_recommendation": recommendation,
                        "confidence_score": confidence_score,
                        "resolution_method": "ai_analysis",
                        "resolved": True,
                        "resolution_date": datetime.now().isoformat()
                    })
            
            return ai_recommendations
        except Exception as e:
            logger.error(f"Failed to resolve conversion rate issues with AI: {e}")
            return []

    async def resolve_error_rate_issues_with_ai(self) -> List[Dict[str, Any]]:
        """Use AI to analyze and provide recommendations for error rate issues"""
        try:
            # Get merchants with error rate issues
            error_issues = await self.elastic.get_error_rate_issues()
            
            ai_recommendations = []
            for issue in error_issues[:5]:  # Limit to 5 for demo
                # Get merchant data
                merchant_data = await self.elastic.get_merchant_by_id(issue["merchant_id"])
                if not merchant_data:
                    search_results = await self.elastic.search_merchants(issue["merchant_id"])
                    if search_results:
                        merchant_data = search_results[0]
                
                if merchant_data:
                    # Generate AI recommendation
                    recommendation = llm_agent.generate_error_rate_recommendation(merchant_data, issue)
                    confidence_score = 0.82
                    
                    # Update Elasticsearch to mark this issue as resolved
                    await self._update_error_rate_resolution(
                        issue["merchant_id"], 
                        recommendation, 
                        confidence_score
                    )
                    
                    ai_recommendations.append({
                        "merchant_id": issue["merchant_id"],
                        "merchant_name": merchant_data.get("merchant_name", "Unknown"),
                        "current_error_rate": issue["error_rate"],
                        "issue_severity": issue["severity"],
                        "ai_recommendation": recommendation,
                        "confidence_score": confidence_score,
                        "resolution_method": "ai_analysis",
                        "resolved": True,
                        "resolution_date": datetime.now().isoformat()
                    })
            
            return ai_recommendations
        except Exception as e:
            logger.error(f"Failed to resolve error rate issues with AI: {e}")
            return [] 