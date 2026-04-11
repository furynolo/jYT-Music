import os
from unittest.mock import patch
from utils.config import get_user_data_path, get_resource_path

def test_get_resource_path_dev():
    # In dev mode, it should point to root
    path = get_resource_path("docs/test.txt")
    assert "docs" in path
    assert "test.txt" in path
    assert os.path.isabs(path)

def test_get_user_data_path_windows():
    with patch('os.name', 'nt'):
        with patch.dict('os.environ', {'APPDATA': 'C:\\MockAppData'}):
            with patch('os.makedirs'): # Don't actually create folders
                path = get_user_data_path("test.json")
                assert path == os.path.join('C:\\MockAppData', 'jYT Music', 'test.json')

def test_get_user_data_path_posix():
    with patch('os.name', 'posix'):
        # Mock expanduser to return a fake home dir
        with patch('os.path.expanduser', return_value='/home/user/.jyt-music'):
            with patch('os.makedirs'):
                path = get_user_data_path("settings.json")
                # Use os.path.join to be cross-platform safe in the assertion
                expected = os.path.join('/home/user/.jyt-music', 'settings.json')
                assert path == expected
