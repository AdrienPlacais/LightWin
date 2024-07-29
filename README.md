# LightWin
LightWin is a tool to automatically find compensation settings for cavity failures in linacs.

## Installation
The full installation instructions are detailed [here](https://adrienplacais.github.io/LightWin/html/manual/installation.html).
The steps are straightforward and can be summarized as follows:
1. Clone the repository:
`git clone git@github.com:AdrienPlacais/LightWin.git`
2. Ensure your `PYTHONPATH` is set and that you have the required packages installed:

 * `cython`
 * `matplotlib`
 * `numpy`
 * `palettable`
 * `pandas`
 * `scipy`
 * `pymoo`
 * `pytest`
 * `setuptools`
 * `tkinter`
3. Compile the Cython packages using the `source/util/setup.py` script.

## Documentation
Documentation is available [here](https://adrienplacais.github.io/LightWin/html/index.html).

## How to run
See [here](https://adrienplacais.github.io/LightWin/html/manual/usage.html).

## Example
See the `data/example` folder.

## Future updates

### BeamCalculator

- [ ] Beam calculator developed by JM Lagniel for SPIRAL2.
- [ ] Envelope solvers with space-charge.

### Quality of life

- [ ] `Plotter` object.
- [ ] Friendlier `Evaluator`.
- [x] Support for `SET_SYNC_PHASE` (see [note](https://adrienplacais.github.io/LightWin/html/manual/usage.html#compatibility-with-tracewin-dat-files)).
- [ ] Better handling of TraceWin errors (currently: a single error and whole run is lost).

### Optimization

- [ ] Correlation matrices.
- [ ] Add [SNS compensation method](doi.org://10.18429/JACoW-LINAC2022-FR1AA06)
