# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# [0.10.x]

## [0.10.4]

### Added

- Introduced `BeamKwargs` typing. Easier to know the values stored in this object.

## [0.10.3] -- 2025-06-30

### Fixed

- Bug introduced in the beam parameters test by 0.10.2.

## [0.10.2] -- 2025-06-30

### Fixed

- `MinimizeDifferenceWithRef` residuals func now returns an always positive value.
  - Does not make any difference with `OptimisationAlgorithm` such as `LeastSquares` which take the squared residuals. May be a game changer for other algorithms.
- Flag to handle `SimulationOutput.get(..., elt=elt)` when `elt: Element` is not in `SimulationOutput.elts`.
  - Fixed some errors at `Objective` creation.

## [0.10.1] -- 2025-06-06

### Fixed

- Update of `CITATION.cff`, `CHANGELOG.md`

## [0.10.0] -- 2025-06-06

### Added

- `release.py` script, `CONTRIBUTING.md` to ease collaboration.

### Changed

- `Accelerator.get`, `SimulationOutput.get`, `ListOfElements.get` now accept arguments found in `FieldMap`.
  - *e.g.*: `ListOfElements.get("freq_cavity_mhz")` is now valid.

## [0.10.0rc0] -- 2025-05-12

### Changed

- Refactored the `get` methods.
    - It may introduce some bugs, do not hesitate to reach me out in case of problem.

### Fixed

- `get` refactoring fixed several bugs:
    - Some `get` methods such as `SimulationOutput.get` did not consider the `phase_space_name` keyword argument.
    - `get` methods behavior are more consistent.

# [0.9.x]

Adhere to development best practices.
In particular, follow advices listed in the great [Scientific Python library development guide](https://learn.scientific-python.org/development/).

## [0.9.4] -- 2025-05-06

### Added

- Wrote the [documentation](https://lightwin.readthedocs.io/en/latest/manual/get_method.html) for the magic `get` methods.
- Added `get` examples in the example notebook.

## [0.9.3] -- 2025-04-09

### Fixed

- The `lightwin.config_manager` symlink pointing to `lightwin.config.config_manager` did not resolve on Windows.
  It was deleted and all `import lightwin.config_manager` were replaced by `import lightwin.config.config_manager`.

### Changed

- `import lightwin.config_manager` no longer works! Replace all occurrences by `import lightwin.config.config_manager`.

## [0.9.2] -- 2025-04-07

### Added

- Type hints for the `.get` methods.
- Notebook example to showcase how LightWin can be used.
- You can give `matplotlib.axes.Axes.plot` kwargs in the `plots` TOML section.

## [0.9.1] -- 2025-01-30

### Added

- When tagging a version:
    - The package is built and tested on several platforms, before being released to PyPI.
    - `CITATION.cff` is automatically updated accordingly.
- Package on `pip` (simpler installation with `pip install lightwin`).

### Changed

- Data used for examples was moved from `data/example/` to `src/lightwin/data/ads/`.
    - It can now be imported for testing purposes.
    - See also: [Including data files](https://learn.scientific-python.org/development/patterns/data-files/)

## [0.9.0] -- 2025-01-21

### Added

- CI/CD tasks:
    - Automatic linting with `pre-commit.ci`.
    - Automatic checking of common mistakes with `pre-commit.ci`.
    - Run automatic tests using `pytest` and GitHub workflows.
- Badges to quickly see if something went wrong.

### Changed

- Introduced optional dependencies.
    - Install them with `pip install -e .[docs]` or `pip install -e .[test]`.
    - It is recommended to install LightWin with the test optional dependencies.

# [0.8.x]

## [0.8.4] 2025-01-15

### Changed

- Tests now rely on the `pytest.approx` functions, much cleaner than previous approach.

## [0.8.3] 2025-01-13

### Added

- Version number and commit number are written in the log file.

### Fixed

- Properly handle opening/closing log files.
- Display of some objective values.


## [0.8.2] 2024-11-11

### Added

- Possibility to save optimization history. Check `[save_wtf]` table in `data/example/lightwin.toml`.

## [0.8.1] 2024-11-11

### Added

- Utility scripts in `ui/workflow_setup.py` defining generic LightWin workflows.
- User can provide `fault_scenario_factory` with a `ObjectivesFactory` to define objectives without altering the source code.
- The `add_objective` in the [plots] TOML table to show position of objective.


## [0.8.0b4] 2024-11-08

### Added

- `SimulationOutput.plot()` method, that calls `.get` under the hood and takes in the same arguments.
- Non-normalized emittance is stored under `non_norm_eps`. Ex: `SimulationOutput.get("non_norm_eps_phiw")`.

### Changed

- Normalized emittances are explicitly marked as normalized in the output.

## [0.8.0b3] 2024-11-07

### Added

- `SET_SYNC_PHASE` commands are now handled for export in DAT file.
- It is now possible to use the `export_phase` in the `[beam_calculator]` table to choose the type of phase to put in the output DAT file.

### Changed

- Display of cavity parameters in `cav.png`, so that 2nd solver does not hide 1st.

### Fixed

- Calculating `phi_0_abs` of a cavity when the reference was `phi_s` raised error.
- `path_cal` not existing in `TraceWin` raised error instead of just creating the folder.
- Interpolation of Twiss to compute mismatch factor was bugged.

## [0.8.0b2] 2024-11-05

### Fixed

- Fixed several bugs that were outside the scope of my pytests.
  - `beam_calc_post` configuration key was no longer recognized.
  - Not providing the `project_folder` key in the `[files]` TOML table led to bug.
  - Some elements created bugs in `CyEnvelope1D`.

## [0.8.0b1] 2024-11-04

### Fixed

- Dot characters in field map file names do not throw an error anymore.
- When several `Element` objects have the same `_personalized_name`, a fallback name and a warning is raised instead of raising an `AssertionError`.

### Changed

- Creation of `DatLine` object, holding a line of the ``.dat`` file. Solves several bugs, e.g. with hyphens in personalized names.
- Makefile for docs is up-to-date. Instructions in README.
- Changed location of `RfField` object, now in `core/em_field/rf_field`.
- The solver `Envelope1D` is now `CyEnvelope1D` when user wants Cython.

## [0.8.0b0] 2024-10-22

### Changed

- The configuration manager was refactored.
- `NewRfField` object officially replaces `RfField`.
- The configurations for the different objects are now in the `specs.py` files, in the same folder as the object they instantiate.

### Deleted

- Constants were removed from the config module to fix circular dependency and bad design issues.
 - `BeamCalculator` objects now need to be given the `beam` configuration dict. Easiest is to instantiate `BeamCalculatorFactory` with `**config`.
 - `Accelerator` will also use data from `beam`. Instantiate `AcceleratorFactory` with `**config`.
 - `SimulationOutputFactory` instantiated with `_beam_kwargs`.

# [0.7.x]

## [0.7.0] 2024-10-22

### Added

- Better display of units in documentation with the new `:unit:` role.

## [0.7.0b3] 2024-10-09

### Added

- Documentation has links to documentation from other libraries (numpy etc).

### Changed

- Documentation is nitpicky.

### Fixed

- Loading function of `evaluations.csv` in `lw-combine-solutions` to handle trailing whitespaces.
- Documentation generation does not raise warnings anymore (except for pymoo).

## [0.7.0b2] 2024-10-01

### Fixed

- Updated path to scripts in `pyproject.toml`; they should work again!

### Changed

- Table of Contents does not show the full path to every module/package anymore. The API section should be much clearer now!
- Better display of the constants in the doc

## [0.7.0b1] 2024-09-30

### Fixed

- Scripts moved to the `lightwin` module so that they can actually be imported.
- `outfolder` argument in `combine-solutions` script is automatically created if it does not exist.
- Documentation includes the API reference again.
- Most of the errors raised during documentation compilation were fixed.

## [0.7.0b0] 2024-09-26

### Fixed

- Released constraints on the versions of installed packages.

## [0.7.0b] 2024-08-07

### Changed

- The code is packaged.
 - Installation instructions were updated.
 - It is not necessary to add LightWin to your `PATH`.
 - Imports of LightWin modules and functions must be imported from `lightwin`: `from lightwin.<foo> import <fee>`.
 - Cython compilation is automatic.

# [0.6.x]

## [0.6.21] 2024-06-07

### Added

- Support for `REPEAT_ELE` command.
- Basic support for `SET_SYNC_PHASE`. This command can be kept in the input `.dat`, but output `.dat` will hold relative or absolute phase (determined by the `BeamCalculator.reference_phase`).

### Changed

- When creating the `BeamCalculator`, prefer `method="RK4"` over `method="RK"` for 4th order Runge-Kutta method.

## [0.6.20] 2024-05-31

### Added

- Basic support for `ADJUST` commands
- New functionality: pass beauty.
 - After a `FaultScenario` is fixed, use `insert_beauty_pass_instructions` from `util.beauty_pass` to add diagnostics and adjust and let TraceWin refine the settings.
 - Prefer providing `TraceWin` with `cancel_matchingP = true` (would be too long).
 - Do NOT provide `cancel_matching = true` nor `cancel_matching = false`. Just drop this argument out (FIXME).
 - Compensating, rephased and failed cavities will be incorrectly displayed as nominal (green) cavities in the output figures (FIXME).

### Fixed

- Personalized name of field maps 1100, 100 and of quadrupoles are now exported in output dat file.
 - Note that this is a temporary patch, a more robust solution will be implemented in future updates.

## [0.6.19] 2024-05-27

### Added

- Support for the TraceWin command line arguments: `algo`, `cancel_matching` and `cancel_matchingP`
- You can provide a `shift` key in `wtf` to shift the window of compensating cavities.
  - Example with 4 compensating lattices:
    - `shift=0` -> 2 upstream and 2 downstream compensating lattices
    - `shift=+1` -> 1 upstream and 3 downstream compensating lattices
    - `shift=-1` -> 3 upstream and 1 downstream compensating lattices
- `Variable`/`Constraint` limits can be changed after creation with the `change_limits` method.
- You can override the default kwargs in the `OptimisationAlgorithm` actual algo.
- Support for pickling/unpickling objects.
    - In other words: some objects such as `Accelerator` or `SimulationOutput` can be saved in binary format, so they can be reloaded and reused in a later Python instance without the hassle of recreating and recomputing everything.

### Changed

- A configuration file is mandatory to select the TraceWin executables.

### Fixed

- SimulationOutput created by TraceWin have a `is_multiparticle` attribute that matches reality.
- Position envelopes are now plotted in deg instead of degdeg (1degdeg = 180 / pi deg).

## [0.6.18] 2024-04-23

### Added

- You can forbid a cavity from being retuned (ex: a rebuncher which is here to rebunch, not to try funny beamy things). Just set `my_cavity.can_be_retuned = False`.
- By default, a lattice without any retunable cavity is skipped when selecting the compensating cavities; this behavior can be modified by setting a `min_number_of_cavities_in_lattice` with `l neighboring lattices` method in the configuration.

### Changed

- New typing features impose the use of Python 3.12.
- The `idx` key in the `wtf` dictionary is now called `id_nature`, which can be one of the following:
    - `cavity`: we consider that `failed = [[10]]` means "the 10th cavity is down".
    - `element`: we consider that `failed = [[10]]` means "the 10th element is down". If the 10th element is not a cavity, an error is raised.
    - `name`: we consider that `failed = [["FM10"]]` means "the first element which name is 'FM10' is down".
- With the `l neighboring lattices` strategy, `l` can now be odd.
- You can provide `tie_strategy = "downstream first"` or `tie_strategy = "upstream first"` to favour up/downstream cavities when there is a tie in distance between compensating cavities/lattices and failed.

### Fixed
- Colors in Evaluator plots are now reset between executions

## [0.6.17] 2024-04-19

### Added

- Switch between different phases at `.dat` save.

### Fixed

- With the `"sync_phase_amplitude"` design space, the synchronous phases were saved in the `.dat` and labelled as relative phase (no `SET_SYNC_PHASE`).

## [0.6.16] 2024-04-17

### Added

- New design space `"rel_phase_amplitude_with_constrained_sync_phase"`
- Pytest for basic compensation with all `BeamCalculator`
- Pytest for every `Design Space`

### Deprecated

- Some design space names are not to be used.
 - `"unconstrained"` -> `"abs_phase_amplitude"`
 - `"unconstrained_rel"` -> `"rel_phase_amplitude"`
 - `"constrained_sync_phase"` -> `"abs_phase_amplitude_with_constrained_sync_phase"`
 - `"sync_phase_as_variable"` -> `"sync_phase_amplitude"`

### Removed

- Support for `.ini` configuration files.
- `"phi_s_fit"` entry in configuration (use the proper design space config entry instead)

### Fixed

- Lattices and their indexes correctly set.
- Synchronous phases correctly calculated and updated; can be used as a variable again.

# Future updates

## [0.?.??] 2024-??-?? -- branch under development

### Changed

- `evaluator` objects are more robust and can be configured from the `.toml`.
- Plotting is now performed thanks to the `plotter` library.

## [0.10.x] -- unreleased

### Added

- `FIELD_MAP 70` does not raise error (warning issued with `Envelope3D`: no transverse tracking).
- `SUPERPOSE_MAP` will be implemented for 1D maps (warning issued with `Envelope3D`: no transverse tracking).


<!-- ## [0.0.0] 1312-01-01 -->
<!---->
<!-- ### Added -->
<!---->
<!-- ### Changed -->
<!---->
<!-- ### Deprecated -->
<!---->
<!-- ### Removed -->
<!---->
<!-- ### Fixed -->
<!---->
<!-- ### Security -->
