from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)

class ElasticClient:
    """Elasticsearch client for merchant data operations"""
    
    def __init__(self):
        # Handle Elastic Cloud connection
        if settings.elasticsearch_cloud_id:
            # Use cloud_id for Elastic Cloud
            self.client = Elasticsearch(
                cloud_id=settings.elasticsearch_cloud_id,
                api_key=settings.elasticsearch_username if settings.elasticsearch_username else None,
                verify_certs=not settings.debug  # Disable SSL verification in debug/production mode
            )
        else:
            # Use traditional host/port connection with API key
            host = settings.elasticsearch_host.replace("https://", "").replace("http://", "")
            hosts = [{"host": host, "port": int(settings.elasticsearch_port), "scheme": "https"}]
            
            # Debug logging
            logger.info(f"Elasticsearch host: {settings.elasticsearch_host}")
            logger.info(f"Elasticsearch port: {settings.elasticsearch_port}")
            logger.info(f"Elasticsearch username (API key): {settings.elasticsearch_username[:20]}..." if settings.elasticsearch_username else "None")
            logger.info(f"Elasticsearch index: {settings.elasticsearch_index}")
            logger.info(f"Debug mode: {settings.debug}")
            
            # Use API key authentication for serverless
            if settings.elasticsearch_username and not settings.elasticsearch_password:
                logger.info("Using API key authentication")
                self.client = Elasticsearch(
                    hosts,
                    api_key=settings.elasticsearch_username,
                    verify_certs=not settings.debug,  # Disable SSL verification in debug/production mode
                    ssl_show_warn=False  # Suppress SSL warnings
                )
            else:
                logger.info("Using basic auth")
                # Fallback to basic auth if password is provided
                self.client = Elasticsearch(
                    hosts,
                    basic_auth=(settings.elasticsearch_username, settings.elasticsearch_password) if settings.elasticsearch_username else None,
                    verify_certs=not settings.debug,  # Disable SSL verification in debug/production mode
                    ssl_show_warn=False  # Suppress SSL warnings
                )
        self.index = settings.elasticsearch_index
    
    async def health_check(self) -> bool:
        """Check Elasticsearch connection health"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return False
    
    async def get_merchants(self, size: int = 100, from_: int = 0) -> List[Dict[str, Any]]:
        """Get all merchants with pagination"""
        try:
            response = self.client.search(
                index=self.index,
                body={
                    "query": {"match_all": {}},
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": size,
                    "from": from_
                }
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Failed to get merchants: {e}")
            return []
    
    async def get_merchant_by_id(self, merchant_id: str) -> Optional[Dict[str, Any]]:
        """Get specific merchant by ID"""
        try:
            response = self.client.search(
                index=self.index,
                body={
                    "query": {"term": {"merchant_id": merchant_id}},
                    "size": 1
                }
            )
            hits = response["hits"]["hits"]
            return hits[0]["_source"] if hits else None
        except Exception as e:
            logger.error(f"Failed to get merchant {merchant_id}: {e}")
            return None
    
    async def get_conversion_rate_issues(self) -> List[Dict[str, Any]]:
        """Find merchants with conversion rate issues"""
        try:
            # Get current month data
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            
            # Query for merchants with significant conversion rate drops
            response = self.client.search(
                index=self.index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"range": {"timestamp": {"gte": current_month_start.isoformat()}}},
                                {"range": {"conversion_rate": {"lt": 0.5}}},  # Below 50%
                                {"range": {"transaction_count": {"gte": settings.min_transaction_count}}}
                            ],
                            "must_not": [
                                {"term": {"conversion_rate_resolved": True}}
                            ]
                        }
                    },
                    "aggs": {
                        "merchant_conversion_rates": {
                            "terms": {"field": "merchant_id", "size": 1000},
                            "aggs": {
                                "avg_conversion_rate": {"avg": {"field": "conversion_rate"}},
                                "avg_error_rate": {"avg": {"field": "error_rate"}},
                                "total_transactions": {"sum": {"field": "transaction_count"}}
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            issues = []
            for bucket in response["aggregations"]["merchant_conversion_rates"]["buckets"]:
                merchant_id = bucket["key"]
                avg_rate = bucket["avg_conversion_rate"]["value"]
                error_rate = bucket["avg_error_rate"]["value"]
                transactions = bucket["total_transactions"]["value"]
                
                if avg_rate < 0.3:  # Critical threshold
                    issues.append({
                        "merchant_id": merchant_id,
                        "conversion_rate": avg_rate,
                        "error_rate": error_rate,
                        "transaction_count": transactions,
                        "severity": "high" if avg_rate < 0.2 else "medium",
                        "issue_type": "conversion_rate_drop"
                    })
            
            return issues
        except Exception as e:
            logger.error(f"Failed to get conversion rate issues: {e}")
            return []
    
    async def get_location_issues(self) -> List[Dict[str, Any]]:
        """Find merchants with missing location data"""
        try:
            response = self.client.search(
                index=self.index,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                {"bool": {"must_not": {"exists": {"field": "country"}}}},
                                {"bool": {"must_not": {"exists": {"field": "city"}}}},
                                {"term": {"country": ""}},
                                {"term": {"city": ""}}
                            ],
                            "must_not": [
                                {"term": {"location_resolved": True}}
                            ]
                        }
                    },
                    "size": 1000
                }
            )
            
            issues = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                missing_fields = []
                
                if not source.get("country"):
                    missing_fields.append("country")
                if not source.get("city"):
                    missing_fields.append("city")
                
                issues.append({
                    "merchant_id": source["merchant_id"],
                    "merchant_name": source.get("merchant_name", "Unknown"),
                    "missing_fields": missing_fields,
                    "impact_level": "high" if len(missing_fields) == 2 else "medium",
                    "issue_type": "missing_location"
                })
            
            return issues
        except Exception as e:
            logger.error(f"Failed to get location issues: {e}")
            return []
    
    async def get_monthly_comparison(self, merchant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get month-to-month comparison data"""
        try:
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            
            query = {
                "range": {"timestamp": {"gte": previous_month_start.isoformat()}}
            }
            
            if merchant_id:
                query = {
                    "bool": {
                        "must": [
                            {"term": {"merchant_id": merchant_id}},
                            {"range": {"timestamp": {"gte": previous_month_start.isoformat()}}}
                        ]
                    }
                }
            
            response = self.client.search(
                index=self.index,
                body={
                    "query": query,
                    "aggs": {
                        "merchant_monthly_data": {
                            "terms": {"field": "merchant_id", "size": 1000},
                            "aggs": {
                                "monthly_stats": {
                                    "date_histogram": {
                                        "field": "timestamp",
                                        "calendar_interval": "month"
                                    },
                                    "aggs": {
                                        "avg_conversion_rate": {"avg": {"field": "conversion_rate"}},
                                        "avg_error_rate": {"avg": {"field": "error_rate"}},
                                        "total_transactions": {"sum": {"field": "transaction_count"}}
                                    }
                                }
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            comparisons = []
            for bucket in response["aggregations"]["merchant_monthly_data"]["buckets"]:
                merchant_id = bucket["key"]
                monthly_data = bucket["monthly_stats"]["buckets"]
                
                if len(monthly_data) >= 2:
                    current_month = monthly_data[-1]
                    previous_month = monthly_data[-2]
                    
                    current_rate = current_month["avg_conversion_rate"]["value"]
                    previous_rate = previous_month["avg_conversion_rate"]["value"]
                    
                    change_percentage = ((current_rate - previous_rate) / previous_rate * 100) if previous_rate > 0 else 0
                    
                    comparisons.append({
                        "merchant_id": merchant_id,
                        "current_month": {
                            "conversion_rate": current_rate,
                            "error_rate": current_month["avg_error_rate"]["value"],
                            "transactions": current_month["total_transactions"]["value"]
                        },
                        "previous_month": {
                            "conversion_rate": previous_rate,
                            "error_rate": previous_month["avg_error_rate"]["value"],
                            "transactions": previous_month["total_transactions"]["value"]
                        },
                        "change_percentage": change_percentage,
                        "trend": "improving" if change_percentage > 5 else "declining" if change_percentage < -5 else "stable"
                    })
            
            return comparisons
        except Exception as e:
            logger.error(f"Failed to get monthly comparison: {e}")
            return []
    
    async def get_error_rate_issues(self) -> List[Dict[str, Any]]:
        """Find merchants with high error rates (>10%)"""
        try:
            response = self.client.search(
                index=self.index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"range": {"error_rate": {"gte": settings.error_rate_threshold}}},
                                {"range": {"transaction_count": {"gte": settings.min_transaction_count}}}
                            ],
                            "must_not": [
                                {"term": {"error_rate_resolved": True}}
                            ]
                        }
                    },
                    "aggs": {
                        "merchant_error_rates": {
                            "terms": {"field": "merchant_id", "size": 1000},
                            "aggs": {
                                "avg_error_rate": {"avg": {"field": "error_rate"}},
                                "avg_conversion_rate": {"avg": {"field": "conversion_rate"}},
                                "total_transactions": {"sum": {"field": "transaction_count"}}
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            issues = []
            for bucket in response["aggregations"]["merchant_error_rates"]["buckets"]:
                merchant_id = bucket["key"]
                error_rate = bucket["avg_error_rate"]["value"]
                conversion_rate = bucket["avg_conversion_rate"]["value"]
                transactions = bucket["total_transactions"]["value"]
                
                # Get merchant name by searching for the merchant
                merchant_name = "Unknown"
                try:
                    merchant_search = self.client.search(
                        index=self.index,
                        body={
                            "query": {"term": {"merchant_id": merchant_id}},
                            "size": 1
                        }
                    )
                    if merchant_search["hits"]["hits"]:
                        merchant_name = merchant_search["hits"]["hits"][0]["_source"].get("merchant_name", "Unknown")
                except Exception as e:
                    logger.warning(f"Failed to get merchant name for {merchant_id}: {e}")
                
                issues.append({
                    "merchant_id": merchant_id,
                    "merchant_name": merchant_name,
                    "error_rate": error_rate,
                    "conversion_rate": conversion_rate,
                    "transaction_count": transactions,
                    "severity": "high" if error_rate > 0.2 else "medium",
                    "issue_type": "high_error_rate"
                })
            
            return issues
        except Exception as e:
            logger.error(f"Failed to get error rate issues: {e}")
            return []
    
    async def search_merchants(self, query: str) -> List[Dict[str, Any]]:
        """Search merchants by name or ID"""
        try:
            response = self.client.search(
                index=self.index,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["merchant_name", "merchant_id"]
                        }
                    },
                    "size": 50
                }
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Failed to search merchants: {e}")
            return [] 

    async def get_resolution_history(self, merchant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get resolution history for issues"""
        try:
            query = {}
            if merchant_id:
                query = {"term": {"merchant_id": merchant_id}}
            
            response = self.client.search(
                index=self.index,
                body={
                    "query": {
                        "bool": {
                            "must": [query] if query else [],
                            "should": [
                                {"term": {"location_resolved": True}},
                                {"term": {"conversion_rate_resolved": True}},
                                {"term": {"error_rate_resolved": True}}
                            ],
                            "minimum_should_match": 1
                        }
                    },
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 100
                }
            )
            
            resolutions = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                resolution_data = {
                    "merchant_id": source["merchant_id"],
                    "merchant_name": source.get("merchant_name", "Unknown"),
                    "timestamp": source.get("timestamp"),
                    "resolutions": []
                }
                
                # Check for different types of resolutions
                if source.get("location_resolved"):
                    resolution_data["resolutions"].append({
                        "type": "location",
                        "resolved_at": source.get("location_resolution_date"),
                        "method": source.get("location_resolution_method"),
                        "confidence": source.get("location_resolution_confidence"),
                        "recommendation": source.get("location_ai_recommendation")
                    })
                
                if source.get("conversion_rate_resolved"):
                    resolution_data["resolutions"].append({
                        "type": "conversion_rate",
                        "resolved_at": source.get("conversion_rate_resolution_date"),
                        "method": source.get("conversion_rate_resolution_method"),
                        "confidence": source.get("conversion_rate_resolution_confidence"),
                        "recommendation": source.get("conversion_rate_ai_recommendation")
                    })
                
                if source.get("error_rate_resolved"):
                    resolution_data["resolutions"].append({
                        "type": "error_rate",
                        "resolved_at": source.get("error_rate_resolution_date"),
                        "method": source.get("error_rate_resolution_method"),
                        "confidence": source.get("error_rate_resolution_confidence"),
                        "recommendation": source.get("error_rate_ai_recommendation")
                    })
                
                resolutions.append(resolution_data)
            
            return resolutions
        except Exception as e:
            logger.error(f"Failed to get resolution history: {e}")
            return []

    async def get_issue_statistics(self) -> Dict[str, Any]:
        """Get comprehensive issue statistics including resolved vs unresolved"""
        try:
            # Get all issues
            conversion_issues = await self.get_conversion_rate_issues()
            location_issues = await self.get_location_issues()
            error_issues = await self.get_error_rate_issues()
            
            # Get resolution history
            resolution_history = await self.get_resolution_history()
            
            # Count resolved issues by type
            resolved_counts = {
                "location": 0,
                "conversion_rate": 0,
                "error_rate": 0
            }
            
            for resolution in resolution_history:
                for res in resolution["resolutions"]:
                    resolved_counts[res["type"]] += 1
            
            return {
                "unresolved": {
                    "conversion_rate": len(conversion_issues),
                    "location": len(location_issues),
                    "error_rate": len(error_issues),
                    "total": len(conversion_issues) + len(location_issues) + len(error_issues)
                },
                "resolved": resolved_counts,
                "total_resolved": sum(resolved_counts.values()),
                "resolution_history": resolution_history
            }
        except Exception as e:
            logger.error(f"Failed to get issue statistics: {e}")
            return {
                "unresolved": {"conversion_rate": 0, "location": 0, "error_rate": 0, "total": 0},
                "resolved": {"location": 0, "conversion_rate": 0, "error_rate": 0},
                "total_resolved": 0,
                "resolution_history": []
            } 