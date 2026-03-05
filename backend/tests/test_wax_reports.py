"""
Wax Reports API Tests - Testing 'Your Week in Wax' feature
Tests cover:
- POST /api/wax-reports/generate - Generate full report
- GET /api/wax-reports/latest - Get latest report for authenticated user
- GET /api/wax-reports/latest/{username} - Get public latest report
- GET /api/wax-reports/history - Get list of past reports
- GET /api/wax-reports/{report_id} - Get specific report by ID
- POST /api/wax-reports/regenerate-label/{report_id} - Regenerate personality label (once per report)
- GET /api/wax-reports/{report_id}/share-card - Get 1080x1080 PNG share card
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWaxReportsAuth:
    """Test authentication for wax reports endpoints"""
    
    def test_latest_requires_auth(self):
        """GET /api/wax-reports/latest requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ GET /api/wax-reports/latest requires auth")
    
    def test_history_requires_auth(self):
        """GET /api/wax-reports/history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/history")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ GET /api/wax-reports/history requires auth")
    
    def test_generate_requires_auth(self):
        """POST /api/wax-reports/generate requires authentication"""
        response = requests.post(f"{BASE_URL}/api/wax-reports/generate")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ POST /api/wax-reports/generate requires auth")


class TestWaxReportsPublic:
    """Test public endpoints"""
    
    def test_public_latest_for_user(self):
        """GET /api/wax-reports/latest/{username} returns public report (no auth required)"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest/demo")
        # Should work if report exists, or 404 if no report yet
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "personality" in data or "id" in data
            print(f"✓ GET /api/wax-reports/latest/demo returns report with id: {data.get('id')}")
        else:
            print("✓ GET /api/wax-reports/latest/demo returns 404 (no report yet)")
    
    def test_public_latest_invalid_user(self):
        """GET /api/wax-reports/latest/{username} returns 404 for non-existent user"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest/nonexistentuser12345")
        assert response.status_code == 404
        print("✓ GET /api/wax-reports/latest/{invalid_user} returns 404")


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for demo user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@example.com",
        "password": "password123"
    })
    if response.status_code != 200:
        pytest.skip("Authentication failed - skipping authenticated tests")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="class")
def headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestWaxReportsGenerate:
    """Test report generation"""
    
    def test_generate_report(self, headers):
        """POST /api/wax-reports/generate creates a full report"""
        response = requests.post(f"{BASE_URL}/api/wax-reports/generate", headers=headers)
        assert response.status_code == 200, f"Generate failed: {response.text}"
        
        data = response.json()
        
        # Verify required fields exist
        required_fields = [
            "id", "user_id", "username", "week_start", "week_end",
            "personality", "listening_stats", "top_artists", "top_records",
            "top_genres", "era_breakdown", "mood_breakdown", "collection_value",
            "wantlist_pulse", "social_stats", "closing_line"
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ POST /api/wax-reports/generate creates report: {data['id']}")
        print(f"  - personality: {data['personality'].get('key')} - {data['personality'].get('label', '')[:50]}...")
        print(f"  - total_spins: {data.get('total_spins', 0)}")
        print(f"  - week: {data['week_start'][:10]} to {data['week_end'][:10]}")
        return data
    
    def test_report_personality_structure(self, headers):
        """Report personality contains key and label"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        personality = data.get("personality", {})
        assert "key" in personality, "personality missing 'key'"
        assert "label" in personality, "personality missing 'label'"
        assert isinstance(personality["label"], str)
        print(f"✓ Personality has key: {personality['key']}, label: {personality['label'][:50]}...")
    
    def test_report_listening_stats_structure(self, headers):
        """Report listening_stats has 6 required stats"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        ls = data.get("listening_stats", {})
        required_stats = ["total_spins", "unique_records", "avg_spins_per_record", 
                         "longest_listening_day", "most_active_day", "most_active_time"]
        for stat in required_stats:
            assert stat in ls, f"listening_stats missing '{stat}'"
        
        print(f"✓ Listening stats: spins={ls['total_spins']}, unique={ls['unique_records']}, "
              f"day={ls['most_active_day']}, time={ls['most_active_time']}")
    
    def test_report_collection_value_structure(self, headers):
        """Report collection_value has value, change, most_valuable, hidden_gem, over_X counts"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        cv = data.get("collection_value", {})
        required_fields = ["total_value", "value_change", "over_50", "over_100", "over_200"]
        for field in required_fields:
            assert field in cv, f"collection_value missing '{field}'"
        
        print(f"✓ Collection value: ${cv['total_value']}, change: {cv['value_change']}, "
              f"over_50: {cv['over_50']}, over_100: {cv['over_100']}, over_200: {cv['over_200']}")
        
        # Check optional fields
        if cv.get("most_valuable"):
            mv = cv["most_valuable"]
            assert "title" in mv and "artist" in mv
            print(f"  - Most valuable: {mv['title']} by {mv['artist']} (${mv.get('value', 0)})")
        
        if cv.get("hidden_gem"):
            hg = cv["hidden_gem"]
            assert "title" in hg and "artist" in hg
            print(f"  - Hidden gem: {hg['title']} by {hg['artist']}")
    
    def test_report_wantlist_pulse_structure(self, headers):
        """Report wantlist_pulse has total, matches_found, longest_hunt_days, trending"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        wp = data.get("wantlist_pulse", {})
        required_fields = ["total", "matches_found", "longest_hunt_days"]
        for field in required_fields:
            assert field in wp, f"wantlist_pulse missing '{field}'"
        
        print(f"✓ Wantlist pulse: total={wp['total']}, matches={wp['matches_found']}, "
              f"longest_hunt={wp['longest_hunt_days']}d")
        
        if wp.get("trending"):
            t = wp["trending"]
            print(f"  - Trending: {t.get('artist')} - {t.get('album')} ({t.get('want_count')} wants)")
    
    def test_report_social_stats_structure(self, headers):
        """Report social_stats has followers, posts, trades"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        ss = data.get("social_stats", {})
        required_fields = ["new_followers", "total_posts", "trades_completed"]
        for field in required_fields:
            assert field in ss, f"social_stats missing '{field}'"
        
        print(f"✓ Social stats: followers={ss['new_followers']}, posts={ss['total_posts']}, "
              f"trades={ss['trades_completed']}")
        
        if ss.get("most_liked_post"):
            mlp = ss["most_liked_post"]
            print(f"  - Most liked: {mlp.get('content', '')[:40]}... ({mlp.get('likes')} likes)")


class TestWaxReportsRetrieve:
    """Test report retrieval endpoints"""
    
    def test_get_latest_report(self, headers):
        """GET /api/wax-reports/latest returns user's most recent report"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "personality" in data
        print(f"✓ GET /api/wax-reports/latest returns report: {data['id']}")
        return data["id"]
    
    def test_get_report_by_id(self, headers):
        """GET /api/wax-reports/{report_id} returns specific report"""
        # First get latest to know the ID
        latest = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert latest.status_code == 200
        report_id = latest.json()["id"]
        
        # Now fetch by ID
        response = requests.get(f"{BASE_URL}/api/wax-reports/{report_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == report_id
        print(f"✓ GET /api/wax-reports/{report_id} returns correct report")
    
    def test_get_report_history(self, headers):
        """GET /api/wax-reports/history returns list of past reports"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            # Each item should have id, week_start, week_end, personality
            item = data[0]
            assert "id" in item
            assert "week_start" in item
            assert "week_end" in item
        
        print(f"✓ GET /api/wax-reports/history returns {len(data)} report(s)")
        return data
    
    def test_get_invalid_report_id(self, headers):
        """GET /api/wax-reports/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/invalid-report-id-12345", headers=headers)
        assert response.status_code == 404
        print("✓ GET /api/wax-reports/{invalid_id} returns 404")


class TestWaxReportsRegenerate:
    """Test personality label regeneration"""
    
    def test_regenerate_label(self, headers):
        """POST /api/wax-reports/regenerate-label/{report_id} changes personality"""
        # First get the latest report
        latest = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert latest.status_code == 200
        report = latest.json()
        report_id = report["id"]
        
        # Check if already regenerated
        if report.get("label_regenerated"):
            print(f"⚠ Report {report_id} already had label regenerated, skipping second regen test")
            return
        
        original_label = report["personality"]["label"]
        
        # Regenerate
        response = requests.post(f"{BASE_URL}/api/wax-reports/regenerate-label/{report_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "personality" in data
        assert "closing_line" in data
        print(f"✓ Regenerated label from '{original_label[:30]}...' to '{data['personality']['label'][:30]}...'")
        return report_id
    
    def test_regenerate_label_twice_fails(self, headers):
        """POST /api/wax-reports/regenerate-label/{report_id} second call returns 400"""
        # Get latest report (should now have label_regenerated = True)
        latest = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert latest.status_code == 200
        report = latest.json()
        report_id = report["id"]
        
        # Try to regenerate again
        response = requests.post(f"{BASE_URL}/api/wax-reports/regenerate-label/{report_id}", headers=headers)
        
        # Should be 400 if already regenerated
        if report.get("label_regenerated"):
            assert response.status_code == 400, f"Expected 400 for already regenerated, got {response.status_code}"
            print(f"✓ Second regenerate attempt correctly returns 400")
        else:
            # First regeneration - should succeed
            assert response.status_code == 200
            print(f"✓ First regenerate succeeded, need another call to test 400")
            
            # Now try again - should fail
            response2 = requests.post(f"{BASE_URL}/api/wax-reports/regenerate-label/{report_id}", headers=headers)
            assert response2.status_code == 400
            print(f"✓ Second regenerate attempt correctly returns 400")


class TestWaxReportsShareCard:
    """Test share card image generation"""
    
    def test_share_card_returns_png(self, headers):
        """GET /api/wax-reports/{report_id}/share-card returns 1080x1080 PNG"""
        # Get latest report ID
        latest = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert latest.status_code == 200
        report_id = latest.json()["id"]
        
        # Get share card
        response = requests.get(f"{BASE_URL}/api/wax-reports/{report_id}/share-card", headers=headers)
        assert response.status_code == 200, f"Share card failed: {response.status_code}"
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "image/png" in content_type, f"Expected image/png, got {content_type}"
        
        # Check PNG magic bytes
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n', "Not a valid PNG file"
        
        print(f"✓ GET /api/wax-reports/{report_id}/share-card returns valid PNG")
        print(f"  - Content-Type: {content_type}")
        print(f"  - Size: {len(response.content)} bytes")
        return response.content
    
    def test_share_card_dimensions(self, headers):
        """Share card PNG is 1080x1080 pixels"""
        from PIL import Image
        import io
        
        # Get latest report ID
        latest = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert latest.status_code == 200
        report_id = latest.json()["id"]
        
        # Get share card
        response = requests.get(f"{BASE_URL}/api/wax-reports/{report_id}/share-card", headers=headers)
        assert response.status_code == 200
        
        # Open as image and check dimensions
        img = Image.open(io.BytesIO(response.content))
        width, height = img.size
        
        assert width == 1080, f"Expected width 1080, got {width}"
        assert height == 1080, f"Expected height 1080, got {height}"
        
        print(f"✓ Share card dimensions: {width}x{height} (correct 1080x1080)")
    
    def test_share_card_requires_auth(self):
        """GET /api/wax-reports/{report_id}/share-card requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/some-id/share-card")
        assert response.status_code in [401, 403]
        print("✓ Share card endpoint requires auth")
    
    def test_share_card_invalid_report(self, headers):
        """GET /api/wax-reports/{invalid_id}/share-card returns 404"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/invalid-id-12345/share-card", headers=headers)
        assert response.status_code == 404
        print("✓ Share card for invalid report returns 404")


class TestWaxReportsDataIntegrity:
    """Test data integrity and structure"""
    
    def test_era_breakdown_has_percentages(self, headers):
        """Era breakdown includes decade, spins, and pct"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        era = data.get("era_breakdown", [])
        if len(era) > 0:
            item = era[0]
            assert "decade" in item
            assert "pct" in item
            print(f"✓ Era breakdown has {len(era)} eras: {[e['decade'] for e in era[:3]]}")
    
    def test_top_artists_have_spin_counts(self, headers):
        """Top artists have artist name and spin counts"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        artists = data.get("top_artists", [])
        if len(artists) > 0:
            item = artists[0]
            assert "artist" in item
            assert "spins" in item
            top_artists_str = ", ".join([f"{a['artist']} ({a['spins']} spins)" for a in artists[:3]])
            print(f"✓ Top {len(artists)} artists: {top_artists_str}")
    
    def test_top_records_have_cover_art(self, headers):
        """Top records have title, artist, cover_url, and spin counts"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        records = data.get("top_records", [])
        if len(records) > 0:
            item = records[0]
            assert "title" in item
            assert "artist" in item
            assert "spins" in item
            # cover_url may be None for some records
            print(f"✓ Top {len(records)} records: {[r['title'][:30] for r in records[:3]]}")
    
    def test_closing_line_exists(self, headers):
        """Report has a closing line"""
        response = requests.get(f"{BASE_URL}/api/wax-reports/latest", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        closing = data.get("closing_line", "")
        assert closing, "Missing closing_line"
        assert len(closing) > 10, "closing_line too short"
        print(f"✓ Closing line: {closing[:60]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
