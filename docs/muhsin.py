import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import os
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SistemYoneticisi:
    def __init__(self, root):
        self.root = root
        self.root.title("Gelişmiş Görev Yöneticisi - Final Projesi")
        self.root.geometry("1000x700")

        # Sekme (Tab) Yapısı
        self.tab_control = ttk.Notebook(root)
        
        self.tab_process = ttk.Frame(self.tab_control)
        self.tab_disk = ttk.Frame(self.tab_control)
        self.tab_files = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_process, text='Süreç Yönetimi (CPU/RAM)')
        self.tab_control.add(self.tab_disk, text='Disk Görselleştirme')
        self.tab_control.add(self.tab_files, text='Büyük Dosya Bulucu')
        
        self.tab_control.pack(expand=1, fill="both")

        # --- SEKME 1: SÜREÇ YÖNETİMİ ---
        self.create_process_tab()

        # --- SEKME 2: DİSK GÖRSELLEŞTİRME ---
        self.create_disk_tab()

        # --- SEKME 3: BÜYÜK DOSYALAR ---
        self.create_files_tab()

    def create_process_tab(self):
        # Üst Panel (Butonlar)
        frame_top = ttk.Frame(self.tab_process)
        frame_top.pack(side="top", fill="x", padx=10, pady=10)

        btn_refresh = ttk.Button(frame_top, text="Listeyi Yenile", command=self.load_processes)
        btn_refresh.pack(side="left", padx=5)

        btn_kill = ttk.Button(frame_top, text="Seçili İşlemi Sonlandır (Kill)", command=self.kill_process)
        btn_kill.pack(side="left", padx=5)
        
        # Arama Kutusu
        self.search_var = tk.StringVar()
        entry_search = ttk.Entry(frame_top, textvariable=self.search_var)
        entry_search.pack(side="right", padx=5)
        ttk.Button(frame_top, text="Ara", command=self.load_processes).pack(side="right")

        # Liste Alanı (Treeview)
        cols = ("PID", "Ad", "CPU %", "RAM %", "Durum")
        self.tree = ttk.Treeview(self.tab_process, columns=cols, show='headings')
        
        for col in cols:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c, False))
            self.tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.tab_process, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.load_processes()

    def load_processes(self):
        # Mevcut listeyi temizle
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        search_term = self.search_var.get().lower()
        
        # İşlemleri çek
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                p_info = proc.info
                if search_term and search_term not in p_info['name'].lower():
                    continue
                
                self.tree.insert("", "end", values=(
                    p_info['pid'],
                    p_info['name'],
                    p_info['cpu_percent'],
                    round(p_info['memory_percent'], 2),
                    p_info['status']
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def sort_treeview(self, col, reverse):
        # Sıralama fonksiyonu
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        # Sayısal değerleri doğru sıralamak için dönüşüm
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def kill_process(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen sonlandırılacak bir işlem seçin.")
            return

        item = self.tree.item(selected_item)
        pid = item['values'][0]
        
        try:
            p = psutil.Process(pid)
            p.terminate()  # veya p.kill()
            messagebox.showinfo("Başarılı", f"PID {pid} başarıyla sonlandırıldı.")
            self.load_processes()
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem sonlandırılamadı: {e}")

    def create_disk_tab(self):
        self.frame_disk_chart = tk.Frame(self.tab_disk)
        self.frame_disk_chart.pack(fill="both", expand=True, padx=20, pady=20)
        
        btn_disk = ttk.Button(self.tab_disk, text="Disk Kullanımını Güncelle", command=self.draw_disk_usage)
        btn_disk.pack(pady=10)
        
        self.draw_disk_usage()

    def draw_disk_usage(self):
        # Önceki grafiği temizle
        for widget in self.frame_disk_chart.winfo_children():
            widget.destroy()

        usage = psutil.disk_usage('/')
        labels = 'Kullanılan', 'Boş'
        sizes = [usage.used, usage.free]
        explode = (0.1, 0) 

        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
               shadow=True, startangle=90, colors=['#ff9999','#66b3ff'])
        ax.axis('equal') 
        ax.set_title(f"Disk Kullanımı (Toplam: {usage.total / (1024**3):.2f} GB)")

        canvas = FigureCanvasTkAgg(fig, master=self.frame_disk_chart)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def create_files_tab(self):
        frame_top = ttk.Frame(self.tab_files)
        frame_top.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_top, text="Taranacak Dizin:").pack(side="left")
        self.path_var = tk.StringVar(value="C:/") # Windows varsayılanı, Linux için "/" yapın
        entry_path = ttk.Entry(frame_top, textvariable=self.path_var, width=40)
        entry_path.pack(side="left", padx=5)

        ttk.Button(frame_top, text="Seç", command=self.choose_directory).pack(side="left")
        ttk.Button(frame_top, text="Büyük Dosyaları Bul (>100MB)", command=self.start_file_scan).pack(side="left", padx=10)

        # Liste
        cols = ("Dosya Adı", "Boyut (MB)", "Yol")
        self.tree_files = ttk.Treeview(self.tab_files, columns=cols, show='headings')
        for col in cols:
            self.tree_files.heading(col, text=col)
            self.tree_files.column(col, width=150)
        
        self.tree_files.pack(fill="both", expand=True, padx=10, pady=10)

    def choose_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def start_file_scan(self):
        # Arayüz donmasın diye Thread kullanıyoruz
        scan_thread = threading.Thread(target=self.scan_files)
        scan_thread.daemon = True
        scan_thread.start()

    def scan_files(self):
        path = self.path_var.get()
        min_size = 100 * 1024 * 1024  # 100 MB
        
        # Listeyi temizle
        for i in self.tree_files.get_children():
            self.tree_files.delete(i)

        files_found = []

        try:
            for root, dirs, files in os.walk(path):
                for name in files:
                    try:
                        filepath = os.path.join(root, name)
                        size = os.path.getsize(filepath)
                        if size > min_size:
                            files_found.append((name, size, filepath))
                    except (OSError, PermissionError):
                        continue
        except Exception as e:
            print(f"Hata: {e}")

        # Boyuta göre sırala (En büyük en üstte)
        files_found.sort(key=lambda x: x[1], reverse=True)

        # Arayüze ekle
        for f in files_found[:50]:  # İlk 50 dosya
            size_mb = f"{f[1] / (1024 * 1024):.2f}"
            self.tree_files.insert("", "end", values=(f[0], size_mb, f[2]))

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemYoneticisi(root)
    root.mainloop()
    input("\nDevam etmek için Enter'a basın...")