from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from app.elastic_client import ElasticClient
from app.models import ConversionRateAnalysis, LocationIssue, MonthlyComparison, TroubleshootingResponse
from app.config import settings

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
            
            # Check location issues
            location_issues = await self.elastic.get_location_issues()
            merchant_location_issue = next((issue for issue in location_issues if issue["merchant_id"] == merchant_id), None)
            
            if merchant_location_issue:
                issues_found.append({
                    "type": "missing_location",
                    "severity": "high" if len(merchant_location_issue["missing_fields"]) == 2 else "medium",
                    "details": f"Missing: {', '.join(merchant_location_issue['missing_fields'])}"
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
            # Get all issues
            conversion_issues = await self.elastic.get_conversion_rate_issues()
            location_issues = await self.elastic.get_location_issues()
            error_issues = await self.elastic.get_error_rate_issues()
            
            # Calculate summary statistics
            total_issues = len(conversion_issues) + len(location_issues) + len(error_issues)
            high_severity_issues = len([i for i in conversion_issues if i["severity"] == "high"]) + \
                                 len([i for i in error_issues if i["severity"] == "high"])
            
            # Get total merchants
            all_merchants = await self.elastic.get_merchants(size=1000)
            total_merchants = len(all_merchants)
            
            return {
                "total_merchants": total_merchants,
                "total_issues": total_issues,
                "high_severity_issues": high_severity_issues,
                "conversion_rate_issues": len(conversion_issues),
                "location_issues": len(location_issues),
                "error_rate_issues": len(error_issues),
                "issue_distribution": {
                    "conversion_rate": len(conversion_issues),
                    "missing_location": len(location_issues),
                    "high_error_rate": len(error_issues)
                },
                "risk_levels": {
                    "high": high_severity_issues,
                    "medium": total_issues - high_severity_issues,
                    "low": 0
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
                "risk_levels": {"high": 0, "medium": 0, "low": 0}
            } 