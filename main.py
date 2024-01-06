from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
import mysql.connector
from mysql.connector import Error
import pandas as pd
# from sqlalchemy import create_engine
import re
import bcrypt

class DatabaseManager:
    def __init__(self):
        self.url = ""
        self.user = ""
        self.password = ""

        # Read database configuration from a file
        with open("currenncy_database_info.txt", "r") as file:
            lines = file.readlines()
            self.url = lines[0].strip()
            self.user = lines[1].strip()
            self.password = lines[2].strip()

    def get_connection(self):
        try:
            engine = create_engine(f"mysql+mysqlconnector://{self.user}:{self.password}@{self.url}/CurrencyEntries")
            return engine
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return None

    def save_currency_entry(self, entry_name, values, total_amount):
        sql = text("""
            INSERT INTO currency_entries 
            (entry_name, pennies, nickels, dimes, quarters, one_dollar, 
             five_dollars, ten_dollars, twenty_dollars, fifty_dollars, hundred_dollars, total_amount) 
            VALUES 
            (:entry_name, :pennies, :nickels, :dimes, :quarters, :one_dollar, 
             :five_dollars, :ten_dollars, :twenty_dollars, :fifty_dollars, :hundred_dollars, :total_amount)
            ON DUPLICATE KEY UPDATE 
            pennies = VALUES(pennies), nickels = VALUES(nickels), dimes = VALUES(dimes), 
            quarters = VALUES(quarters), one_dollar = VALUES(one_dollar), five_dollars = VALUES(five_dollars), 
            ten_dollars = VALUES(ten_dollars), twenty_dollars = VALUES(twenty_dollars), 
            fifty_dollars = VALUES(fifty_dollars), hundred_dollars = VALUES(hundred_dollars), 
            total_amount = VALUES(total_amount)
        """)
        engine = self.get_connection()
        if engine is not None:
            with engine.connect() as conn:
                conn.execute(sql, {**values, "entry_name": entry_name, "total_amount": total_amount})
            engine.dispose()
            return True
        else:
            return False

    def load_currency_entry(self, entry_name):
        sql = text("""
            SELECT pennies, nickels, dimes, quarters, one_dollar, five_dollars, ten_dollars, 
            twenty_dollars, fifty_dollars, hundred_dollars, total_amount 
            FROM currency_entries 
            WHERE entry_name = :entry_name
        """)
        engine = self.get_connection()
        if engine is not None:
            with engine.connect() as conn:
                result = conn.execute(sql, {"entry_name": entry_name}).fetchone()
            engine.dispose()
            return result
        else:
            return None

    def get_currency_entry_names(self):
        sql = text("SELECT entry_name FROM currency_entries")
        engine = self.get_connection()
        if engine is not None:
            with engine.connect() as conn:
                entries = conn.execute(sql).fetchall()
            engine.dispose()
            return [entry[0] for entry in entries]
        else:
            return []

    def delete_entry(self, entry_name):
        sql = text("DELETE FROM currency_entries WHERE entry_name = :entry_name")
        engine = self.get_connection()
        if engine is not None:
            with engine.connect() as conn:
                conn.execute(sql, {"entry_name": entry_name})
            engine.dispose()
            return True
        else:
            return False

    def clear_database(self):
        sql = text("DELETE FROM currency_entries")
        engine = self.get_connection()
        if engine is not None:
            with engine.connect() as conn:
                conn.execute(sql)
            engine.dispose()
            return True
        else:
            return False

    def export_data_to_excel(self, file_path):
        engine = self.get_connection()
        if engine is None:
            print("Failed to connect to the database")
            return False

        query = "SELECT * FROM currency_entries"
        try:
            df = pd.read_sql(query, engine)
            df.to_excel(file_path, index=False)
            return True
        except Error as e:
            print(f"Error: {e}")
            return False
        finally:
            engine.dispose()

    def create_users_table(self):
        create_table_query = text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password VARCHAR(50) NOT NULL
            )
        """)
        engine = self.get_connection()
        if engine:
            with engine.connect() as conn:
                conn.execute(create_table_query)
            engine.dispose()

    def insert_new_user(self, username, email, password):
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        sql = text("""
            INSERT INTO users (username, email, password)
            VALUES (:username, :email, :password)
        """)
        try:
            engine = self.get_connection()
            with engine.connect() as conn:
                conn.execute(sql, {'username': username, 'email': email, 'password': hashed_password})
                conn.commit()  # Explicitly commit the transaction
            return True
        except Exception as e:
            print(f"Error while inserting new user: {e}")
            return False

    def verify_user(self, username, password):
        verify_query = text("""
            SELECT password FROM users WHERE username = :username
        """)
        try:
            engine = self.get_connection()
            with engine.connect() as conn:
                result = conn.execute(verify_query, {"username": username}).fetchone()
                if result:
                    stored_hashed_password = result[0]
                    # Ensure the stored password is in byte format
                    if isinstance(stored_hashed_password, str):
                        stored_hashed_password = stored_hashed_password.encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password):
                        return True
                return False
        except Exception as e:
            print(f"Error while verifying user: {e}")
            return False


class CreateAccount:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.window = tk.Toplevel()
        self.window.title("Create Account")
        self.setup_ui()
        self.parent.withdraw()  # Hide the parent window (Homepage)

    def setup_ui(self):
        ttk.Label(self.window, text="Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(self.window)
        self.username_entry.grid(row=0, column=1)

        ttk.Label(self.window, text="Email:").grid(row=1, column=0)
        self.email_entry = ttk.Entry(self.window)
        self.email_entry.grid(row=1, column=1)

        ttk.Label(self.window, text="Password:").grid(row=2, column=0)
        self.password_entry = ttk.Entry(self.window, show='*')
        self.password_entry.grid(row=2, column=1)

        self.create_button = ttk.Button(self.window, text="Create Account", command=self.create_account)
        self.create_button.grid(row=3, column=0, columnspan=2)

        # Back to Homepage button
        self.back_button = ttk.Button(self.window, text="← Back to Homepage", command=self.back_to_homepage)
        self.back_button.grid(row=4, column=0, pady=10)

        # Add 'Login' button
        self.login_button = ttk.Button(self.window, text="Login", command=self.goto_login)
        self.login_button.grid(row=4, column=1, pady=10)

    def back_to_homepage(self):
        self.window.destroy()
        self.parent.deiconify()  # Show the parent window (Homepage) again

    def goto_login(self):
        self.window.destroy()
        Login(self.parent, self.db_manager)  # Missing the third argument

    def create_account(self):
        # Get user input
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        # Input Validation
        if not username or not email or not password:
            messagebox.showerror("Error", "All fields are required.")
            return

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format.")
            return

        # Password strength validation
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters.")
            return

        if not re.search("[a-z]", password):
            messagebox.showerror("Error", "Password must contain at least one lowercase letter.")
            return

        if not re.search("[A-Z]", password):
            messagebox.showerror("Error", "Password must contain at least one uppercase letter.")
            return

        if not re.search("[0-9]", password):
            messagebox.showerror("Error", "Password must contain at least one number.")
            return

        if not re.search("[!@#$%^&*()_+]", password):
            messagebox.showerror("Error", "Password must contain at least one special character (!@#$%^&*()_+).")
            return

        # Save to database
        success = self.db_manager.insert_new_user(username, email, password)
        if success:
            messagebox.showinfo("Success", "Account successfully created!")
            self.goto_login()  # Optionally redirect to login after account creation
        else:
            messagebox.showerror("Error", "Failed to create account")

class Login:
    def __init__(self, parent, db_manager, currency_app):
        self.parent = parent
        self.db_manager = db_manager
        self.currency_app = currency_app  # Store the reference to CurrencyApp instance
        self.window = tk.Toplevel()
        self.window.title("Login")
        self.setup_ui()
        self.parent.withdraw()  # Hide the parent window (Homepage)

    def setup_ui(self):
        ttk.Label(self.window, text="Username:").grid(row=0, column=0)
        self.username_entry = ttk.Entry(self.window)
        self.username_entry.grid(row=0, column=1)

        ttk.Label(self.window, text="Password:").grid(row=1, column=0)
        self.password_entry = ttk.Entry(self.window, show='*')
        self.password_entry.grid(row=1, column=1)

        self.login_button = ttk.Button(self.window, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2)

        # Go to Create Account button
        self.create_account_button = ttk.Button(self.window, text="Create an Account", command=self.goto_create_account)
        self.create_account_button.grid(row=3, column=1, pady=10)

        # Back to Homepage button
        self.back_button = ttk.Button(self.window, text="← Back to Homepage", command=self.back_to_homepage)
        self.back_button.grid(row=3, column=0, pady=10)

    def goto_create_account(self):
        self.window.destroy()
        CreateAccount(self.parent, self.db_manager)

    def back_to_homepage(self):
        self.window.destroy()
        self.parent.deiconify()  # Show the parent window (Homepage) again

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.db_manager.verify_user(username, password):
            self.window.destroy()  # Close the login window
            self.currency_app.currency_app_setup()  # Setup and display the main app UI
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password")

# Homepage
class Homepage:
    def __init__(self, parent, db_manager, currency_app):
        self.parent = parent
        self.db_manager = db_manager
        self.currency_app = currency_app  # Store the reference to CurrencyApp instance
        self.setup_ui()

    def setup_ui(self):
        # Read welcome message and summary from a file
        with open("welcome_summary.txt", "r") as file: # replace with your MySQL info file
            welcome_text = file.read()

        self.welcome_label = ttk.Label(self.parent, text=welcome_text, font=('Helvetica', 12), justify=tk.LEFT)
        self.welcome_label.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='w')

        # Buttons positioned at the top right corner
        self.create_account_button = ttk.Button(self.parent, text="Create an Account", command=self.open_create_account)
        self.create_account_button.grid(row=0, column=2, padx=10, pady=10, sticky='ne')

        self.login_button = ttk.Button(self.parent, text="Login", command=self.open_login)
        self.login_button.grid(row=0, column=3, padx=10, pady=10, sticky='ne')

    def open_create_account(self):
        CreateAccount(self.parent, self.db_manager)

    def open_login(self):
        # Login(self.parent, self.db_manager)
        Login(self.parent, self.db_manager, self.currency_app)  # Pass CurrencyApp instance to Login

class CurrencyApp:
    def __init__(self, root):
        self.root = root
        self.db_manager = DatabaseManager()
        self.db_manager.create_users_table()  # Initialize the users table
        root.title("Currency Tally Application")
        self.homepage = Homepage(root, self.db_manager, self)  # Pass 'self' as the currency_app instance

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', font=('Helvetica', 12))
        style.configure('TEntry', font=('Helvetica', 12))
        style.configure('TButton', font=('Helvetica', 12, 'bold'))

        # Setting up label and entry fields for each currency denomination
        self.setup_label_entry('Pennies:', 0)
        self.setup_label_entry('Nickels:', 1)
        self.setup_label_entry('Dimes:', 2)
        self.setup_label_entry('Quarters:', 3)
        self.setup_label_entry('One Dollar:', 4)
        self.setup_label_entry('Five Dollars:', 5)
        self.setup_label_entry('Ten Dollars:', 6)
        self.setup_label_entry('Twenty Dollars:', 7)
        self.setup_label_entry('Fifty Dollars:', 8)
        self.setup_label_entry('Hundred Dollars:', 9)

        # Button for calculating the total amount
        self.calculate_button = ttk.Button(self.root, text="Calculate", command=self.calculate_total)
        self.calculate_button.grid(row=10, column=0, columnspan=2, pady=10)

        # Label for displaying the total amount
        self.total_label = ttk.Label(self.root, text="Total: $0.00", font=('Helvetica', 14, 'bold'))
        self.total_label.grid(row=11, column=0, columnspan=2)

        # Button for showing the distribution chart
        ttk.Button(self.root, text="Show Chart", command=self.show_chart).grid(row=12, column=0, pady=10)

        # Entry and button for saving data to the database
        self.save_name_entry = ttk.Entry(self.root)
        self.save_name_entry.grid(row=13, column=0, pady=10)
        self.save_button = ttk.Button(self.root, text="Save to DB", command=self.save_to_db)
        self.save_button.grid(row=13, column=1, pady=10)

        # Combobox and button for loading data from the database
        self.load_combobox = ttk.Combobox(self.root)
        self.load_combobox.grid(row=14, column=0, pady=10)
        self.load_button = ttk.Button(self.root, text="Load from DB", command=self.load_from_db)
        self.load_button.grid(row=14, column=1, pady=10)

        # Dropdown for selecting entries to delete
        self.delete_combobox = ttk.Combobox(self.root)
        self.delete_combobox.grid(row=15, column=0, pady=10)

        # Button for deleting selected entries
        self.delete_button = ttk.Button(self.root, text="Delete Selected", command=self.delete_selected)
        self.delete_button.grid(row=15, column=1, pady=10)

        # Button for clearing the database
        self.clear_db_button = ttk.Button(self.root, text="Clear DB", command=self.clear_database)
        self.clear_db_button.grid(row=16, column=0, columnspan=2, pady=10)

        # Export Data to Excel File
        self.export_button = ttk.Button(self.root, text="Export to Excel", command=self.export_to_excel)
        self.export_button.grid(row=17, column=0, columnspan=2, pady=10)

        self.logout_button = ttk.Button(self.root, text="Logout", command=self.logout)
        self.logout_button.grid(row=0, column=3, padx=10, pady=10, sticky='ne')

        # Update the dropdown with entry names from the database
        self.update_dropdown()

    def setup_label_entry(self, label, row):
        ttk.Label(self.root, text=label).grid(row=row, column=0, padx=10, pady=5)
        entry = ttk.Entry(self.root)
        entry.grid(row=row, column=1, padx=10, pady=5)
        setattr(self, f'{label.replace(" ", "_")[:-1].lower()}_entry', entry)

    def calculate_total(self):
        currency_values = {
            'pennies': 1, 'nickels': 5, 'dimes': 10, 'quarters': 25,
            'one_dollar': 100, 'five_dollars': 500, 'ten_dollars': 1000,
            'twenty_dollars': 2000, 'fifty_dollars': 5000, 'hundred_dollars': 10000
        }
        total_cents = sum(int(getattr(self, f'{currency}_entry').get() or 0) * value
                          for currency, value in currency_values.items())
        self.total_dollars = total_cents / 100
        self.total_label.config(text=f"Total: ${self.total_dollars:.2f}")

        # Update the new total_calculated_entry with the calculated total
        self.save_name_entry.delete(0, tk.END)
        self.save_name_entry.insert(0, f"${self.total_dollars:.2f}")

    def show_chart(self):
        labels = ['Pennies', 'Nickels', 'Dimes', 'Quarters', 'One Dollar', 'Five Dollars', 'Ten Dollars',
                  'Twenty Dollars', 'Fifty Dollars', 'Hundred Dollars']
        values = [int(getattr(self, f"{label.lower().replace(' ', '_')}_entry").get() or 0) for label in labels]
        plt.figure(figsize=(10, 6))
        plt.bar(labels, values, color='skyblue')
        plt.bar(labels, values, color='skyblue')
        plt.xlabel('Currency')
        plt.ylabel('Count')
        plt.title('Currency Distribution')
        plt.xticks(rotation=45)
        plt.show()

    def save_to_db(self):
        values = {currency: int(getattr(self, f'{currency}_entry').get() or 0)
                  for currency in ['pennies', 'nickels', 'dimes', 'quarters',
                                   'one_dollar', 'five_dollars', 'ten_dollars',
                                   'twenty_dollars', 'fifty_dollars', 'hundred_dollars']}

        entry_name = self.save_name_entry.get()
        if not entry_name:
            messagebox.showerror("Error", "Please provide a name for the entry.")
            return

        total_amount = sum(values.values())  # Calculate the total amount based on your logic
        saved = self.db_manager.save_currency_entry(entry_name, values, total_amount)
        if saved:
            messagebox.showinfo("Success", "Entry saved successfully.")
            self.update_dropdown()
        else:
            messagebox.showerror("Error", "Failed to save the entry.")

    def load_from_db(self):
        entry_name = self.load_combobox.get()
        if not entry_name:
            messagebox.showerror("Error", "Please select an entry to load.")
            return

        result = self.db_manager.load_currency_entry(entry_name)
        if result:
            currencies = ['pennies', 'nickels', 'dimes', 'quarters',
                          'one_dollar', 'five_dollars', 'ten_dollars',
                          'twenty_dollars', 'fifty_dollars', 'hundred_dollars']
            for i, currency in enumerate(currencies):
                getattr(self, f'{currency}_entry').delete(0, tk.END)
                getattr(self, f'{currency}_entry').insert(0, str(result[i]))

            self.total_label.config(text=f"Total: ${result[-1]:.2f}")
        else:
            messagebox.showinfo("Not Found", "The selected entry was not found.")

    def update_dropdown(self):
        entry_names = self.db_manager.get_currency_entry_names()
        self.load_combobox['values'] = entry_names
        self.delete_combobox['values'] = entry_names

    def delete_selected(self):
        entry_name = self.delete_combobox.get()
        if not entry_name:
            messagebox.showerror("Error", "Please select an entry to delete.")
            return

        deleted = self.db_manager.delete_entry(entry_name)
        if deleted:
            messagebox.showinfo("Success", "Entry deleted successfully.")
            self.update_dropdown()  # Update dropdown to reflect the deletion
        else:
            messagebox.showerror("Error", "Failed to delete the entry.")

    def validate_currency_input(self):
        try:
            for currency in ['pennies', 'nickels', 'dimes', 'quarters', 'one_dollar', 'five_dollars', 'ten_dollars',
                             'twenty_dollars', 'fifty_dollars', 'hundred_dollars']:
                value = int(getattr(self, f'{currency}_entry').get())
                if value < 0:
                    raise ValueError("Currency values cannot be negative.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return False
        return True

    def clear_all_entries(self):
        for currency in ['pennies', 'nickels', 'dimes', 'quarters', 'one_dollar', 'five_dollars', 'ten_dollars',
                         'twenty_dollars', 'fifty_dollars', 'hundred_dollars']:
            getattr(self, f'{currency}_entry').delete(0, tk.END)

    def update_existing_entry(self, entry_name):
        values = {currency: int(getattr(self, f'{currency}_entry').get() or 0)
                  for currency in ['pennies', 'nickels', 'dimes', 'quarters',
                                   'one_dollar', 'five_dollars', 'ten_dollars',
                                   'twenty_dollars', 'fifty_dollars', 'hundred_dollars']}

        total_amount = sum(values.values())
        updated = self.db_manager.update_currency_entry(entry_name, values, total_amount)
        if updated:
            messagebox.showinfo("Success", "Entry updated successfully.")
        else:
            messagebox.showerror("Error", "Failed to update the entry.")

    def update_currency_entry(self, entry_name, values, total_amount):
        sql = """UPDATE currency_entries SET pennies = %s, nickels = %s, dimes = %s, quarters = %s, 
                 one_dollar = %s, five_dollars = %s, ten_dollars = %s, twenty_dollars = %s, fifty_dollars = %s, 
                 hundred_dollars = %s, total_amount = %s WHERE entry_name = %s"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (*values.values(), total_amount, entry_name))
                conn.commit()
            return True
        except Error as e:
            print(f"Error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_currency_entry(self, entry_name):
        deleted = self.db_manager.delete_entry(entry_name)
        if deleted:
            messagebox.showinfo("Success", "Entry deleted successfully.")
            self.update_dropdown()  # Update dropdown to reflect the deletion
        else:
            messagebox.showerror("Error", "Failed to delete the entry.")

    def clear_database(self):
        confirm = messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire database?")
        if confirm:
            cleared = self.db_manager.clear_database()
            if cleared:
                messagebox.showinfo("Success", "Database cleared successfully.")
                self.update_dropdown()  # Update dropdown to reflect the changes
            else:
                messagebox.showerror("Error", "Failed to clear the database.")

    def export_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                 filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if file_path:
            success = self.db_manager.export_data_to_excel(file_path)
            if success:
                messagebox.showinfo("Success", "Data exported successfully to " + file_path)
            else:
                messagebox.showerror("Error", "Failed to export data")

    def currency_app_setup(self):
        # Make sure the root window is not withdrawn and is lifted to the front
        self.root.deiconify()
        self.root.lift()

        # Clear any existing widgets in the root window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Setup the main application UI
        self.setup_ui()

    def logout(self):
        # Close the main application window
        self.root.withdraw()

        # Reset any application state as necessary
        self.reset_application_state()

        # Reinitialize the homepage window
        homepage_window = tk.Toplevel(self.root)
        Homepage(homepage_window, self.db_manager, self)

    def reset_application_state(self):
        # Clear all entries or reset variables
        self.clear_all_entries()

        # Reset any other application state or data
        # For example, clearing user-specific data, resetting UI elements, etc.

    def clear_all_entries(self):
        # Example method to clear all entry fields in the application
        for currency in ['pennies', 'nickels', 'dimes', 'quarters',
                         'one_dollar', 'five_dollars', 'ten_dollars',
                         'twenty_dollars', 'fifty_dollars', 'hundred_dollars']:
            entry_field = getattr(self, f'{currency}_entry', None)
            if entry_field:
                entry_field.delete(0, tk.END)

def main():
    root = tk.Tk()
    currency_app = CurrencyApp(root)  # Create CurrencyApp instance
    Homepage(root, currency_app.db_manager, currency_app)  # Pass CurrencyApp instance to Homepage
    root.mainloop()

if __name__ == "__main__":
    main()