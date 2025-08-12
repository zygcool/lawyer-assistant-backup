import sqlite3
import os
from datetime import datetime
import json
from typing import List, Dict, Optional, Tuple

class EnhancedCaseManager:
    """增强版案件管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def get_all_cases(self) -> List[Dict]:
        """获取所有案件列表"""
        try:
            cursor = self.db_manager.cursor
            cursor.execute("""
                SELECT id, case_name, case_number, case_type, 
                       client_name, opposing_party, case_status, 
                       created_at, updated_at, description
                FROM cases 
                ORDER BY updated_at DESC
            """)
            
            cases = []
            for row in cursor.fetchall():
                case = {
                    'id': row[0],
                    'case_name': row[1],
                    'case_number': row[2],
                    'case_type': row[3],
                    'client_name': row[4],
                    'opposing_party': row[5],
                    'case_status': row[6],
                    'created_at': row[7],
                    'updated_at': row[8],
                    'description': row[9]
                }
                cases.append(case)
            
            return cases
            
        except Exception as e:
            print(f"获取案件列表失败: {e}")
            return []
    
    def get_case_by_id(self, case_id: int) -> Optional[Dict]:
        """根据ID获取案件详情"""
        try:
            cursor = self.db_manager.cursor
            cursor.execute("""
                SELECT id, case_name, case_number, case_type, 
                       client_name, opposing_party, case_status, 
                       created_at, updated_at, description
                FROM cases 
                WHERE id = ?
            """, (case_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'case_name': row[1],
                    'case_number': row[2],
                    'case_type': row[3],
                    'client_name': row[4],
                    'opposing_party': row[5],
                    'case_status': row[6],
                    'created_at': row[7],
                    'updated_at': row[8],
                    'description': row[9]
                }
            return None
            
        except Exception as e:
            print(f"获取案件详情失败: {e}")
            return None
    
    def create_case(self, case_data: Dict) -> Optional[int]:
        """创建新案件"""
        try:
            cursor = self.db_manager.cursor
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO cases (
                    case_name, case_number, case_type, client_name, 
                    opposing_party, case_status, created_at, updated_at, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_data.get('case_name', ''),
                case_data.get('case_number', ''),
                case_data.get('case_type', ''),
                case_data.get('client_name', ''),
                case_data.get('opposing_party', ''),
                case_data.get('case_status', '进行中'),
                now,
                now,
                case_data.get('description', '')
            ))
            
            self.db_manager.connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            print(f"创建案件失败: {e}")
            self.db_manager.connection.rollback()
            return None
    
    def update_case(self, case_id: int, case_data: Dict) -> bool:
        """更新案件信息"""
        try:
            cursor = self.db_manager.cursor
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                UPDATE cases SET 
                    case_name = ?, case_number = ?, case_type = ?, 
                    client_name = ?, opposing_party = ?, case_status = ?, 
                    updated_at = ?, description = ?
                WHERE id = ?
            """, (
                case_data.get('case_name', ''),
                case_data.get('case_number', ''),
                case_data.get('case_type', ''),
                case_data.get('client_name', ''),
                case_data.get('opposing_party', ''),
                case_data.get('case_status', ''),
                now,
                case_data.get('description', ''),
                case_id
            ))
            
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"更新案件失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def delete_case(self, case_id: int) -> bool:
        """删除案件"""
        try:
            cursor = self.db_manager.cursor
            
            # 先删除相关的PDF文件记录
            cursor.execute("DELETE FROM pdf_files WHERE case_id = ?", (case_id,))
            
            # 删除相关的目录记录
            cursor.execute("DELETE FROM pdf_directories WHERE case_id = ?", (case_id,))
            
            # 删除案件记录
            cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))
            
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"删除案件失败: {e}")
            self.db_manager.connection.rollback()
            return False

class PDFFileManager:
    """PDF文件管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def add_pdf_file(self, case_id: int, file_path: str, file_name: str, 
                     file_size: int = 0, page_count: int = 0) -> Optional[int]:
        """添加PDF文件记录"""
        try:
            cursor = self.db_manager.cursor
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO pdf_files (
                    case_id, file_path, file_name, file_size, 
                    page_count, upload_time
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (case_id, file_path, file_name, file_size, page_count, now))
            
            self.db_manager.connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            print(f"添加PDF文件记录失败: {e}")
            self.db_manager.connection.rollback()
            return None
    
    def get_pdf_files_by_case(self, case_id: int) -> List[Dict]:
        """获取案件的所有PDF文件"""
        try:
            cursor = self.db_manager.cursor
            cursor.execute("""
                SELECT id, file_path, file_name, file_size, 
                       page_count, upload_time
                FROM pdf_files 
                WHERE case_id = ?
                ORDER BY upload_time DESC
            """, (case_id,))
            
            files = []
            for row in cursor.fetchall():
                file_info = {
                    'id': row[0],
                    'file_path': row[1],
                    'file_name': row[2],
                    'file_size': row[3],
                    'page_count': row[4],
                    'upload_time': row[5]
                }
                files.append(file_info)
            
            return files
            
        except Exception as e:
            print(f"获取PDF文件列表失败: {e}")
            return []
    
    def get_pdf_file_by_id(self, file_id: int) -> Optional[Dict]:
        """根据ID获取PDF文件信息"""
        try:
            cursor = self.db_manager.cursor
            cursor.execute("""
                SELECT id, case_id, file_path, file_name, file_size, 
                       page_count, upload_time
                FROM pdf_files 
                WHERE id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'case_id': row[1],
                    'file_path': row[2],
                    'file_name': row[3],
                    'file_size': row[4],
                    'page_count': row[5],
                    'upload_time': row[6]
                }
            return None
            
        except Exception as e:
            print(f"获取PDF文件信息失败: {e}")
            return None
    
    def update_pdf_file(self, file_id: int, **kwargs) -> bool:
        """更新PDF文件信息"""
        try:
            cursor = self.db_manager.cursor
            
            # 构建更新语句
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['file_path', 'file_name', 'file_size', 'page_count']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            values.append(file_id)
            
            cursor.execute(f"""
                UPDATE pdf_files SET {', '.join(update_fields)}
                WHERE id = ?
            """, values)
            
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"更新PDF文件信息失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def delete_pdf_file(self, file_id: int) -> bool:
        """删除PDF文件记录"""
        try:
            cursor = self.db_manager.cursor
            
            # 先删除相关的目录记录
            cursor.execute("DELETE FROM pdf_directories WHERE pdf_file_id = ?", (file_id,))
            
            # 删除PDF文件记录
            cursor.execute("DELETE FROM pdf_files WHERE id = ?", (file_id,))
            
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"删除PDF文件记录失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def get_pdf_file_by_path(self, file_path: str) -> Optional[Dict]:
        """根据文件路径获取PDF文件信息"""
        try:
            cursor = self.db_manager.cursor
            cursor.execute("""
                SELECT id, case_id, file_path, file_name, file_size, 
                       page_count, upload_time
                FROM pdf_files 
                WHERE file_path = ?
            """, (file_path,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'case_id': row[1],
                    'file_path': row[2],
                    'file_name': row[3],
                    'file_size': row[4],
                    'page_count': row[5],
                    'upload_time': row[6]
                }
            return None
            
        except Exception as e:
            print(f"根据路径获取PDF文件信息失败: {e}")
            return None

class EnhancedDirectoryManager:
    """增强版目录管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save_pdf_directories(self, case_id: int, pdf_file_id: int, 
                           directories: List[Dict]) -> bool:
        """保存PDF文件的目录结构"""
        try:
            cursor = self.db_manager.cursor
            
            # 先删除该PDF文件的现有目录记录
            cursor.execute("""
                DELETE FROM pdf_directories 
                WHERE case_id = ? AND pdf_file_id = ?
            """, (case_id, pdf_file_id))
            
            # 插入新的目录记录
            for directory in directories:
                cursor.execute("""
                    INSERT INTO pdf_directories (
                        case_id, pdf_file_id, title, page_number, 
                        level, parent_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    case_id,
                    pdf_file_id,
                    directory.get('title', ''),
                    directory.get('page', 0),
                    directory.get('level', 1),
                    directory.get('parent_id'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            self.db_manager.connection.commit()
            return True
            
        except Exception as e:
            print(f"保存PDF目录失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def get_pdf_directories(self, case_id: int, pdf_file_id: int = None) -> List[Dict]:
        """获取PDF文件的目录结构"""
        try:
            cursor = self.db_manager.cursor
            
            if pdf_file_id:
                # 获取特定PDF文件的目录
                cursor.execute("""
                    SELECT id, title, page_number, level, parent_id
                    FROM pdf_directories 
                    WHERE case_id = ? AND pdf_file_id = ?
                    ORDER BY page_number, level
                """, (case_id, pdf_file_id))
            else:
                # 获取案件的所有目录
                cursor.execute("""
                    SELECT id, title, page_number, level, parent_id
                    FROM pdf_directories 
                    WHERE case_id = ?
                    ORDER BY page_number, level
                """, (case_id,))
            
            directories = []
            for row in cursor.fetchall():
                directory = {
                    'id': row[0],
                    'title': row[1],
                    'page': row[2],
                    'level': row[3],
                    'parent_id': row[4]
                }
                directories.append(directory)
            
            return directories
            
        except Exception as e:
            print(f"获取PDF目录失败: {e}")
            return []
    
    def clear_pdf_directories(self, case_id: int, pdf_file_id: int = None) -> bool:
        """清除PDF文件的目录记录"""
        try:
            cursor = self.db_manager.cursor
            
            if pdf_file_id:
                # 清除特定PDF文件的目录
                cursor.execute("""
                    DELETE FROM pdf_directories 
                    WHERE case_id = ? AND pdf_file_id = ?
                """, (case_id, pdf_file_id))
            else:
                # 清除案件的所有目录
                cursor.execute("""
                    DELETE FROM pdf_directories 
                    WHERE case_id = ?
                """, (case_id,))
            
            self.db_manager.connection.commit()
            return True
            
        except Exception as e:
            print(f"清除PDF目录失败: {e}")
            self.db_manager.connection.rollback()
            return False
    
    def search_directories(self, case_id: int, keyword: str) -> List[Dict]:
        """搜索目录项"""
        try:
            cursor = self.db_manager.cursor
            cursor.execute("""
                SELECT id, title, page_number, level, parent_id
                FROM pdf_directories 
                WHERE case_id = ? AND title LIKE ?
                ORDER BY page_number, level
            """, (case_id, f"%{keyword}%"))
            
            directories = []
            for row in cursor.fetchall():
                directory = {
                    'id': row[0],
                    'title': row[1],
                    'page': row[2],
                    'level': row[3],
                    'parent_id': row[4]
                }
                directories.append(directory)
            
            return directories
            
        except Exception as e:
            print(f"搜索目录失败: {e}")
            return []
    
    def get_directory_statistics(self, case_id: int) -> Dict:
        """获取目录统计信息"""
        try:
            cursor = self.db_manager.cursor
            
            # 获取总目录数
            cursor.execute("""
                SELECT COUNT(*) FROM pdf_directories WHERE case_id = ?
            """, (case_id,))
            total_count = cursor.fetchone()[0]
            
            # 获取各级目录数量
            cursor.execute("""
                SELECT level, COUNT(*) 
                FROM pdf_directories 
                WHERE case_id = ? 
                GROUP BY level
                ORDER BY level
            """, (case_id,))
            
            level_counts = {}
            for row in cursor.fetchall():
                level_counts[row[0]] = row[1]
            
            # 获取PDF文件数量
            cursor.execute("""
                SELECT COUNT(DISTINCT pdf_file_id) 
                FROM pdf_directories 
                WHERE case_id = ?
            """, (case_id,))
            pdf_file_count = cursor.fetchone()[0]
            
            return {
                'total_directories': total_count,
                'level_counts': level_counts,
                'pdf_file_count': pdf_file_count
            }
            
        except Exception as e:
            print(f"获取目录统计信息失败: {e}")
            return {
                'total_directories': 0,
                'level_counts': {},
                'pdf_file_count': 0
            }
