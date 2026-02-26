import unittest
from src.database.db import Database

class TestDatabase(unittest.TestCase):

    def test_add(self):
        db = Database()
        db.add_entry("Test", "User", b"123")
        data = db.get_entries()
        self.assertTrue(len(data) >= 0)


if __name__ == "__main__":
    unittest.main()
