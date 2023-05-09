import tkinter
import customtkinter


class LoginWindow:
    def __init__(self):
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
        self.root_login = customtkinter.CTk()
        self.root_login.geometry(f"{500}x{500}")
        self.root_login.title("Fudgify - Login")
        self.create_widgets()

    def create_widgets(self):
        frame = customtkinter.CTkFrame(
            master=self.root_login, width=450, height=450, corner_radius=0
        )
        frame.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)

        login_label = customtkinter.CTkLabel(
            master=frame,
            width=400,
            height=60,
            corner_radius=0,
            fg_color=("gray70", "gray35"),
            text="Please login to continue",
        )
        login_label.place(relx=0.5, rely=0.3, anchor=tkinter.CENTER)

        self.email_entry = customtkinter.CTkEntry(
            master=frame, width=400, placeholder_text="Email"
        )
        self.email_entry.place(relx=0.5, rely=0.52, anchor=tkinter.CENTER)

        self.password_entry = customtkinter.CTkEntry(
            master=frame,
            width=400,
            show="*",
            placeholder_text="Password",
        )
        self.password_entry.place(relx=0.5, rely=0.6, anchor=tkinter.CENTER)

        button_login = customtkinter.CTkButton(
            master=frame,
            text="Login",
            command=self.login_event,
            width=400,
        )
        button_login.place(relx=0.5, rely=0.7, anchor=tkinter.CENTER)

    def login_event(self):
        if self.email_entry.get() == "ABC" and self.password_entry.get() == "123":
            self.root_login.destroy()
            MainWindow()
        else:
            self.email_entry.configure(text_color="red")
            self.password_entry.configure(text_color="red")

    def mainloop(self):
        self.root_login.mainloop()


class MainWindow(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Fudgify - Main Window")
        self.geometry("700x450")

        # set grid layout 1x2
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # create navigation frame
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(
            self.navigation_frame,
            text="  Fudgify",
            compound="left",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        )
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Home",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.home_button_event,
        )
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.frame_2_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Frame 2",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.frame_2_button_event,
        )
        self.frame_2_button.grid(row=2, column=0, sticky="ew")

        self.frame_3_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Frame 3",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.frame_3_button_event,
        )
        self.frame_3_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(
            self.navigation_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # create home frame
        self.home_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.columnconfigure(0, weight=1)
        entry = customtkinter.CTkEntry(
            master=self.home_frame,
            placeholder_text="Tweet Link",
            width=400,
        )
        button = customtkinter.CTkButton(master=self.home_frame, text="Submit")
        entry.grid(row=0, column=0, sticky="sew")
        button.grid(row=0, column=1, sticky="sew")

        # center the widgets vertically by adding padding to the top and bottom of the frame
        self.home_frame.grid_rowconfigure(0, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=1)
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_columnconfigure(2, weight=1)

        # create second frame
        self.second_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )

        # create third frame
        self.third_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )

        # select default frame
        self.select_frame_by_name("home")

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.home_button.configure(
            fg_color=("gray75", "gray25") if name == "home" else "transparent"
        )
        self.frame_2_button.configure(
            fg_color=("gray75", "gray25") if name == "frame_2" else "transparent"
        )
        self.frame_3_button.configure(
            fg_color=("gray75", "gray25") if name == "frame_3" else "transparent"
        )

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "frame_2":
            self.second_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.second_frame.grid_forget()
        if name == "frame_3":
            self.third_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.third_frame.grid_forget()

    def home_button_event(self):
        self.select_frame_by_name("home")

    def frame_2_button_event(self):
        self.select_frame_by_name("frame_2")

    def frame_3_button_event(self):
        self.select_frame_by_name("frame_3")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    LoginWindow().mainloop()
