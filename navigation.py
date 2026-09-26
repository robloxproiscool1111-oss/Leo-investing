import customtkinter as ctk
import theme

# local aliases
CARD = theme.CARD
GREEN = theme.GREEN


class Sidebar(ctk.CTkFrame):

    def __init__(self, parent):

        super().__init__(
            parent,
            width=230,
            fg_color=CARD
        )


        logo = ctk.CTkLabel(
            self,
            text="Leo\nInvesting",
            font=("Arial",30,"bold"),
            text_color=GREEN
        )

        logo.pack(
            pady=40
        )


        buttons = [

            ("🏠 Home", parent.show_home),
            ("🔍 Search", parent.show_search),
            ("📈 Portfolio", parent.show_home),
            ("⭐ Watchlist", parent.show_home),
            ("👤 Account", parent.show_home)

        ]


        for text, command in buttons:

            ctk.CTkButton(
                self,
                text=text,
                command=command,
                height=45,
                corner_radius=12,
                fg_color="transparent",
                hover_color="#222222",
                font=("Arial",18)
            ).pack(
                fill="x",
                padx=20,
                pady=8
            )