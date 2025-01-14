# LightWin
LightWin is a tool to automatically find compensation settings for cavity failures in linacs.

## Installation
The full installation instructions are detailed [here](https://adrienplacais.github.io/LightWin/html/main/manual/installation.html).
The steps are straightforward and can be summarized as follows:
1. Clone the repository: `git clone git@github.com:AdrienPlacais/LightWin.git`
2. Navigate to the `LightWin` directory, and switch to the last released version: `git checkout v0.7.0`.
3. Install LightWin with all its dependencies: `pip install -e .`
4. Test that everything is working with `pytest -m "not tracewin and not implementation"`

Note that the TraceWin module will not work out of the box.
You will need to tell LightWin were to find your TraceWin executables.
See [dedicated instructions](https://adrienplacais.github.io/LightWin/html/main/manual/installation.tracewin.html).

## Documentation
Documentation is now automatically built and hosted on [Read the docs](https://lightwin.readthedocs.io/en/latest/)

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
