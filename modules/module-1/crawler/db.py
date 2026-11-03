import os

import mysql.connector
from mysql.connector import Error


# =========================================================
# MySQL 基础配置
# =========================================================

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"

DB_NAME = "bidding_system"

# 不把数据库密码直接写死在代码里
# 从 Windows 环境变量读取
DB_PASSWORD = os.getenv(
    "BIDDING_DB_PASSWORD"
)


# =========================================================
# 获取数据库连接
# =========================================================

def get_connection():

    if not DB_PASSWORD:

        raise RuntimeError(
            "没有找到环境变量 BIDDING_DB_PASSWORD。"
            "请先设置 MySQL 密码环境变量。"
        )

    try:

        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            use_unicode=True,
        )

        return connection

    except Error as e:

        raise RuntimeError(
            f"MySQL 连接失败：{e}"
        )


# =========================================================
# 测试连接
# =========================================================

def test_connection():

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT DATABASE();"
        )

        database_name = (
            cursor.fetchone()[0]
        )

        print(
            "MySQL连接成功"
        )

        print(
            f"当前数据库：{database_name}"
        )

        return True

    except Exception as e:

        print(
            "MySQL连接失败：",
            e,
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if (
            connection
            and connection.is_connected()
        ):
            connection.close()


# =========================================================
# 直接运行 db.py 时测试
# =========================================================

if __name__ == "__main__":

    test_connection()