# 数据库配置文件
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
from datetime import datetime, timedelta

class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库连接配置
    DB_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'database': 'lawyer_assistant',
        'user': 'root',  # 请根据实际情况修改
        'password': '',  # 请根据实际情况修改
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    @staticmethod
    def get_connection():
        """获取数据库连接"""
        try:
            connection = mysql.connector.connect(**DatabaseConfig.DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"数据库连接错误: {e}")
            return None
    
    @staticmethod
    def close_connection(connection):
        """关闭数据库连接"""
        if connection and connection.is_connected():
            connection.close()

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        self.connection = DatabaseConfig.get_connection()
        return self.connection is not None
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            DatabaseConfig.close_connection(self.connection)
            self.connection = None
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"查询执行错误: {e}")
            return None
    
    def execute_update(self, query, params=None):
        """执行更新语句"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Error as e:
            print(f"更新执行错误: {e}")
            self.connection.rollback()
            return -1
    
    def execute_insert(self, query, params=None):
        """执行插入语句，返回插入的ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            insert_id = cursor.lastrowid
            cursor.close()
            return insert_id
        except Error as e:
            print(f"插入执行错误: {e}")
            self.connection.rollback()
            return -1

class UserManager:
    """用户管理类"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    @staticmethod
    def hash_password(password):
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_session_token():
        """生成会话令牌"""
        return secrets.token_urlsafe(32)
    
    def authenticate_user(self, username, password):
        """用户认证"""
        hashed_password = self.hash_password(password)
        query = """
            SELECT id, username, full_name, role, status 
            FROM users 
            WHERE username = %s AND password = %s AND status = 'active'
        """
        result = self.db.execute_query(query, (username, hashed_password))
        
        if result:
            user = result[0]
            # 更新最后登录时间
            self.update_last_login(user['id'])
            return user
        return None
    
    def update_last_login(self, user_id):
        """更新最后登录时间"""
        query = "UPDATE users SET last_login = %s WHERE id = %s"
        self.db.execute_update(query, (datetime.now(), user_id))
    
    def create_session(self, user_id):
        """创建用户会话"""
        token = self.generate_session_token()
        expires_at = datetime.now() + timedelta(hours=24)  # 24小时过期
        
        query = """
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s)
        """
        
        session_id = self.db.execute_insert(query, (user_id, token, expires_at))
        if session_id > 0:
            return token
        return None
    
    def validate_session(self, token):
        """验证会话令牌"""
        query = """
            SELECT s.user_id, u.username, u.full_name, u.role
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = %s AND s.expires_at > %s AND u.status = 'active'
        """
        
        result = self.db.execute_query(query, (token, datetime.now()))
        return result[0] if result else None
    
    def logout_user(self, token):
        """用户登出"""
        query = "DELETE FROM user_sessions WHERE session_token = %s"
        return self.db.execute_update(query, (token,)) > 0

class CaseManager:
    """卷宗管理类"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_case(self, case_name, case_number, description, created_by):
        """创建新卷宗"""
        query = """
            INSERT INTO cases (case_name, case_number, description, created_by)
            VALUES (%s, %s, %s, %s)
        """
        return self.db.execute_insert(query, (case_name, case_number, description, created_by))
    
    def get_user_cases(self, user_id):
        """获取用户的卷宗列表"""
        query = """
            SELECT 
                c.id,
                c.case_name,
                c.case_number,
                c.description,
                c.status,
                c.created_at,
                COUNT(cd.id) as directory_count
            FROM cases c
            LEFT JOIN case_directories cd ON c.id = cd.case_id
            WHERE c.created_by = %s AND c.status = 'active'
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """
        return self.db.execute_query(query, (user_id,))
    
    def get_case_by_id(self, case_id, user_id):
        """根据ID获取卷宗信息"""
        query = """
            SELECT * FROM cases 
            WHERE id = %s AND created_by = %s AND status = 'active'
        """
        result = self.db.execute_query(query, (case_id, user_id))
        return result[0] if result else None
    
    def update_case(self, case_id, case_name, case_number, description, user_id):
        """更新卷宗信息"""
        query = """
            UPDATE cases 
            SET case_name = %s, case_number = %s, description = %s, updated_at = %s
            WHERE id = %s AND created_by = %s
        """
        return self.db.execute_update(query, (case_name, case_number, description, datetime.now(), case_id, user_id))
    
    def delete_case(self, case_id, user_id):
        """删除卷宗（软删除）"""
        query = """
            UPDATE cases 
            SET status = 'deleted', updated_at = %s
            WHERE id = %s AND created_by = %s
        """
        return self.db.execute_update(query, (datetime.now(), case_id, user_id))

class DirectoryManager:
    """目录管理类"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def save_directory(self, case_id, directory_data):
        """保存目录数据"""
        # 先清除现有目录
        self.clear_case_directories(case_id)
        
        # 插入新目录数据
        query = """
            INSERT INTO case_directories (case_id, sequence_number, file_name, page_number, end_page)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        success_count = 0
        for item in directory_data:
            result = self.db.execute_insert(query, (
                case_id,
                item.get('sequence_number', ''),
                item.get('file_name', ''),
                item.get('page_number', ''),
                item.get('end_page', '')
            ))
            if result > 0:
                success_count += 1
        
        return success_count
    
    def get_case_directories(self, case_id):
        """获取卷宗目录"""
        query = """
            SELECT sequence_number, file_name, page_number, end_page
            FROM case_directories
            WHERE case_id = %s
            ORDER BY id
        """
        return self.db.execute_query(query, (case_id,))
    
    def clear_case_directories(self, case_id):
        """清除卷宗目录"""
        query = "DELETE FROM case_directories WHERE case_id = %s"
        return self.db.execute_update(query, (case_id,))
    
    def search_directories(self, case_id, keyword):
        """搜索目录项"""
        query = """
            SELECT sequence_number, file_name, page_number, end_page
            FROM case_directories
            WHERE case_id = %s AND (file_name LIKE %s OR sequence_number LIKE %s)
            ORDER BY id
        """
        search_term = f"%{keyword}%"
        return self.db.execute_query(query, (case_id, search_term, search_term))
