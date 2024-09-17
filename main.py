import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import csv
from datetime import datetime, timedelta
from tkcalendar import DateEntry

class BloodBankApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Hide the main window until login is successful

        # Load and store the image
        self.logo_img = tk.PhotoImage(file="image2.png")

        # Ensure the database is set up
        self.create_database()
        self.add_default_users()

        # User role will be determined at login
        self.current_user_role = None

        # Launch the login window
        self.login_gui()

    def create_database(self):
        with sqlite3.connect('blood_bank.db', timeout=30) as conn:  # Added timeout to prevent locking
            c = conn.cursor()
            # Set SQLite to use WAL mode
            c.execute("PRAGMA journal_mode=WAL;")
            c.execute("PRAGMA busy_timeout=30000;")  # Wait up to 30 seconds for a lock to clear

            c.execute('''CREATE TABLE IF NOT EXISTS donors (
                         id INTEGER PRIMARY KEY,
                         name TEXT NOT NULL,
                         id_number TEXT NOT NULL,
                         blood_type TEXT NOT NULL,
                         donation_date TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS blood_supply (
                         blood_type TEXT PRIMARY KEY,
                         quantity INTEGER NOT NULL,
                         donation_date TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS audit_trail (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         action TEXT NOT NULL,
                         details TEXT,
                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            c.execute('''CREATE TABLE IF NOT EXISTS users  (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT NOT NULL,
                         password TEXT NOT NULL,
                         role TEXT NOT NULL)''')
            c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            donor_name TEXT NOT NULL,
                            blood_type TEXT NOT NULL,
                            appointment_date TEXT NOT NULL,
                            appointment_time TEXT NOT NULL)''')
            try:
                c.execute("ALTER TABLE blood_supply ADD COLUMN donation_date TEXT")
            except sqlite3.OperationalError:
                pass  # The column already exists, so we pass

    def add_default_users(self):
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin', 'admin')")
        c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('user', 'user', 'user')")
        c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('student', 'student', 'student')")
        conn.commit()
        conn.close()

    def login_gui(self):
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Login")

        frame = ttk.Frame(self.login_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Username:").grid(row=0, column=0, pady=5)
        ttk.Label(frame, text="Password:").grid(row=1, column=0, pady=5)

        self.entry_username = ttk.Entry(frame, font=("Arial", 12))
        self.entry_password = ttk.Entry(frame, font=("Arial", 12), show="*")

        self.entry_username.grid(row=0, column=1, pady=5, padx=5)
        self.entry_password.grid(row=1, column=1, pady=5, padx=5)

        ttk.Button(frame, text="Login",
                   command=self.login).grid(row=2, columnspan=2, pady=10)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        result = c.fetchone()
        if result:
            self.current_user_role = result[0]  # Store the role of the logged-in user
            self.login_window.destroy()  # Close login window
            self.root.deiconify()  # Show the main window
            self.create_main_window()  # Open main window
        else:
            messagebox.showerror("Error", "Invalid username or password")
        conn.close()

    def create_main_window(self):
        # Main frame setup
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Display the logo image
        logo_label = tk.Label(main_frame, image=self.logo_img)
        logo_label.pack(pady=10)

        # Add buttons for different actions
        if self.current_user_role in ["admin", "user"]:
            ttk.Button(main_frame, text="Schedule Appointment", command=self.schedule_appointment_gui).pack(pady=10,
                                                                                                            fill=tk.X)
            ttk.Button(main_frame, text="View Appointments", command=self.view_appointments_gui).pack(pady=10,
                                                                                                      fill=tk.X)
        if self.current_user_role == "admin":
            ttk.Button(main_frame, text="Manage Users", command=self.manage_users_gui).pack(pady=10, fill=tk.X)
            ttk.Button(main_frame, text="View Metadata", command=self.view_metadata_gui).pack(pady=10, fill=tk.X)

        if self.current_user_role in ["admin", "user"]:
            ttk.Button(main_frame, text="Add Donor", command=self.donor_gui).pack(pady=10, fill=tk.X)
            ttk.Button(main_frame, text="Issue Blood", command=self.issue_blood_gui).pack(pady=10, fill=tk.X)
            ttk.Button(main_frame, text="Emergency Blood Issue", command=self.emergency_blood_gui).pack(pady=10,
                                                                                                        fill=tk.X)

        if self.current_user_role in ["student"]:
            ttk.Button(main_frame, text="Issue Blood", command=self.issue_blood_gui).pack(pady=10, fill=tk.X)
            ttk.Button(main_frame, text="Emergency Blood Issue", command=self.emergency_blood_gui).pack(pady=10,
                                                                                                        fill=tk.X)
        ttk.Button(main_frame, text="Export Records", command=self.export_gui).pack(pady=10, fill=tk.X)

    # Manage users (Admin)
    def manage_users_gui(self):
        if self.current_user_role != "admin":
            messagebox.showerror("Error", "You don't have permission to manage users!")
            return

        manage_users_window = tk.Toplevel(self.root)
        manage_users_window.title("Manage Users")

        frame = ttk.Frame(manage_users_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Username:").grid(row=0, column=0, pady=5)
        ttk.Label(frame, text="Password:").grid(row=1, column=0, pady=5)
        ttk.Label(frame, text="Role:").grid(row=2, column=0, pady=5)

        entry_username = ttk.Entry(frame, font=("Arial", 12))
        entry_password = ttk.Entry(frame, font=("Arial", 12), show="*")
        role_combobox = ttk.Combobox(frame, values=["admin", "user", "student"], font=("Arial", 12))

        entry_username.grid(row=0, column=1, pady=5, padx=5)
        entry_password.grid(row=1, column=1, pady=5, padx=5)
        role_combobox.grid(row=2, column=1, pady=5, padx=5)

        ttk.Button(frame, text="Create User",
                   command=lambda: self.add_user(entry_username.get(), entry_password.get(), role_combobox.get())).grid(row=3, columnspan=2, pady=10)

    def add_user(self, username, password, role):
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "User added successfully")

    # View metadata (Admin)
    def view_metadata_gui(self):
        if self.current_user_role != "admin":
            messagebox.showerror("Error", "You don't have permission to view metadata!")
            return

        # Create the metadata window
        metadata_window = tk.Toplevel(self.root)
        metadata_window.title("View Metadata (Audit Log)")

        # Create a canvas with a scrollbar
        canvas = tk.Canvas(metadata_window)
        scrollbar = ttk.Scrollbar(metadata_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Query the audit trail logs from the database
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("SELECT * FROM audit_trail")
        logs = c.fetchall()
        conn.close()

        # Display each log in the scrollable frame
        for idx, log in enumerate(logs):
            ttk.Label(scrollable_frame, text=log).grid(row=idx, column=0, pady=5, padx=10)

    # View de-identified data (Research Student)
    def view_deidentified_data_gui(self):
        if self.current_user_role != "student":
            messagebox.showerror("Error", "You don't have permission to view de-identified data!")
            return

        deid_window = tk.Toplevel(self.root)
        deid_window.title("View De-Identified Data")

        frame = ttk.Frame(deid_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("SELECT blood_type, donation_date FROM donors")
        data = c.fetchall()
        conn.close()

        for idx, row in enumerate(data):
            ttk.Label(frame, text=row).grid(row=idx, column=0, pady=5)

    # Existing donor, issue blood, emergency blood methods remain the same

    # Export records to CSV
    def export_gui(self):
        export_window = tk.Toplevel(self.root)
        export_window.title("Export Records")

        frame = ttk.Frame(export_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Button(frame, text="Export Records to CSV", command=self.export_records_to_csv).grid(row=0, column=0, pady=10)

    def export_records_to_csv(self):
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("SELECT * FROM donors")
        donors = c.fetchall()
        c.execute("SELECT * FROM blood_supply")
        blood_supply = c.fetchall()
        c.execute("SELECT * FROM audit_trail")
        audit_trail = c.fetchall()

        with open('donors.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Name', 'ID Number', 'Blood Type', 'Donation Date'])
            writer.writerows(donors)

        with open('blood_supply.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Blood Type', 'Quantity'])
            writer.writerows(blood_supply)

        with open('audit_trail.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Action', 'Details', 'Timestamp'])
            writer.writerows(audit_trail)

        conn.close()
        messagebox.showinfo("Success", "Records exported successfully")

    def donor_gui(self):
        donor_window = tk.Toplevel(self.root)
        donor_window.title("Add Donor")

        frame = ttk.Frame(donor_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Name:").grid(row=0, column=0, pady=5)
        ttk.Label(frame, text="ID Number:").grid(row=1, column=0, pady=5)
        ttk.Label(frame, text="Blood Type:").grid(row=2, column=0, pady=5)
        ttk.Label(frame, text="Donation Date:").grid(row=3, column=0, pady=5)

        entry_name = ttk.Entry(frame, font=("Arial", 12))
        entry_id_number = ttk.Entry(frame, font=("Arial", 12))
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        combobox_blood_type = ttk.Combobox(frame, values=blood_types, font=("Arial", 12),
                                           state="readonly")  # Read-only selection
        entry_donation_date = DateEntry(frame, font=("Arial", 12), date_pattern="yyyy-mm-dd")

        entry_name.grid(row=0, column=1, pady=5, padx=5)
        entry_id_number.grid(row=1, column=1, pady=5, padx=5)
        combobox_blood_type.grid(row=2, column=1, pady=5, padx=5)
        entry_donation_date.grid(row=3, column=1, pady=5, padx=5)

        ttk.Button(frame, text="Add Donor",
                   command=lambda: self.add_donor(entry_name.get(), entry_id_number.get(), combobox_blood_type.get(),
                                                  entry_donation_date.get())).grid(row=4, columnspan=2, pady=10)

        # Add donor function

    def add_donor(self, name, id_number, blood_type, donation_date):
        """
        Add a donor only if their blood is not expired.
        """
        # Ensure the donation_date is passed, otherwise set it to today
        if not donation_date:
            donation_date = datetime.now().strftime('%Y-%m-%d')

        # Check if the blood is expired before adding
        if not self.check_blood_expiration(blood_type, donation_date):
            messagebox.showerror("Error", f"Cannot add donor. Blood of type {blood_type} is expired.")
            return  # Exit without adding the donor if blood is expired

        with sqlite3.connect('blood_bank.db', timeout=10) as conn:  # Added timeout and 'with' statement
            c = conn.cursor()

            # Insert the donor information
            c.execute("INSERT INTO donors (name, id_number, blood_type, donation_date) VALUES (?, ?, ?, ?)",
                      (name, id_number, blood_type, donation_date))

            # Update the blood supply and set the donation date for the blood
            c.execute("UPDATE blood_supply SET quantity = quantity + 1, donation_date = ? WHERE blood_type = ?",
                      (donation_date, blood_type))

            # Insert into blood_supply if the blood type doesn't already exist
            c.execute("INSERT OR IGNORE INTO blood_supply (blood_type, quantity, donation_date) VALUES (?, 1, ?)",
                      (blood_type, donation_date))

            conn.commit()  # Ensure that the transaction is committed

        self.log_action("Add Donor", f"Name: {name}, ID: {id_number}, Blood Type: {blood_type}, Date: {donation_date}")
        messagebox.showinfo("Success", "Donor added successfully")
    # GUI for issuing blood (used by Admin and User)

    def issue_blood_gui(self):
        issue_window = tk.Toplevel(self.root)
        issue_window.title("Issue Blood")

        frame = ttk.Frame(issue_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Blood type combobox with predefined options
        ttk.Label(frame, text="Blood Type:").grid(row=0, column=0, pady=5)
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        combobox_blood_type = ttk.Combobox(frame, values=blood_types, font=("Arial", 12),
                                           state="readonly")  # Only allow selection
        combobox_blood_type.grid(row=0, column=1, pady=5, padx=5)

        # Entry for quantity
        ttk.Label(frame, text="Quantity:").grid(row=1, column=0, pady=5)
        entry_issue_quantity = ttk.Entry(frame, font=("Arial", 12))
        entry_issue_quantity.grid(row=1, column=1, pady=5, padx=5)

        # Button to issue blood
        ttk.Button(frame, text="Issue Blood",
                   command=lambda: self.issue_blood(combobox_blood_type.get(), entry_issue_quantity.get())).grid(row=2,
                                                                                                                 columnspan=2,
                                                                                                                 pady=10)

    # Issue blood function
    def issue_blood(self, blood_type, quantity):
        if not blood_type or not quantity.isdigit():
            messagebox.showerror("Error", "Please select a valid blood type and enter a valid quantity.")
            return

        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("SELECT quantity FROM blood_supply WHERE blood_type=?", (blood_type,))
        result = c.fetchone()
        if result and result[0] >= int(quantity):
            c.execute("UPDATE blood_supply SET quantity = quantity - ? WHERE blood_type=?", (quantity, blood_type))
            conn.commit()
            self.log_action("Issue Blood", f"Blood Type: {blood_type}, Quantity: {quantity}")
            messagebox.showinfo("Success", "Blood issued successfully")
        else:
            self.suggest_alternative_blood(blood_type)
        conn.close()

    # Suggest alternative blood function
    def suggest_alternative_blood(self, requested_blood_type):
        compatibility = {
            'A+': ['A-', 'O+', 'O-'],
            'A-': ['O-'],
            'B+': ['B-', 'O+', 'O-'],
            'B-': ['O-'],
            'AB+': ['AB-', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-'],
            'AB-': ['A-', 'B-', 'O-'],
            'O+': ['O-'],
            'O-': []
        }
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        for alt_type in compatibility.get(requested_blood_type, []):
            c.execute("SELECT quantity FROM blood_supply WHERE blood_type=?", (alt_type,))
            result = c.fetchone()
            if result and result[0] > 0:
                self.log_action("Suggest Alternative Blood",
                                f"Requested: {requested_blood_type}, Suggested: {alt_type}")
                messagebox.showinfo("Alternative Available",
                                    f"Not enough {requested_blood_type}. Consider using {alt_type}.")
                return
        self.log_action("No Alternative Blood Available", f"Requested: {requested_blood_type}")
        messagebox.showerror("Error", f"No compatible blood type available for {requested_blood_type}.")
        conn.close()

        # GUI for emergency blood issue (used by Admin and User)

    def emergency_blood_gui(self):
        emergency_window = tk.Toplevel(self.root)
        emergency_window.title("Emergency Blood Issue")

        frame = ttk.Frame(emergency_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Button(frame, text="Issue Emergency Blood (O-)", command=self.emergency_blood).pack(pady=10)

        # Emergency blood function

    def emergency_blood(self):
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("SELECT quantity FROM blood_supply WHERE blood_type='O-'")
        result = c.fetchone()
        if result and result[0] > 0:
            c.execute("UPDATE blood_supply SET quantity = 0 WHERE blood_type='O-'")
            conn.commit()
            self.log_action("Emergency Blood Issued", "All O- blood units issued")
            messagebox.showinfo("Success", "All O- blood units issued")
        else:
            self.log_action("No Emergency Blood Available", "No O- blood units available")
            messagebox.showerror("Error", "No O- blood units available")
        conn.close()

    def log_action(self, action, details=""):
        with sqlite3.connect('blood_bank.db', timeout=30) as conn:  # Added timeout
            c = conn.cursor()
            c.execute("PRAGMA journal_mode=WAL;")  # Use WAL mode
            c.execute("PRAGMA busy_timeout=30000;")  # Set busy timeout to 30 seconds
            c.execute("INSERT INTO audit_trail (action, details) VALUES (?, ?)", (action, details))
            conn.commit()  # Ensure changes are committed

    def schedule_appointment_gui(self):
        appointment_window = tk.Toplevel(self.root)
        appointment_window.title("Schedule Appointment")

        frame = ttk.Frame(appointment_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Labels for the input fields
        ttk.Label(frame, text="Donor Name:").grid(row=0, column=0, pady=5)
        ttk.Label(frame, text="Blood Type:").grid(row=1, column=0, pady=5)
        ttk.Label(frame, text="Appointment Date:").grid(row=2, column=0, pady=5)
        ttk.Label(frame, text="Appointment Time:").grid(row=3, column=0, pady=5)

        # Entry for donor name
        entry_donor_name = ttk.Entry(frame, font=("Arial", 12))

        # Combobox for blood type with predefined options
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        combobox_blood_type = ttk.Combobox(frame, values=blood_types, font=("Arial", 12),
                                           state="readonly")  # Read-only selection

        # DateEntry for appointment date
        calendar_appointment_date = DateEntry(frame, font=("Arial", 12), date_pattern="yyyy-mm-dd")

        # Time selection using combobox for hours and minutes
        hours = [f"{i:02d}" for i in range(24)]  # 00 to 23
        minutes = [f"{i:02d}" for i in range(0, 60, 15)]  # 00, 15, 30, 45

        hour_combobox = ttk.Combobox(frame, values=hours, font=("Arial", 12), width=3)
        minute_combobox = ttk.Combobox(frame, values=minutes, font=("Arial", 12), width=3)

        hour_combobox.set("12")  # Default value for hour
        minute_combobox.set("00")  # Default value for minute

        # Place the fields in the grid
        entry_donor_name.grid(row=0, column=1, pady=5, padx=5)
        combobox_blood_type.grid(row=1, column=1, pady=5, padx=5)
        calendar_appointment_date.grid(row=2, column=1, pady=5, padx=5)
        hour_combobox.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)
        minute_combobox.grid(row=3, column=1, pady=5, padx=5, sticky=tk.E)

        # Button to schedule the appointment
        ttk.Button(frame, text="Schedule Appointment",
                   command=lambda: self.add_appointment(entry_donor_name.get(), combobox_blood_type.get(),
                                                        calendar_appointment_date.get(),
                                                        f"{hour_combobox.get()}:{minute_combobox.get()}")).grid(row=4,
                                                                                                                columnspan=2,
                                                                                                                pady=10)

    def add_appointment(self, donor_name, blood_type, appointment_date, appointment_time):
        if not donor_name or not blood_type or not appointment_date or not appointment_time:
            messagebox.showerror("Error", "All fields must be filled!")
            return

        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO appointments (donor_name, blood_type, appointment_date, appointment_time) VALUES (?, ?, ?, ?)",
            (donor_name, blood_type, appointment_date, appointment_time))
        conn.commit()
        conn.close()

        self.log_action("Schedule Appointment",
                        f"Donor: {donor_name}, Blood Type: {blood_type}, Date: {appointment_date}, Time: {appointment_time}")
        messagebox.showinfo("Success", "Appointment scheduled successfully!")

    def view_appointments_gui(self):
        view_window = tk.Toplevel(self.root)
        view_window.title("View Appointments")

        frame = ttk.Frame(view_window, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute(
            "SELECT id, donor_name, blood_type, appointment_date, appointment_time FROM appointments ORDER BY appointment_date, appointment_time")
        appointments = c.fetchall()
        conn.close()

        for idx, appointment in enumerate(appointments):
            appointment_info = f"{appointment[1]}, {appointment[2]}, {appointment[3]} {appointment[4]}"
            ttk.Label(frame, text=appointment_info).grid(row=idx, column=0, pady=5)

            ttk.Button(frame, text="Delete",
                       command=lambda appt_id=appointment[0]: self.delete_appointment(appt_id, view_window)).grid(
                row=idx, column=1, pady=5)

    def delete_appointment(self, appointment_id, view_window):
        conn = sqlite3.connect('blood_bank.db')
        c = conn.cursor()
        c.execute("DELETE FROM appointments WHERE id=?", (appointment_id,))
        conn.commit()
        conn.close()

        view_window.destroy()
        self.view_appointments_gui()  # Refresh the window to show updated appointments

        self.log_action("Delete Appointment", f"Appointment ID: {appointment_id}")
        messagebox.showinfo("Success", "Appointment deleted successfully!")

    def check_blood_expiration(self, blood_type, donation_date):
        """
        Check if the blood type is expired (over 35 days old) based on the given donation date.
        Returns True if the blood is valid (not expired), otherwise returns False and logs/removes the expired blood.
        """
        expiration_limit = timedelta(days=35)  # 35-day expiration limit
        today = datetime.now().date()

        try:
            donation_date_dt = datetime.strptime(donation_date, "%Y-%m-%d").date()
        except ValueError:
            self.log_action("Invalid Date Format", f"Invalid donation date for {blood_type}: {donation_date}")
            messagebox.showerror("Error", "Invalid donation date format!")
            return False

        # Check if the donation date is more than 35 days old
        if today - donation_date_dt > expiration_limit:
            # Log and indicate that the blood is expired
            self.log_action("Remove Expired Blood", f"Blood Type: {blood_type}, Donation Date: {donation_date}")
            messagebox.showinfo("Expired Blood", f"Blood type {blood_type} donated on {donation_date} has expired.")
            return False  # Blood is expired

        return True  # Blood is valid


if __name__ == "__main__":

    root = tk.Tk()
    app = BloodBankApp(root)
    root.mainloop()

