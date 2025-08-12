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
from page_manager import PageManager, UIComponents, FileManager, ChatManager, TOCManager

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

# CaseInfoDialog类已删除，功能已整合到页面上的卷宗信息框中

class PDFChatApp:
    def __init__(self, root, current_user=None, session_token=None, db_manager=None):
        self.root = root
        self.root.title("律师办案智能助手")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f8ff')
        
        # 用户信息和会话管理
        self.current_user = current_user
        self.session_token = session_token
        
        # 初始化数据库连接
        if db_manager:
            self.db_manager = db_manager
        else:
            self.db_manager = DatabaseManager()
            self.db_manager.connect()
        
        self.case_manager = CaseManager(self.db_manager)
        self.directory_manager = DirectoryManager(self.db_manager)
        # 初始化增强版管理器
        self.enhanced_case_manager = EnhancedCaseManager(self.db_manager)
        self.pdf_file_manager = PDFFileManager(self.db_manager)
        self.enhanced_directory_manager = EnhancedDirectoryManager(self.db_manager)
        self.current_case_id = None  # 当前选中的卷宗ID
        self.current_batch_case_id = None  # 当前批量上传的卷宗ID
        self.current_pdf_file_id = None  # 当前加载的PDF文件ID
        self.is_loading = False  # 加载状态标志
        self.pdf_cache = {}  # PDF预加载缓存 {file_name: {case_id, images, toc_data}}
        self.all_files_loaded = False  # 所有文件是否已预加载完成
        
        # 页面管理
        self.current_page = "case_list"  # 当前页面：case_list(阅卷) 或 add_case(添加案件)
        self.main_content_frame = None  # 主内容区域框架
        
        # 初始化管理器
        self.page_manager = PageManager(self)
        self.ui_components = UIComponents(self)
        self.file_manager = FileManager(self)
        self.chat_manager = ChatManager(self)
        self.toc_manager = TOCManager(self)
        
        # 设置窗口关闭协议
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置窗口图标和样式
        self.setup_styles()
        
        # 创建主框架
        self.create_main_layout()
        
        # 初始化聊天记录和PDF文件列表
        self.chat_history = []
        self.pdf_files = []
        # 初始化PDF图像引用列表
        self.pdf_images = []
        
    def create_gradient_button(self, parent, text, command, width=60, height=45):
        """创建带渐变效果的美观按钮"""
        # 创建Canvas作为按钮背景
        canvas = tk.Canvas(parent, width=width, height=height, 
                          highlightthickness=0, bd=0, bg='#f8f9fa')
        
        # 绘制渐变背景
        def draw_gradient():
            canvas.delete("all")
            
            # 绘制圆角矩形背景
            radius = 8
            # 主体矩形
            canvas.create_rectangle(radius, 0, width-radius, height, 
                                  fill='#FF8C00', outline='#FF8C00')
            canvas.create_rectangle(0, radius, width, height-radius, 
                                  fill='#FF8C00', outline='#FF8C00')
            
            # 四个圆角
            canvas.create_oval(0, 0, radius*2, radius*2, 
                             fill='#FF8C00', outline='#FF8C00')
            canvas.create_oval(width-radius*2, 0, width, radius*2, 
                             fill='#FF8C00', outline='#FF8C00')
            canvas.create_oval(0, height-radius*2, radius*2, height, 
                             fill='#E67E00', outline='#E67E00')
            canvas.create_oval(width-radius*2, height-radius*2, width, height, 
                             fill='#E67E00', outline='#E67E00')
            
            # 添加渐变效果
            for i in range(height//2):
                alpha = i / (height//2)
                r = int(255 - alpha * 20)
                g = int(140 - alpha * 20)
                color = f"#{r:02x}{g:02x}00"
                canvas.create_line(radius, i, width-radius, i, fill=color, width=1)
            
            # 添加文字 - 使用更大的字体确保完整显示
            canvas.create_text(width//2, height//2, text=text, 
                             font=('Segoe UI Emoji', 20), fill='white',
                             anchor='center')
        
        draw_gradient()
        
        # 绑定点击事件
        def on_click(event):
            command()
        
        # 绑定悬停效果
        def on_enter(event):
            canvas.delete("all")
            
            # 悬停时的圆角矩形背景
            radius = 8
            canvas.create_rectangle(radius, 0, width-radius, height, 
                                  fill='#FF7F00', outline='#FF7F00')
            canvas.create_rectangle(0, radius, width, height-radius, 
                                  fill='#FF7F00', outline='#FF7F00')
            
            # 四个圆角 - 悬停效果
            canvas.create_oval(0, 0, radius*2, radius*2, 
                             fill='#FF7F00', outline='#FF7F00')
            canvas.create_oval(width-radius*2, 0, width, radius*2, 
                             fill='#FF7F00', outline='#FF7F00')
            canvas.create_oval(0, height-radius*2, radius*2, height, 
                             fill='#CC6600', outline='#CC6600')
            canvas.create_oval(width-radius*2, height-radius*2, width, height, 
                             fill='#CC6600', outline='#CC6600')
            
            # 添加高亮渐变
            for i in range(height//2):
                alpha = i / (height//2)
                r = int(255 - alpha * 15)
                g = int(127 - alpha * 15)
                color = f"#{r:02x}{g:02x}00"
                canvas.create_line(radius, i, width-radius, i, fill=color, width=1)
            
            # 文字稍微放大
            canvas.create_text(width//2, height//2, text=text, 
                             font=('Segoe UI Emoji', 22), fill='white',
                             anchor='center')
        
        def on_leave(event):
            draw_gradient()
        
        canvas.bind('<Button-1>', on_click)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.config(cursor='hand2')
        
        return canvas

    # 注意：这是main.py文件的前半部分
    # 完整的文件包含更多方法和功能
    # 由于文件较大，这里只展示了核心的类定义和初始化部分
    
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFChatApp(root)
    root.mainloop()