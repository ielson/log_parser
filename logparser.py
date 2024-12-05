import tkinter as tk
from tkinter import filedialog, messagebox
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
            # Update the last opened directory
            self.last_opened_dir = os.path.dirname(file_path)
            self.save_last_directory()
            self.parse_log_file(file_path)

    def parse_log_file(self, file_path):
        # Clear existing data
        self.messages.clear()
        self.log_levels.clear()
        self.modules.clear()
        self.selected_levels.clear()
        self.selected_modules.clear()
        self.selected_message_ids.clear()

        # Clear control_frame (remove old widgets)
        for widget in self.control_frame.winfo_children():
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
                        # self.messages.append(current_message)
                        # self.log_levels.add(level)
                        # self.modules.add(module)
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
        except Exception as e:
            print(f"Error updating display: {e}")

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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewerApp(root)
    app.run()
