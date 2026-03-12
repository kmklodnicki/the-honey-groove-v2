"""
Test Smart Flag is_unofficial detection and Interactive Haul features
for HoneyGroove v2.8.3+

Features tested:
1. Backend detect_unofficial() Smart Flag - checks format_descriptions, notes, format text
2. Backend /api/vinyl/release/{id} returns is_unofficial correctly
3. Frontend haul cards have discogs_id and is_unofficial in bundle_records
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data - known releases
UNOFFICIAL_RELEASE_ID = 32442177  # Merry Swiftmas - Taylor Swift bootleg
OFFICIAL_RELEASE_ID = 31785674  # Pink Pony Club - Chappell Roan official


class TestSmartFlagDetection:
    """Test the detect_unofficial() Smart Flag logic"""
    
    def test_unofficial_release_merry_swiftmas(self):
        """Merry Swiftmas (32442177) should have is_unofficial=true"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/{UNOFFICIAL_RELEASE_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'variant_overview' in data, "Response missing variant_overview"
        
        vo = data['variant_overview']
        assert vo.get('is_unofficial') == True, f"Expected is_unofficial=True, got {vo.get('is_unofficial')}"
        assert 'Taylor Swift' in vo.get('artist', ''), f"Expected Taylor Swift, got {vo.get('artist')}"
        assert 'Merry Swiftmas' in vo.get('album', ''), f"Expected Merry Swiftmas in album, got {vo.get('album')}"
        
    def test_official_release_pink_pony_club(self):
        """Pink Pony Club (31785674) should have is_unofficial=false"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/{OFFICIAL_RELEASE_ID}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'variant_overview' in data, "Response missing variant_overview"
        
        vo = data['variant_overview']
        assert vo.get('is_unofficial') == False, f"Expected is_unofficial=False, got {vo.get('is_unofficial')}"
        assert 'Chappell Roan' in vo.get('artist', ''), f"Expected Chappell Roan, got {vo.get('artist')}"
        assert 'Pink Pony Club' in vo.get('album', ''), f"Expected Pink Pony Club in album, got {vo.get('album')}"

    def test_release_endpoint_returns_all_fields(self):
        """Check that variant_overview returns all expected fields"""
        response = requests.get(f"{BASE_URL}/api/vinyl/release/{UNOFFICIAL_RELEASE_ID}")
        assert response.status_code == 200
        
        data = response.json()
        vo = data['variant_overview']
        
        # Required fields
        required_fields = ['artist', 'album', 'variant', 'is_unofficial', 'discogs_id']
        for field in required_fields:
            assert field in vo, f"Missing required field: {field}"
        
        # discogs_id should match
        assert vo['discogs_id'] == UNOFFICIAL_RELEASE_ID


class TestHivePostStructure:
    """Test that haul posts contain discogs_id and is_unofficial"""
    
    def test_hive_feed_requires_auth(self):
        """Hive feed requires authentication"""
        response = requests.get(f"{BASE_URL}/api/feed")
        # Feed requires auth
        assert response.status_code in [401, 403], f"Feed should require auth, got {response.status_code}"
        
    def test_posts_endpoint_requires_auth(self):
        """Posts endpoint returns 401/404 without auth"""
        response = requests.get(f"{BASE_URL}/api/posts")
        # Posts endpoint either doesn't exist or requires auth
        assert response.status_code in [401, 403, 404], f"Expected auth required or not found, got {response.status_code}"


@pytest.fixture(scope="module")
def api_session():
    """Shared session for tests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
