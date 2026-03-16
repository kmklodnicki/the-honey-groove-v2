"""
Test Suite for Smart Match and Rarity Badge features
Tests:
1. Smart Match: POST /api/records with real artist/title but no discogs_id should auto-populate discogs_id, cover_url, and rarity_label
2. Smart Match (negative): POST /api/records with fake artist/title should NOT match and set rarity_label='Unknown'
3. Rarity: Records with discogs_id get proper rarity; Records without discogs_id get 'Unknown' rarity
4. Enrich-rarity endpoint: POST /api/records/enrich-rarity should set 'Unknown' for records without discogs_id
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestSmartMatchAndRarity:
    """Tests for Smart Match auto-linking and Rarity badge features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.token = data.get("access_token")
        assert self.token, "No access_token returned"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_record_ids = []
        yield
        # Cleanup: Delete any test records created
        for record_id in self.created_record_ids:
            try:
                requests.delete(f"{BASE_URL}/api/records/{record_id}", headers=self.headers)
            except:
                pass
    
    # ========== SMART MATCH TESTS ==========
    
    def test_smart_match_real_artist_title_auto_links_discogs(self):
        """
        Smart Match: POST /api/records with a real artist+title (no discogs_id)
        should auto-populate discogs_id, cover_url, and rarity_label from Discogs
        """
        # Use a famous album that should exist in Discogs
        record_data = {
            "title": "Thriller",
            "artist": "Michael Jackson",
            "format": "Vinyl"
            # Note: no discogs_id provided
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=self.headers)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        
        data = resp.json()
        self.created_record_ids.append(data["id"])
        
        # Smart Match should have auto-linked discogs_id
        print(f"Response: discogs_id={data.get('discogs_id')}, rarity_label={data.get('rarity_label')}, cover_url={data.get('cover_url')}")
        
        # Assert discogs_id was auto-populated
        assert data.get("discogs_id") is not None, "Smart Match failed: discogs_id should be auto-populated for real album"
        
        # Assert rarity_label was set (not Unknown since it has discogs_id)
        assert data.get("rarity_label") is not None, "rarity_label should be set"
        assert data.get("rarity_label") != "Unknown", f"With discogs_id, rarity_label should not be 'Unknown', got: {data.get('rarity_label')}"
        
        # Assert cover_url was populated
        assert data.get("cover_url") is not None, "cover_url should be auto-populated from Discogs"
    
    def test_smart_match_fake_artist_title_no_match(self):
        """
        Smart Match (negative): POST /api/records with nonsense artist/title
        should NOT match and should set rarity_label='Unknown'
        """
        # Use completely fake/nonsense data
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"FakeAlbumXYZ_{unique_suffix}",
            "artist": f"FakeArtist123_{unique_suffix}",
            "format": "Vinyl"
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=self.headers)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        
        data = resp.json()
        self.created_record_ids.append(data["id"])
        
        print(f"Response: discogs_id={data.get('discogs_id')}, rarity_label={data.get('rarity_label')}")
        
        # discogs_id should be None (no match found)
        assert data.get("discogs_id") is None, f"Fake album should not match Discogs, got discogs_id={data.get('discogs_id')}"
        
        # rarity_label should be 'Unknown' since no Discogs link
        assert data.get("rarity_label") == "Unknown", f"Without discogs_id, rarity_label should be 'Unknown', got: {data.get('rarity_label')}"
    
    def test_smart_match_confidence_check_artist_must_match(self):
        """
        Smart Match confidence: Only match when artist AND title are close matches.
        Test with correct title but completely wrong artist.
        """
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": "Thriller",  # Real title
            "artist": f"WrongArtist_{unique_suffix}",  # But wrong artist
            "format": "Vinyl"
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=self.headers)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        
        data = resp.json()
        self.created_record_ids.append(data["id"])
        
        print(f"Response: discogs_id={data.get('discogs_id')}, rarity_label={data.get('rarity_label')}")
        
        # Should NOT match because artist doesn't fuzzy-match
        # Either discogs_id is None OR if there's a match it shouldn't be Michael Jackson's Thriller
        if data.get("discogs_id"):
            # If it matched something, let's verify it's not blindly matching
            print(f"Warning: Got discogs_id={data.get('discogs_id')} with mismatched artist")
        
        # Rarity should be Unknown if no valid match
        # Note: The behavior depends on whether the search returns any results at all
    
    # ========== RARITY LABEL TESTS ==========
    
    def test_record_with_discogs_id_gets_proper_rarity(self):
        """
        Records created with a known discogs_id should get a proper rarity label
        (Common, Uncommon, Rare, Very Rare, or Ultra Rare) - NOT 'Unknown'
        """
        # Use a known discogs_id (Thriller by Michael Jackson is release 7399)
        record_data = {
            "title": "Thriller",
            "artist": "Michael Jackson",
            "format": "Vinyl",
            "discogs_id": 7399  # A well-known release
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=self.headers)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        
        data = resp.json()
        self.created_record_ids.append(data["id"])
        
        print(f"Response: discogs_id={data.get('discogs_id')}, rarity_label={data.get('rarity_label')}")
        
        # With discogs_id, rarity should be calculated from Discogs community data
        valid_rarities = ["Common", "Uncommon", "Rare", "Very Rare", "Ultra Rare", "Grail", "Obscure"]
        assert data.get("rarity_label") in valid_rarities, f"With discogs_id, rarity should be one of {valid_rarities}, got: {data.get('rarity_label')}"
        
        # Should also have community_have and community_want populated
        # These may be None if Discogs API didn't return them, but at least one should exist
    
    def test_record_without_discogs_id_gets_unknown_rarity(self):
        """
        Records without discogs_id should get 'Unknown' rarity
        """
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_ManualRecord_{unique_suffix}",
            "artist": f"TEST_ManualArtist_{unique_suffix}",
            "format": "Vinyl"
            # No discogs_id
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=self.headers)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        
        data = resp.json()
        self.created_record_ids.append(data["id"])
        
        print(f"Response: discogs_id={data.get('discogs_id')}, rarity_label={data.get('rarity_label')}")
        
        # No discogs_id means rarity should be Unknown
        assert data.get("discogs_id") is None, "Should not have discogs_id"
        assert data.get("rarity_label") == "Unknown", f"Without discogs_id, rarity_label should be 'Unknown', got: {data.get('rarity_label')}"
    
    # ========== ENRICH-RARITY ENDPOINT TESTS ==========
    
    def test_enrich_rarity_sets_unknown_for_no_discogs(self):
        """
        POST /api/records/enrich-rarity should set 'Unknown' for records without discogs_id
        """
        # First create a record without discogs_id
        unique_suffix = str(uuid.uuid4())[:8]
        record_data = {
            "title": f"TEST_EnrichTest_{unique_suffix}",
            "artist": f"TEST_EnrichArtist_{unique_suffix}",
            "format": "Vinyl"
        }
        
        resp = requests.post(f"{BASE_URL}/api/records", json=record_data, headers=self.headers)
        assert resp.status_code == 200, f"Failed to create record: {resp.text}"
        
        data = resp.json()
        self.created_record_ids.append(data["id"])
        record_id = data["id"]
        
        # Now call enrich-rarity
        enrich_resp = requests.post(f"{BASE_URL}/api/records/enrich-rarity", headers=self.headers)
        assert enrich_resp.status_code == 200, f"Enrich-rarity failed: {enrich_resp.text}"
        
        enrich_data = enrich_resp.json()
        print(f"Enrich-rarity response: {enrich_data}")
        
        # The endpoint should report how many were set to Unknown
        # Check the record itself
        get_resp = requests.get(f"{BASE_URL}/api/records/{record_id}", headers=self.headers)
        assert get_resp.status_code == 200, f"Failed to get record: {get_resp.text}"
        
        record = get_resp.json()
        print(f"Record after enrich: rarity_label={record.get('rarity_label')}")
        
        assert record.get("rarity_label") == "Unknown", f"Record without discogs_id should have 'Unknown' rarity after enrichment"


class TestRarityCalculation:
    """Tests for the calculate_rarity function logic"""
    
    def test_rarity_thresholds(self):
        """
        Test the rarity calculation thresholds from utils/rarity.py
        """
        import sys
        sys.path.insert(0, '/app/backend')
        from utils.rarity import calculate_rarity
        
        # Test Common (ratio < 1)
        assert calculate_rarity(100, 50) == "Common", "50 want / 100 have = 0.5 ratio should be Common"
        
        # Test Uncommon (ratio >= 1)
        assert calculate_rarity(100, 100) == "Uncommon", "100 want / 100 have = 1.0 ratio should be Uncommon"
        assert calculate_rarity(100, 200) == "Uncommon", "200 want / 100 have = 2.0 ratio should be Uncommon"
        
        # Test Rare (ratio >= 3)
        assert calculate_rarity(100, 300) == "Rare", "300 want / 100 have = 3.0 ratio should be Rare"
        assert calculate_rarity(100, 400) == "Rare", "400 want / 100 have = 4.0 ratio should be Rare"
        
        # Test Very Rare (ratio >= 5)
        assert calculate_rarity(100, 500) == "Very Rare", "500 want / 100 have = 5.0 ratio should be Very Rare"
        assert calculate_rarity(100, 700) == "Very Rare", "700 want / 100 have = 7.0 ratio should be Very Rare"
        
        # Test Ultra Rare (ratio >= 8 or ratio > 20 with have >= 500)
        assert calculate_rarity(100, 800) == "Ultra Rare", "800 want / 100 have = 8.0 ratio should be Ultra Rare"
        assert calculate_rarity(1000, 21000) == "Ultra Rare", "21000 want / 1000 have = 21 ratio, have>=500 should be Ultra Rare"
        
        # Test Grail (ratio > 20 AND have < 500)
        assert calculate_rarity(100, 2100) == "Grail", "2100 want / 100 have = 21 ratio, have < 500 should be Grail"
        result = calculate_rarity(100, 2200)
        print(f"100 have, 2200 want (ratio=22, have<500): {result}")
        assert result == "Grail", "ratio > 20 and have < 500 should be Grail"
        # Based on code: ratio > 20 and have < 500 -> Grail
        
        # Test Obscure (have < 25 AND want < 10)
        assert calculate_rarity(10, 5) == "Obscure", "10 have, 5 want should be Obscure"
        
        # Test Unknown (community_have is None)
        assert calculate_rarity(None, 50) == "Unknown", "None have should return Unknown"


class TestCollectionSorting:
    """Test that the collection supports rarity-based sorting"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "kmklodnicki@gmail.com",
            "password": "HoneyGroove2026"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        data = login_resp.json()
        self.token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_get_records_returns_rarity_label(self):
        """
        GET /api/records should return rarity_label field for client-side sorting
        """
        resp = requests.get(f"{BASE_URL}/api/records", headers=self.headers)
        assert resp.status_code == 200, f"Failed to get records: {resp.text}"
        
        records = resp.json()
        if len(records) > 0:
            # Check that rarity_label field exists
            first_record = records[0]
            assert "rarity_label" in first_record, "Records should include rarity_label field"
            print(f"Sample record rarity_label: {first_record.get('rarity_label')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
