import importlib
import os
import tempfile
import unittest


class InMemoryPersistenceTests(unittest.TestCase):
    def test_inmemory_database_persists_across_instances(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ['MEMORY_DB_PATH'] = os.path.join(temp_dir, 'memory_db.json')
            import database.connection as connection_module

            connection_module = importlib.reload(connection_module)
            first_client = connection_module.InMemoryClient()
            first_client.get_default_database(default='miniproject').users.insert_one({'email': 'persist@example.com'})

            second_client = connection_module.InMemoryClient()
            stored_user = second_client.get_default_database(default='miniproject').users.find_one({'email': 'persist@example.com'})

            self.assertIsNotNone(stored_user)
            self.assertEqual(stored_user['email'], 'persist@example.com')


if __name__ == '__main__':
    unittest.main()
