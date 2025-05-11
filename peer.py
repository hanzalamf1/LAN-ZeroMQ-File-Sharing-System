import os
import zmq
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox
import socket
import threading
import zlib

DEFAULT_PORT = 5555
current_port = DEFAULT_PORT

def validate_received_zip(filepath):
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

def receive_zip(ip):
    global current_port
    
    context = zmq.Context()
    socket_recv = context.socket(zmq.REP)
    socket_recv.setsockopt(zmq.RCVHWM, 1)
    socket_recv.setsockopt(zmq.SNDHWM, 1)
    
    port_bound = False
    while not port_bound and current_port < 5560:
        try:
            socket_recv.bind(f"tcp://*:{current_port}")
            port_bound = True
            messagebox.showinfo("Info", f"Listening on port {current_port}...")
        except zmq.ZMQError as e:
            if e.errno == zmq.EADDRINUSE:
                current_port += 1
            else:
                messagebox.showerror("Error", f"ZMQ Error: {str(e)}")
                return
    
    if not port_bound:
        messagebox.showerror("Error", "No available port found!")
        return

    def listen():
        try:
            while True:
                checksum_str, size_str = socket_recv.recv_string(encoding='utf-8').split('|')
                expected_checksum = int(checksum_str)
                expected_size = int(size_str)
                
                data = socket_recv.recv()
                actual_checksum = zlib.adler32(data)
                
                if len(data) != expected_size:
                    socket_recv.send_string("ERROR: Size mismatch")
                    continue
                
                if actual_checksum != expected_checksum:
                    socket_recv.send_string("ERROR: Checksum mismatch")
                    continue
                
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".zip",
                    filetypes=[("Zip Files", "*.zip")],
                    title="Save the received file"
                )
                
                if file_path:
                    try:
                        with open(file_path, "wb") as f:
                            f.write(data)
                        validate_received_zip(file_path)
                        socket_recv.send_string(f"SUCCESS: File successfully saved: {file_path}")
                        messagebox.showinfo("Success", 
                            f"File successfully received!\n\n"
                            f"Saved Location: {file_path}\n"
                            f"File Size: {len(data)/1024:.2f} KB")
                    except Exception as e:
                        socket_recv.send_string(f"ERROR: {str(e)}")
                        messagebox.showerror("Error", f"File could not be saved: {str(e)}")
                else:
                    socket_recv.send_string("ERROR: Save canceled")
        except Exception as e:
            messagebox.showerror("Error", f"Listening Error: {str(e)}")
    
    threading.Thread(target=listen).start()

def start_interface():
    def scan():
        ip_prefix = get_local_ip().rsplit('.', 1)[0]
        scan_network(ip_prefix, listbox, window)

    def start_receiving():
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "You must select an IP.")
            return

        ip = listbox.get(selected[0])
        if not ip:
            messagebox.showwarning("Warning", "No IP address selected.")
            return

        threading.Thread(target=receive_zip, args=(ip,)).start()

    window = tk.Tk()
    window.title("LAN File Receiver (Peer) - Advanced")
    window.geometry("450x450")
    
    try:
        window.tk.call('encoding', 'system', 'utf-8')
    except:
        pass

    tk.Label(window, text="Computers in Network:").pack()
    listbox = tk.Listbox(window, width=50, height=8)
    listbox.pack(pady=5)

    tk.Button(window, text="Scan Network", command=scan).pack(pady=5)
    tk.Button(window, text="Start Receiving", command=start_receiving, bg='lightgreen').pack(pady=10)

    local_ip = get_local_ip()
    tk.Label(window, text=f"Your IP: {local_ip}").pack(pady=5)
    tk.Label(window, text=f"Default Port: {DEFAULT_PORT}").pack()

    window.mainloop()

if __name__ == "__main__":
    start_interface()
