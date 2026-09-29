#!/usr/bin/env python3
"""Cross-platform GUI for the SALFA CTF code generator."""

from __future__ import annotations

import argparse
import re
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from flare_generator import DEFAULT_UPDATE_SEED, REGIONS, generate_code


EXAMPLE_RESULTS = (
    ("SALFA2AEXEH401960", "EU", "2A8AD051"),
    ("SALFA2AE8DH343605", "EU", "2921B711"),
)


def parse_vins(value: str) -> list[str]:
    """Parse newline, whitespace, comma, or semicolon separated VINs."""
    vins = [item.strip().upper() for item in re.split(r"[\s,;]+", value) if item.strip()]
    return list(dict.fromkeys(vins))


def self_test() -> bool:
    return all(
        generate_code(vin, DEFAULT_UPDATE_SEED, region) == expected
        for vin, region, expected in EXAMPLE_RESULTS
    )


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SALFA Code Generator")
        self.geometry("760x500")
        self.minsize(620, 420)

        self.region = tk.StringVar(value="EU")
        self.status = tk.StringVar(value="Ready")
        self._build()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(4, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="SALFA Code Generator", font=("TkDefaultFont", 15, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="Region").grid(row=0, column=1, padx=(16, 6))
        region = ttk.Combobox(
            header,
            textvariable=self.region,
            values=REGIONS,
            state="readonly",
            width=7,
        )
        region.grid(row=0, column=2, sticky="e")

        ttk.Label(root, text="VINs").grid(row=1, column=0, sticky="w", pady=(18, 6))
        input_frame = ttk.Frame(root)
        input_frame.grid(row=2, column=0, sticky="nsew")
        input_frame.columnconfigure(0, weight=1)
        self.vin_input = tk.Text(input_frame, height=6, wrap="none", undo=True)
        self.vin_input.grid(row=0, column=0, sticky="nsew")
        input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=self.vin_input.yview)
        input_scroll.grid(row=0, column=1, sticky="ns")
        self.vin_input.configure(yscrollcommand=input_scroll.set)

        actions = ttk.Frame(root)
        actions.grid(row=3, column=0, sticky="ew", pady=12)
        ttk.Button(actions, text="Generate", command=self._generate).pack(side="left")
        ttk.Button(actions, text="Copy", command=self._copy).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Clear", command=self._clear).pack(side="left", padx=(8, 0))

        table_frame = ttk.Frame(root)
        table_frame.grid(row=4, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.results = ttk.Treeview(
            table_frame,
            columns=("vin", "region", "code"),
            show="headings",
            selectmode="extended",
        )
        self.results.heading("vin", text="VIN")
        self.results.heading("region", text="Region")
        self.results.heading("code", text="Code")
        self.results.column("vin", width=280, minwidth=180, anchor="w")
        self.results.column("region", width=90, minwidth=70, anchor="center", stretch=False)
        self.results.column("code", width=160, minwidth=120, anchor="center")
        self.results.grid(row=0, column=0, sticky="nsew")
        result_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.results.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.results.configure(yscrollcommand=result_scroll.set)

        ttk.Label(root, textvariable=self.status).grid(row=5, column=0, sticky="w", pady=(10, 0))

        self.bind("<Control-Return>", lambda _event: self._generate())
        self.vin_input.focus_set()

    def _generate(self) -> None:
        try:
            vins = parse_vins(self.vin_input.get("1.0", "end"))
            if not vins:
                raise ValueError("Enter at least one VIN.")
            region = self.region.get()
            generated = [(vin, region, generate_code(vin, DEFAULT_UPDATE_SEED, region)) for vin in vins]
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error), parent=self)
            self.status.set("Generation failed")
            return

        self._clear_results()
        for row in generated:
            self.results.insert("", "end", values=row)
        self.status.set(f"Generated {len(generated)} code(s)")

    def _copy(self) -> None:
        selected = self.results.selection()
        items = selected or self.results.get_children()
        lines = []
        for item in items:
            vin, region, code = self.results.item(item, "values")
            lines.append(f"{vin} [{region}] -> {code}")
        if not lines:
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        self.status.set(f"Copied {len(lines)} result(s)")

    def _clear_results(self) -> None:
        for item in self.results.get_children():
            self.results.delete(item)

    def _clear(self) -> None:
        self.vin_input.delete("1.0", "end")
        self._clear_results()
        self.status.set("Ready")
        self.vin_input.focus_set()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--self-test", action="store_true")
    args, _unknown = parser.parse_known_args(argv)
    if args.self_test:
        return 0 if self_test() else 1
    App().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
