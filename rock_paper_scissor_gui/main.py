import enum
import random
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from PIL import Image, ImageTk

import typing as t


class RPSChoices(enum.StrEnum):
  ROCK = 'rock'
  PAPER = 'paper'
  SCISSOR = 'scissor'


WINDOW_BG_COLOUR = "#1f1f1f"
WINDOW_FG_COLOUR = "white"

dark_bg_fg_kwargs = {
  'bg': WINDOW_BG_COLOUR,
  'fg': WINDOW_FG_COLOUR
}


assets_path = Path(__file__).parent / 'assets'
RPSChoicesList: list[RPSChoices] = list(RPSChoices)


class HasWindowSizeMethods(t.Protocol):
  def geometry(self, size: str) -> None: ...
  def minsize(self, x: int, y: int) -> None: ...
  def maxsize(self, x: int, y: int) -> None: ...


def set_window_size_fixed(obj: HasWindowSizeMethods , x: int, y: int | None = None) -> None:
  if y is None:
    y = x

  obj.geometry(f'{x}x{y}')
  obj.minsize(x, y)
  obj.maxsize(x, y)



class DarkModeLabel(tk.Label):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs, **dark_bg_fg_kwargs)


class DarkModeButton(tk.Button):
  def __init__(self, *args, **kwargs):
    super().__init__(
      *args, **kwargs,
      bg="#363636", fg=WINDOW_FG_COLOUR, activebackground="#414141", activeforeground=WINDOW_FG_COLOUR,
      border=0, borderwidth=0
    )


class DarkFrame(tk.Frame):
  def __init__(self, parent: tk.Tk, *args, **kwargs) -> None:
    super().__init__(parent, *args, **kwargs, bg=WINDOW_BG_COLOUR)


class Player(DarkFrame):
  def __init__(self, parent: tk.Frame, name: str, side: t.Literal['left', 'right']):
    super().__init__(parent)

    self.wins = 0
    self.losses = 0
    self.ties = 0
    self.current_move: RPSChoices | str = RPSChoices.ROCK

    # Images list
    self.imgs = {
      i: ImageTk.PhotoImage(Image.open(assets_path / f'{side}_hand' / f'{i}.png').convert('RGBA'))
      for i in RPSChoices
    }

    # Player move displayer (canvas)
    self.player_hand_img_canvas = tk.Canvas(
      self, width=196, height=220, bg=WINDOW_BG_COLOUR, bd=0, highlightthickness=0
    )

    # Background image
    self.bg_image = ImageTk.PhotoImage(Image.open(assets_path / f'{side}_hand' / f'{side}_bg.png').convert('RGBA'))
    self.player_hand_img_canvas.create_image(98, 110, image=self.bg_image)

    # Image of the current player's move
    self.player_move_img = self.player_hand_img_canvas.create_image(100, 110, image=self.imgs[self.current_move])
    self.player_hand_img_canvas.grid(row=0, column=0, pady=20)

    # Player stats and details

    # Player's username
    self.player_name_label = DarkModeLabel(self, text=name, font=('Helvetica', 18))
    self.player_name_label.grid(row=1, column=0)

    # Wins counter
    self.player_wins_label = DarkModeLabel(self, text=f'Wins: {self.wins}', font=('Helvetica', 13))
    self.player_wins_label.grid(row=2, column=0)

    # Losses counter
    self.player_losses_label = DarkModeLabel(self, text=f'Loss: {self.losses}', font=('Helvetica', 13))
    self.player_losses_label.grid(row=3, column=0)

    # Ties counter
    self.player_ties_label = DarkModeLabel(self, text=f'Ties: {self.ties}', font=('Helvetica', 13))
    self.player_ties_label.grid(row=4, column=0)

  def set_wins(self, value: int) -> None:
    if value < 0:
      raise ValueError(f'Expected wins to be a non-negative integer, but got {value}')

    self.wins = value
    self.player_wins_label['text'] = f'Wins: {value}'

  def set_losses(self, value: int) -> None:
    if value < 0:
      raise ValueError(f'Expected losses to be a non-negative integer, but got {value}')

    self.losses = value
    self.player_losses_label['text'] = f'Loss: {value}'

  def set_ties(self, value: int) -> None:
    if value < 0:
      raise ValueError(f'Expected ties to be a non-negative integer, but got {value}')

    self.ties = value
    self.player_ties_label['text'] = f'Ties: {value}'

  def set_current_move(self, value: RPSChoices | str) -> None:
    if value not in ('rock', 'paper', 'scissor'):
      raise ValueError(f"{value} is not a valid option.")

    self.current_move = value
    self.player_hand_img_canvas.itemconfig(self.player_move_img, image=self.imgs[value])

  def won(self):
    self.set_wins(self.wins + 1)

  def lost(self):
    self.set_losses(self.losses + 1)

  def tied(self):
    self.set_ties(self.ties + 1)

  def reset(self):
    self.set_current_move(RPSChoices.ROCK)
    self.set_wins(0)
    self.set_losses(0)
    self.set_ties(0)


class ChoiceButton(DarkModeButton):
  def __init__(self, parent: tk.Frame, player: Player, value: RPSChoices | str):
    self.player = player
    self.value = value.lower()
    self.image = ImageTk.PhotoImage(
      Image.open(assets_path / 'left_hand' / f'{self.value}.png').resize((98, 110))
    )
    super().__init__(
      parent, text=value.title(), image=self.image, compound="top",
      command=self.set_player_move
    )

  def set_player_move(self) -> None:
    self.player.set_current_move(self.value)


class UsernameDialog(simpledialog._QueryString):
  def body(self, master: tk.Tk):
    set_window_size_fixed(self, 430, 120)
    self.config(bg=WINDOW_BG_COLOUR)
    master.config(bg=WINDOW_BG_COLOUR)

    w = DarkModeLabel(master, text=self.prompt, justify='center')
    w.grid(row=0, padx=5, sticky='we')

    validate_func = (master.register(self.check_length), '%P')

    self.entry = tk.Entry(
      master, name="entry", background=WINDOW_BG_COLOUR, fg=WINDOW_FG_COLOUR, validate='key',
      validatecommand=validate_func, width=65
    )
    self.entry.grid(row=1, padx=5, sticky='we')

    self.err_msg = tk.Label(
      master, text='', font=('Helvetica', 10, 'bold'), fg="#ff0000", bg=WINDOW_BG_COLOUR
    )
    self.err_msg.grid(row=2, padx=5, sticky='we')

    if self.initialvalue is not None:
      self.entry.insert(0, self.initialvalue)
      self.entry.select_range(0, 'end')

    return self.entry

  def buttonbox(self):
    box = DarkFrame(self)

    w = DarkModeButton(box, text='OK', width=10, command=self.ok, default='active')
    w.pack(side='left', padx=5, pady=5)

    w = DarkModeButton(box, text='Cancel', width=10, command=self.cancel)
    w.pack(side='left', padx=5, pady=5)

    self.bind('<Return>', self.ok)
    self.bind('<Escape>', self.cancel)

    box.pack()

  def check_length(self, curr_username_input: str) -> bool:
    condn = len(curr_username_input.strip()) > 16

    if condn:
      self.err_msg['text'] = 'Name should not exceed 16 characters (Spaces are stripped)'

    elif self.err_msg['text']:
      self.err_msg['text'] = ''

    return not condn

  def ok(self, event=None):
    val = self.entry.get()

    if not val.strip():
      self.err_msg['text'] = 'Name cannot be empty'
      return

    return super().ok(event)


class GUI(tk.Tk):
  def __init__(self) -> None:
    tk.Tk.__init__(self)
    # ttk.Style(self).theme_use('default')

    self.games_played = 0

    # Window config
    set_window_size_fixed(self, 640, 720)
    self.title("Rock Paper Scissor")

    self.app_logo = ImageTk.PhotoImage(Image.open(assets_path / 'window_logo.png').convert('RGBA'))
    self.wm_iconphoto(True, self.app_logo)

    # Menubar config
    menubar = tk.Menu(self, borderwidth=0, **dark_bg_fg_kwargs)

    # Game menu
    game_menu = tk.Menu(menubar, tearoff=0, borderwidth=0, **dark_bg_fg_kwargs)
    menubar.add_cascade(label ='Game', menu=game_menu)
    game_menu.add_command(label='New Game', command=self.reset)
    game_menu.add_separator()
    game_menu.add_command(label ='Exit', command = self.destroy)

    # Help menu
    help_menu = tk.Menu(menubar, tearoff=0, borderwidth=0, **dark_bg_fg_kwargs)
    menubar.add_cascade(label ='Help', menu=help_menu)
    help_menu.add_command(label='About Game', command=self.display_help)

    self.config(menu=menubar, bg=WINDOW_BG_COLOUR)

    # Frame for displaying the current turns of each user
    display_turns_frame = DarkFrame(self)
    display_turns_frame.pack(side='top', expand=True, padx=10, pady=10)

    display_turns_frame.columnconfigure(0, weight=1)
    display_turns_frame.columnconfigure(1, weight=1)
    display_turns_frame.columnconfigure(2, weight=1)
    display_turns_frame.rowconfigure(0, weight=1)

    # Label to display the total number of games played
    self.no_of_games_label = DarkModeLabel(display_turns_frame, text="Press 'Submit' to start!", font=("Arial", 20, 'bold'), pady=15)
    self.no_of_games_label.grid(row=0, column=0, columnspan=3)

    # Label that shows result of the current turn
    self.result_display_label = DarkModeLabel(display_turns_frame, text='', width=10, font=("Helvetica", 16, 'bold'), anchor='center')
    self.result_display_label.grid(row=1, column=1, padx=10)

    # Players
    self.player = Player(display_turns_frame, self.get_username(), side='left')
    self.player.grid(row=1, column=0)
    self.bot = Player(display_turns_frame, 'Computer', side='right')
    self.bot.grid(row=1, column=2)

    # RPS choice buttons frame
    choice_btns_frame = DarkFrame(self)
    choice_btns_frame.pack(side='top', expand=True, padx=10, pady=10)

    choice_btns_frame.columnconfigure(0, weight=1)
    choice_btns_frame.columnconfigure(1, weight=1)
    choice_btns_frame.columnconfigure(2, weight=1)

    choice_btns_frame.rowconfigure(0, weight=1)

    # RPS choice buttons
    for idx, val in enumerate(RPSChoicesList):
      ChoiceButton(choice_btns_frame, self.player, value=val).grid(row=0, column=idx, padx=5, ipady=5)

    # Submit and Reset button frame
    self.submit_btn_frame = DarkFrame(self)
    self.submit_btn_frame.columnconfigure(1, minsize=40)
    self.submit_btn_frame.pack(side='top', expand=True, padx=10, pady=10)

    # Submit button
    self.user_input_submit_btn = DarkModeButton(
      self.submit_btn_frame, text='Submit', command=self.play, padx=20
    )
    self.user_input_submit_btn.grid(row=0, column=0)

    # Reset button
    self.reset_btn = DarkModeButton(
      self.submit_btn_frame, text='Reset', command=self.reset, padx=20
    )
    self.reset_btn.grid(row=0, column=2)

    self.loop()

  def get_username(self) -> str | t.NoReturn:
    self.withdraw()

    while True:
      player_name: str | None = UsernameDialog('Player name required', 'Enter your name', parent=self).result
      if player_name is None:
        # If user presses 'Cancel', exit out of the application
        exit(1)

      player_name = player_name.strip()
      if player_name != "":
        self.deiconify()
        return player_name

  def evaluate_winner(self) -> None:
    player_move_idx = RPSChoicesList.index(self.player.current_move)
    bot_move_idx = RPSChoicesList.index(self.bot.current_move)
    diff = player_move_idx - bot_move_idx

    if diff == 0:
      self.player.tied()
      self.bot.tied()
      self.result_display_label['text'] = 'TIED'
      self.result_display_label.config(foreground='orange')

    elif diff in (-1, 2):
      self.player.lost()
      self.bot.won()
      self.result_display_label['text'] = 'LOST'
      self.result_display_label.config(foreground='#ff1c1c')

    else:
      self.player.won()
      self.bot.lost()
      self.result_display_label['text'] = 'VICTORY'
      self.result_display_label.config(foreground='green')

  def set_no_of_games_played(self, value: int) -> None:
    if value < 0:
      raise ValueError(f"Expected no_of_games to be a positive integer, but got {value}")

    self.games_played = value
    self.no_of_games_label['text'] = f'Game #{self.games_played}'

  def reset(self):
    self.player.reset()
    self.bot.reset()
    self.set_no_of_games_played(0)
    self.result_display_label['text'] = ''
    self.no_of_games_label['text'] = "Press 'Submit' to start!"

  def play(self) -> None:
    self.bot.set_current_move(random.choice(RPSChoicesList))
    self.evaluate_winner()
    self.set_no_of_games_played(self.games_played + 1)

  def display_help(self) -> None:
    # Help window
    self.help_window = tk.Toplevel(self, bg=WINDOW_BG_COLOUR)

    # Help window config
    set_window_size_fixed(self.help_window, 480, 480)
    self.help_window.title("Help")

    # Help window contents
    DarkModeLabel(self.help_window, image=self.app_logo).pack(side='top', pady=30)

    DarkModeLabel(self.help_window, text='Rock Paper Scissor Game', font=('Helvetica', 20, 'bold')).pack(side="top", pady=20)
    DarkModeLabel(self.help_window, text='Created by Mouhsen Kamil', font=('Helvetica', 12)).pack(side="top")
    DarkModeLabel(self.help_window, text='Created using Tkinter, Python', font=('Helvetica', 12)).pack(side="top")

  def loop(self):
    self.mainloop()


if __name__ == '__main__':
  GUI()
