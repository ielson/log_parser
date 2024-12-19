import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import font
from tkinter import ttk
import re
from datetime import datetime
import os
from gui_components import GUIComponents
from file_handler import FileHandler
from log_parser import LogParser
from message_manager import MessageManager


class LogViewerApp:
    def __init__(self, root):
        self.root = root
        self.gui = GUIComponents(root)
        self.file_handler = FileHandler()
        self.log_parser = LogParser()
        self.message_manager = MessageManager(self.gui.saved_messages_listbox)

        self.messages = []
        self.log_levels = set()
        self.modules = set()
        self.current_log_file = None
        self.last_opened_dir = None

        self.setup()

        # self.root.title("Log Viewer")

        # # Time variables
        # self.min_time = None
        # self.max_time = None

        # # Selected message IDs
        # self.selected_message_ids = set()

        # # Last opened directory
        # self.last_opened_dir = None
        # self.config_file = "config.txt"
        # self.load_last_directory()

        # # Create GUI components
        # self.create_widgets()

    def setup(self):
        self.gui.create_menu(self.open_log_file)
        self.gui.create_frames()
        self.gui.create_controls(self.update_display)
        self.gui.create_log_display(self.update_display)

        # Bind events
        self.gui.saved_messages_listbox.bind(
            "<<ListboxSelect>>", self.on_saved_message_select
        )
        self.gui.log_tree.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Control-c>", self.copy_selected_message)

        self.config_file = "config.txt"
        self.load_last_directory()

    def open_log_file(self):
        # Use the last opened directory if available
        initial_dir = self.last_opened_dir if self.last_opened_dir else os.getcwd()

        file_path = filedialog.askopenfilename(
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
            initialdir=initial_dir,
        )
        if not file_path:
            return

        self.current_log_file = file_path
        self.save_last_directory()

        # Parse the file
        self.messages = self.log_parser.parse(file_path)
        self.last_opened_dir = os.path.dirname(file_path)

        # Normalize timestamps and store in messages
        # for msg in self.messages:
        #     msg["normalized_timestamp"] = (
        #         (msg["timestamp"] - self.min_timestamp) / self.time_span * 1000
        #     )

        # Extract log levels and modules
        self.log_levels = {msg["level"] for msg in self.messages}
        self.modules = {msg["module"] for msg in self.messages}

        # Get time range from parsed messages
        self.min_timestamp, self.max_timestamp = self.log_parser.get_time_range(
            self.messages
        )

        self.start_timestamp = self.min_timestamp
        self.end_timestamp = self.max_timestamp

        self.time_span = (
            self.max_timestamp - self.min_timestamp or 1
        )  # Avoid division by zero

        # Update GUI with parsed data
        self.gui.update_log_levels(self.log_levels, self.update_display)
        self.gui.update_modules(self.modules, self.update_display)

        # Update the time sliders
        min_time, max_time = self.log_parser.get_time_range(self.messages)
        self.gui.create_time_sliders(self.update_start_time, self.update_end_time)
        self.gui.update_time_sliders(min_time, max_time)

        self.message_manager.load_saved_messages(self.current_log_file)

        # Update display
        self.update_display()

    def update_display(self):
        selected_levels = {
            level for level, var in self.gui.log_level_vars.items() if var.get()
        }
        selected_modules = {
            module for module, var in self.gui.module_vars.items() if var.get()
        }

        filtered_messages = [
            msg
            for msg in self.messages
            if msg["level"] in selected_levels
            and msg["module"] in selected_modules
            and self.start_timestamp <= msg["timestamp"] <= self.end_timestamp
        ]

        # Display messages in the log tree
        self.gui.populate_log_tree(filtered_messages)

    def update_start_time(self, value):
        self.log_parser.set_start_time(value)
        self.update_display()

    def update_end_time(self, value):
        self.log_parser.set_end_time(value)
        self.update_display()

    # def create_widgets(self):
    #     Configure styles
    #     style = ttk.Style()

    #     # Use the system default font for better rendering
    #     default_font = tk.font.nametofont("TkDefaultFont")
    #     default_font.configure(size=10)  # Adjust size as needed

    #     # Configure Treeview style
    #     style.configure("Custom.Treeview", font=default_font)
    #     style.configure(
    #         "Custom.Treeview.Heading", font=(default_font.actual("family"), 10, "bold")
    #     )

    #     Set initial values
    #     self.start_time_slider.set(0)
    #     self.end_time_slider.set(1000)

    #     Initialize start and end timestamps
    #     self.start_timestamp = self.min_timestamp
    #     self.end_timestamp = self.max_timestamp

    #     # Update the time displays
    #     self.update_start_time(0)
    #     self.update_end_time(1000)

    def format_timestamp(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S.%f")[:-3]  # Display time with milliseconds

    def update_start_time(self, val):
        try:
            print(f"start pos {float(val)}, time span {self.time_span}")
            self.start_pos = float(val)
            self.start_timestamp = (
                self.min_timestamp + (self.start_pos / 1000) * self.time_span
            )

            # self.time_span = (
            #     self.max_timestamp - self.min_timestamp or 1
            # )  # Avoid division by zero

            # # Normalize timestamps and store in messages
            # for msg in self.messages:
            #     msg["normalized_timestamp"] = (
            #         (msg["timestamp"] - self.min_timestamp) / self.time_span * 1000
            #     )

            print(f"value sent to update start time display: {self.start_timestamp}")
            # Update the GUI component with the formatted timestamp
            self.gui.update_start_time_display(self.start_timestamp)
            self.update_display()
        except Exception as e:
            print(f"Error updating start time: {e}")

    def update_end_time(self, val):
        try:
            self.end_pos = float(val)
            self.end_timestamp = (
                self.min_timestamp + (self.end_pos / 1000) * self.time_span
            )
            self.gui.update_end_time_display(self.end_timestamp)
            self.update_display()
        except Exception as e:
            print(f"Error updating end time: {e}")

        # def open_log_file(self):
        #     # Use the last opened directory if available
        #     initial_dir = self.last_opened_dir if self.last_opened_dir else os.getcwd()

        #     # file_path = filedialog.askopenfilename(
        #     #     filetypes=[("Log files", "*.log"), ("All files", "*.*")],
        #     #     initialdir=initial_dir,
        #     # )
        #     if file_path:
        #         self.current_log_file = os.path.abspath(file_path)
        #         # Update the last opened directory
        #         self.last_opened_dir = os.path.dirname(file_path)
        #         self.save_last_directory()
        #         self.parse_log_file(file_path)
        #         self.load_saved_messages(file_path)

        # def parse_log_file(self, file_path):
        #     # Clear existing data
        #     self.messages.clear()
        #     self.log_levels.clear()
        #     self.modules.clear()
        #     self.selected_levels.clear()
        #     self.selected_modules.clear()
        #     self.selected_message_ids.clear()

        #     # Preserve saved messages listbox and its label
        #     saved_messages_widgets = [
        #         self.saved_messages_label,
        #         self.saved_messages_listbox,
        #     ]

        #     # Clear control_frame (remove old widgets)
        #     for widget in self.control_frame.winfo_children():
        #         if widget not in saved_messages_widgets:
        #             widget.destroy()

        #     # Regular expression to parse log lines
        #     # log_pattern = re.compile(r"\[(.*?)\]\[(.*?)\]\[(.*?)\] (.*)")

        #     try:
        #         # self.time_span = (
        #         #     self.max_timestamp - self.min_timestamp or 1
        #         # )  # Avoid division by zero

        #         # Normalize timestamps and store in messages
        #         # for msg in self.messages:
        #         #     msg["normalized_timestamp"] = (
        #         #         (msg["timestamp"] - self.min_timestamp) / self.time_span * 1000
        #         #     )

        #         # Initialize start and end positions
        #         # self.start_pos = 0  # Corresponds to min_timestamp
        #         # self.end_pos = 1000  # Corresponds to max_timestamp

        #         # # Re-create time sliders
        #         # self.create_time_sliders()

        #         # # Re-create Labels
        #         # self.log_level_label = tk.Label(self.control_frame, text="Log Levels")
        #         # self.log_level_label.pack()

        #         # Create Checkbuttons for log levels
        #         # for level in sorted(self.log_levels):
        #         #     var = tk.BooleanVar(value=True)
        #         #     cb = tk.Checkbutton(
        #         #         self.control_frame,
        #         #         text=level,
        #         #         variable=var,
        #         #         command=self.update_display,
        #         #     )
        #         #     cb.pack(anchor="w")
        #         #     self.log_level_vars[level] = var
        #             # self.selected_levels[level] = True

        #         # Separator
        #         separator = tk.Frame(self.control_frame, height=2, bd=1, relief=tk.SUNKEN)
        #         separator.pack(fill=tk.X, padx=5, pady=5)

        #         # Re-create Modules Label
        #         self.module_label = tk.Label(self.control_frame, text="Modules")
        #         self.module_label.pack()

        #         # Create Checkbuttons for modules
        #         # for module in sorted(self.modules):
        #         #     var = tk.BooleanVar(value=False)
        #         #     cb = tk.Checkbutton(
        #         #         self.control_frame,
        #         #         text=module,
        #         #         variable=var,
        #         #         command=self.update_display,
        #         #     )
        #         #     cb.pack(anchor="w")
        #         #     self.module_vars[module] = var
        #             # self.selected_modules[module] = True

        #         self.update_display()
        #     except Exception as e:
        #         print(f"Failed to read log file: {e}")  # Print error to terminal
        #         messagebox.showerror("Error", f"Failed to read log file: {e}")

        # def load_saved_messages(self, file_path):
        #     self.saved_messages_listbox.delete(0, tk.END)  # Clear existing list
        #     saved_file = "saved_messages.txt"

        #     if not os.path.exists(saved_file):
        #         return

        #     # Normalize the file path for comparison
        #     normalized_file_path = os.path.abspath(file_path)

        #     with open(saved_file, "r") as f:
        #         for line in f:
        #             saved_message = eval(line.strip())  # Deserialize the saved message

        #             # Normalize the saved log file path for comparison
        #             saved_log_file = os.path.abspath(saved_message["log_file"])

        #             # Only load messages associated with the current log file
        #             if saved_log_file == normalized_file_path:
        #                 name = saved_message.get(
        #                     "name", f"Message {saved_message['message_id']}"
        #                 )
        #                 self.saved_messages_listbox.insert(
        #                     tk.END, f"{name}: {saved_message['details'][3]}"
        #                 )

        # def on_saved_message_select(self, event):
        selection = self.gui.saved_messages_listbox.curselection()
        if not selection:
            return

        selected_text = self.saved_messages_listbox.get(selection[0])

        try:
            # Extract the message ID from the saved entry
            # Assuming the format is now "Name: Message"
            # Find the message by its text content instead
            message_details = selected_text.split(
                ": ", 1
            )  # Split only at the first ": "
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

    # def update_display(self):
    #     try:
    #         # Update selected levels and modules
    #         # for level, var in self.log_level_vars.items():
    #         #     self.selected_levels[level] = var.get()
    #         # for module, var in self.module_vars.items():
    #         #     self.selected_modules[module] = var.get()

    #         # Get the currently selected message IDs before updating
    #         selected_items = self.log_tree.selection()
    #         self.selected_message_ids.clear()
    #         for item in selected_items:
    #             message_id = int(self.log_tree.item(item, "tags")[0])
    #             self.selected_message_ids.add(message_id)

    #         # Clear the display
    #         for item in self.log_tree.get_children():
    #             self.log_tree.delete(item)
    #         self.displayed_messages = []

    #         # Display filtered messages
    #         for msg in self.messages:
    #             # Filter by log level and module
    #             if not (
    #                 self.selected_levels.get(msg["level"], False)
    #                 and self.selected_modules.get(msg["module"], False)
    #             ):
    #                 continue

    #             # Filter by timespan
    #             if msg["timestamp"] < self.start_timestamp:
    #                 continue
    #             if msg["timestamp"] > self.end_timestamp:
    #                 continue

    #             # Insert into Treeview
    #             item_id = self.log_tree.insert(
    #                 "",
    #                 tk.END,
    #                 values=(
    #                     msg["time_only_str"],
    #                     msg["level"],
    #                     msg["module"],
    #                     msg["message"],
    #                 ),
    #                 tags=(str(msg["id"]),),
    #             )
    #             self.displayed_messages.append(msg)

    #         # Reselect previously selected messages
    #         for item in self.log_tree.get_children():
    #             message_id = int(self.log_tree.item(item, "tags")[0])
    #             if message_id in self.selected_message_ids:
    #                 self.log_tree.selection_add(item)

    #         # Adjust column widths
    #         self.adjust_column_widths()
    #         self.ensure_selected_item_visible()

    #         # Update saved messages listbox
    #         # self.update_saved_messages_listbox()

    #     except Exception as e:
    #         print(f"Error updating display: {e}")

    # def update_saved_messages_listbox(self):
    #     """
    #     Updates the saved messages listbox to reflect only the saved messages relevant
    #     to the currently loaded log file.
    #     """
    #     try:
    #         saved_file = "saved_messages.txt"
    #         if not os.path.exists(saved_file):
    #             return

    #         # Clear the listbox
    #         self.saved_messages_listbox.delete(0, tk.END)

    #         # Reload saved messages for the current log file
    #         with open(saved_file, "r") as f:
    #             for line in f:
    #                 saved_message = eval(line.strip())  # Deserialize the saved message
    #                 if saved_message["log_file"] == self.last_opened_dir:
    #                     self.saved_messages_listbox.insert(
    #                         tk.END,
    #                         f"Message {saved_message['message_id']}: {saved_message['details'][3]}",
    #                     )
    #     except Exception as e:
    #         print(f"Error updating saved messages listbox: {e}")

    # def adjust_column_widths(self):
    #     # Get font used in the Treeview
    #     font_style = tk.font.nametofont("TkDefaultFont")
    #     # Column identifiers
    #     columns = ("timestamp", "level", "module", "message")
    #     # Initialize a dictionary to keep track of max widths
    #     max_width = {}
    #     # Minimum widths for each column
    #     min_widths = {"timestamp": 80, "level": 60, "module": 80, "message": 100}

    #     # Measure width of header text
    #     for col in columns:
    #         header_text = self.log_tree.heading(col, option="text")
    #         max_width[col] = font_style.measure(header_text)

    #     # Iterate over displayed messages to find max width for each column
    #     for msg in self.displayed_messages:
    #         for col in columns:
    #             if col == "timestamp":
    #                 text = msg["time_only_str"]
    #             else:
    #                 text = msg[col]
    #             text_width = font_style.measure(str(text))
    #             if text_width > max_width[col]:
    #                 max_width[col] = text_width

    #     # Set column widths
    #     for col in columns:
    #         # Add padding to the width
    #         width = max(max_width[col] + 20, min_widths[col])
    #         self.log_tree.column(col, width=width)

    # def on_message_select(self, event):
    #     # Update selected message IDs based on selection
    #     selected_items = self.log_tree.selection()
    #     self.selected_message_ids.clear()
    #     for item in selected_items:
    #         message_id = int(self.log_tree.item(item, "tags")[0])
    #         self.selected_message_ids.add(message_id)

    # def load_last_directory(self):
    #     try:
    #         if os.path.exists(self.config_file):
    #             with open(self.config_file, "r") as f:
    #                 self.last_opened_dir = f.readline().strip()
    #                 if not os.path.isdir(self.last_opened_dir):
    #                     self.last_opened_dir = None
    #     except Exception as e:
    #         print(f"Error loading last directory: {e}")
    #         self.last_opened_dir = None

    # def save_last_directory(self):
    #     try:
    #         with open(self.config_file, "w") as f:
    #             f.write(self.last_opened_dir or "")
    #     except Exception as e:
    #         print(f"Error saving last directory: {e}")

    def copy_selected_message(self, event=None):
        # Get the currently selected item
        selection = self.gui.log_tree.selection()
        if not selection:
            return  # No item selected

        # Assuming the columns are (timestamp, level, module, message)
        # The message is the 4th column (index 3 in values tuple)
        item_id = selection[0]
        values = self.gui.log_tree.item(item_id, "values")
        if values and len(values) > 3:
            message_text = values[3]
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(message_text)

    def on_right_click(self, event):
        self.gui.show_context_menu(event, self.copy_selected_message, self.save_message)
        #     # Select the row under the cursor
        #     row_id = self.log_tree.identify_row(event.y)
        #     if row_id:
        #         # Clear existing selection
        #         self.log_tree.selection_remove(*self.log_tree.selection())
        #         # Select this row
        #         self.log_tree.selection_add(row_id)
        #         self.log_tree.focus(row_id)

        #     # Display the context menu
        #     self.popup_menu.tk_popup(event.x_root, event.y_root)
        #     self.popup_menu.grab_release()

        # def ensure_selected_item_visible(self):
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
        values = self.gui.log_tree.item(item_id, "values")
        if not values:
            return

        # Ask the user for a name for the saved message
        name = simpledialog.askstring("Save Message", "Enter a name for this message:")
        if not name:  # If no name is provided, do not save the message
            return

        # Construct the saved message data
        message_id = self.gui.log_tree.item(item_id, "tags")[0]
        self.message_manager.save_message(
            self.current_log_file, message_id, name, values
        )
        # saved_message = {
        #     "log_file": self.current_log_file,  # Reference the current log file
        #     "message_id": message_id,
        #     "name": name,  # Add the name to the saved data
        #     "details": values,
        # }

        # Save to a file or in-memory structure
        saved_file = "saved_messages.txt"
        with open(saved_file, "a") as f:
            f.write(f"{saved_message}\n")

        # Add to "Saved Messages" listbox
        self.saved_messages_listbox.insert(tk.END, f"{name}: {values[3]}")

        messagebox.showinfo("Save Message", "Message saved successfully!")

    def on_saved_message_select(self, event):
        selection = self.gui.saved_messages_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        saved_message = self.message_manager.get_saved_message(index)
        if saved_message:
            # Find and select the corresponding message in the Treeview
            self.gui.select_message_in_log_tree(saved_message["message_id"])

    def load_last_directory(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.last_opened_dir = f.readline().strip()
                    print("loading last dir")
                    if not os.path.isdir(self.last_opened_dir):
                        self.last_opened_dir = None
        except Exception as e:
            print(f"Error loading last directory: {e}")
            self.last_opened_dir = None

    def save_last_directory(self):
        try:
            with open(self.config_file, "w") as f:
                f.write(self.last_opened_dir or "")
                print("saving last directory")
        except Exception as e:
            print(f"Error saving last directory: {e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewerApp(root)
    app.run()
