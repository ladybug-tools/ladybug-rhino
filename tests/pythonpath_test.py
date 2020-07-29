# coding=utf-8
from ladybug_rhino.pythonpath import iron_python_search_path_windows, \
    iron_python_search_path_mac

import os
import io
import plistlib


def test_iron_python_search_path_windows():
    """Test the iron_python_search_path_windows method with a sample XML file."""
    package_dir = os.path.join('ladybug_tools', 'python', 'Lib', 'site-packages')
    settings_file = './tests/ironpython/settings-Scheme__Default.xml'
    dest_file = './tests/ironpython/new_settings.xml'

    edited_file = iron_python_search_path_windows(package_dir, settings_file, dest_file)
    assert os.path.isfile(edited_file)

    with io.open(edited_file, 'r', encoding='utf-8') as fp:
        set_data = fp.read()
    assert package_dir in set_data
    os.remove(edited_file)


def test_iron_python_search_path_windows_mingbo():
    """Test the iron_python_search_path_windows method with Mingbo's sample XML file."""
    package_dir = os.path.join('ladybug_tools', 'python', 'Lib', 'site-packages')
    settings_file = './tests/ironpython/settings-Scheme__Default_mingbo.xml'
    dest_file = './tests/ironpython/new_settings_mingbo.xml'

    edited_file = iron_python_search_path_windows(package_dir, settings_file, dest_file)
    assert os.path.isfile(edited_file)

    with io.open(edited_file, 'r', encoding='utf-8') as fp:
        set_data = fp.read()
    assert package_dir in set_data
    os.remove(edited_file)


def test_iron_python_search_path_mac():
    """Test the iron_python_search_path_mac method with a sample plist file."""
    package_dir = os.path.join('ladybug_tools', 'python', 'Lib', 'site-packages')
    setting_file = './tests/ironpython/com.mcneel.rhinoceros.plist'
    dest_file = './tests/ironpython/new.settings.plist'

    edited_file = iron_python_search_path_mac(package_dir, setting_file, dest_file)

    assert os.path.isfile(edited_file)

    with open(edited_file, 'rb') as fp:
        pl = plistlib.load(fp)

    sp_key = 'User.Plug-Ins.814d908a-e25c-493d-97e9-ee3861957f49.Settings.SearchPaths'
    assert package_dir in pl[sp_key]
    os.remove(edited_file)
