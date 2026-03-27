from server import get_sets, get_set


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