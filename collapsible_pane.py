import tkinter as tk
from tkinter import ttk


class CollapsiblePane(ttk.Frame):
    def __init__(self, parent, expanded_text="Collapse <<",
                 collapsed_text="Expand >>"):

        ttk.Frame.__init__(self, parent)

        # These are the class variable
        # see a underscore in expanded_text and _collapsed_text
        # this means these are private to class
        self.parent = parent
        self._expanded_text = expanded_text
        self._collapsed_text = collapsed_text

        # Here weight implies that it can grow it's
        # size if extra space is available
        # default weight is 0
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._title = tk.Label(self, text="Test", width=100, bd=1)
        self._title.grid(row=0, column=0, sticky=tk.W)

        # Tkinter variable storing integer value
        self._variable = tk.IntVar()

        # Checkbutton is created but will behave as Button
        # cause in style, Button is passed
        # main reason to do this is Button do not support
        # variable option but checkbutton do
        self._button = ttk.Checkbutton(self, variable=self._variable, command=self._activate, style="TButton")
        self._button.grid(row=1, column=0, sticky=tk.E)

        self._bt = tk.Button(self, text="+", bd=0)
        self._bt.grid(row=2, column=1, sticky=tk.E)

        # This wil create a separator
        # A separator is a line, we can also set thickness
        #self._separator = ttk.Separator(self, orient="horizontal")
        #self._separator.grid(row=0, column=1, sticky="we")

        self.frame = ttk.Frame(self)

        # This will call activate function of class
        self._activate()

    def _activate(self):
        if not self._variable.get():

            # As soon as button is pressed it removes this widget
            # but is not destroyed means can be displayed again
            self.frame.grid_forget()

            # This will change the text of the checkbutton
            self._button.configure(text=self._collapsed_text)

        elif self._variable.get():
            # increasing the frame area so new widgets
            # could reside in this container
            self.frame.grid(row=1, column=0, columnspan=2)
            self._button.configure(text=self._expanded_text)

    def toggle(self):
        self._variable.set(not self._variable.get())
        self._activate()
