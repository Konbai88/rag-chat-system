import os
import hashlib
import config.config_data as config


def check_md5(md5_str: str) -> bool:
    """检查 md5 是否已存在（防重复入库）"""
    if not os.path.exists(config.md5_path):
        open(config.md5_path, "w", encoding="utf-8").close()
        return False
    with open(config.md5_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if md5_str == line.strip():
                return True
    return False


def save_md5(md5_str: str) -> None:
    """保存 md5 到文件"""
    with open(config.md5_path, "a", encoding="utf-8") as f:
        f.write(md5_str + "\n")


def get_string_md5(input_str: str, encoding: str = "utf-8") -> str:
    """计算字符串的 MD5 值"""
    return hashlib.md5(input_str.encode(encoding=encoding)).hexdigest()


def delete_md5(md5_str: str) -> bool:
    """从文件中删除指定的 md5"""
    if not os.path.exists(config.md5_path):
        return False
    new_lines: list[str] = []
    target_found = False
    with open(config.md5_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            if line.strip() == md5_str:
                target_found = True
            else:
                new_lines.append(line)
    if not target_found:
        return False
    with open(config.md5_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return True
