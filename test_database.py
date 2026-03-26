import gzip

from server import get_sets


class MockDatabase:
    def __init__(self, mock_data):
        self.mock_data = mock_data

    def execute_and_fetch_all(self, query):
        #Save query to mock for future testing
        self.endpoint_query = query
        return self.mock_data

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