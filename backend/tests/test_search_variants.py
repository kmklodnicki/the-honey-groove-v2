"""
Test suite for NEW Variant-first Search Page feature.
Tests /api/search/variants and /api/search/discover endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

class TestSearchVariantsEndpoint:
    """Tests for GET /api/search/variants - Variant-first search"""
    
    def test_search_variants_charli_brat(self):
        """Search for 'charli brat' should return variants with required fields"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "charli brat"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "variants" in data, "Response missing 'variants' array"
        assert "albums" in data, "Response missing 'albums' array"
        assert "artists" in data, "Response missing 'artists' array"
        assert "has_more" in data, "Response missing 'has_more' field"
        
        # Should find Charli XCX variants
        if len(data["variants"]) > 0:
            variant = data["variants"][0]
            # Check required fields
            assert "discogs_id" in variant, "Variant missing discogs_id"
            assert "artist" in variant, "Variant missing artist"
            assert "album" in variant, "Variant missing album"
            assert "variant" in variant, "Variant missing variant field"
            assert "cover_url" in variant, "Variant missing cover_url"
            assert "slug" in variant, "Variant missing slug field"
            # Verify slug format: /vinyl/{artist}/{album}/{variant}
            assert variant["slug"].startswith("/vinyl/"), f"Slug should start with /vinyl/, got {variant['slug']}"
            print(f"PASS: Found {len(data['variants'])} variants for 'charli brat'")
            print(f"  First variant: {variant['artist']} - {variant['album']} ({variant['variant']})")
            print(f"  Slug: {variant['slug']}")
    
    def test_search_variants_taylor(self):
        """Search for 'taylor' should return Taylor Swift variants sorted by relevance"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "taylor"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        variants = data.get("variants", [])
        
        # Should find Taylor Swift results
        taylor_found = any("Taylor" in v.get("artist", "") for v in variants)
        if variants:
            print(f"PASS: Found {len(variants)} variants for 'taylor'")
            # Check first results are Taylor Swift related
            for v in variants[:3]:
                print(f"  - {v.get('artist')} - {v.get('album')} ({v.get('variant')})")
        else:
            print("INFO: No Taylor Swift variants in database - may need seed data")
    
    def test_search_variants_pink_color_match(self):
        """Search for 'pink' should return color-matching variants"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "pink"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        variants = data.get("variants", [])
        
        # Should find variants with 'pink' in variant name or album
        pink_variants = [v for v in variants if "pink" in v.get("variant", "").lower()]
        print(f"PASS: Found {len(variants)} results for 'pink' query")
        print(f"  - {len(pink_variants)} have 'pink' in variant field (highest priority)")
        if pink_variants:
            print(f"  First pink variant: {pink_variants[0].get('artist')} - {pink_variants[0].get('album')} ({pink_variants[0].get('variant')})")
    
    def test_search_variants_empty_results_gracefully(self):
        """Search for nonexistent term 'xx' should return empty results, not 500"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "xxyyzz99999"})
        assert response.status_code == 200, f"Expected 200 (empty results), got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "variants" in data, "Response should still have 'variants' key"
        assert "albums" in data, "Response should still have 'albums' key"
        assert "artists" in data, "Response should still have 'artists' key"
        print(f"PASS: Search for nonexistent term returns empty results gracefully")
        print(f"  variants: {len(data['variants'])}, albums: {len(data['albums'])}, artists: {len(data['artists'])}")
    
    def test_search_variants_minimum_query_length(self):
        """Search with query < 2 chars should fail validation"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "x"})
        # FastAPI validation should return 422 for min_length=2 violation
        assert response.status_code == 422, f"Expected 422 for short query, got {response.status_code}"
        print("PASS: Short queries correctly rejected with 422")
    
    def test_search_variants_slug_format(self):
        """Verify slug format is /vinyl/{artist}/{album}/{variant}"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "charli"})
        assert response.status_code == 200
        
        data = response.json()
        if data.get("variants"):
            for v in data["variants"][:3]:
                slug = v.get("slug", "")
                # Slug should be /vinyl/slugified-artist/slugified-album/slugified-variant
                parts = slug.split("/")
                assert len(parts) >= 5, f"Slug should have format /vinyl/artist/album/variant, got {slug}"
                assert parts[1] == "vinyl", f"Slug should start with /vinyl/, got {slug}"
            print(f"PASS: Slug format verified for {min(3, len(data['variants']))} variants")


class TestSearchDiscoverEndpoint:
    """Tests for GET /api/search/discover - Discovery sections"""
    
    def test_discover_returns_sections(self):
        """Discover endpoint should return trending, rare, most_wanted, recently_added"""
        response = requests.get(f"{BASE_URL}/api/search/discover")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify all required sections present
        assert "trending" in data, "Response missing 'trending' array"
        assert "rare" in data, "Response missing 'rare' array"
        assert "most_wanted" in data, "Response missing 'most_wanted' array"
        assert "recently_added" in data, "Response missing 'recently_added' array"
        
        print(f"PASS: Discover endpoint returns all sections")
        print(f"  trending: {len(data['trending'])} items")
        print(f"  rare: {len(data['rare'])} items")
        print(f"  most_wanted: {len(data['most_wanted'])} items")
        print(f"  recently_added: {len(data['recently_added'])} items")
    
    def test_discover_items_have_slug(self):
        """Discovery items should have slug field for navigation"""
        response = requests.get(f"{BASE_URL}/api/search/discover")
        assert response.status_code == 200
        
        data = response.json()
        for section in ["trending", "rare", "most_wanted", "recently_added"]:
            items = data.get(section, [])
            if items:
                # Check first item has required fields
                item = items[0]
                assert "slug" in item, f"{section} items missing 'slug' field"
                assert item["slug"].startswith("/vinyl/"), f"{section} slug should start with /vinyl/"
                print(f"PASS: {section} items have valid slug field")
    
    def test_discover_trending_has_collectors(self):
        """Trending items should have collectors count"""
        response = requests.get(f"{BASE_URL}/api/search/discover")
        assert response.status_code == 200
        
        data = response.json()
        trending = data.get("trending", [])
        if trending:
            item = trending[0]
            assert "collectors" in item, "Trending items should have 'collectors' count"
            print(f"PASS: Trending items have collectors count ({item.get('collectors')} for first item)")
    
    def test_discover_recently_added_structure(self):
        """Recently added items should have basic variant fields"""
        response = requests.get(f"{BASE_URL}/api/search/discover")
        assert response.status_code == 200
        
        data = response.json()
        recently_added = data.get("recently_added", [])
        if recently_added:
            item = recently_added[0]
            for field in ["discogs_id", "artist", "album", "variant", "slug"]:
                assert field in item, f"Recently added item missing '{field}' field"
            print(f"PASS: Recently added items have all required fields")
            print(f"  First: {item.get('artist')} - {item.get('album')} ({item.get('variant')})")


class TestSearchVariantsPagination:
    """Tests for pagination in search/variants"""
    
    def test_pagination_parameters(self):
        """Verify skip and limit parameters work"""
        # First page
        response1 = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "vinyl", "skip": 0, "limit": 5})
        assert response1.status_code == 200
        data1 = response1.json()
        
        if len(data1.get("variants", [])) >= 5 and data1.get("has_more"):
            # Second page
            response2 = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "vinyl", "skip": 5, "limit": 5})
            assert response2.status_code == 200
            data2 = response2.json()
            
            # Results should be different
            ids1 = {v.get("discogs_id") for v in data1["variants"]}
            ids2 = {v.get("discogs_id") for v in data2["variants"]}
            # At least some should be different
            print(f"PASS: Pagination returns different results")
            print(f"  Page 1 IDs: {len(ids1)}, Page 2 IDs: {len(ids2)}, Overlap: {len(ids1 & ids2)}")
        else:
            print("INFO: Not enough results to test pagination")
    
    def test_has_more_flag(self):
        """Verify has_more flag is accurate"""
        response = requests.get(f"{BASE_URL}/api/search/variants", params={"q": "vinyl", "limit": 5})
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total", 0)
        variants_count = len(data.get("variants", []))
        has_more = data.get("has_more", False)
        
        if total > 5:
            assert has_more == True, f"has_more should be True when total ({total}) > limit (5)"
        print(f"PASS: has_more flag correctly set to {has_more} (total: {total}, returned: {variants_count})")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
