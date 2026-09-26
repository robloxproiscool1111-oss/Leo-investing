import customtkinter as ctk

import theme
import cloud_backend

from components.sidebar import Sidebar

from pages.home import HomePage
from pages.search import SearchPage
from pages.stock import StockPage
from pages.watchlist import WatchlistPage
from pages.portfolio import PortfolioPage
from pages.account import AccountPage
from pages.auth import AuthPage
from database import initialize_database


APP_TITLE = "Leo Investing"
WINDOW_SIZE = "1320x860"

MIN_WIDTH = 1100
MIN_HEIGHT = 700


class LeoInvesting(ctk.CTk):

    def __init__(self):

        super().__init__()

        if not cloud_backend.is_configured():
            initialize_database()
        self.account = None

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)

        self.minsize(
            MIN_WIDTH,
            MIN_HEIGHT,
        )

        self.configure(
            fg_color=theme.BG
        )

        # Main layout
        self.grid_rowconfigure(
            0,
            weight=1
        )

        self.grid_columnconfigure(
            1,
            weight=1
        )

        # Main content
        self.content = ctk.CTkFrame(
            self,
            fg_color=theme.BG,
            corner_radius=0
        )

        self.content.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.current_page_class = None
        self.current_page_args = ()

        self.show_auth()

    def show_auth(self):
        sidebar = getattr(self, "sidebar", None)
        if sidebar is not None:
            sidebar.destroy()
        self.account = None
        self.content.grid_configure(column=0, columnspan=2)
        self._show_page(AuthPage)

    def login_success(self, account):
        self.account = account
        self.sidebar = Sidebar(self)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.content.grid_configure(column=1, columnspan=1)
        self.show_home()

    def logout(self):
        try:
            cloud_backend.sign_out()
        except Exception:
            pass
        self.show_auth()

    # ========================================================
    # PAGE MANAGEMENT
    # ========================================================

    def _show_page(
        self,
        page_class,
        *args
    ):

        for widget in self.content.winfo_children():
            widget.destroy()

        page = page_class(
            self.content,
            self,
            *args
        )

        page.pack(
            fill="both",
            expand=True
        )
        # track current page for rebuilds after theme changes
        self.current_page_class = page_class
        self.current_page_args = args

    # ========================================================
    # NAVIGATION
    # ========================================================

    def show_home(self):

        self.sidebar.set_active("home")
        self._show_page(HomePage)

    def show_search(self):

        self.sidebar.set_active("search")
        self._show_page(SearchPage)

    def show_stock(
        self,
        ticker
    ):

        self.sidebar.set_active("search")

        self._show_page(
            StockPage,
            ticker
        )

    def show_watchlist(self):

        self.sidebar.set_active("watchlist")
        self._show_page(WatchlistPage)

    def show_portfolio(self):

        self.sidebar.set_active("portfolio")
        self._show_page(PortfolioPage)

    def show_account(self):

        self.sidebar.set_active("account")
        self._show_page(AccountPage)

    def refresh_current_page(self):
        """Rebuild the current page using the stored class and args."""
        if self.current_page_class is None:
            return
        self._show_page(self.current_page_class, *self.current_page_args)


if __name__ == "__main__":

    theme.setup_theme()

    app = LeoInvesting()

    app.mainloop()