import tkinter as tk
import tkinter.ttk as ttk


class GUIComponents:
    def __init__(self, root):
        self.root = root
        self.menu = tk.Menu(self.root)
        self.control_frame = None
        self.display_frame = None
        self.log_tree = None
        self.saved_messages_listbox = tk.Listbox(root)
        self.start_time_slider = None
        self.end_time_slider = None
        self.start_time_display = None
        self.end_time_display = None
        self.log_level_vars = {}
        self.module_vars = {}

    def create_menu(self, open_callback):
        file_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Log File", command=open_callback)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.root.config(menu=self.menu)

    def create_frames(self):
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def create_log_display(self, display_callback):
        columns = ("timestamp", "level", "module", "message")
        self.log_tree = ttk.Treeview(
            self.display_frame, columns=columns, show="headings"
        )
        self.log_tree.pack(fill=tk.BOTH, expand=True)

        # Define column headings
        for col in columns:
            self.log_tree.heading(col, text=col.capitalize())

        # Add scrollbars
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

        # self.log_tree.column("timestamp", width=100, anchor="center", stretch=False)
        # self.log_tree.column("level", width=80, anchor="center", stretch=False)
        # self.log_tree.column("module", width=150, anchor="center", stretch=False)
        # self.log_tree.column("message", width=400, anchor="w", stretch=False)
        self.log_tree.bind("<<TreeviewSelect>>", display_callback)

    def create_controls(self, update_display_callback):
        # Log Levels Label
        self.log_level_label = tk.Label(self.control_frame, text="Log Levels")
        self.log_level_label.pack()

        self.log_level_frame = tk.Frame(self.control_frame)  # Placeholder for log level checkboxes
        self.log_level_frame.pack(fill=tk.X, pady=(5, 10))

        # Placeholder for log level checkboxes (set dynamically)
        self.log_level_vars = {}

        # Modules Label
        self.module_label = tk.Label(self.control_frame, text="Modules")
        self.module_label.pack()

        self.module_frame = tk.Frame(self.control_frame)  # Placeholder for module checkboxes
        self.module_frame.pack(fill=tk.X, pady=(5, 10))


        # Placeholder for module checkboxes (set dynamically)
        self.module_vars = {}

        # Saved Messages Section
        saved_messages_label = tk.Label(self.control_frame, text="Saved Messages")
        saved_messages_label.pack(pady=(10, 0))

        self.saved_messages_listbox = tk.Listbox(self.control_frame, height=10)
        self.saved_messages_listbox.pack(fill=tk.X, padx=5, pady=5)

    def create_time_sliders(self, update_start_time, update_end_time):
        separator = tk.Frame(self.control_frame, height=2, bd=1, relief=tk.SUNKEN)
        separator.pack(fill=tk.X, padx=5, pady=5)

        time_filter_label = tk.Label(self.control_frame, text="Time Filter")
        time_filter_label.pack()

        self.start_time_label = tk.Label(self.control_frame, text="Start Time:")
        self.start_time_label.pack()

        self.start_time_slider = tk.Scale(
            self.control_frame,
            from_=0,
            to=1000,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=False,
            command=update_start_time,
        )
        self.start_time_slider.pack()

        self.start_time_display = tk.Label(self.control_frame, text="")
        self.start_time_display.pack()

        self.end_time_label = tk.Label(self.control_frame, text="End Time:")
        self.end_time_label.pack()

        self.end_time_slider = tk.Scale(
            self.control_frame,
            from_=0,
            to=1000,
            orient=tk.HORIZONTAL,
            length=200,
            showvalue=False,
            command=update_end_time,
        )
        self.end_time_slider.pack()

        self.end_time_display = tk.Label(self.control_frame, text="")
        self.end_time_display.pack()

    def update_log_levels(self, log_levels, update_callback):
        # Clear existing log level checkboxes
        for widget in self.control_frame.pack_slaves():
            if hasattr(widget, "is_log_level"):  # Custom attribute to identify log level widgets
                widget.destroy()

        # Add new log level checkboxes
        for level in sorted(log_levels):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(
                self.log_level_frame,
                text=level,
                variable=var,
                command=update_callback,
            )
            cb.is_log_level = True  # Mark this widget as a log level widget
            cb.pack(anchor="w")
            self.log_level_vars[level] = var

    def update_start_time_display(self, timestamp):
        formatted_time = self.format_timestamp(timestamp)
        self.start_time_display.config(text=formatted_time)

    def update_end_time_display(self, timestamp):
        formatted_time = self.format_timestamp(timestamp)
        self.end_time_display.config(text=formatted_time)

    def update_modules(self, modules, update_callback):
        # Clear existing module checkboxes
        for widget in self.control_frame.pack_slaves():
            if hasattr(widget, "is_module"):  # Custom attribute to identify module widgets
                widget.destroy()

        # Add new module checkboxes
        for module in sorted(modules):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(
                self.module_frame,
                text=module,
                variable=var,
                command=update_callback,
            )
            cb.is_module = True  # Mark this widget as a module widget
            cb.pack(anchor="w")
            self.module_vars[module] = var

    def show_context_menu(self, event, copy_callback, save_callback):
        # Create context menu if not already created
        if not hasattr(self, "popup_menu"):
            self.popup_menu = tk.Menu(self.root, tearoff=0)
            self.popup_menu.add_command(label="Copy", command=copy_callback)
            self.popup_menu.add_command(label="Save Message", command=save_callback)
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.popup_menu.grab_release()

    def select_message_in_log_tree(self, message_id):
        # Iterate over log tree items to find the message
        for item in self.log_tree.get_children():
            item_tags = self.log_tree.item(item, "tags")
            if message_id in item_tags:
                self.log_tree.selection_set(item)
                self.log_tree.see(item)
                break

    def populate_log_tree(self, messages):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        for msg in messages:
            formatted_timestamp = self.format_timestamp(msg["timestamp"])
            self.log_tree.insert(
                "",
                tk.END,
                values=(
                    formatted_timestamp,
                    msg["level"],
                    msg["module"],
                    msg["message"],
                ),
            )

    def update_time_sliders(self, min_time, max_time):
        """
        Update the time sliders with the minimum and maximum timestamps.
        """
        self.start_time_slider.config(from_=0, to=1000)
        self.end_time_slider.config(from_=0, to=1000)

        # Reset slider positions to the new range
        self.start_time_slider.set(0)
        self.end_time_slider.set(1000)

        # Update display labels
        self.start_time_display.config(text=self.format_timestamp(min_time))
        self.end_time_display.config(text=self.format_timestamp(max_time))

    def format_timestamp(self, timestamp):
        """
        Format a UNIX timestamp into a human-readable string.
        """
        from datetime import datetime

        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
