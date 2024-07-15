import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import psutil
import time
import threading
import pystray
from PIL import Image, ImageDraw

# Variable global para almacenar los hilos de monitoreo
monitoring_threads = {}

# Función para obtener una lista de procesos
def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            processes.append(proc.info)
        except psutil.NoSuchProcess:
            pass
    return processes

# Función para reducir la prioridad del proceso seleccionado
def reduce_priority(pid):
    try:
        p = psutil.Process(pid)
        p.nice(psutil.IDLE_PRIORITY_CLASS)  # Para Windows, usar psutil.BELOW_NORMAL_PRIORITY_CLASS o psutil.IDLE_PRIORITY_CLASS
        # En Unix, podrías usar p.nice(19)
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", "Proceso no encontrado")
    except psutil.AccessDenied:
        messagebox.showwarning("Warning", "Acceso denegado. Intente ejecutar la aplicación como administrador.")

# Función para restaurar la prioridad del proceso seleccionado
def restore_priority(pid):
    try:
        p = psutil.Process(pid)
        p.nice(psutil.NORMAL_PRIORITY_CLASS)  # Para Windows, usar psutil.NORMAL_PRIORITY_CLASS
        # En Unix, podrías usar p.nice(0)
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", "Proceso no encontrado")
    except psutil.AccessDenied:
        messagebox.showwarning("Warning", "Acceso denegado. Intente ejecutar la aplicación como administrador.")

# Función que se ejecuta en segundo plano para monitorizar el proceso
def monitor_process(pid, stop_event):
    while not stop_event.is_set():
        try:
            p = psutil.Process(pid)
            if p.status() != psutil.STATUS_RUNNING:
                reduce_priority(pid)
            else:
                restore_priority(pid)
            time.sleep(5)
        except psutil.NoSuchProcess:
            break

# Función para iniciar el monitoreo
def start_monitoring():
    try:
        pid = int(entry.get())
        if pid in monitoring_threads:
            messagebox.showwarning("Warning", "El proceso ya está siendo monitoreado.")
            return
        stop_event = threading.Event()
        thread = threading.Thread(target=monitor_process, args=(pid, stop_event), daemon=True)
        thread.start()
        monitoring_threads[pid] = stop_event
        messagebox.showinfo("Info", "Monitoreo iniciado para el proceso con PID: " + str(pid))
        root.configure(bg='green')
    except ValueError:
        messagebox.showerror("Error", "Por favor ingrese un PID válido")

# Función para detener el monitoreo
def stop_monitoring():
    try:
        pid = int(entry.get())
        if pid in monitoring_threads:
            monitoring_threads[pid].set()
            del monitoring_threads[pid]
            messagebox.showinfo("Info", "Monitoreo detenido para el proceso con PID: " + str(pid))
            root.configure(bg='red')
        else:
            messagebox.showwarning("Warning", "El proceso no está siendo monitoreado.")
    except ValueError:
        messagebox.showerror("Error", "Por favor ingrese un PID válido")

# Función para actualizar la lista de procesos basada en la búsqueda
def update_process_list(event=None):
    search_term = search_var.get().lower()
    process_listbox.delete(*process_listbox.get_children())
    for proc in processes:
        if search_term in proc['name'].lower() or search_term in str(proc['pid']):
            process_listbox.insert("", "end", values=(proc['name'], proc['pid']))

# Función para ocultar la ventana en lugar de cerrarla
def hide_window():
    root.withdraw()
    create_tray_icon()

# Función para crear el icono en la bandeja del sistema
def create_tray_icon():
    def on_click(icon, item):
        root.deiconify()
        icon.stop()

    def quit_app(icon, item):
        icon.stop()
        root.quit()

    image = Image.new('RGB', (64, 64), (0, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill=(255, 0, 0))
    
    icon = pystray.Icon("test_icon", image, "Administrador de Procesos", menu=pystray.Menu(
        pystray.MenuItem("Mostrar", on_click),
        pystray.MenuItem("Cerrar", quit_app)
    ))
    icon.run()

# Crear la GUI
root = tk.Tk()
root.title("Administrador de Procesos")
root.geometry("600x400")

# Asociar el evento de cierre de la ventana a la función hide_window
root.protocol("WM_DELETE_WINDOW", hide_window)

frame = ttk.Frame(root, padding="10")
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Buscar Proceso:").pack(pady=5)
search_var = tk.StringVar()
search_entry = ttk.Entry(frame, textvariable=search_var)
search_entry.pack(fill=tk.X, pady=5)
search_entry.bind("<KeyRelease>", update_process_list)

columns = ("Nombre del Proceso", "PID")
process_listbox = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    process_listbox.heading(col, text=col)
process_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

ttk.Label(frame, text="Ingrese el PID del proceso:").pack(pady=5)
entry = ttk.Entry(frame)
entry.pack(pady=5)

ttk.Button(frame, text="Iniciar Monitoreo", command=start_monitoring).pack(pady=5)
ttk.Button(frame, text="Detener Monitoreo", command=stop_monitoring).pack(pady=5)

processes = get_processes()
update_process_list()

root.mainloop()
