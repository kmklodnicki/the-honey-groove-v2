"""
Test Vinyl Rarity Score System - Discogs-Sourced Data
Tests the rarity calculation using Discogs community stats (have/want/num_for_sale)
and /api/vinyl/rarity/{discogs_id} endpoint

Key changes from previous version:
- Rarity now uses Discogs community stats instead of Honeygroove platform data
- Fields: discogs_owners, discogs_wantlist, listings_available (not owners, collectors_seeking, active_listings)
- Score calculation: _owner_score + _demand_score + _supply_score
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestRarityCalculation:
    """Tests for rarity score calculation using Discogs community data"""
    
    def test_chappell_roan_rarity_fields(self):
        """Test that rarity object has all Discogs-sourced fields"""
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity")
        
        # Verify rarity object exists with Discogs-sourced fields
        assert rarity is not None, "rarity field should be present in response"
        assert "score" in rarity, "rarity should have 'score' field"
        assert "tier" in rarity, "rarity should have 'tier' field"
        assert "discogs_owners" in rarity, "rarity should have 'discogs_owners' field"
        assert "discogs_wantlist" in rarity, "rarity should have 'discogs_wantlist' field"
        assert "listings_available" in rarity, "rarity should have 'listings_available' field"
    
    def test_chappell_roan_common_tier(self):
        """Test Chappell Roan - Baby Pink has Common tier (8949 owners = score 1)
        
        Calculation:
        - _owner_score(8949) = 1 (>5000 owners)
        - _demand_score(1027, 8949) = 1 (ratio ~0.11, < 0.5)
        - _supply_score(72) = 1 (>50 listings)
        - Total = 3 → Common tier
        """
        response = requests.get(f"{BASE_URL}/api/vinyl/chappell-roan/pink-pony-club/baby-pink")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity", {})
        
        assert rarity.get("tier") == "Common", f"Expected 'Common' tier, got {rarity.get('tier')}"
        assert rarity.get("score") == 3, f"Expected score 3, got {rarity.get('score')}"
        assert rarity.get("discogs_owners") == 8949, f"Expected 8949 owners, got {rarity.get('discogs_owners')}"
        assert rarity.get("discogs_wantlist") == 1027, f"Expected 1027 wantlist, got {rarity.get('discogs_wantlist')}"
        assert rarity.get("listings_available") == 72, f"Expected 72 listings, got {rarity.get('listings_available')}"
    
    def test_charli_xcx_uncommon_tier(self):
        """Test Charli XCX - Brat has Uncommon tier (4204 owners)
        
        Calculation:
        - _owner_score(4204) = 2 (1000-5000 owners)
        - _demand_score(516, 4204) = 1 (ratio ~0.12, < 0.5)
        - _supply_score(73) = 1 (>50 listings)
        - Total = 4 → Uncommon tier
        """
        response = requests.get(f"{BASE_URL}/api/vinyl/charli-xcx/brat/black-translucent")
        assert response.status_code == 200
        
        data = response.json()
        rarity = data.get("rarity", {})
        
        assert rarity.get("tier") == "Uncommon", f"Expected 'Uncommon' tier, got {rarity.get('tier')}"
        assert rarity.get("score") == 4, f"Expected score 4, got {rarity.get('score')}"
        assert rarity.get("discogs_owners") == 4204, f"Expected 4204 owners, got {rarity.get('discogs_owners')}"


class TestRarityEndpoint:
    """Tests for the lightweight /api/vinyl/rarity/{discogs_id} endpoint"""
    
    def test_chappell_roan_rarity_endpoint(self):
        """Test /api/vinyl/rarity/31785674 returns Discogs-sourced rarity data"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/31785674")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required Discogs-sourced fields
        assert "score" in data
        assert "tier" in data
        assert "discogs_owners" in data
        assert "discogs_wantlist" in data
        assert "listings_available" in data
        assert "discogs_id" in data
        
        # Metadata fields
        assert data.get("discogs_id") == 31785674
        assert data.get("artist") == "Chappell Roan"
        assert data.get("album") == "Pink Pony Club"
        assert data.get("variant") == "Baby Pink"
        
        # Verify tier and data
        assert data.get("tier") == "Common"
        assert data.get("discogs_owners") == 8949
    
    def test_charli_xcx_rarity_endpoint(self):
        """Test /api/vinyl/rarity/30984958 returns Uncommon tier (different from Chappell Roan)"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/30984958")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("discogs_id") == 30984958
        assert data.get("tier") == "Uncommon", f"Expected 'Uncommon', got {data.get('tier')}"
        assert data.get("artist") == "Charli XCX"
        assert data.get("album") == "Brat"
        assert data.get("discogs_owners") == 4204
    
    def test_borns_very_rare_tier(self):
        """Test /api/vinyl/rarity/33762579 (BORNS) returns Very Rare tier
        
        Expected: 71 owners, 0 listings → Very Rare
        Calculation:
        - _owner_score(71) = 4 (50-200 owners)
        - _demand_score(12, 71) = 1 (ratio ~0.17, < 0.5)
        - _supply_score(0) = 5 (0 listings)
        - Total = 10 → Very Rare tier
        """
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/33762579")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("discogs_id") == 33762579
        assert data.get("tier") == "Very Rare", f"Expected 'Very Rare', got {data.get('tier')}"
        assert data.get("discogs_owners") == 71
        assert data.get("listings_available") == 0
    
    def test_nonexistent_id_graceful_handling(self):
        """Test /api/vinyl/rarity/99999999 handles nonexistent release gracefully (no 500)"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/99999999")
        
        # Should not return 500 error
        assert response.status_code != 500, f"Got server error: {response.text}"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should still return rarity object with defaults
        assert "score" in data
        assert "tier" in data
        assert data.get("discogs_id") == 99999999
        assert data.get("discogs_owners") == 0, "Nonexistent ID should have 0 owners"
        assert data.get("discogs_wantlist") == 0, "Nonexistent ID should have 0 wantlist"
        assert data.get("listings_available") == 0, "Nonexistent ID should have 0 listings"


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
    
    def test_score_calculation_chappell_roan(self):
        """Verify score calculation: _owner_score(8949)=1, _demand_score(1027,8949)=1, _supply_score(72)=1 = 3"""
        response = requests.get(f"{BASE_URL}/api/vinyl/rarity/31785674")
        assert response.status_code == 200
        
        data = response.json()
        
        # With 8949 owners: _owner_score = 1 (>5000)
        # With ratio 1027/8949 ≈ 0.11: _demand_score = 1 (<0.5)
        # With 72 listings: _supply_score = 1 (>50)
        # Total = 1 + 1 + 1 = 3
        assert data.get("score") == 3, f"Expected score 3, got {data.get('score')}"


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
        assert variant_rarity.get("discogs_owners") == rarity_data.get("discogs_owners"), "Discogs owners count should match"
        assert variant_rarity.get("discogs_wantlist") == rarity_data.get("discogs_wantlist"), "Discogs wantlist should match"
        assert variant_rarity.get("listings_available") == rarity_data.get("listings_available"), "Listings available should match"
    
    def test_charli_xcx_vs_chappell_roan_different_tiers(self):
        """Verify Charli XCX (Uncommon) has different tier than Chappell Roan (Common)"""
        chappell_response = requests.get(f"{BASE_URL}/api/vinyl/rarity/31785674")
        charli_response = requests.get(f"{BASE_URL}/api/vinyl/rarity/30984958")
        
        assert chappell_response.status_code == 200
        assert charli_response.status_code == 200
        
        chappell_tier = chappell_response.json().get("tier")
        charli_tier = charli_response.json().get("tier")
        
        assert chappell_tier == "Common", f"Chappell Roan should be Common, got {chappell_tier}"
        assert charli_tier == "Uncommon", f"Charli XCX should be Uncommon, got {charli_tier}"
        assert chappell_tier != charli_tier, "Tiers should be different"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
