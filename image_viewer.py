import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

# 尝试导入拖拽库，若未安装则降级为普通Tk
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD

    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("提示: 若要支持图片拖拽功能，请运行: pip install tkinterdnd2")


class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("图片像素查看器")
        self.root.geometry("800x600")

        # 变量初始化
        self.image = None  # PIL Image 对象
        self.photo = None  # ImageTk.PhotoImage 对象
        self.scale = 1.0  # 缩放比例
        self.canvas = None

        # 文件夹切换相关变量
        self.current_dir = ""
        self.current_file = ""
        self.image_files = []
        self.current_index = -1

        # 创建界面
        self.create_widgets()

        # 绑定键盘事件（左右方向键）
        self.root.bind("<Left>", lambda e: self.switch_image(-1))
        self.root.bind("<Right>", lambda e: self.switch_image(1))

    def create_widgets(self):
        # 顶部工具栏
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 打开图片按钮
        btn_open = tk.Button(toolbar, text="打开图片", command=self.open_image)
        btn_open.pack(side=tk.LEFT, padx=(0, 10))

        # --- 新增：左右切换虚拟按钮 ---
        btn_prev = tk.Button(toolbar, text="◀ 上一张", command=lambda: self.switch_image(-1))
        btn_prev.pack(side=tk.LEFT, padx=2)

        btn_next = tk.Button(toolbar, text="下一张 ▶", command=lambda: self.switch_image(1))
        btn_next.pack(side=tk.LEFT, padx=2)
        # ----------------------------

        # 状态栏（显示像素信息）
        self.status = tk.Label(self.root, text="未加载图片", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # 画布（显示图片）
        self.canvas = tk.Canvas(self.root, bg="#f0f0f0")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 绑定事件：鼠标移动 + 窗口尺寸变化
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # 如果支持拖拽，注册拖拽目标
        if HAS_DND:
            self.canvas.drop_target_register(DND_FILES)
            self.canvas.dnd_bind('<<Drop>>', self.on_drop)

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.load_image_from_path(file_path)

    def on_drop(self, event):
        """处理文件拖拽事件"""
        file_path = event.data
        # 移除可能存在的花括号（Windows拖拽常见问题）
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path):
        """核心加载图片方法，并更新图片列表"""
        try:
            self.image = Image.open(file_path)
            self.fit_image_to_canvas()
            self.show_image()
            self.status.config(text=f"当前图片: {os.path.basename(file_path)}")

            # 更新文件夹图片列表供左右键切换
            self.update_file_list(file_path)

        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")

    def update_file_list(self, file_path):
        """获取当前文件夹下所有图片路径"""
        self.current_dir = os.path.dirname(file_path)
        self.current_file = os.path.basename(file_path)

        # 支持的图片扩展名
        extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff')
        # 过滤出同文件夹下的图片并排序
        self.image_files = [f for f in os.listdir(self.current_dir) if f.lower().endswith(extensions)]
        self.image_files.sort()

        # 找到当前图片的索引
        try:
            self.current_index = self.image_files.index(self.current_file)
        except ValueError:
            self.current_index = -1

    def switch_image(self, delta):
        """按按钮或键盘切换图片 (delta: -1 向左, 1 向右)"""
        if not self.image_files or self.current_index == -1:
            return

        new_idx = self.current_index + delta
        # 实现循环切换
        if new_idx < 0:
            new_idx = len(self.image_files) - 1
        elif new_idx >= len(self.image_files):
            new_idx = 0

        self.current_index = new_idx
        new_path = os.path.join(self.current_dir, self.image_files[new_idx])
        self.load_image_from_path(new_path)

    def fit_image_to_canvas(self):
        """计算缩放比例，使图片适应画布大小（保留比例）"""
        if not self.image:
            return
        self.root.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width, canvas_height = 800, 600

        img_width, img_height = self.image.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.scale = min(scale_x, scale_y)
        if self.scale <= 0:
            self.scale = 1.0

    def show_image(self):
        """在画布正中央绘制图片"""
        if not self.image:
            return

        new_size = (int(self.image.width * self.scale), int(self.image.height * self.scale))

        # 兼容不同版本 Pillow 的缩放写法
        try:
            resized_img = self.image.resize(new_size, Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                resized_img = self.image.resize(new_size, Image.LANCZOS)
            except AttributeError:
                resized_img = self.image.resize(new_size, Image.ANTIALIAS)

        self.photo = ImageTk.PhotoImage(resized_img)

        self.canvas.delete("all")
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        center_x = canvas_w / 2
        center_y = canvas_h / 2
        self.canvas.create_image(center_x, center_y, anchor=tk.CENTER, image=self.photo)

    def on_canvas_resize(self, event):
        """窗口改变大小时，重新居中图片"""
        if self.image:
            self.show_image()

    def on_mouse_move(self, event):
        if not self.image:
            self.status.config(text="未加载图片")
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        scaled_w = self.image.width * self.scale
        scaled_h = self.image.height * self.scale
        offset_x = (canvas_w - scaled_w) / 2
        offset_y = (canvas_h - scaled_h) / 2

        x_canvas = event.x - offset_x
        y_canvas = event.y - offset_y

        x_orig = int(x_canvas / self.scale)
        y_orig = int(y_canvas / self.scale)

        if x_orig < 0: x_orig = 0
        if y_orig < 0: y_orig = 0
        if x_orig >= self.image.width: x_orig = self.image.width - 1
        if y_orig >= self.image.height: y_orig = self.image.height - 1

        pixel = self.image.getpixel((x_orig, y_orig))
        if isinstance(pixel, int):
            pixel_str = f"灰度: {pixel}"
        else:
            pixel_str = f"R:{pixel[0]} G:{pixel[1]} B:{pixel[2]}"

        self.status.config(text=f"位置: ({x_orig}, {y_orig})  像素值: {pixel_str}")


if __name__ == "__main__":
    # 根据是否有拖拽库，决定根窗口类型
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = ImageViewer(root)
    root.mainloop()