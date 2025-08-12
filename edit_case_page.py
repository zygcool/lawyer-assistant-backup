#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编辑卷宗页面
复制自添加卷宗页面的功能，用于编辑现有卷宗
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from datetime import datetime
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
from database_config import DatabaseManager, CaseManager, DirectoryManager
from database_config_enhanced import EnhancedCaseManager, PDFFileManager, EnhancedDirectoryManager

class ToolTip:
    """创建工具提示框"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        
    def on_enter(self, event=None):
        """鼠标进入时显示提示框"""
        if self.tooltip_window or not self.text:
            return
        try:
            x, y, cx, cy = self.widget.bbox("insert")
        except:
            # 对于按钮等控件，使用控件的位置
            x, y = 0, 0
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background='#ffffe0', relief='solid', borderwidth=1,
                        font=('Microsoft YaHei', 9), wraplength=300)
        label.pack(ipadx=1)
        
    def on_leave(self, event=None):
        """鼠标离开时隐藏提示框"""
        tw = self.tooltip_window
        self.tooltip_window = None
        if tw:
            tw.destroy()

class EditCasePage:
    """编辑卷宗页面类"""
    
    def __init__(self, parent, case_id, case_info, current_user, case_manager, 
                 pdf_file_manager=None, enhanced_pdf_manager=None, enhanced_directory_manager=None, on_save_callback=None):
        self.parent = parent
        self.case_id = case_id
        self.case_info = case_info
        self.current_user = current_user
        self.case_manager = case_manager
        self.pdf_file_manager = pdf_file_manager
        self.enhanced_pdf_manager = enhanced_pdf_manager
        self.enhanced_directory_manager = enhanced_directory_manager
        self.on_save_callback = on_save_callback
        
        # PDF缓存字典
        self.pdf_cache = {}
        
        self.current_pdf_file_id = None  # 当前加载的PDF文件ID
        self.is_loading = False  # 加载状态标志
        self.pdf_cache = {}  # PDF预加载缓存
        self.pdf_images = []  # 初始化PDF图像引用列表
        
        # 创建编辑窗口
        self.create_edit_window()
        
        # 加载卷宗数据
        self.load_case_data()
        
    def create_edit_window(self):
        """创建编辑窗口"""
        self.edit_window = tk.Toplevel(self.parent)
        self.edit_window.title("编辑卷宗")
        self.edit_window.geometry("1200x800")
        self.edit_window.configure(bg='#f0f8ff')
        
        # 设置窗口关闭协议
        self.edit_window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 创建主框架
        self.main_frame = tk.Frame(self.edit_window, bg='#f0f8ff')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题栏
        self.create_title_bar()
        
        # 创建内容区域
        self.create_content_area()
        
    def create_title_bar(self):
        """创建标题栏"""
        title_frame = tk.Frame(self.main_frame, bg='#f0f8ff')
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 标题
        title_label = tk.Label(title_frame, text="📝 编辑卷宗", 
                              font=('Microsoft YaHei', 16, 'bold'),
                              bg='#f0f8ff', fg='#333333')
        title_label.pack(side=tk.LEFT)
        
        # 按钮区域
        btn_frame = tk.Frame(title_frame, bg='#f0f8ff')
        btn_frame.pack(side=tk.RIGHT)
        
        # 保存按钮
        save_btn = tk.Button(btn_frame, text="💾 保存", 
                            command=self.save_case,
                            bg='#28a745', fg='white',
                            font=('Microsoft YaHei', 10),
                            relief=tk.FLAT, bd=0,
                            padx=15, pady=5,
                            cursor='hand2')
        save_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # 取消按钮
        cancel_btn = tk.Button(btn_frame, text="❌ 取消", 
                              command=self.on_closing,
                              bg='#dc3545', fg='white',
                              font=('Microsoft YaHei', 10),
                              relief=tk.FLAT, bd=0,
                              padx=15, pady=5,
                              cursor='hand2')
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
    def get_pdf_file_id_by_path(self, file_path):
        """根据文件路径获取PDF文件ID - 修复版本"""
        try:
            # 从pdf_file_manager获取卷宗的PDF文件列表
            if self.pdf_file_manager:
                pdf_files = self.pdf_file_manager.get_case_pdf_files(self.case_id)
                print(f"🔍 查找PDF文件ID，目标路径: {file_path}")
                print(f"🔍 数据库中的PDF文件列表: {len(pdf_files)} 个")
                
                # 标准化目标路径
                target_path = os.path.normpath(file_path)
                target_name = os.path.basename(target_path)
                
                # 查找匹配的文件路径（优先完整路径匹配）
                for pdf_file in pdf_files:
                    db_path = os.path.normpath(pdf_file['file_path'])
                    print(f"🔍 完整路径比较: {db_path} vs {target_path}")
                    if db_path == target_path:
                        print(f"✓ 通过完整路径找到PDF文件ID: {pdf_file['id']}")
                        return pdf_file['id']
                
                # 如果完整路径没有匹配，尝试文件名匹配（但要确保路径相似）
                print(f"🔍 尝试文件名匹配: {target_name}")
                best_match = None
                best_score = 0
                
                for pdf_file in pdf_files:
                    db_path = os.path.normpath(pdf_file['file_path'])
                    db_name = os.path.basename(db_path)
                    
                    print(f"🔍 文件名比较: {db_name} vs {target_name}")
                    
                    # 文件名必须完全匹配
                    if db_name == target_name:
                        # 计算路径相似度（目录部分）
                        target_dir = os.path.dirname(target_path)
                        db_dir = os.path.dirname(db_path)
                        
                        # 如果目录路径包含相同的部分，给予更高的分数
                        if target_dir in db_dir or db_dir in target_dir:
                            score = len(os.path.commonpath([target_dir, db_dir]))
                            print(f"🔍 路径相似度评分: {score}")
                            
                            if score > best_score:
                                best_match = pdf_file['id']
                                best_score = score
                
                if best_match:
                    print(f"✓ 通过文件名和路径相似度找到PDF文件ID: {best_match}")
                    return best_match
                
                print(f"⚠️ 未找到匹配的PDF文件ID")
            else:
                print(f"⚠️ pdf_file_manager 不可用")
            
            return None
        except Exception as e:
            print(f"获取PDF文件ID失败：{str(e)}")
            return None
    
    def load_directory_from_database_by_pdf_id(self, pdf_file_id):
        """根据PDF文件ID从数据库加载目录数据 - 修复版本"""
        try:
            if hasattr(self, 'enhanced_directory_manager') and self.enhanced_directory_manager:
                print(f"🔍 正在查询PDF文件ID {pdf_file_id} 的目录数据...")
                # 使用enhanced_directory_manager的get_pdf_directories方法
                directories = self.enhanced_directory_manager.get_pdf_directories(pdf_file_id)
                
                print(f"🔍 查询结果：找到 {len(directories)} 条目录记录")
                if directories:
                    # 打印前几条记录的详细信息
                    for i, directory in enumerate(directories[:3]):
                        print(f"🔍 目录记录 {i+1}: pdf_file_id={directory.get('pdf_file_id')}, file_name={directory.get('file_name')}, sequence_number={directory.get('sequence_number')}")
                    
                    # 清空现有目录树
                    for item in self.toc_tree.get_children():
                        self.toc_tree.delete(item)
                    
                    # 填充目录树
                    for directory in directories:
                        sequence_number = directory.get('sequence_number', '')
                        file_name = directory.get('file_name', '')
                        page_number = directory.get('page_number', '')
                        end_page = directory.get('end_page', '')
                        
                        # 插入到目录树
                        self.toc_tree.insert('', 'end', values=(sequence_number, file_name, page_number, end_page))
                    
                    print(f"✓ 从数据库加载了 {len(directories)} 条PDF目录记录")
                    return True
                else:
                    # 清空现有目录树（因为没有找到目录数据）
                    for item in self.toc_tree.get_children():
                        self.toc_tree.delete(item)
                    print(f"⚠️ 数据库中没有找到PDF文件ID {pdf_file_id} 的目录数据")
                    return False
            else:
                print("⚠️ enhanced_directory_manager 不可用")
                return False
        except Exception as e:
            print(f"从数据库加载PDF目录数据失败：{str(e)}")
            return False
    
    # 注意：这是edit_case_page.py文件的前半部分
    # 完整的文件包含更多方法和功能
    # 由于文件较大，这里只展示了核心的修复部分
