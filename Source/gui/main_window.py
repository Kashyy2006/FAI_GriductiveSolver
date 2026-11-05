"""TV5: Tkinter application and controller integration boundary."""

from tkinter import Tk

from agent.agent import DeductiveAgent
from game.engine import GameEngine


class MainWindow:
    def __init__(self, root: Tk, engine: GameEngine, agent: DeductiveAgent) -> None:
        raise NotImplementedError("TV5: build UI and connect controller actions")

    def refresh(self) -> None:
        raise NotImplementedError("TV5: render current public state on the main thread")
