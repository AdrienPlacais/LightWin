# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.6.??] 2024-??-?? -- branch under development

## [0.6.22] 2024-??-??

### Added
- `FIELD_MAP 70` will not raise error (warning issued with `Envelope3D`).

### Changed
- Creation of `DatLine` object, holding a line of the ``.dat`` file. Solves several bugs, e.g. with hyphens in personalized names.

### Changed
- `evaluator` objects are more robust and can be configured from the `.toml`.
- Plotting is now performed thanks to the `plotter` library.

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
