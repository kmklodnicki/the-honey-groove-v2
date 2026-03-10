"""
Test Vinyl Rarity Score System
Tests the rarity calculation and /api/vinyl/rarity/{discogs_id} endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestRarityCalculation:
    """Tests for rarity score calculation in variant page response"""
    
    def test_chappell_roan_rarity_in_variant_page(self):
        """Test that rarity object is included in variant page response"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity")
        
        # Verify rarity object exists with all required fields
        assert rarity is not None, "rarity field should be present in response"
        assert "score" in rarity, "rarity should have 'score' field"
        assert "tier" in rarity, "rarity should have 'tier' field"
        assert "owners" in rarity, "rarity should have 'owners' field"
        assert "collectors_seeking" in rarity, "rarity should have 'collectors_seeking' field"
        assert "active_listings" in rarity, "rarity should have 'active_listings' field"
    
    def test_chappell_roan_rarity_tier_calculation(self):
        """Test rarity tier is calculated correctly for Chappell Roan - Baby Pink
        Expected: 1 owner (5pts) + 0 seeking/1 owner ratio (1pt) + 0 listings (5pts) = 11 → Very Rare"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity", {})
        
        assert rarity.get("score") == 11, f"Expected score 11, got {rarity.get('score')}"
        assert rarity.get("tier") == "Very Rare", f"Expected 'Very Rare' tier, got {rarity.get('tier')}"
        assert rarity.get("owners") == 1, f"Expected 1 owner, got {rarity.get('owners')}"
    
    def test_charli_xcx_rarity_in_variant_page(self):
        """Test rarity is included for Charli XCX - Brat (Black Translucent)"""
        response = requests.get(f"{BASE_URL}/api/vinyl/charli-xcx/brat/black-translucent")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity")
        
        assert rarity is not None, "rarity field should be present"
        assert "score" in rarity
        assert "tier" in rarity
        assert rarity.get("tier") in ["Ultra Rare", "Very Rare", "Rare", "Uncommon", "Common"]


class TestRarityEndpoint:
    """Tests for the lightweight /api/vinyl/rarity/{discogs_id} endpoint"""
    
    def test_rarity_endpoint_returns_data(self):
        """Test /api/vinyl/rarity/{discogs_id} returns rarity data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/31785674")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        assert "score" in data
        assert "tier" in data
        assert "owners" in data
        assert "collectors_seeking" in data
        assert "active_listings" in data
        assert "discogs_id" in data
        
        # Extra fields for identification
        assert data.get("discogs_id") == 31785674
        assert data.get("artist") == "Chappell Roan"
        assert data.get("album") == "Pink Pony Club"
        assert data.get("variant") == "Baby Pink"
    
    def test_rarity_endpoint_nonexistent_id(self):
        """Test /api/vinyl/rarity/{discogs_id} handles nonexistent IDs gracefully"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/88888888")
        
        # Should not return 500 error
        assert response.status_code != 500, f"Got server error: {response.text}"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should still return rarity object with defaults
        assert "score" in data
        assert "tier" in data
        assert data.get("discogs_id") == 88888888
        assert data.get("owners") == 0, "Nonexistent ID should have 0 owners"
    
    def test_rarity_charli_xcx_endpoint(self):
        """Test rarity endpoint for Charli XCX (discogs_id: 30984958)"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/30984958")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("discogs_id") == 30984958
        assert data.get("tier") in ["Ultra Rare", "Very Rare", "Rare", "Uncommon", "Common"]


class TestRarityTierThresholds:
    """Tests validating the rarity tier calculation thresholds"""
    
    def test_tier_mapping_logic(self):
        """Verify tier thresholds from backend code:
        Ultra Rare: >= 13
        Very Rare: >= 10
        Rare: >= 7
        Uncommon: >= 4
        Common: >= 0
        """
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity", {})
        score = rarity.get("score", 0)
        tier = rarity.get("tier", "")
        
        # Validate tier matches score based on thresholds
        if score >= 13:
            assert tier == "Ultra Rare", f"Score {score} should be Ultra Rare"
        elif score >= 10:
            assert tier == "Very Rare", f"Score {score} should be Very Rare"
        elif score >= 7:
            assert tier == "Rare", f"Score {score} should be Rare"
        elif score >= 4:
            assert tier == "Uncommon", f"Score {score} should be Uncommon"
        else:
            assert tier == "Common", f"Score {score} should be Common"


class TestRarityDataConsistency:
    """Tests that rarity data is consistent between endpoints"""
    
    def test_variant_page_matches_rarity_endpoint(self):
        """Verify rarity data in variant page matches standalone rarity endpoint"""
        # Get from variant page
        variant_response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert variant_response.status_code == 200
        variant_rarity = variant_response.json().get("rarity", {})
        
        # Get from rarity endpoint
        rarity_response = requests.get(f"{BASE_URL}/api/vinyl/rarity/31785674")
        assert rarity_response.status_code == 200
        rarity_data = rarity_response.json()
        
        # Core fields should match
        assert variant_rarity.get("score") == rarity_data.get("score"), "Scores should match"
        assert variant_rarity.get("tier") == rarity_data.get("tier"), "Tiers should match"
        assert variant_rarity.get("owners") == rarity_data.get("owners"), "Owners count should match"
        assert variant_rarity.get("collectors_seeking") == rarity_data.get("collectors_seeking")
        assert variant_rarity.get("active_listings") == rarity_data.get("active_listings")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
