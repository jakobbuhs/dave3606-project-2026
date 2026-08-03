import io
import struct

import server
from server import get_sets, get_set, get_set_binary
from read_binary_set import read_string


class MockDatabase:
    def __init__(self, set_data, bricks_data=None):
        self.set_data = set_data
        self.bricks_data = bricks_data or []

    def execute_and_fetch_all(self, query, vars=None):
        #Save query to mock for future testing
        self.endpoint_query = query
        if "lego_set" in query:
            return self.set_data
        return self.bricks_data

    def close(self):
        pass

def test_get_sets():
    #Arrange mock data
    mock_data = [
    ("25-2", "Basic Set"),
    ("35-2", "Basic Set"),
    ("611-3", "Police Car {La Redoute Version} (054 4965)"),
    ("700.0-2", "Gift Package (Swiss Edition)"),
    ("785-2", "Red Box"),
    ("955-2", "TC logo Slot Card Pack (Apple)"),
    ("965-1", "TC logo Slot Card Pack (MS-DOS)"),
    ("1081-1", "Baseplates and Beams"),
]
    mock_db = MockDatabase(mock_data)

    #Call function
    result = get_sets(mock_db, "utf-8")


    #Check if result is valid
    assert mock_db.endpoint_query == "select id, name from lego_set order by id"

    #Check if the values from mock data exists

    assert "25-2" in result
    assert "785-2" in result
    assert "Basic Set" in result
    assert "Red Box" in result

def test_api_set():
    #Arrange mock data for test
    mock_set = [("00-1", "Weetabix Castle", 1970, "Catalog: Sets: LEGOLAND: Castle")]

    mock_bricks = [
    ("Black Brick, Round 1 x 1 - Solid Stud, Bottom Lip", 11, 8),
    ("Blue Brick 1 x 2", 7, 3),
    ("Blue Brick 2 x 2 without Inside Supports", 7, 3),
]
    
    mock_db = MockDatabase(mock_set, mock_bricks)

    #Perform Query
    result = get_set(mock_db, "00-1")

    #Test results

    #Test for set
    assert result["name"] == "Weetabix Castle"
    assert result["year"] == 1970

    #Test for bricks
    assert len(result["bricks"]) == 3
    brick_names = [b["name"] for b in result["bricks"]]
    assert "Black Brick, Round 1 x 1 - Solid Stud, Bottom Lip" in brick_names
    assert "Blue Brick 1 x 2" in brick_names
    assert "Blue Brick 2 x 2 without Inside Supports" in brick_names
    assert result["bricks"]


def test_binary_set_round_trip():
    # Encode a set with get_set_binary (the writer in server.py) and decode it
    # again using read_string (the reader helper in read_binary_set.py). The two
    # sides must agree on the custom big-endian, length-prefixed format.
    mock_set = [("00-1", "Weetabix Castle", 1970, "Catalog: Sets: LEGOLAND: Castle")]
    mock_bricks = [
        ("Blue Brick 1 x 2", 7, 3),
        ("Black Brick, Round 1 x 1 - Solid Stud, Bottom Lip", 11, 8),
    ]
    mock_db = MockDatabase(mock_set, mock_bricks)

    blob = get_set_binary(mock_db, "00-1")

    f = io.BytesIO(blob)
    assert f.read(4) == b"LEGO"                      # magic bytes
    assert read_string(f) == "00-1"                  # set id
    assert read_string(f) == "Weetabix Castle"       # name
    assert struct.unpack(">H", f.read(2))[0] == 1970 # year
    assert read_string(f) == "Catalog: Sets: LEGOLAND: Castle"  # category

    num_bricks = struct.unpack(">I", f.read(4))[0]
    assert num_bricks == 2

    decoded = []
    for _ in range(num_bricks):
        name = read_string(f)
        color_id = struct.unpack(">i", f.read(4))[0]
        count = struct.unpack(">i", f.read(4))[0]
        decoded.append((name, color_id, count))

    assert decoded == mock_bricks                    # bricks survive the round trip
    assert f.read() == b""                           # no trailing bytes


class CacheMockDatabase:
    """Minimal Database stand-in for exercising the /api/set endpoint without
    a live PostgreSQL instance. Returns a synthetic row for the requested id."""

    def execute_and_fetch_all(self, query, vars=None):
        if "lego_set" in query:
            set_id = vars[0]
            return [(set_id, f"Name {set_id}", 2000, "cat")]
        return []  # no bricks

    def close(self):
        pass


def test_api_set_lru_eviction(monkeypatch):
    # Fill the LRU cache past capacity and assert it never grows beyond the cap
    # and that the least-recently-used entries are the ones evicted.
    monkeypatch.setattr(server, "Database", CacheMockDatabase)
    server.set_cache.clear()
    client = server.app.test_client()

    cap = server.CACHE_MAX_SIZE
    total = cap + 5
    for i in range(total):
        resp = client.get(f"/api/set?id=set-{i}")
        assert resp.status_code == 200

    assert len(server.set_cache) == cap
    # The first five inserted ids are the least recently used -> evicted.
    for i in range(5):
        assert f"set-{i}" not in server.set_cache
    # The most recently inserted ids are still present.
    assert f"set-{total - 1}" in server.set_cache
    assert "set-5" in server.set_cache


def test_api_set_recently_used_survives_eviction(monkeypatch):
    # A cache HIT should move an entry to most-recently-used, protecting it from
    # eviction when a new entry is later inserted.
    monkeypatch.setattr(server, "Database", CacheMockDatabase)
    server.set_cache.clear()
    client = server.app.test_client()

    cap = server.CACHE_MAX_SIZE
    for i in range(cap):
        client.get(f"/api/set?id=set-{i}")
    assert len(server.set_cache) == cap

    # Touch the oldest entry so it becomes most-recently-used (cache HIT path).
    client.get("/api/set?id=set-0")
    # Insert one new entry, forcing a single eviction.
    client.get(f"/api/set?id=set-{cap}")

    assert len(server.set_cache) == cap
    assert "set-0" in server.set_cache      # protected by the recent access
    assert "set-1" not in server.set_cache  # now the true least-recently-used