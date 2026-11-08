# schematic-ocr

Makes old scanned schematic PDFs searchable, so you can press Cmd-F / Ctrl-F and
jump to a part number, wire colour, coil or switch name.

It was written for pinball schematics, but it works on any large scanned drawing.
Ordinary OCR tools assume all text reads left to right. On a schematic many labels
run sideways along the wires, so those tools either miss them or put the hidden
text in the wrong place. `schematic-ocr` reads every page four times (as-is and
turned 90, 180 and 270 degrees), keeps the best reading for each spot, and puts
the invisible text back at the right place and angle. The page still looks
exactly like the scan.

It also fixes a common scanner quirk where the visible page (CropBox) is smaller
than the full page (MediaBox), which otherwise gives blank or squashed results.

## What you need

- **Python 3.9 or newer**
- **Tesseract** (the OCR engine) and **Poppler** (for its `pdftoppm` tool), which
  pip can't install for you:

| System | Command |
|---|---|
| macOS ([Homebrew](https://brew.sh)) | `brew install tesseract poppler` |
| Debian / Ubuntu / Raspberry Pi OS | `sudo apt install tesseract-ocr poppler-utils` |
| Fedora | `sudo dnf install tesseract poppler-utils` |
| Windows | Tesseract from the [UB Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki), Poppler from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases); add both `bin` folders to your PATH |

Check they're found: `tesseract --version` and `pdftoppm -v`.

## Install

The easiest way is [pipx](https://pipx.pypa.io), which gives the tool its own
Python environment and puts the `schematic-ocr` command on your path:

```bash
brew install pipx        # or: sudo apt install pipx   /   python3 -m pip install --user pipx
pipx ensurepath          # once; then open a new terminal
pipx install "git+https://github.com/NunjoBiznezz/playfield-tools#subdirectory=ocr"
```

**From a downloaded release:** on the
[Releases page](https://github.com/NunjoBiznezz/playfield-tools/releases), download the
`schematic_ocr-<version>-py3-none-any.whl` file from the latest `ocr-v...` release, then:

```bash
pipx install ./schematic_ocr-1.0.0-py3-none-any.whl
```

**With plain pip** (in a virtual environment):

```bash
python3 -m venv ~/.venvs/schematic-ocr
~/.venvs/schematic-ocr/bin/pip install "git+https://github.com/NunjoBiznezz/playfield-tools#subdirectory=ocr"
~/.venvs/schematic-ocr/bin/schematic-ocr --help
```

**Without installing** (from a copy of this folder):
`pip install -r requirements.txt`, then run `python3 -m schematic_ocr` from inside `src/`.

To upgrade later: `pipx upgrade schematic-ocr` (or `pipx install --force ...` with a newer wheel).

## Use

```bash
schematic-ocr "Lady Luck schematic.pdf" "Lady Luck schematic OCR.pdf"
```

Open the new PDF in Preview, Acrobat or any PDF viewer and search it.

| Option | Default | What it does |
|---|---|---|
| `--dpi` | 300 | Resolution the pages are read at. Higher can help with tiny print, but is slower and makes a bigger file. |
| `--lang` | `eng` | Tesseract language (e.g. `deu`; that language's data must be installed) |
| `--min-conf` | 55 | Lowest confidence (0-100) for a word to be kept. Lower finds more text but also more junk. |
| `--single-orientation` | off | Only read the page the normal way up. About 4x faster; fine for manuals and other ordinary documents. |
| `--jpeg-quality` | 82 | Quality of the page image in the output (1-100). Lower makes a smaller file. |
| `--version` | | Show the version |

### Tips

- Large schematics take a while: each page is read four times. A big page can take
  several minutes; progress is printed as it goes.
- The output page image is a re-compressed JPEG of the scan. If you need the
  original quality, raise `--jpeg-quality` to 90-95.
- Scans that are very faint or very small print read better at `--dpi 400`.

## Troubleshooting

- **`'tesseract' not found` / `'pdftoppm' not found`** - install them (see above), then
  open a new terminal.
- **`schematic-ocr: command not found`** after pipx - run `pipx ensurepath` and open a
  new terminal.
- **Blank or empty output pages** - make sure the input really is a scan (an image).
  PDFs that already have text don't need this tool.

## For maintainers: making a release

The version is in `src/schematic_ocr/__init__.py`. To publish a new one:

1. Change `__version__` (e.g. to `1.1.0`) and commit.
2. Tag and push: `git tag ocr-v1.1.0 && git push origin ocr-v1.1.0`

GitHub Actions (`.github/workflows/release-ocr.yml`) then builds the wheel and source
archive and attaches them to a GitHub Release named for the tag. To build locally:
`python3 -m pip install build && python3 -m build ocr` (files land in `ocr/dist/`).

## License

MIT - see `LICENSE`. Free to use, change and share.
