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
                http_auth=(settings.elasticsearch_username, settings.elasticsearch_password) if settings.elasticsearch_username else None,
                verify_certs=True
            )
        else:
            # Use traditional host/port connection
            self.client = Elasticsearch(
                hosts=[{
                    'host': settings.elasticsearch_host,
                    'port': settings.elasticsearch_port
                }],
                http_auth=(settings.elasticsearch_username, settings.elasticsearch_password) if settings.elasticsearch_username else None,
                use_ssl=settings.elasticsearch_use_ssl,
                verify_certs=True if settings.elasticsearch_use_ssl else False
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
                
                issues.append({
                    "merchant_id": merchant_id,
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