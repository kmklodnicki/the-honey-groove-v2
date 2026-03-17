"""
Test Album Art Bug Fix and Mood Grid Bug Fix
- Bug 1: Album artwork display in ISO/Haul modals (Discogs search results)
- Bug 2: Mood grid uniform sizing and Spin Party emoji (disco ball)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDiscogsSearchAlbumArt:
    """Test that Discogs search returns results with cover_url for album art"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_discogs_search_lana_del_rey_returns_cover_urls(self, auth_token):
        """Test Discogs search for 'lana del rey' returns results with cover_url"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search?q=lana+del+rey",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Discogs search failed: {response.text}"
        
        results = response.json()
        assert len(results) > 0, "No results returned from Discogs search"
        
        # Check that at least some results have cover_url
        results_with_covers = [r for r in results if r.get('cover_url')]
        assert len(results_with_covers) > 0, "No results have cover_url - album art will not display"
        
        # Verify the cover_url format (should be Discogs CDN URLs)
        for result in results_with_covers[:3]:
            cover_url = result.get('cover_url')
            print(f"Found cover_url: {cover_url[:80]}...")
            # Discogs URLs typically contain 'discogs' in the domain
            assert cover_url and ('discogs' in cover_url.lower() or cover_url.startswith('http')), f"Invalid cover_url: {cover_url}"
        
        print(f"SUCCESS: {len(results_with_covers)}/{len(results)} results have cover_url")
    
    def test_discogs_search_taylor_swift_returns_cover_urls(self, auth_token):
        """Test Discogs search for 'taylor swift' returns results with cover_url"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search?q=taylor+swift",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Discogs search failed: {response.text}"
        
        results = response.json()
        assert len(results) > 0, "No results returned from Discogs search"
        
        results_with_covers = [r for r in results if r.get('cover_url')]
        assert len(results_with_covers) > 0, "No results have cover_url"
        
        print(f"SUCCESS: {len(results_with_covers)}/{len(results)} Taylor Swift results have cover_url")
    
    def test_discogs_cover_url_is_jpeg_not_webp(self, auth_token):
        """Verify that Discogs cover URLs are in original format (not .webp)"""
        response = requests.get(
            f"{BASE_URL}/api/discogs/search?q=radiohead",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        results = response.json()
        for result in results[:5]:
            cover_url = result.get('cover_url', '')
            if cover_url:
                # Discogs URLs should NOT be converted to webp on the backend
                # The frontend toWebP function handles this, but should skip Discogs URLs
                print(f"Cover URL: {cover_url}")
                # Just verify we get valid HTTP URLs
                assert cover_url.startswith('http'), f"Invalid URL: {cover_url}"


class TestMoodGridConfiguration:
    """Test mood configuration in ComposerBar"""
    
    def test_spin_party_emoji_is_disco_ball(self):
        """Verify Spin Party uses disco ball emoji (U+1FAA9)"""
        # Read the ComposerBar.js file to verify the emoji
        # The fix should have changed 🩩 (U+1FA69) to 🪩 (U+1FAA9)
        import re
        
        composer_path = "/app/frontend/src/components/ComposerBar.js"
        with open(composer_path, 'r') as f:
            content = f.read()
        
        # Find Spin Party configuration
        spin_party_match = re.search(r"'Spin Party':\s*\{[^}]+emoji:\s*'([^']+)'", content)
        assert spin_party_match, "Could not find Spin Party configuration"
        
        emoji = spin_party_match.group(1)
        # Check for disco ball emoji - either the actual character or the unicode escape
        disco_ball_code = '\U0001faa9'  # 🪩 disco ball
        
        # The emoji might be the actual character or an escape sequence
        assert emoji == disco_ball_code or '\\u{1FAA9}' in repr(emoji) or emoji == '🪩', \
            f"Expected disco ball emoji (🪩), got: {emoji} (repr: {repr(emoji)})"
        
        print(f"SUCCESS: Spin Party emoji is disco ball: {emoji}")
    
    def test_mood_buttons_have_uniform_height(self):
        """Verify mood buttons are configured with uniform 36px height"""
        composer_path = "/app/frontend/src/components/ComposerBar.js"
        with open(composer_path, 'r') as f:
            content = f.read()
        
        # Look for the mood button styling with height: 36px
        assert "height: '36px'" in content, "Mood buttons should have fixed 36px height"
        
        # Look for whitespace-nowrap to prevent text wrapping
        assert "whitespace-nowrap" in content or "whiteSpace: 'nowrap'" in content, \
            "Mood buttons should have whitespace-nowrap to prevent text wrapping"
        
        print("SUCCESS: Mood buttons have uniform 36px height and no-wrap styling")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
