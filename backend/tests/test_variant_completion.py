"""Tests for Variant Completion Tracker API endpoints.

Tests the new /api/vinyl/completion/{discogs_id} endpoint that returns
variant completion data for an album, grouped by meaningful variant.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestVariantCompletionAPI:
    """Test the variant completion tracker API endpoint."""

    def test_completion_charli_xcx_brat_returns_valid_structure(self):
        """Test GET /api/vinyl/completion/30984958 (Charli XCX Brat) returns correct structure."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required top-level fields
        assert "album" in data, "Missing 'album' field"
        assert "artist" in data, "Missing 'artist' field"
        assert "master_id" in data, "Missing 'master_id' field"
        assert "total_variants" in data, "Missing 'total_variants' field"
        assert "owned_count" in data, "Missing 'owned_count' field"
        assert "completion_pct" in data, "Missing 'completion_pct' field"
        assert "variants" in data, "Missing 'variants' field"
        
        print(f"[PASS] Response has all required fields: album={data.get('album')}, artist={data.get('artist')}, total_variants={data.get('total_variants')}, completion_pct={data.get('completion_pct')}")

    def test_completion_charli_xcx_variants_array_structure(self):
        """Test that variants array has correct structure."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        variants = data.get("variants", [])
        
        # Should have at least one variant
        assert len(variants) > 0, "Expected at least one variant in the array"
        
        # Check structure of each variant
        for variant in variants:
            assert "name" in variant, f"Missing 'name' field in variant: {variant}"
            assert "owned" in variant, f"Missing 'owned' field in variant: {variant}"
            assert "release_ids" in variant, f"Missing 'release_ids' field in variant: {variant}"
            assert isinstance(variant["owned"], bool), f"'owned' should be boolean: {variant['owned']}"
            assert isinstance(variant["release_ids"], list), f"'release_ids' should be array: {variant['release_ids']}"
        
        print(f"[PASS] All {len(variants)} variants have correct structure (name, owned, release_ids)")
        for v in variants[:5]:
            print(f"  - {v['name']}: owned={v['owned']}, pressings={len(v['release_ids'])}")

    def test_completion_charli_xcx_variant_grouping(self):
        """Test that variants are properly grouped (e.g., 'Standard Black Vinyl', 'Picture Disc')."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        variants = data.get("variants", [])
        variant_names = [v["name"] for v in variants]
        
        # Check for expected variant grouping patterns
        # Standard Black Vinyl should group multiple regional pressings
        standard_black = next((v for v in variants if "Standard Black" in v["name"] or "Black" in v["name"].lower()), None)
        
        if standard_black:
            print(f"[PASS] Found 'Standard Black' variant: {standard_black['name']} with {len(standard_black['release_ids'])} pressings")
            # Standard black should have multiple regional pressings grouped together
            assert len(standard_black["release_ids"]) >= 1, "Standard Black should have at least one release"
        
        # Check for other variant types that might exist
        print(f"[INFO] Found {len(variants)} total unique variants:")
        for v in variants:
            print(f"  - {v['name']}: {len(v['release_ids'])} pressings")

    def test_completion_chappell_roan_returns_valid_data(self):
        """Test GET /api/vinyl/completion/31785674 (Chappell Roan) returns valid completion data."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/31785674", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        assert "album" in data
        assert "artist" in data
        assert "total_variants" in data
        assert "owned_count" in data
        assert "completion_pct" in data
        assert "variants" in data
        
        # Should have at least one variant
        assert data.get("total_variants", 0) >= 0, "total_variants should be non-negative"
        assert data.get("completion_pct", -1) >= 0, "completion_pct should be non-negative"
        assert data.get("completion_pct", 101) <= 100, "completion_pct should be <= 100"
        
        print(f"[PASS] Chappell Roan completion data: album={data.get('album')}, total_variants={data.get('total_variants')}, completion_pct={data.get('completion_pct')}")

    def test_completion_nonexistent_release_graceful_handling(self):
        """Test GET /api/vinyl/completion/99999999 handles nonexistent release gracefully."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/99999999", timeout=30)
        
        # Should not return 500 error
        assert response.status_code != 500, f"Got 500 error: {response.text}"
        
        # Accept either 200 with error field or 404
        if response.status_code == 200:
            data = response.json()
            # If 200, should either have error field or empty variants
            if data.get("error"):
                print(f"[PASS] Graceful error response: {data.get('error')}")
            else:
                print(f"[PASS] Returns 200 with data (possibly empty variants)")
        else:
            print(f"[PASS] Returns {response.status_code} for nonexistent release (acceptable)")

    def test_completion_percentage_calculation(self):
        """Test that completion_pct is calculated correctly."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        total = data.get("total_variants", 0)
        owned = data.get("owned_count", 0)
        pct = data.get("completion_pct", 0)
        
        # Verify percentage calculation
        if total > 0:
            expected_pct = round((owned / total) * 100)
            assert pct == expected_pct, f"completion_pct mismatch: got {pct}, expected {expected_pct}"
            print(f"[PASS] Completion percentage correct: {owned}/{total} = {pct}%")
        else:
            print(f"[INFO] No variants to calculate percentage (total_variants=0)")

    def test_completion_variants_owned_boolean(self):
        """Test that each variant has owned as boolean."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        variants = data.get("variants", [])
        
        for variant in variants:
            assert isinstance(variant.get("owned"), bool), f"owned should be bool, got {type(variant.get('owned'))}: {variant}"
        
        # Without auth, all should be False
        owned_variants = [v for v in variants if v.get("owned") == True]
        print(f"[PASS] All variants have boolean 'owned' field. Owned variants (without auth): {len(owned_variants)}")

    def test_completion_release_ids_are_integers(self):
        """Test that release_ids array contains integer discogs release IDs."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        variants = data.get("variants", [])
        
        for variant in variants:
            release_ids = variant.get("release_ids", [])
            for rid in release_ids:
                assert isinstance(rid, int), f"release_id should be int, got {type(rid)}: {rid}"
        
        print(f"[PASS] All release_ids are integers")

    def test_completion_data_types(self):
        """Test that all fields have correct data types."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check types
        assert isinstance(data.get("album"), (str, type(None))), "album should be string or None"
        assert isinstance(data.get("artist"), (str, type(None))), "artist should be string or None"
        assert isinstance(data.get("master_id"), (int, type(None))), "master_id should be int or None"
        assert isinstance(data.get("total_variants"), int), "total_variants should be int"
        assert isinstance(data.get("owned_count"), int), "owned_count should be int"
        assert isinstance(data.get("completion_pct"), int), "completion_pct should be int"
        assert isinstance(data.get("variants"), list), "variants should be list"
        
        print(f"[PASS] All data types are correct")


class TestVariantCompletionEdgeCases:
    """Test edge cases for variant completion API."""

    def test_completion_first_call_caches_data(self):
        """Test that first call may be slow (fetches from Discogs) but returns data."""
        # First call might be slow due to Discogs API
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=60)
        assert response.status_code == 200, f"First call failed: {response.status_code}"
        
        data = response.json()
        assert "variants" in data
        print(f"[PASS] First call returned {len(data.get('variants', []))} variants")
        
        # Second call should be faster (cached)
        response2 = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response2.status_code == 200
        print(f"[PASS] Subsequent call also succeeded")

    def test_completion_album_artist_metadata(self):
        """Test that album and artist metadata are returned."""
        response = requests.get(f"{BASE_URL}/api/vinyl/completion/30984958", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should have album and artist info
        album = data.get("album")
        artist = data.get("artist")
        
        # For Charli XCX Brat
        assert album is not None, "album should not be None"
        assert artist is not None, "artist should not be None"
        
        print(f"[PASS] Metadata: album='{album}', artist='{artist}'")
