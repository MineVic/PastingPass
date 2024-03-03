import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from cryptography.fernet import Fernet
import json
import os
from ttkthemes import ThemedStyle
import pyperclip

passwordPlaceholder = ""

class PasswordManager:
    def __init__(self, key_file="secret.key",
                       data_file="passwords.json"):
        self.key_file = key_file
        self.data_file = data_file
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)
        self.passwords = self.load_passwords()

    def load_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as key_file:
                key = key_file.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as key_file:
                key_file.write(key)
        return key

    def load_passwords(self):
        try:
            with open(self.data_file, "rb") as file:
                encrypted_data = file.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                passwords = json.loads(decrypted_data)
        except (FileNotFoundError, json.JSONDecodeError):
            passwords = {}
        return passwords

    def save_passwords(self):
        encrypted_data = self.cipher.encrypt(json.dumps(self.passwords).encode())
        with open(self.data_file, "wb") as file:
            file.write(encrypted_data)

    def add_password(self, service, username, password):
        if service not in self.passwords:
            self.passwords[service] = {}
        self.passwords[service][username] = password
        self.save_passwords()

    def get_password(self, service, username):
        return self.passwords.get(service, {}).get(username, None)

    def delete_password(self, service, username):
        if service in self.passwords and username in self.passwords[service]:
            del self.passwords[service][username]
            self.save_passwords()

class PasswordManagerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Password Manager")

        self.check_password()
        
        self.master.deiconify()
        self.style = ThemedStyle(self.master)
        self.style.set_theme("arc") 
        self.password_manager = PasswordManager()

        
        self.service_label = ttk.Label(self.master, text="Service:")
        self.service_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.service_entry = ttk.Entry(self.master, style="TEntry")
        self.service_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.username_label = ttk.Label(self.master, text="Username:")
        self.username_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

        self.username_entry = ttk.Entry(self.master, style="TEntry")
        self.username_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        self.password_label = ttk.Label(self.master, text="Password:")
        self.password_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")

        self.password_entry = ttk.Entry(self.master, show="*", style="TEntry")
        self.password_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.show_password_var = tk.BooleanVar()
        self.show_password_var.set(False)
        self.show_password_button = ttk.Checkbutton(self.master, text="Show Password", variable=self.show_password_var, command=self.toggle_show_password)
        self.show_password_button.grid(row=3, column=0, columnspan=2, pady=5)

        self.add_button = ttk.Button(self.master, text="Add Password", command=self.add_password, style="TButton")
        self.add_button.grid(row=4, column=0, pady=10)

        self.get_button = ttk.Button(self.master, text="Get Password", command=self.select_to_get_password, style="TButton")
        self.get_button.grid(row=4, column=1, pady=10)

        self.delete_button = ttk.Button(self.master, text="Delete Password", command=self.delete_password, style="TButton")
        self.delete_button.grid(row=5, column=0, pady=10)

        self.refresh_button = ttk.Button(self.master, text="Refresh", command=self.refresh_tree, style="TButton")
        self.refresh_button.grid(row=5, column=1, pady=10)

 
        self.tree = ttk.Treeview(self.master, columns=("Service", "Username", "Password"))
        self.tree.heading("#0", text="Password")
        self.tree.heading("Service", text="Service")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Password", text="Password")
        self.tree.column("#0", width=0, stretch=tk.NO)  
        self.tree.column("Service", width=150)
        self.tree.column("Username", width=150)
        self.tree.column("Password", width=150)
        self.tree.grid(row=6, column=0, columnspan=2, pady=10)

        # Populate the treeview initially
        self.refresh_tree()

    def check_password(self):
        password_manager = PasswordManager()
        password = simpledialog.askstring("Password", "Enter password:", show='*')

        if password == passwordPlaceholder:
            messagebox.showinfo("Success", "Password correct. Access granted.")
        else:
            messagebox.showerror("Error", "Incorrect password. Access denied.")
            self.master.destroy()  # Close the application if the password is incorrect

    def add_password(self):
        service = self.service_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if service and username and password:
            self.password_manager.add_password(service, username, password)
            messagebox.showinfo("Success", "Password added successfully.")
            self.refresh_tree()

            # Clear text fields after adding password
            self.service_entry.delete(0, "end")
            self.username_entry.delete(0, "end")
            self.password_entry.delete(0, "end")
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    def get_password(self, service, username):
        if service == "":
            service = self.service_entry.get()
        if username == "": 
            username = self.username_entry.get()

        if service and username:
            password = self.password_manager.get_password(service, username)
            if password:
                result = messagebox.askyesno("Password", f"Password: {password}\n\nDo you want to copy it to the clipboard?")
                if result:
                    pyperclip.copy(password)
                    messagebox.showinfo("Success", "Password copied to clipboard.")
            else:
                messagebox.showerror("Error", "Password not found.")
        else:
            messagebox.showerror("Error", "Please fill in all fields.")
                  

    def delete_password(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a password to delete.")
            return

        password = self.tree.item(selected_item, "text")
        service = self.tree.item(selected_item, "values")[0]
        username = self.tree.item(selected_item, "values")[1]

        if messagebox.askyesno("Delete Password", f"Do you want to delete the password for {username} on {service}?"):
            self.password_manager.delete_password(service, username)
            self.refresh_tree()
            messagebox.showinfo("Success", "Password deleted successfully.")
            
    def select_to_get_password(self):
        selected_item = self.tree.selection()
        if not selected_item:
            self.get_password("", "")
            return
            
        service = self.tree.item(selected_item, "values")[0]    
        username = self.tree.item(selected_item, "values")[1]    
        self.get_password(service, username)

    def toggle_show_password(self):
        # Toggle between showing and hiding password
        show_password = self.show_password_var.get()
        if show_password:
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def refresh_tree(self):
        # Clear existing items in the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate treeview
        for service, users in self.password_manager.passwords.items():
            for user, password in users.items():
                self.tree.insert("", "end", text=password, values=(service, user, "********"))
        
if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    root.withdraw()
    app = PasswordManagerApp(root)
    root.mainloop()
