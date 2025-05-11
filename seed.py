import os
import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import zmq
import zipfile
import zlib
import time

DEFAULT_PORT = 5555
MAX_RETRIES = 3
RETRY_DELAY = 1
ZIP_PATH = "temp.zip"

def create_zip_file(source_path, output_zip=None):
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"{source_path} not found.")
    if output_zip is None:
        output_zip = os.path.basename(source_path) + ".zip"
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isdir(source_path): #klasör içerisinde birden fazla dosya varsa
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, source_path))
        else: #tek dosya var ise
            zipf.write(source_path, os.path.basename(source_path))

def validate_zip(filepath):
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            bad_file = zip_ref.testzip()
            if bad_file:
                raise ValueError(f"Corrupted file: {bad_file}")
            return True
    except Exception as e:
        raise ValueError(f"ZIP validation error: {str(e)}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "127.0.0.1"

def scan_network(ip_prefix, listbox, window):
    listbox.delete(0, tk.END)

    def scan():
        active_ips = []
        local_ip = get_local_ip()

        def check_ip(ip):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                sock.connect((ip, DEFAULT_PORT))
                active_ips.append(ip)
                sock.close()
            except:
                pass

        threads = []
        for i in range(1, 255):
            ip = f"{ip_prefix}.{i}"
            if ip == local_ip:
                continue
            thread = threading.Thread(target=check_ip, args=(ip,))
            threads.append(thread)
            thread.start()

        active_ips.append(local_ip)

        for t in threads:
            t.join()

        def update_listbox():
            for ip in active_ips:
                listbox.insert(tk.END, ip)

        window.after(0, update_listbox)

    threading.Thread(target=scan).start()

def secure_send(ip, file_path):
    try:
        # Create and validate the ZIP
        create_zip_file(file_path, ZIP_PATH)
        validate_zip(ZIP_PATH)
        
        with open(ZIP_PATH, 'rb') as f:
            data = f.read()
        checksum = zlib.adler32(data)
        
        context = zmq.Context()
        socket_send = context.socket(zmq.REQ)
        socket_send.setsockopt(zmq.SNDHWM, 1)
        
        port = DEFAULT_PORT
        connected = False
        while not connected and port <= 5560:
            try:
                socket_send.connect(f"tcp://{ip}:{port}")
                connected = True
            except zmq.ZMQError:
                port += 1

        if not connected:
            raise ConnectionError("Unable to connect")

        for attempt in range(MAX_RETRIES):
            try:
                socket_send.send_string(f"{checksum}|{len(data)}", encoding='utf-8', flags=zmq.SNDMORE)
                socket_send.send(data)
                
                response = socket_send.recv_string(encoding='utf-8')
                if response.startswith("SUCCESS"):
                    messagebox.showinfo("Success", 
                        f"File successfully sent!\n\n"
                        f"Sender IP: {ip}\n"
                        f"Receiver Message: {response[8:]}\n"
                        f"File Size: {len(data)/1024:.2f} KB")
                    return True
                elif attempt == MAX_RETRIES - 1:
                    raise ValueError("Max retry attempts exceeded")
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_DELAY)
    except Exception as e:
        messagebox.showerror("Error", 
            f"File transfer failed!\n\n"
            f"Error Detail: {str(e)}\n"
            f"Sender IP: {ip}\n"
            f"Port: {port}")
        return False
    finally:
        if 'socket_send' in locals():
            socket_send.close()
        if 'context' in locals():
            context.term()
        if os.path.exists(ZIP_PATH):
            os.remove(ZIP_PATH)

def start_interface():
    def select_file():
        selection = filedialog.askopenfilename()
        if selection:
            selected_file.set(selection)

    def select_folder():
        selection = filedialog.askdirectory()
        if selection:
            selected_file.set(selection)

    def send():
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "You must select an IP.")
            return

        ip = listbox.get(selected[0])
        if not ip:
            messagebox.showwarning("Warning", "No IP address selected.")
            return

        file = selected_file.get()
        if not file:
            messagebox.showwarning("Warning", "You must select a file/folder.")
            return

        threading.Thread(target=secure_send, args=(ip, file)).start()

    def scan():
        ip_prefix = get_local_ip().rsplit('.', 1)[0]
        scan_network(ip_prefix, listbox, window)

    window = tk.Tk()
    window.title("LAN File Sender (Seed) - Advanced")
    window.geometry("450x450")
    
    try:
        window.tk.call('encoding', 'system', 'utf-8')
    except:
        pass

    tk.Label(window, text="Selected File/Folder:").pack()
    selected_file = tk.StringVar()
    tk.Entry(window, textvariable=selected_file, width=50).pack(pady=5)

    tk.Button(window, text="Select File", command=select_file).pack(pady=5)
    tk.Button(window, text="Select Folder", command=select_folder).pack(pady=5)

    tk.Label(window, text="Computers in Network:").pack()
    listbox = tk.Listbox(window, width=50, height=8)
    listbox.pack(pady=5)

    tk.Button(window, text="Scan Network", command=scan).pack(pady=5)
    tk.Button(window, text="Send to Selected IP", command=send, bg='lightgreen').pack(pady=10)

    local_ip = get_local_ip()
    tk.Label(window, text=f"Your IP: {local_ip}").pack(pady=5)
    tk.Label(window, text=f"Default Port: {DEFAULT_PORT}").pack()

    window.mainloop()

if __name__ == "__main__":
    start_interface()
