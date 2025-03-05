import tkinter as tk
from tkinter import ttk
from itertools import product
import re
import os


# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HANZI_QUERY_DIR = SCRIPT_DIR

# 定义拼音数据库文件路径与中文名的对应关系（使用绝对路径）
DATABASE_MAPPING = {
    os.path.join(HANZI_QUERY_DIR, 'zdic.txt'): '  汉典网',
    os.path.join(HANZI_QUERY_DIR, 'kMandarin.txt'): '  普通话常用读音数据',
    os.path.join(HANZI_QUERY_DIR, 'kTGHZ2013.txt'): '《通用规范汉字字典》',
    os.path.join(HANZI_QUERY_DIR, 'kHanyuPinlu.txt'): '《现代汉语频率词典》',
    os.path.join(HANZI_QUERY_DIR, 'kMandarin_8105.txt'): '《通用规范汉字表》',
    os.path.join(HANZI_QUERY_DIR, 'kXHC1983.txt'): '《现代汉语词典》',
    os.path.join(HANZI_QUERY_DIR, 'kHanyuPinyin.txt'): '《汉语大字典》',
}


class CCBSearchApp:
    def __init__(self, root):
        self.root = root
        # 减小窗口的初始宽度
        self.root.title("汉字组合查询")
        self.root.geometry("900x500")  # 从 1000x500 减小到 800x500
        self.shuffle_mode = False  # 新增乱序模式标志
        self.shuffle_seed = None   # 新增随机种子
        self.current_database = os.path.join(HANZI_QUERY_DIR, 'kTGHZ2013.txt')
        
        # 窗口居中逻辑
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2  # 根据新的宽度计算 x 坐标
        y = (screen_height - 500) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # 初始化分页属性
        self.current_page = 1
        self.page_size = 100
        self.generator = None
        
        self.init_data()
        self.create_widgets()

    def create_widgets(self):
        """恢复原始界面组件"""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="输入混合序列:").pack(side=tk.LEFT)
        self.entry = ttk.Entry(input_frame, width=20)
        self.entry.pack(side=tk.LEFT, padx=5)
        
        # 新增乱序模式复选框
        self.shuffle_var = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="乱序模式", variable=self.shuffle_var).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(input_frame, text="查询", command=self.search).pack(side=tk.LEFT)
        self.entry.bind('<Return>', self.search)
        
        # 新增选择拼音数据库的下拉菜单
        database_label = ttk.Label(input_frame, text="选择数据库:")
        database_label.pack(side=tk.LEFT, padx=10)
        # 增大 Combobox 的宽度
        self.database_combobox = ttk.Combobox(input_frame, values=list(DATABASE_MAPPING.values()), width=40)  # 增加宽度
        self.database_combobox.set(DATABASE_MAPPING[self.current_database])
        # 设置为只读状态，禁止手动输入
        self.database_combobox.config(state='readonly')
        self.database_combobox.bind("<<ComboboxSelected>>", self.change_database)
        self.database_combobox.pack(side=tk.LEFT, padx=5)
        
        # 结果显示
        style = ttk.Style()
        style.configure('Treeview', 
                      rowheight=25,
                      background='#FFFFFF',
                      fieldbackground='#FFFFFF',
                      font=('宋体', 10)  # 设置Treeview的字体为宋体，大小为10
                      )
        style.configure('Treeview.Heading', font=('微软雅黑', 10))
        style.configure('Treeview', 
                      rowheight=25,
                      background='#FFFFFF',
                      fieldbackground='#FFFFFF')
        style.configure('Treeview', fieldbackground='white')
        # 修改选中行背景颜色为深蓝色
        style.map('Treeview', background=[('selected', '#1E90FF')])
        style.configure('Treeview', font=('微软雅黑', 10)) 
        self.tree = ttk.Treeview(main_frame, columns=('chars', 'pinyins', 'codes'), 
                               show='headings', style='Treeview')
        self.tree.column('chars', width=200, anchor=tk.W)
        # 修改拼音列的字体为微软雅黑
        self.tree.heading('pinyins', text='拼音', anchor=tk.W)
        self.tree.column('pinyins', width=250, anchor=tk.W, stretch=tk.YES)
        style.configure('Treeview', fieldbackground='white')
        # 将选中行背景改为天蓝色
        style.map('Treeview', background=[('selected', '#1E90FF')])
        style.configure('Treeview', font=('微软雅黑', 10)) 
        style.map('Treeview', background=[('selected', '#1E90FF')])
        style.configure('Treeview', font=('微软雅黑', 10)) 
        # 修改编码列的字体为微软雅黑
        self.tree.heading('codes', text='编码', anchor=tk.W)
        self.tree.column('codes', width=150, anchor=tk.W, stretch=tk.YES)
        self.tree.heading('chars', text='汉字组合')
        self.tree.heading('pinyins', text='拼音')
        self.tree.heading('codes', text='编码')
        
        # 添加双击事件绑定（新增）
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 分页控件
        page_frame = ttk.Frame(main_frame)
        page_frame.pack(pady=5)
        
        ttk.Button(page_frame, text="上一页", command=self.prev_page).pack(side=tk.LEFT)
        ttk.Button(page_frame, text="下一页", command=self.next_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(page_frame, text="第1页")
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        # 新增组合总数显示
        self.total_label = ttk.Label(page_frame, text="总数：0")
        self.total_label.pack(side=tk.LEFT, padx=10)  # 添加到分页控件同一行
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        # 默认输入
        self.entry.insert(0, 'ccb')
    def init_data(self):
        """解析数据文件并建立索引"""
        self.char_db = {}
        self.char_map = {}  
        pattern = re.compile(r'U\+([0-9A-F]+):\s*([^#]+)#\s*(.+)')
        
        import os
        is_8105 = os.path.basename(self.current_database) == 'kMandarin_8105.txt'
        
        with open(self.current_database, 'r', encoding='utf-8') as f:
            for line in f:
                # 仅对8105数据库应用注释标记过滤
                if is_8105 and any(mark in line.split('#', 1)[-1] for mark in ('->', '?', '<-')):
                    continue
                    
                if match := pattern.match(line):
                    code, pinyins, char = match.groups()
                    char_text = char.strip()
                    pinyins = [p.strip() for p in pinyins.split(',')]
                    # 保留8105数据库的特殊过滤
                    if is_8105:
                        try:
                            code_point = int(code, 16)
                            if not (0x4E00 <= code_point <= 0x9FA5) or not pinyins:
                                continue
                        except ValueError:
                            continue
                    initials = set()
                    for py in pinyins:
                        clean = re.sub(r'\W+', '', py).lower()
                        if clean.startswith('ch'): initials.add('c')
                        elif clean.startswith('sh'): initials.add('s')
                        elif clean.startswith('zh'): initials.add('z')
                        elif clean: initials.add(clean[0])
                    
                    entry = {
                        'char': char_text,
                        'code': f'U+{code}',
                        'pinyin': '/'.join(pinyins)
                    }
                    for initial in initials:
                        self.char_db.setdefault(initial, []).append(entry)
                    self.char_map[char_text] = entry
    def change_database(self, event):
        """切换拼音数据库"""
        selected_name = self.database_combobox.get()
        for path, name in DATABASE_MAPPING.items():
            if name == selected_name:
                self.current_database = path
                self.init_data()  # 重新加载数据
                break
    def search(self, event=None):
        """改进的搜索方法（支持混合输入）"""
        # 清空旧数据
        # 确保 tree 已经被创建
        # 确保 tree 已经被创建，如果未创建则创建它
        if not hasattr(self, 'tree'):
            self.tree = ttk.Treeview(self.root, columns=('汉字', '拼音', '编码'), show='headings')
            self.tree.heading('汉字', text='汉字')
            self.tree.heading('拼音', text='拼音')
            self.tree.heading('编码', text='编码')
            self.tree.pack(pady=20)
        # 清空旧数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 重置分页
        self.current_page = 1
        self.generator = None

        # 验证输入
        # 假设 entry 是输入框，在 _create_widgets 方法中创建
        if not hasattr(self, 'entry'):
            self.entry = tk.Entry(self.root)
            self.entry.pack(pady=10)
        input_str = self.entry.get().lower()
        if not input_str.isalpha():
            return
        
        # 创建候选列表（保持原状）
        candidates = []
        for c in input_str:
            if c.isalpha() and c.islower():
                candidates.append(self.char_db.get(c, [{'char':'?', 'pinyin':'', 'code':''}]))
            else:
                entry = self.char_map.get(c, {'char':'?', 'pinyin':'', 'code':''})
                candidates.append([entry])
        
        # 计算组合总数（新增）
        total = 1
        for c in candidates:
            if len(c) == 0:  # 处理空候选列表
                total = 0
                break
            total *= len(c)
        self.total_label.config(text=f"总数：{total:,}")  # 添加千位分隔符
        
        # 修复方法调用位置（移动shuffled_generator到类方法层级）
        if self.shuffle_var.get():
            self.generator = self.shuffled_generator(candidates)
        else:
            self.generator = product(*candidates)
        
        self.load_page()
    def shuffled_generator(self, candidates):
        """数学随机生成器（内存优化版）"""
        import random
        from math import prod
        rng = random.SystemRandom()
        
        # 计算总组合数
        sizes = [len(c) for c in candidates]
        if any(s == 0 for s in sizes) or (total := prod(sizes)) == 0:
            return
        remaining = total
        for i in range(total):
            # 动态计算随机位置（避免存储整个索引列表）
            j = rng.randint(0, remaining - 1) if remaining > 1 else 0
            yield self._index_to_combo(j, candidates, sizes)
            remaining -= 1
    def _index_to_combo(self, index, candidates, sizes):
        """优化后的索引转换方法"""
        combo = []
        for i in range(len(candidates)-1, -1, -1):
            size = len(candidates[i])
            index, rem = divmod(index, size)
            combo.append(candidates[i][rem])
        return tuple(reversed(combo))
    def load_page(self):
        """修复分页显示问题"""
        if not self.generator:
            return
        
        # 清空当前显示
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 动态计算每页显示数量（修复逻辑）
        self.tree.update_idletasks()  # 强制更新界面
        
        # 修复行高测量逻辑（新增代码）
        style = ttk.Style()
        self.row_height = style.lookup('Treeview', 'rowheight') or 25
        
        # 强制计算实际高度（新增）
        self.tree.pack_propagate(False)  # 禁止自动调整大小
        self.tree.update()
        tree_height = self.tree.winfo_height()
        
        # 动态计算每页行数（修复公式）
        if tree_height > 0:
            self.page_size = max(10, tree_height // self.row_height - 2)  # 增加可视行数
        else:
            self.page_size = 30  # 默认值提高为30行
        
        # 加载指定页数据（后续代码保持不变）
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        count = 0
        
        while count < end:
            try:
                combo = next(self.generator)
                if count >= start:
                    chars = ''.join([item['char'] for item in combo])
                    pinyins = ' '.join([item['pinyin'] for item in combo])
                    codes = ' '.join([item['code'] for item in combo])
                    # 去掉处理每个字符字体的代码
                    self.tree.insert('', 'end', values=(chars, pinyins, codes))
                count += 1
            except StopIteration:
                self.generator = None
                break
        
        self.page_label.config(text=f"第{self.current_page}页")
    def can_display(self, char, font_name):
        """检查指定字体是否能显示指定字符"""
        import tkinter.font as tkfont
        font = tkfont.Font(family=font_name)
        return font.measure(char) > 0
    def next_page(self):
        if self.generator:
            self.current_page += 1
            self.load_page()
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_page()
    def on_tree_double_click(self, event):
        """处理双击复制事件（优化分栏复制）"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        # 获取具体点击的列和行
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        # 获取列索引（columns: ['chars', 'pinyins', 'codes']）
        col_index = int(column[1:]) - 1
        values = self.tree.item(item, 'values')
        if not values or col_index >= len(values):
            return
        
        # 复制指定列文本（移除高亮代码）
        text = values[col_index]
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        
        # 添加简洁的文本提示（修复显示问题）
        feedback = tk.Label(
            self.root,
            text="✓ 已复制",
            fg="#4CAF50",
            font=('微软雅黑', 9, 'bold'),
        )
        feedback.place(
            x=10,  # 左侧对齐
            y=self.total_label.winfo_rooty() - self.root.winfo_rooty()  # 转换为窗口相对坐标
        )
        
        # 1秒后淡出
        feedback.after(1000, feedback.destroy)  # 简化销毁逻辑
if __name__ == "__main__":
    root = tk.Tk()
    app = CCBSearchApp(root)
    root.mainloop()
