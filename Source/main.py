"""Composition root for the Griductive desktop application."""

import argparse
from pathlib import Path
from tkinter import Tk

from agent.agent import DeductiveAgent
from game.engine import GameEngine
from game.puzzle_loader import load_puzzle
from gui.main_window import MainWindow
from gui.preview import run_preview
from logic.cnf_encoder import CNFEncoder
from solver.dpll import DPLLSolver


def main() -> None:
    """Create the canonical logic stack and open the GUI."""
    parser = argparse.ArgumentParser(description="Griductive desktop application")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="open the static public board preview without backend modules",
    )
    args = parser.parse_args()
    if args.preview:
        run_preview()
        return

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
