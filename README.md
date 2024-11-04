# LightWin
LightWin is a tool to automatically find compensation settings for cavity failures in linacs.

## Important notice
You are on a development branch, based on `superpose_field_map`.
The objective is to make SPIRAL2 linac work.

## Installation
The full installation instructions are detailed [here](https://adrienplacais.github.io/LightWin/html/main/manual/installation.html).
The steps are straightforward and can be summarized as follows:
1. Clone the repository:
`git clone git@github.com:AdrienPlacais/LightWin.git`
2. Navigate to the `LightWin` and install it with all dependencies: `pip install -e .`
3. Test that everything is working with `pytest -m "not tracewin"`

Note that the TraceWin module will not work out of the box.
You will need to tell LightWin were to find your TraceWin executables.
See [dedicated instructions](https://adrienplacais.github.io/LightWin/html/main/manual/installation.tracewin.html).

## Documentation
Documentation is available [here](https://adrienplacais.github.io/LightWin/html/main/index.html).
To build the documentation from scratch:
1. Build the source files `make -C docs/ apidoc`
2. Build the CSV files used for documenting configuration `make -C docs/ generate_csv`
3. Build the documentation `make -C docs/ multiversion`
Note that for quick tests, you can also build the unversioned documentation with `make -C docs/ html`

## How to run
See [here](https://adrienplacais.github.io/LightWin/html/main/manual/usage.html).

## Example
See the `data/example` folder.

## Future updates

### BeamCalculator

- [ ] Beam calculator developed by JM Lagniel for SPIRAL2.
- [ ] Envelope solvers with space-charge.

### Quality of life

- [ ] `Plotter` object.
- [ ] Friendlier `Evaluator`.
- [x] Support for `SET_SYNC_PHASE` (see [note](https://adrienplacais.github.io/LightWin/html/main/manual/usage.html#compatibility-with-tracewin-dat-files)).
- [ ] Better handling of TraceWin errors (currently: a single error and whole run is lost).

### Optimization

- [ ] Correlation matrices.
- [ ] Add [SNS compensation method](doi.org://10.18429/JACoW-LINAC2022-FR1AA06)
