import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import font
from tkinter import ttk
import re
from datetime import datetime
import os


class LogViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Log Viewer")

        # Initialize data structures
        self.messages = []
        self.log_levels = set()
        self.modules = set()

        # Dictionaries to hold the Tkinter variables for checkboxes
        self.log_level_vars = {}
        self.module_vars = {}

        # Selected log levels and modules
        self.selected_levels = {}
        self.selected_modules = {}

        # Time variables
        self.min_time = None
        self.max_time = None

        # Selected message IDs
        self.selected_message_ids = set()

        # Last opened directory
        self.last_opened_dir = None
        self.config_file = "config.txt"
        self.load_last_directory()

        # Create GUI components
        self.create_widgets()

    def create_widgets(self):
        # Create a menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Log File", command=self.open_log_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Create frames for controls and log display
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create Labels for placeholders (will be updated after file load)
        self.log_level_label = tk.Label(self.control_frame, text="Log Levels")
        self.log_level_label.pack()

        self.module_label = tk.Label(self.control_frame, text="Modules")
        self.module_label.pack()

        # Create "Saved Messages" section
        self.saved_messages_label = tk.Label(self.control_frame, text="Saved Messages")
        self.saved_messages_label.pack(pady=(10, 0))

        self.saved_messages_listbox = tk.Listbox(self.control_frame, height=10)
        self.saved_messages_listbox.pack(fill=tk.X, padx=5, pady=5)

        self.saved_messages_listbox.bind(
            "<<ListboxSelect>>", self.on_saved_message_select
        )

        # Create Treeview widget for log messages
        columns = ("timestamp", "level", "module", "message")
        self.log_tree = ttk.Treeview(
            self.display_frame, columns=columns, show="headings"
        )
        self.log_tree.pack(fill=tk.BOTH, expand=True)

        # Define headings
        self.log_tree.heading("timestamp", text="Timestamp")
        self.log_tree.heading("level", text="Level")
        self.log_tree.heading("module", text="Module")
        self.log_tree.heading("message", text="Message")

        # Set initial column widths and allow 'message' column to stretch
        self.log_tree.column("timestamp", width=100, anchor="center", stretch=False)
        self.log_tree.column("level", width=80, anchor="center", stretch=False)
        self.log_tree.column("module", width=150, anchor="center", stretch=False)
        self.log_tree.column("message", width=400, anchor="w", stretch=False)

        # Dealing with copying through ctrl-c or left click menu
        self.root.bind("<Control-c>", self.copy_selected_message)
        self.popup_menu = tk.Menu(self.root, tearoff=False)
        self.popup_menu.add_command(label="Copy", command=self.copy_selected_message)
        self.popup_menu.add_command(label="Save Message", command=self.save_message)
        self.log_tree.bind("<Button-3>", self.on_right_click)

        # Configure styles
        style = ttk.Style()

        # Use the system default font for better rendering
        default_font = tk.font.nametofont("TkDefaultFont")
        default_font.configure(size=10)  # Adjust size as needed

        # Configure Treeview style
        style.configure("Custom.Treeview", font=default_font)
        style.configure(
            "Custom.Treeview.Heading", font=(default_font.actual("family"), 10, "bold")
        )

        # Apply the custom style to the Treeview
        self.log_tree.configure(style="Custom.Treeview")

        # Bind selection event
        self.log_tree.bind("<<TreeviewSelect>>", self.on_message_select)

        # Add scrollbars to the Treeview
        scrollbar_y = tk.Scrollbar(
            self.display_frame, orient=tk.VERTICAL, command=self.log_tree.yview
        )
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_tree.config(yscrollcommand=scrollbar_y.set)

        scrollbar_x = tk.Scrollbar(
            self.display_frame, orient=tk.HORIZONTAL, command=self.log_tree.xview
        )
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_tree.config(xscrollcommand=scrollbar_x.set)

    def create_time_sliders(self):
        # Separator
        separator = tk.Frame(self.control_frame, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=5)

        time_filter_label = tk.Label(self.control_frame, text="Time Filter")
        time_filter_label.pack()

        # Labels to display selected times
        self.start_time_label = tk.Label(self.control_frame, text="Start Time:")
        self.start_time_label.pack()

        # Start time slider
        self.start_time_slider = tk.Scale(
            self.control_frame,
            from_=0,
            to=1000,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=False,
            command=self.update_start_time,
        )
        self.start_time_slider.pack()

        self.start_time_display = tk.Label(self.control_frame, text="")
        self.start_time_display.pack()

        self.end_time_label = tk.Label(self.control_frame, text="End Time:")
        self.end_time_label.pack()

        # End time slider
        self.end_time_slider = tk.Scale(
            self.control_frame,
            from_=0,
            to=1000,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=False,
            command=self.update_end_time,
        )
        self.end_time_slider.pack()

        self.end_time_display = tk.Label(self.control_frame, text="")
        self.end_time_display.pack()

        # Set initial values
        self.start_time_slider.set(0)
        self.end_time_slider.set(1000)

        # Initialize start and end timestamps
        self.start_timestamp = self.min_timestamp
        self.end_timestamp = self.max_timestamp

        # Update the time displays
        self.update_start_time(0)
        self.update_end_time(1000)

    def format_timestamp(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S.%f")[:-3]  # Display time with milliseconds

    def update_start_time(self, val):
        try:
            self.start_pos = float(val)
            self.start_timestamp = (
                self.min_timestamp + (self.start_pos / 1000) * self.time_span
            )
            self.start_time_display.config(
                text=self.format_timestamp(self.start_timestamp)
            )
            self.update_display()
        except Exception as e:
            print(f"Error updating start time: {e}")

    def update_end_time(self, val):
        try:
            self.end_pos = float(val)
            self.end_timestamp = (
                self.min_timestamp + (self.end_pos / 1000) * self.time_span
            )
            self.end_time_display.config(text=self.format_timestamp(self.end_timestamp))
            self.update_display()
        except Exception as e:
            print(f"Error updating end time: {e}")

    def open_log_file(self):
        # Use the last opened directory if available
        initial_dir = self.last_opened_dir if self.last_opened_dir else os.getcwd()

        file_path = filedialog.askopenfilename(
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
            initialdir=initial_dir,
        )
        if file_path:
            self.current_log_file = os.path.abspath(file_path)
            # Update the last opened directory
            self.last_opened_dir = os.path.dirname(file_path)
            self.save_last_directory()
            self.parse_log_file(file_path)
            self.load_saved_messages(file_path)

    def parse_log_file(self, file_path):
        # Clear existing data
        self.messages.clear()
        self.log_levels.clear()
        self.modules.clear()
        self.selected_levels.clear()
        self.selected_modules.clear()
        self.selected_message_ids.clear()

        # Preserve saved messages listbox and its label
        saved_messages_widgets = [
            self.saved_messages_label,
            self.saved_messages_listbox,
        ]

        # Clear control_frame (remove old widgets)
        for widget in self.control_frame.winfo_children():
            if widget not in saved_messages_widgets:
                widget.destroy()

        # Regular expression to parse log lines
        log_pattern = re.compile(r"\[(.*?)\]\[(.*?)\]\[(.*?)\] (.*)")

        try:
            with open(file_path, "r") as f:
                current_message = None
                for idx, line in enumerate(f):
                    line = line.strip()
                    match = log_pattern.match(line)
                    if match:
                        # If a new log entry starts, save the previous one
                        if current_message:
                            self.messages.append(current_message)
                            self.log_levels.add(level)
                            self.modules.add(module)
                        timestamp_str, level, module, message = match.groups()

                        # Parse timestamp into datetime object
                        try:
                            dt = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S.%f"
                            )
                            timestamp = dt.timestamp()  # Convert to UNIX timestamp
                        except ValueError as e:
                            # If parsing fails, skip this line
                            print(f"Failed to parse timestamp '{timestamp_str}': {e}")
                            continue

                        current_message = {
                            "id": idx,  # Unique ID for the message
                            "timestamp": timestamp,
                            "timestamp_str": timestamp_str,  # Keep original string for display
                            "time_only_str": dt.strftime("%H:%M:%S.%f")[
                                :-3
                            ],  # Time with milliseconds
                            "level": level,
                            "module": module,
                            "message": message,
                        }
                    else:
                        # continuation of the previous message
                        if current_message:
                            current_message["message"] += " " + line

                # Append the last message
                if current_message:
                    self.messages.append(current_message)
                    self.log_levels.add(level)
                    self.modules.add(module)

            if not self.messages:
                messagebox.showinfo(
                    "No messages", "No valid log messages found in the file."
                )
                return

            # Find minimum and maximum timestamps
            timestamps = [msg["timestamp"] for msg in self.messages]
            self.min_timestamp = min(timestamps)
            self.max_timestamp = max(timestamps)
            self.time_span = (
                self.max_timestamp - self.min_timestamp or 1
            )  # Avoid division by zero

            # Normalize timestamps and store in messages
            for msg in self.messages:
                msg["normalized_timestamp"] = (
                    (msg["timestamp"] - self.min_timestamp) / self.time_span * 1000
                )

            # Initialize start and end positions
            self.start_pos = 0  # Corresponds to min_timestamp
            self.end_pos = 1000  # Corresponds to max_timestamp

            # Re-create time sliders
            self.create_time_sliders()

            # Re-create Labels
            self.log_level_label = tk.Label(self.control_frame, text="Log Levels")
            self.log_level_label.pack()

            # Create Checkbuttons for log levels
            for level in sorted(self.log_levels):
                var = tk.BooleanVar(value=True)
                cb = tk.Checkbutton(
                    self.control_frame,
                    text=level,
                    variable=var,
                    command=self.update_display,
                )
                cb.pack(anchor="w")
                self.log_level_vars[level] = var
                self.selected_levels[level] = True

            # Separator
            separator = tk.Frame(self.control_frame, height=2, bd=1, relief=tk.SUNKEN)
            separator.pack(fill=tk.X, padx=5, pady=5)

            # Re-create Modules Label
            self.module_label = tk.Label(self.control_frame, text="Modules")
            self.module_label.pack()

            # Create Checkbuttons for modules
            for module in sorted(self.modules):
                var = tk.BooleanVar(value=True)
                cb = tk.Checkbutton(
                    self.control_frame,
                    text=module,
                    variable=var,
                    command=self.update_display,
                )
                cb.pack(anchor="w")
                self.module_vars[module] = var
                self.selected_modules[module] = True

            self.update_display()
        except Exception as e:
            print(f"Failed to read log file: {e}")  # Print error to terminal
            messagebox.showerror("Error", f"Failed to read log file: {e}")

    def load_saved_messages(self, file_path):
        self.saved_messages_listbox.delete(0, tk.END)  # Clear existing list
        saved_file = "saved_messages.txt"

        if not os.path.exists(saved_file):
            return

        # Normalize the file path for comparison
        normalized_file_path = os.path.abspath(file_path)

        with open(saved_file, "r") as f:
            for line in f:
                saved_message = eval(line.strip())  # Deserialize the saved message

                # Normalize the saved log file path for comparison
                saved_log_file = os.path.abspath(saved_message["log_file"])

                # Only load messages associated with the current log file
                if saved_log_file == normalized_file_path:
                    name = saved_message.get(
                        "name", f"Message {saved_message['message_id']}"
                    )
                    self.saved_messages_listbox.insert(
                        tk.END, f"{name}: {saved_message['details'][3]}"
                    )

    def on_saved_message_select(self, event):
        selection = self.saved_messages_listbox.curselection()
        if not selection:
            return

        selected_text = self.saved_messages_listbox.get(selection[0])

        try:
            # Extract the message ID from the saved entry
            # Assuming the format is now "Name: Message"
            # Find the message by its text content instead
            message_details = selected_text.split(": ", 1)  # Split only at the first ": "
            if len(message_details) < 2:
                return  # Malformed entry, ignore

            # Find and select the corresponding message in the Treeview
            message_text = message_details[1]
            for item in self.log_tree.get_children():
                if self.log_tree.item(item, "values")[3] == message_text:
                    self.log_tree.selection_set(item)
                    self.log_tree.see(item)
                    break
        except Exception as e:
            print(f"Error selecting saved message: {e}")

    def update_display(self):
        try:
            # Update selected levels and modules
            for level, var in self.log_level_vars.items():
                self.selected_levels[level] = var.get()
            for module, var in self.module_vars.items():
                self.selected_modules[module] = var.get()

            # Get the currently selected message IDs before updating
            selected_items = self.log_tree.selection()
            self.selected_message_ids.clear()
            for item in selected_items:
                message_id = int(self.log_tree.item(item, "tags")[0])
                self.selected_message_ids.add(message_id)

            # Clear the display
            for item in self.log_tree.get_children():
                self.log_tree.delete(item)
            self.displayed_messages = []

            # Display filtered messages
            for msg in self.messages:
                # Filter by log level and module
                if not (
                    self.selected_levels.get(msg["level"], False)
                    and self.selected_modules.get(msg["module"], False)
                ):
                    continue

                # Filter by timespan
                if msg["timestamp"] < self.start_timestamp:
                    continue
                if msg["timestamp"] > self.end_timestamp:
                    continue

                # Insert into Treeview
                item_id = self.log_tree.insert(
                    "",
                    tk.END,
                    values=(
                        msg["time_only_str"],
                        msg["level"],
                        msg["module"],
                        msg["message"],
                    ),
                    tags=(str(msg["id"]),),
                )
                self.displayed_messages.append(msg)

            # Reselect previously selected messages
            for item in self.log_tree.get_children():
                message_id = int(self.log_tree.item(item, "tags")[0])
                if message_id in self.selected_message_ids:
                    self.log_tree.selection_add(item)

            # Adjust column widths
            self.adjust_column_widths()
            self.ensure_selected_item_visible()

            # Update saved messages listbox
            # self.update_saved_messages_listbox()

        except Exception as e:
            print(f"Error updating display: {e}")

    def update_saved_messages_listbox(self):
        """
        Updates the saved messages listbox to reflect only the saved messages relevant
        to the currently loaded log file.
        """
        try:
            saved_file = "saved_messages.txt"
            if not os.path.exists(saved_file):
                return

            # Clear the listbox
            self.saved_messages_listbox.delete(0, tk.END)

            # Reload saved messages for the current log file
            with open(saved_file, "r") as f:
                for line in f:
                    saved_message = eval(line.strip())  # Deserialize the saved message
                    if saved_message["log_file"] == self.last_opened_dir:
                        self.saved_messages_listbox.insert(
                            tk.END,
                            f"Message {saved_message['message_id']}: {saved_message['details'][3]}",
                        )
        except Exception as e:
            print(f"Error updating saved messages listbox: {e}")

    def adjust_column_widths(self):
        # Get font used in the Treeview
        font_style = tk.font.nametofont("TkDefaultFont")
        # Column identifiers
        columns = ("timestamp", "level", "module", "message")
        # Initialize a dictionary to keep track of max widths
        max_width = {}
        # Minimum widths for each column
        min_widths = {"timestamp": 80, "level": 60, "module": 80, "message": 100}

        # Measure width of header text
        for col in columns:
            header_text = self.log_tree.heading(col, option="text")
            max_width[col] = font_style.measure(header_text)

        # Iterate over displayed messages to find max width for each column
        for msg in self.displayed_messages:
            for col in columns:
                if col == "timestamp":
                    text = msg["time_only_str"]
                else:
                    text = msg[col]
                text_width = font_style.measure(str(text))
                if text_width > max_width[col]:
                    max_width[col] = text_width

        # Set column widths
        for col in columns:
            # Add padding to the width
            width = max(max_width[col] + 20, min_widths[col])
            self.log_tree.column(col, width=width)

    def on_message_select(self, event):
        # Update selected message IDs based on selection
        selected_items = self.log_tree.selection()
        self.selected_message_ids.clear()
        for item in selected_items:
            message_id = int(self.log_tree.item(item, "tags")[0])
            self.selected_message_ids.add(message_id)

    def load_last_directory(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.last_opened_dir = f.readline().strip()
                    if not os.path.isdir(self.last_opened_dir):
                        self.last_opened_dir = None
        except Exception as e:
            print(f"Error loading last directory: {e}")
            self.last_opened_dir = None

    def save_last_directory(self):
        try:
            with open(self.config_file, "w") as f:
                f.write(self.last_opened_dir or "")
        except Exception as e:
            print(f"Error saving last directory: {e}")

    def copy_selected_message(self, event=None):
        # Get the currently selected item
        selection = self.log_tree.selection()
        if not selection:
            return  # No item selected

        # Assuming the columns are (timestamp, level, module, message)
        # The message is the 4th column (index 3 in values tuple)
        item_id = selection[0]
        values = self.log_tree.item(item_id, "values")
        if values and len(values) > 3:
            message_text = values[3]
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(message_text)

    def on_right_click(self, event):
        # Select the row under the cursor
        row_id = self.log_tree.identify_row(event.y)
        if row_id:
            # Clear existing selection
            self.log_tree.selection_remove(*self.log_tree.selection())
            # Select this row
            self.log_tree.selection_add(row_id)
            self.log_tree.focus(row_id)

        # Display the context menu
        self.popup_menu.tk_popup(event.x_root, event.y_root)
        self.popup_menu.grab_release()

    def ensure_selected_item_visible(self):
        selected_items = self.log_tree.selection()
        if not selected_items:
            return  # No selection to handle

        # Ensure the first selected item is visible
        item = selected_items[0]
        self.log_tree.see(item)

    def save_message(self):
        # Ensure a message is selected
        selection = self.log_tree.selection()
        if not selection:
            messagebox.showinfo("Save Message", "Please select a message to save.")
            return

        # Get the selected message details
        item_id = selection[0]
        values = self.log_tree.item(item_id, "values")
        if not values:
            return

        # Ask the user for a name for the saved message
        name = simpledialog.askstring("Save Message", "Enter a name for this message:")
        if not name:  # If no name is provided, do not save the message
            return

        # Construct the saved message data
        message_id = self.log_tree.item(item_id, "tags")[0]
        saved_message = {
            "log_file": self.current_log_file,  # Reference the current log file
            "message_id": message_id,
            "name": name,  # Add the name to the saved data
            "details": values,
        }

        # Save to a file or in-memory structure
        saved_file = "saved_messages.txt"
        with open(saved_file, "a") as f:
            f.write(f"{saved_message}\n")

        # Add to "Saved Messages" listbox
        self.saved_messages_listbox.insert(tk.END, f"{name}: {values[3]}")

        messagebox.showinfo("Save Message", "Message saved successfully!")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewerApp(root)
    app.run()
