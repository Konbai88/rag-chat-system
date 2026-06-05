"""utils/md5 模块的单元测试"""
import os
import tempfile
from utils.md5 import check_md5, save_md5, get_string_md5, delete_md5
import config.config_data as config


def setup_function():
    """每个测试前重置 md5.text 文件"""
    if os.path.exists(config.md5_path):
        os.remove(config.md5_path)


def test_get_string_md5():
    """测试 MD5 计算是否正确"""
    result = get_string_md5("hello")
    assert result == "5d41402abc4b2a76b9719d911017c592"
    result = get_string_md5("test123")
    assert result == "cc03e747a6afbbcbf8be7668acfebee5"


def test_check_md5_returns_false_for_new_file():
    """文件不存在时 check_md5 应返回 False"""
    assert check_md5("anything") is False


def test_save_and_check_md5():
    """保存 MD5 后应能通过 check_md5 查到"""
    test_hash = "a1b2c3d4"
    save_md5(test_hash)
    assert check_md5(test_hash) is True


def test_check_md5_for_unknown_hash():
    """未保存的 MD5 应返回 False"""
    save_md5("existing_hash")
    assert check_md5("non_existent") is False


def test_delete_md5():
    """删除 MD5 后应不再能被查到"""
    test_hash = "deletable_hash"
    save_md5(test_hash)
    assert check_md5(test_hash) is True
    delete_md5(test_hash)
    assert check_md5(test_hash) is False


def test_delete_md5_nonexistent():
    """删除不存在的 MD5 应返回 False"""
    assert delete_md5("non_existent") is False
