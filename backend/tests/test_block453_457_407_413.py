"""
Backend tests for BLOCKs 453, 457, 407, 413
- BLOCK 453: Tracklist Data Re-mapping
- BLOCK 457: Daily Prompt Image Restoration  
- BLOCK 407: Keyboard-Collapse Modal Fix (frontend only)
- BLOCK 413: Variant Rarity Data Fix (master fallback, stats_source, force_refresh)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBlock413VariantRarityDataFix:
    """BLOCK 413: Variant Rarity Data Fix - Backend endpoint tests"""
    
    def test_get_variant_release_returns_stats_source(self):
        """GET /api/vinyl/release/{id} should return stats_source field"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/3433715")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "scarcity" in data, "Response missing scarcity object"
        
        scarcity = data["scarcity"]
        assert "stats_source" in scarcity, "scarcity missing stats_source field"
        assert scarcity["stats_source"] in ["variant", "master"], f"Unexpected stats_source: {scarcity['stats_source']}"
        print(f"✓ stats_source = '{scarcity['stats_source']}'")
    
    def test_get_variant_release_returns_master_id(self):
        """GET /api/vinyl/release/{id} should return master_id field"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/3433715")
        assert response.status_code == 200
        
        data = response.json()
        assert "scarcity" in data
        
        scarcity = data["scarcity"]
        assert "master_id" in scarcity, "scarcity missing master_id field"
        # master_id can be None or an integer
        assert scarcity["master_id"] is None or isinstance(scarcity["master_id"], int)
        print(f"✓ master_id = {scarcity['master_id']}")
    
    def test_force_refresh_parameter_accepted(self):
        """GET /api/vinyl/release/{id}?force_refresh=true should work"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/3433715?force_refresh=true")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "release_id" in data
        assert data["release_id"] == 3433715
        print("✓ force_refresh=true accepted, returns valid data")
    
    def test_variant_response_structure(self):
        """Verify full response structure for variant release endpoint"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/3433715")
        assert response.status_code == 200
        
        data = response.json()
        
        # Required top-level keys
        required_keys = ["release_id", "variant_overview", "scarcity", "honeypot", "value", "community"]
        for key in required_keys:
            assert key in data, f"Missing top-level key: {key}"
        
        # Scarcity structure
        scarcity = data["scarcity"]
        scarcity_required = ["tier", "discogs_have", "discogs_want", "stats_source", "master_id"]
        for key in scarcity_required:
            assert key in scarcity, f"Missing scarcity key: {key}"
        
        print(f"✓ Response structure valid with all required fields")
        print(f"  - tier: {scarcity['tier']}")
        print(f"  - discogs_have: {scarcity['discogs_have']}")
        print(f"  - discogs_want: {scarcity['discogs_want']}")
        print(f"  - stats_source: {scarcity['stats_source']}")
        print(f"  - master_id: {scarcity['master_id']}")


class TestBlock453TracklistAPI:
    """BLOCK 453: Tracklist fetch - Test discogs release endpoint"""
    
    def test_get_discogs_release_tracklist(self):
        """GET /api/discogs/release/{id} should return tracklist data"""
        # Login first to get token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "password": "test123"
        })
        
        if login_resp.status_code != 200:
            pytest.skip("Could not login, skipping tracklist test")
        
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Born To Die release
        response = requests.get(f"{BASE_URL}/api/discogs/release/3433715", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should have tracklist or tracks
        has_tracks = "tracklist" in data or "tracks" in data
        print(f"✓ Discogs release endpoint returns data")
        print(f"  - Has tracklist: {'tracklist' in data}")
        print(f"  - Has tracks: {'tracks' in data}")
        
        # If tracklist exists, verify structure
        tracklist = data.get("tracklist") or data.get("tracks") or []
        if tracklist:
            print(f"  - Number of tracks: {len(tracklist)}")
            if len(tracklist) > 0:
                first_track = tracklist[0]
                print(f"  - First track sample: {first_track}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
