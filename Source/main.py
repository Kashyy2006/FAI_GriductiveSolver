"""Composition root for the Griductive desktop application."""

from pathlib import Path
from tkinter import Tk

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.puzzle_loader import load_puzzle
from gui.main_window import MainWindow
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver


def main() -> None:
    """Create the canonical logic stack and open the GUI."""
    source_dir = Path(__file__).resolve().parent
    puzzle = load_puzzle(source_dir / "puzzles" / "3x3" / "example_01.json")
    encoder = CNFEncoder()
    solver = DPLLSolver()
    agent = DeductiveAgent(encoder, solver)
    engine = GameEngine(puzzle, agent.verify_verdict)
    root = Tk()
    MainWindow(root, engine, agent)
    root.mainloop()


if __name__ == "__main__":
    main()
