import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from datetime import datetime
from pathlib import Path
import json
import calendar

# Global variables
accounts = {}
current_entries = []
undo_stack = []
redo_stack = []
current_expenses = []
undo_expense_stack = []
redo_expense_stack = []
financial_data = {}  # Dictionary to store financial data by date (format: "YYYY-MM-DD")


def format_row(label, amount):
    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError):
        numeric_amount = 0.0
    return f"{label.ljust(30)}{numeric_amount:10.2f}"

# Persistence paths
DATA_PATH = Path(__file__).with_name("money_rider_data.json")


def load_persisted_state():
    global accounts, financial_data
    if not DATA_PATH.exists():
        return
    try:
        with DATA_PATH.open("r", encoding="utf-8") as data_file:
            raw = json.load(data_file)
    except (json.JSONDecodeError, OSError):
        return

    accounts = raw.get("accounts", {})

    raw_financial = raw.get("financial_data", {})
    financial_data.clear()
    for date_str, payload in raw_financial.items():
        entries = [
            (item[0], float(item[1]))
            for item in payload.get("entries", [])
            if isinstance(item, (list, tuple)) and len(item) == 2
        ]
        expense_entries = [
            (item[0], float(item[1]))
            for item in payload.get("expense_entries", [])
            if isinstance(item, (list, tuple)) and len(item) == 2
        ]
        financial_data[date_str] = {
            "income": float(payload.get("income", 0)),
            "expenses": float(payload.get("expenses", 0)),
            "entries": entries,
            "expense_entries": expense_entries,
        }


def persist_state():
    serializable_data = {
        "accounts": accounts,
        "financial_data": {
            date_str: {
                "income": payload.get("income", 0),
                "expenses": payload.get("expenses", 0),
                "entries": [[entry[0], float(entry[1])] for entry in payload.get("entries", [])],
                "expense_entries": [
                    [entry[0], float(entry[1])] for entry in payload.get("expense_entries", [])
                ],
            }
            for date_str, payload in financial_data.items()
        },
    }
    try:
        with DATA_PATH.open("w", encoding="utf-8") as data_file:
            json.dump(serializable_data, data_file, indent=2)
    except OSError:
        messagebox.showerror("Error", "Failed to save data to disk.")


load_persisted_state()


class PageNode:
    def __init__(self, name, render_fn, args=()):
        self.name = name
        self.render_fn = render_fn
        self.args = args
        self.prev = None
        self.next = None


current_page = None


def navigate_to(name, render_fn, *args):
    global current_page
    node = PageNode(name, render_fn, args)
    if current_page:
        current_page.next = node
        node.prev = current_page
    current_page = node
    render_fn(*args)


def go_back(window):
    global current_page
    if current_page and current_page.prev:
        prev_node = current_page.prev
        prev_node.next = None
        current_page = prev_node
        window.destroy()
        prev_node.render_fn(*prev_node.args)
    else:
        window.destroy()

# Splash Screen
def splash_screen():
    splash = tk.Tk()
    splash.title("Money Rider")
    splash.geometry("570x700")
    splash.configure(bg="#1C1C1C")  # Dark background for rider theme

    title = tk.Label(splash, text="Money Rider 🚵", font=("Bubblegum Sans", 36, "bold"), bg="#1C1C1C", fg="white")
    title.pack(pady=50)

    login_btn = tk.Button(splash, text="Login", font=("Bubblegum Sans", 18), bg="#404040", fg="white",
                          command=lambda: [splash.destroy(), navigate_to("login", login_screen)])
    login_btn.pack(pady=10)

    create_account_btn = tk.Button(splash, text="Create Account", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
                                   command=lambda: [splash.destroy(), navigate_to("create_account", create_account_screen)])
    create_account_btn.pack()

    splash.mainloop()

# Create Account Screen
def create_account_screen():
    create = tk.Tk()
    create.title("Create Account")
    create.geometry("570x700")
    create.configure(bg="#1C1C1C")

    tk.Label(create, text="Create Username", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
    username_entry = tk.Entry(create, font=("Bubblegum Sans", 14))
    username_entry.pack(pady=5)

    tk.Label(create, text="Create Password", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
    password_entry = tk.Entry(create, show="*", font=("Bubblegum Sans", 14))
    password_entry.pack(pady=5)

    def create_account():
        username = username_entry.get()
        password = password_entry.get()
        if username and password:
            accounts[username] = password
            persist_state()
            messagebox.showinfo("Success", "Account Created!")
            go_back(create)
        else:
            messagebox.showerror("Error", "Fill all fields")

    tk.Button(create, text="Create", font=("Bubblegum Sans", 14), bg="#404040", fg="white", command=create_account).pack(pady=20)
    tk.Button(create, text="Back", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=lambda: go_back(create)).pack(pady=10)

# Login Screen
def login_screen():
    login = tk.Tk()
    login.title("Login")
    login.geometry("570x700")
    login.configure(bg="#1C1C1C")

    tk.Label(login, text="Username", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
    username_entry = tk.Entry(login, font=("Bubblegum Sans", 14))
    username_entry.pack(pady=5)

    tk.Label(login, text="Password", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
    password_entry = tk.Entry(login, show="*", font=("Bubblegum Sans", 14))
    password_entry.pack(pady=5)

    def validate_login():
        username = username_entry.get()
        password = password_entry.get()
        if username in accounts and accounts[username] == password:
            login.destroy()
            navigate_to("calendar", calendar_screen)
        else:
            messagebox.showerror("Error", "Wrong Username or Password!")

    tk.Button(login, text="Login", font=("Bubblegum Sans", 14), bg="#404040", fg="white", command=validate_login).pack(pady=20)
    tk.Button(login, text="Back", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=lambda: go_back(login)).pack(pady=10)

# Calendar Screen
def calendar_screen():
    cal = tk.Tk()
    cal.title("Money Rider - Calendar")
    cal.geometry("570x700")
    cal.configure(bg="#1C1C1C")

    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    def show_saved_data(date_str, day):
        # Create a popup window to display saved data
        popup = tk.Toplevel(cal)
        popup.title(f"Saved Data - {date_str}")
        popup.geometry("500x600")
        popup.configure(bg="#1C1C1C")
        
        # Main frame
        main_frame = tk.Frame(popup, bg="#1C1C1C")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        tk.Label(main_frame, text=f"Saved Financial Data", bg="#1C1C1C", fg="white", 
                font=("Bubblegum Sans", 20, "bold")).pack(pady=10)
        tk.Label(main_frame, text=date_str, bg="#1C1C1C", fg="#4CAF50", 
                font=("Bubblegum Sans", 14)).pack(pady=5)
        
        # Get the saved data
        data = financial_data[date_str]
        
        # Summary frame
        summary_frame = tk.Frame(main_frame, bg="#2C2C2C", bd=2, relief=tk.RIDGE)
        summary_frame.pack(fill=tk.X, padx=10, pady=15)
        
        # Income summary
        income_frame = tk.Frame(summary_frame, bg="#2C2C2C")
        income_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(income_frame, text="Total Income:", bg="#2C2C2C", fg="white",
                font=("Bubblegum Sans", 14)).pack(side=tk.LEFT)
        tk.Label(income_frame, text=f"₱{data['income']:,.2f}", bg="#2C2C2C", fg="#4CAF50",
                font=("Bubblegum Sans", 14, "bold")).pack(side=tk.RIGHT)
        
        # Expenses summary
        expenses_frame = tk.Frame(summary_frame, bg="#2C2C2C")
        expenses_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(expenses_frame, text="Total Expenses:", bg="#2C2C2C", fg="white",
                font=("Bubblegum Sans", 14)).pack(side=tk.LEFT)
        tk.Label(expenses_frame, text=f"₱{data['expenses']:,.2f}", bg="#2C2C2C", fg="#F44336",
                font=("Bubblegum Sans", 14, "bold")).pack(side=tk.RIGHT)
        
        # Net total
        net_frame = tk.Frame(summary_frame, bg="#2C2C2C")
        net_frame.pack(fill=tk.X, padx=10, pady=10)
        
        net_total = data['income'] - data['expenses']
        tk.Label(net_frame, text="Net Total:", bg="#2C2C2C", fg="white",
                font=("Bubblegum Sans", 16)).pack(side=tk.LEFT)
        tk.Label(net_frame, text=f"₱{net_total:,.2f}", bg="#2C2C2C", 
                fg="#4CAF50" if net_total >= 0 else "#F44336",
                font=("Bubblegum Sans", 16, "bold")).pack(side=tk.RIGHT)
        
        # Details frame
        details_frame = tk.Frame(main_frame, bg="#1C1C1C")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Notebook for income/expense details
        notebook = ttk.Notebook(details_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Income tab
        income_tab = tk.Frame(notebook, bg="#1C1C1C")
        notebook.add(income_tab, text="Income Details")
        
        if data['entries']:
            income_listbox = tk.Listbox(income_tab, bg="#404040", fg="white", 
                                      font=("Courier New", 12), width=50)
            income_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for entry in data['entries']:
                income_listbox.insert(tk.END, format_row(entry[0], entry[1]))
        else:
            tk.Label(income_tab, text="No income data", bg="#1C1C1C", fg="white",
                   font=("Bubblegum Sans", 14)).pack(pady=20)
        
        # Expenses tab
        expense_tab = tk.Frame(notebook, bg="#1C1C1C")
        notebook.add(expense_tab, text="Expense Details")
        
        if data['expense_entries']:
            expense_listbox = tk.Listbox(expense_tab, bg="#404040", fg="white", 
                                       font=("Courier New", 12), width=50)
            expense_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for expense in data['expense_entries']:
                expense_listbox.insert(tk.END, format_row(expense[0], expense[1]))
        else:
            tk.Label(expense_tab, text="No expense data", bg="#1C1C1C", fg="white",
                   font=("Bubblegum Sans", 14)).pack(pady=20)
        
        # Button frame
        button_frame = tk.Frame(main_frame, bg="#1C1C1C")
        button_frame.pack(pady=10)
        
        def open_for_edit():
            global current_entries, current_expenses
            reset_stacks()
            current_entries.extend(data['entries'])
            current_expenses.extend(data['expense_entries'])
            popup.destroy()
            cal.destroy()
            navigate_to("income", income_screen, day, current_year, current_month)

        edit_btn = tk.Button(button_frame, text="View/Edit", font=("Bubblegum Sans", 12),
                            bg="#404040", fg="white", width=12,
                            command=open_for_edit)
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(button_frame, text="Close", font=("Bubblegum Sans", 12),
                             bg="#404040", fg="white", width=12,
                             command=popup.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)

    def reset_stacks():
        current_entries.clear()
        current_expenses.clear()
        undo_stack.clear()
        redo_stack.clear()
        undo_expense_stack.clear()
        redo_expense_stack.clear()

    def go_to_income(day):
        global current_entries, current_expenses

        # Save current date for later reference
        selected_date = f"{current_year}-{current_month:02d}-{day:02d}"

        # Check if we have data for this date
        if selected_date in financial_data:
            # Show the saved data in a popup window
            show_saved_data(selected_date, day)
        else:
            reset_stacks()
            cal.destroy()
            navigate_to("income", income_screen, day, current_year, current_month)

    month_var = tk.StringVar(value=calendar.month_name[current_month])
    year_var = tk.StringVar(value=str(current_year))

    def create_calendar_grid():
        for widget in cal.winfo_children():
            widget.destroy()

        month_var.set(calendar.month_name[current_month])
        year_var.set(str(current_year))

        cal_frame = tk.Frame(cal, bg="#1C1C1C")
        cal_frame.pack(fill=tk.BOTH, expand=True)

        # Month and year selection
        header_frame = tk.Frame(cal_frame, bg="#1C1C1C")
        header_frame.pack(pady=10)

        month_menu = ttk.Combobox(header_frame, textvariable=month_var, 
                                 values=list(calendar.month_name[1:]), 
                                 state="readonly", 
                                 font=("Bubblegum Sans", 16), 
                                 justify="center")
        month_menu.grid(row=0, column=0, padx=10, pady=10)
        month_menu.bind("<<ComboboxSelected>>", lambda e: change_month())

        year_menu = ttk.Combobox(header_frame, textvariable=year_var, 
                                values=list(range(2020, 2031)), 
                                state="readonly", 
                                font=("Bubblegum Sans", 16), 
                                justify="center")
        year_menu.grid(row=0, column=1, padx=10, pady=10)
        year_menu.bind("<<ComboboxSelected>>", lambda e: change_year())

        # Days of week header
        days_frame = tk.Frame(cal_frame, bg="#1C1C1C")
        days_frame.pack()

        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, day in enumerate(days_of_week):
            tk.Label(days_frame, text=day, bg="#1C1C1C", fg="white", 
                    font=("Bubblegum Sans", 12)).grid(row=0, column=col, padx=5, pady=5)

        # Calendar days grid
        month_cal = calendar.monthcalendar(current_year, current_month)
        for row, week in enumerate(month_cal):
            for col, day in enumerate(week):
                if day == 0:
                    # Empty space for days not in the month
                    tk.Label(days_frame, text="", bg="#1C1C1C", width=5, height=2).grid(row=row+1, column=col, padx=2, pady=2)
                    continue
                
                date_str = f"{current_year}-{current_month:02d}-{day:02d}"
                day_button = tk.Button(days_frame, text=str(day), bg="#E0E0E0", fg="black",
                                     font=("Bubblegum Sans", 14), width=5, height=2,
                                     command=lambda d=day: go_to_income(d))
                day_button.grid(row=row + 1, column=col, padx=2, pady=2)
                
                # Highlight current day
                if (day == current_date.day and 
                    current_month == current_date.month and 
                    current_year == current_date.year):
                    day_button.config(bg="#4CAF50", fg="white")
                
                # Highlight days with saved data
                if date_str in financial_data:
                    day_button.config(bg="#2196F3", fg="white")

        # Date range calculation section
        range_frame = tk.Frame(cal_frame, bg="#1C1C1C")
        range_frame.pack(pady=20)

        tk.Label(range_frame, text="Date Range Calculator", bg="#1C1C1C", fg="white", 
                font=("Bubblegum Sans", 14)).grid(row=0, column=0, columnspan=2, pady=10)

        # Start date
        tk.Label(range_frame, text="From:", bg="#1C1C1C", fg="white", 
                font=("Bubblegum Sans", 12)).grid(row=1, column=0, sticky="e")
        start_day = ttk.Combobox(range_frame, values=list(range(1, 32)), width=3, 
                               font=("Bubblegum Sans", 12))
        start_day.grid(row=1, column=1, sticky="w")
        start_day.set("1")
        
        start_month = ttk.Combobox(range_frame, values=list(calendar.month_name[1:]), width=10, 
                                 font=("Bubblegum Sans", 12))
        start_month.grid(row=1, column=2, sticky="w")
        start_month.set(calendar.month_name[current_month])
        
        start_year = ttk.Combobox(range_frame, values=list(range(2020, 2031)), width=5, 
                                font=("Bubblegum Sans", 12))
        start_year.grid(row=1, column=3, sticky="w")
        start_year.set(str(current_year))

        # End date
        tk.Label(range_frame, text="To:", bg="#1C1C1C", fg="white", 
                font=("Bubblegum Sans", 12)).grid(row=2, column=0, sticky="e")
        end_day = ttk.Combobox(range_frame, values=list(range(1, 32)), width=3, 
                             font=("Bubblegum Sans", 12))
        end_day.grid(row=2, column=1, sticky="w")
        end_day.set("1")
        
        end_month = ttk.Combobox(range_frame, values=list(calendar.month_name[1:]), width=10, 
                               font=("Bubblegum Sans", 12))
        end_month.grid(row=2, column=2, sticky="w")
        end_month.set(calendar.month_name[current_month])
        
        end_year = ttk.Combobox(range_frame, values=list(range(2020, 2031)), width=5, 
                              font=("Bubblegum Sans", 12))
        end_year.grid(row=2, column=3, sticky="w")
        end_year.set(str(current_year))

        # Calculate button
        def calculate_range():
            try:
                # Get start date components
                start_d = int(start_day.get())
                start_m = list(calendar.month_name).index(start_month.get())
                start_y = int(start_year.get())
                
                # Get end date components
                end_d = int(end_day.get())
                end_m = list(calendar.month_name).index(end_month.get())
                end_y = int(end_year.get())
                
                # Create date strings for comparison
                start_date_str = f"{start_y}-{start_m:02d}-{start_d:02d}"
                end_date_str = f"{end_y}-{end_m:02d}-{end_d:02d}"
                
                # Validate date range
                if start_date_str > end_date_str:
                    messagebox.showerror("Error", "Start date must be before end date")
                    return
                
                # Calculate totals
                total_income = 0
                total_expenses = 0
                days_with_data = 0
                
                for date_str in sorted(financial_data.keys()):
                    if start_date_str <= date_str <= end_date_str:
                        data = financial_data[date_str]
                        total_income += data["income"]
                        total_expenses += data["expenses"]
                        days_with_data += 1
                
                net_total = total_income - total_expenses
                
                # Display results
                result_window = tk.Toplevel(cal)
                result_window.title("Date Range Results")
                result_window.geometry("400x300")
                result_window.configure(bg="#1C1C1C")
                
                tk.Label(result_window, text=f"Date Range: {start_date_str} to {end_date_str}", 
                        bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 12)).pack(pady=10)
                
                tk.Label(result_window, text=f"Days with data: {days_with_data}", 
                        bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 12)).pack(pady=5)
                
                tk.Label(result_window, text=f"Total Income: ₱{total_income:,.2f}", 
                        bg="#1C1C1C", fg="#4CAF50", font=("Bubblegum Sans", 12)).pack(pady=5)
                
                tk.Label(result_window, text=f"Total Expenses: ₱{total_expenses:,.2f}", 
                        bg="#1C1C1C", fg="#F44336", font=("Bubblegum Sans", 12)).pack(pady=5)
                
                tk.Label(result_window, text=f"Net Total: ₱{net_total:,.2f}", 
                        bg="#1C1C1C", fg="#4CAF50" if net_total >= 0 else "#F44336", 
                        font=("Bubblegum Sans", 14, "bold")).pack(pady=10)
                
            except ValueError:
                messagebox.showerror("Error", "Invalid date selection")
            
        calc_button = tk.Button(range_frame, text="Calculate Range", font=("Bubblegum Sans", 12), 
                              bg="#404040", fg="white", command=calculate_range)
        calc_button.grid(row=3, column=0, columnspan=4, pady=10)

        # Navigation buttons
        nav_frame = tk.Frame(cal_frame, bg="#1C1C1C")
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="Back", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
                 command=lambda: go_back(cal)).pack(side=tk.LEFT, padx=10)

    def change_month():
        nonlocal current_month
        selected_month = month_var.get()
        try:
            new_month = list(calendar.month_name).index(selected_month)
        except ValueError:
            return
        if new_month == 0:
            return
        current_month = new_month
        create_calendar_grid()

    def change_year():
        nonlocal current_year
        try:
            current_year = int(year_var.get())
        except ValueError:
            return
        create_calendar_grid()

    create_calendar_grid()
    cal.mainloop()

# Income Screen
def income_screen(day, year, month):
    inc = tk.Tk()
    inc.title("Income")
    inc.geometry("570x700")
    inc.configure(bg="#1C1C1C")

    name_var = tk.StringVar()
    income_var = tk.StringVar()

    # Store the current date
    current_date_str = f"{year}-{month:02d}-{day:02d}"
    
    # Display the current date
    date_label = tk.Label(inc, text=f"Date: {year}-{month:02d}-{day:02d}", 
                         bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14))
    date_label.pack(pady=10)

    tk.Label(inc, text="Customer Name", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
    name_entry = tk.Entry(inc, textvariable=name_var, font=("Bubblegum Sans", 14))
    name_entry.pack(pady=5)

    tk.Label(inc, text="Income", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
    income_entry = tk.Entry(inc, textvariable=income_var, font=("Bubblegum Sans", 14))
    income_entry.pack(pady=5)

    display_frame = tk.Frame(inc, bg="#1C1C1C")
    display_frame.pack(pady=10)

    # Create a frame for the header with fixed column widths
    header_frame = tk.Frame(display_frame, bg="#1C1C1C")
    header_frame.pack()
    
    # Header labels with fixed width
    tk.Label(header_frame, text="Customer Name".ljust(30), bg="#1C1C1C", fg="white", 
             font=("Bubblegum Sans", 14)).grid(row=0, column=0, padx=5)
    tk.Label(header_frame, text="Income".rjust(10), bg="#1C1C1C", fg="white", 
             font=("Bubblegum Sans", 14)).grid(row=0, column=1, padx=5)

    # Create a listbox with monospace font for alignment
    listbox = tk.Listbox(display_frame, width=45, font=("Courier New", 14), 
                        bg="#404040", fg="white", justify=tk.LEFT)
    listbox.pack()

    # Populate listbox with existing entries
    for entry in current_entries:
        listbox.insert(tk.END, format_row(entry[0], entry[1]))

    def enter_income():
        name = name_var.get()
        income = income_var.get()
        if not name or not income:
            messagebox.showinfo("Error", "Something's missing!")
            return
        
        try:
            income_val = float(income)
        except ValueError:
            messagebox.showerror("Error", "Income must be a number")
            return
            
        entry = (name, income_val)
        current_entries.insert(0, entry)
        undo_stack.append(entry)
        # Format with fixed width columns
        listbox.insert(0, format_row(name, income_val))
        name_var.set("")
        income_var.set("")

    def undo():
        if listbox.curselection():
            index = listbox.curselection()[0]
            redo_stack.append(current_entries.pop(index))
            listbox.delete(index)
        elif current_entries:
            redo_stack.append(current_entries.pop(0))
            listbox.delete(0)

    def redo():
        if redo_stack:
            entry = redo_stack.pop()
            current_entries.insert(0, entry)
            listbox.insert(0, format_row(entry[0], entry[1]))

    button_row = tk.Frame(inc, bg="#1C1C1C")
    button_row.pack(pady=10)

    tk.Button(button_row, text="Enter", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=enter_income, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(button_row, text="Undo", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=undo, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(button_row, text="Redo", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=redo, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(button_row, text="Expenses", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=lambda:[save_data(current_date_str), inc.destroy(), navigate_to("expenses", expenses_screen, day, year, month)],
              width=12).pack(side=tk.LEFT, padx=5)

    tk.Button(inc, text="Back", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=lambda: go_back(inc)).pack(pady=10)

    inc.mainloop()

# Expenses Screen
def expenses_screen(day, year, month):
    exp = tk.Tk()
    exp.title("Expenses")
    exp.geometry("570x700")
    exp.configure(bg="#1C1C1C")

    expense_var = tk.StringVar()
    amount_var = tk.StringVar()

    # Store the current date
    current_date_str = f"{year}-{month:02d}-{day:02d}"
    
    # Display the current date
    date_label = tk.Label(exp, text=f"Date: {year}-{month:02d}-{day:02d}", 
                         bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14))
    date_label.pack(pady=10)

    def add_option():
        popup = tk.Toplevel(exp)
        popup.title("Add Expense")
        popup.geometry("400x300")
        popup.configure(bg="#1C1C1C")

        tk.Label(popup, text="Expense", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
        expense_entry = tk.Entry(popup, textvariable=expense_var, font=("Bubblegum Sans", 14))
        expense_entry.pack(pady=5)

        tk.Label(popup, text="Amount", bg="#1C1C1C", fg="white", font=("Bubblegum Sans", 14)).pack(pady=5)
        amount_entry = tk.Entry(popup, textvariable=amount_var, font=("Bubblegum Sans", 14))
        amount_entry.pack(pady=5)

        def save_expense():
            expense = expense_var.get()
            amount = amount_var.get()
            if not expense or not amount:
                messagebox.showerror("Error", "Something's missing!")
                return
            
            try:
                amount_val = float(amount)
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number")
                return
                
            entry = (expense, amount_val)
            current_expenses.insert(0, entry)
            undo_expense_stack.append(entry)
            # Format with fixed width columns
            listbox.insert(0, format_row(expense, amount_val))
            expense_var.set("")
            amount_var.set("")
            popup.destroy()

        tk.Button(popup, text="Save", font=("Bubblegum Sans", 14), bg="#404040", fg="white", command=save_expense).pack(pady=10)

    display_frame = tk.Frame(exp, bg="#1C1C1C")
    display_frame.pack(pady=10)

    # Create a frame for the header with fixed column widths
    header_frame = tk.Frame(display_frame, bg="#1C1C1C")
    header_frame.pack()
    
    # Header labels with fixed width
    tk.Label(header_frame, text="Expense".ljust(30), bg="#1C1C1C", fg="white", 
             font=("Bubblegum Sans", 14)).grid(row=0, column=0, padx=5)
    tk.Label(header_frame, text="Amount".rjust(10), bg="#1C1C1C", fg="white", 
             font=("Bubblegum Sans", 14)).grid(row=0, column=1, padx=5)

    # Create a listbox with monospace font for alignment
    listbox = tk.Listbox(display_frame, width=45, font=("Courier New", 14), 
                        bg="#404040", fg="white", justify=tk.LEFT)
    listbox.pack()

    # Populate listbox with existing expenses
    for expense in current_expenses:
        listbox.insert(tk.END, format_row(expense[0], expense[1]))

    def undo():
        if listbox.curselection():
            index = listbox.curselection()[0]
            redo_expense_stack.append(current_expenses.pop(index))
            listbox.delete(index)
        elif current_expenses:
            redo_expense_stack.append(current_expenses.pop(0))
            listbox.delete(0)

    def redo():
        if redo_expense_stack:
            entry = redo_expense_stack.pop()
            current_expenses.insert(0, entry)
            listbox.insert(0, format_row(entry[0], entry[1]))

    tk.Button(exp, text="Add Option", font=("Bubblegum Sans", 14), bg="#404040", fg="white", command=add_option).pack(pady=5)
    tk.Button(exp, text="Undo", font=("Bubblegum Sans", 14), bg="#404040", fg="white", command=undo).pack(pady=5)
    tk.Button(exp, text="Redo", font=("Bubblegum Sans", 14), bg="#404040", fg="white", command=redo).pack(pady=5)

    tk.Button(exp, text="Back", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=lambda: go_back(exp)).pack(pady=5)

    tk.Button(exp, text="Show Totals", font=("Bubblegum Sans", 14), bg="#404040", fg="white",
              command=lambda:[save_data(current_date_str), exp.destroy(), navigate_to("total", total_screen, day, year, month)]).pack(pady=20)

    exp.mainloop()

# Save data for the current date
def save_data(date_str):
    total_income = sum(float(entry[1]) for entry in current_entries)
    total_expenses = sum(float(expense[1]) for expense in current_expenses)
    
    financial_data[date_str] = {
        "income": total_income,
        "expenses": total_expenses,
        "entries": current_entries.copy(),
        "expense_entries": current_expenses.copy()
    }
    persist_state()

# Total Screen
def total_screen(day, year, month):
    total = tk.Tk()
    total.title("Total")
    total.geometry("570x700")
    total.configure(bg="#1C1C1C")

    # Main frame
    main_frame = tk.Frame(total, bg="#1C1C1C")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Title
    tk.Label(main_frame, text="Financial Summary", bg="#1C1C1C", fg="white", 
            font=("Bubblegum Sans", 24, "bold")).pack(pady=20)

    # Date display
    date_str = f"{year}-{month:02d}-{day:02d}"
    tk.Label(main_frame, text=f"Date: {date_str}", bg="#1C1C1C", fg="white", 
            font=("Bubblegum Sans", 14)).pack()

    # Summary frame
    summary_frame = tk.Frame(main_frame, bg="#2C2C2C", bd=2, relief=tk.RIDGE)
    summary_frame.pack(fill=tk.X, padx=20, pady=10)

    # Income section
    income_frame = tk.Frame(summary_frame, bg="#2C2C2C")
    income_frame.pack(fill=tk.X, padx=10, pady=10)

    total_income = sum(float(i[1]) for i in current_entries)
    tk.Label(income_frame, text="Total Income:", bg="#2C2C2C", fg="white", 
            font=("Bubblegum Sans", 16)).pack(side=tk.LEFT, padx=10)
    tk.Label(income_frame, text=f"₱{total_income:,.2f}", bg="#2C2C2C", fg="#4CAF50", 
            font=("Bubblegum Sans", 16, "bold")).pack(side=tk.RIGHT, padx=10)

    # Expenses section
    expenses_frame = tk.Frame(summary_frame, bg="#2C2C2C")
    expenses_frame.pack(fill=tk.X, padx=10, pady=10)

    total_expenses = sum(float(e[1]) for e in current_expenses)
    tk.Label(expenses_frame, text="Total Expenses:", bg="#2C2C2C", fg="white", 
            font=("Bubblegum Sans", 16)).pack(side=tk.LEFT, padx=10)
    tk.Label(expenses_frame, text=f"₱{total_expenses:,.2f}", bg="#2C2C2C", fg="#F44336", 
            font=("Bubblegum Sans", 16, "bold")).pack(side=tk.RIGHT, padx=10)


# Total Screen
def total_screen(day, year, month):
    total = tk.Tk()
    total.title("Total")
    total.geometry("570x700")
    total.configure(bg="#1C1C1C")

    # Main frame
    main_frame = tk.Frame(total, bg="#1C1C1C")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Tit
    tk.Label(main_frame, text="Financial Summary", bg="#1C1C1C", fg="white", 
            font=("Bubblegum Sans", 24, "bold")).pack(pady=20)

    # Date display
    date_str = f"{year}-{month:02d}-{day:02d}"
    tk.Label(main_frame, text=f"Date: {date_str}", bg="#1C1C1C", fg="white", 
            font=("Bubblegum Sans", 14)).pack()

    # Summary frame
    summary_frame = tk.Frame(main_frame, bg="#2C2C2C", bd=2, relief=tk.RIDGE)
    summary_frame.pack(fill=tk.X, padx=20, pady=10)

    # Income section
    income_frame = tk.Frame(summary_frame, bg="#2C2C2C")
    income_frame.pack(fill=tk.X, padx=10, pady=10)

    total_income = sum(float(i[1]) for i in current_entries)
    tk.Label(income_frame, text="Total Income:", bg="#2C2C2C", fg="white", 
            font=("Bubblegum Sans", 16)).pack(side=tk.LEFT, padx=10)
    tk.Label(income_frame, text=f"₱{total_income:,.2f}", bg="#2C2C2C", fg="#4CAF50", 
            font=("Bubblegum Sans", 16, "bold")).pack(side=tk.RIGHT, padx=10)

    # Expenses section
    expenses_frame = tk.Frame(summary_frame, bg="#2C2C2C")
    expenses_frame.pack(fill=tk.X, padx=10, pady=10)

    total_expenses = sum(float(e[1]) for e in current_expenses)
    tk.Label(expenses_frame, text="Total Expenses:", bg="#2C2C2C", fg="white", 
            font=("Bubblegum Sans", 16)).pack(side=tk.LEFT, padx=10)
    tk.Label(expenses_frame, text=f"₱{total_expenses:,.2f}", bg="#2C2C2C", fg="#F44336", 
            font=("Bubblegum Sans", 16, "bold")).pack(side=tk.RIGHT, padx=10)

    # Net total section
    net_frame = tk.Frame(summary_frame, bg="#2C2C2C")
    net_frame.pack(fill=tk.X, padx=10, pady=20)

    day_total = total_income - total_expenses
    tk.Label(net_frame, text="Net Total:", bg="#2C2C2C", fg="white", 
            font=("Bubblegum Sans", 18)).pack(side=tk.LEFT, padx=10)
    tk.Label(net_frame, text=f"₱{day_total:,.2f}", bg="#2C2C2C", 
            fg="#4CAF50" if day_total >= 0 else "#F44336", 
            font=("Bubblegum Sans", 18, "bold")).pack(side=tk.RIGHT, padx=10)

    # Navigation buttons
    button_frame = tk.Frame(main_frame, bg="#1C1C1C")
    button_frame.pack(pady=30)

    back_btn = tk.Button(button_frame, text="Back", font=("Bubblegum Sans", 14), 
                        bg="#404040", fg="white", width=10,
                        command=lambda: go_back(total))
    back_btn.pack(side=tk.LEFT, padx=10)

    end_btn = tk.Button(button_frame, text="End", font=("Bubblegum Sans", 14), 
                       bg="#404040", fg="white", width=10,
                       command=lambda:[total.destroy(), navigate_to("calendar", calendar_screen)])
    end_btn.pack(side=tk.LEFT, padx=10)

    total.mainloop()

navigate_to("splash", splash_screen)
