import pytest
from datetime import datetime
from app.models import (
    Merchant, MerchantStatus, ConversionRateAnalysis, 
    LocationIssue, MonthlyComparison, TroubleshootingRequest
)

class TestMerchant:
    def test_merchant_creation(self):
        """Test creating a merchant with valid data"""
        merchant = Merchant(
            merchant_id="TEST_001",
            merchant_name="Test Merchant",
            country="US",
            city="New York",
            conversion_rate=0.75,
            error_rate=0.05,
            transaction_count=1000,
            timestamp=datetime.now(),
            status=MerchantStatus.ACTIVE
        )
        
        assert merchant.merchant_id == "TEST_001"
        assert merchant.merchant_name == "Test Merchant"
        assert merchant.conversion_rate == 0.75
        assert merchant.status == MerchantStatus.ACTIVE

    def test_merchant_optional_fields(self):
        """Test creating a merchant with optional fields"""
        merchant = Merchant(
            merchant_id="TEST_002",
            merchant_name="Test Merchant 2",
            conversion_rate=0.5,
            error_rate=0.1,
            transaction_count=500,
            timestamp=datetime.now(),
            status=MerchantStatus.ACTIVE
        )
        
        assert merchant.country is None
        assert merchant.city is None

class TestConversionRateAnalysis:
    def test_conversion_analysis_creation(self):
        """Test creating conversion rate analysis"""
        analysis = ConversionRateAnalysis(
            merchant_id="TEST_001",
            merchant_name="Test Merchant",
            current_rate=0.25,
            previous_rate=0.75,
            change_percentage=-66.67,
            is_issue=True,
            severity="high",
            recommendation="Immediate intervention required"
        )
        
        assert analysis.merchant_id == "TEST_001"
        assert analysis.change_percentage == -66.67
        assert analysis.is_issue is True
        assert analysis.severity == "high"

class TestLocationIssue:
    def test_location_issue_creation(self):
        """Test creating location issue"""
        issue = LocationIssue(
            merchant_id="TEST_001",
            merchant_name="Test Merchant",
            missing_fields=["country", "city"],
            impact_level="high",
            recommendation="Update merchant profile immediately"
        )
        
        assert len(issue.missing_fields) == 2
        assert "country" in issue.missing_fields
        assert issue.impact_level == "high"

class TestTroubleshootingRequest:
    def test_troubleshooting_request_creation(self):
        """Test creating troubleshooting request"""
        request = TroubleshootingRequest(
            merchant_id="TEST_001",
            include_recommendations=True
        )
        
        assert request.merchant_id == "TEST_001"
        assert request.include_recommendations is True
        assert request.issue_type is None 