"""Define an object to hold variables and constraints."""

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self, overload

import numpy as np
import pandas as pd

from lightwin.beam_calculation.simulation_output.simulation_output import (
    SimulationOutput,
)
from lightwin.optimisation.design_space.constraint import Constraint
from lightwin.optimisation.design_space.design_space_parameter import (
    DesignSpaceParameter,
)
from lightwin.optimisation.design_space.variable import Variable


@dataclass
class DesignSpace:
    """Hold variables and constraints of an optimisation problem."""

    variables: list[Variable]
    constraints: list[Constraint]

    @classmethod
    def from_files(
        cls,
        elements_names: Sequence[str],
        filepath_variables: Path,
        variables_names: Sequence[str],
        filepath_constraints: Path | None = None,
        constraints_names: Sequence[str] | None = None,
        delimiter: str = ",",
    ) -> Self:
        """Generate design space from files.

        Parameters
        ----------
        elements_names :
            Name of the elements with variables and constraints.
        filepath_variables :
            Path to the :file:`variables.csv` file.
        variables_names :
            Name of the variables to create.
        filepath_constraints :
            Path to the :file:`constraints.csv` file.
        constraints_names :
            Name of the constraints to create.
        delimiter :
            Delimiter in the files.

        """
        variables = _from_file(
            Variable,
            filepath_variables,
            elements_names,
            variables_names,
            delimiter=delimiter,
        )
        if filepath_constraints is None:
            return cls(variables, [])
        if constraints_names is None:
            return cls(variables, [])

        constraints = _from_file(
            Constraint,
            filepath_constraints,
            elements_names,
            constraints_names,
            delimiter=delimiter,
        )
        return cls(variables, constraints)

    def compute_constraints(
        self, simulation_output: SimulationOutput
    ) -> np.ndarray:
        """Compute constraint violation for ``simulation_output``."""
        constraints_with_tuples = [
            constraint.evaluate(simulation_output)
            for constraint in self.constraints
        ]
        constraint_violation = [
            single_constraint
            for constraint_with_tuples in constraints_with_tuples
            for single_constraint in constraint_with_tuples
            if ~np.isnan(single_constraint)
        ]
        return np.array(constraint_violation)

    def __str__(self) -> str:
        """Give nice output of the variables and constraints."""
        return "\n\n".join((self._str_variables(), self._str_constraints()))

    def _str_variables(self) -> str:
        """Generate information on the variables that were created."""
        info = [str(variable) for variable in self.variables]
        info.insert(0, "=" * 100)
        info.insert(1, Variable.str_header())
        info.insert(2, "-" * 100)
        info.append("=" * 100)
        return "\n".join(info)

    def _str_constraints(self) -> str:
        """Generate information on the constraints that were created."""
        info = [str(constraint) for constraint in self.constraints]
        info.insert(0, "=" * 100)
        info.insert(1, Constraint.str_header())
        info.insert(2, "-" * 100)
        info.append("=" * 100)
        return "\n".join(info)

    def to_pandas_dataframe(self) -> pd.DataFrame:
        """Convert list of variables to a pandas dataframe."""
        to_get = ("element_name", "x_min", "x_max", "x_0")
        dicts = [var.to_dict(*to_get) for var in self.variables]
        return pd.DataFrame(dicts, columns=to_get)

    def to_files(
        self,
        basepath: Path,
        variables_filename: str | Path = Path("variables"),
        constraints_filename: str | Path = Path("constraints"),
        overwrite: bool = False,
        **to_csv_kw: Any,
    ) -> None:
        """Save variables and constraints in files.

        Parameters
        ----------
        basepath :
            Folder where the files will be stored.
        variables_filename, constraints_filename :
            Name of the output files without extension.
        overwrite :
            To overwrite an existing file with the same name or not. The
            default is False.
        to_csv_kw :
            Keyword arguments given to the pandas ``to_csv`` method.

        """
        if isinstance(variables_filename, str):
            variables_filename = Path(variables_filename)
        if isinstance(constraints_filename, str):
            constraints_filename = Path(constraints_filename)
        zipper = zip(
            ("variables", "constraints"),
            (variables_filename, constraints_filename),
        )
        for parameter_name, filename in zipper:
            filepath = Path(basepath, filename.with_suffix(".csv"))

            if filepath.is_file() and not overwrite:
                logging.warning(f"{filepath = } already exists. Skipping...")
                continue

            parameter = getattr(self, parameter_name)
            if len(parameter) == 0:
                logging.info(
                    f"{parameter_name} not defined for this DesignSpace. "
                    "Skipping... "
                )
                continue

            self._to_file(parameter, filepath, **to_csv_kw)
            logging.info(f"{parameter_name} saved in {filepath}")

    def _to_file(
        self,
        parameters: list[DesignSpaceParameter],
        filepath: Path,
        delimiter: str = ",",
        **to_csv_kw: Any,
    ) -> None:
        """Save all the design space parameters in a compact file.

        Parameters
        ----------
        parameters :
            All the defined parameters.
        filepath :
            Where file will be stored.
        delimiter :
            Delimiter between two columns. The default is ``','``.
        to_csv_kw :
            Keyword arguments given to the pandas ``to_csv`` method.

        """
        elements_and_parameters = _gather_dicts_by_key(
            parameters, "element_name"
        )
        lines = [
            self._parameters_to_single_file_line(name, param)
            for name, param in elements_and_parameters.items()
        ]
        as_df = pd.DataFrame(lines, columns=list(lines[0].keys()))
        as_df.to_csv(filepath, sep=delimiter, index=False, **to_csv_kw)

    def _parameters_to_single_file_line(
        self, element_name: str, parameters: list[DesignSpaceParameter]
    ) -> dict[str, float | None | tuple[float, float]]:
        """Prepare a dict containing all info of a single element.

        Parameters
        ----------
        element_name :
            Name of the element, which will be inserted in the output dict.
        parameters :
            Parameters concerning the element, which ``limits`` (``x_0`` if
            appliable) will be inserted in the dict.

        Returns
        -------
            Contains all :class:`.Variable` or :class:`.Constraint` information
            of the element.

        """
        line_as_list_of_dicts = _parameters_to_dict(
            parameters, ("x_min", "x_max", "x_0")
        )
        line_as_list_of_dicts.insert(0, {"element_name": element_name})
        line_as_dict = _merge(line_as_list_of_dicts)
        return line_as_dict

    def _check_dimensions(
        self, parameters: list[Variable] | list[Constraint]
    ) -> int:
        """Ensure that all elements have the same number of var or const."""
        n_parameters = len(parameters)
        n_elements = len(self.compensating_elements)
        if n_parameters % n_elements != 0:
            raise NotImplementedError(
                "As for now, all elements must have the "
                "same number of Variables "
                "(or Constraints)."
            )
        n_different_parameters = n_parameters // n_elements
        return n_different_parameters


# =============================================================================
# Private helpers
# =============================================================================
def _gather_dicts_by_key(
    parameters: list[DesignSpaceParameter], key: str
) -> dict[str, list[DesignSpaceParameter]]:
    """Gather parameters with the same ``key`` attribute value in lists.

    Parameters
    ----------
    parameters :
        Objects to study.
    key :
        Name of the attribute against which ``parameters`` should be gathered.

    Returns
    -------
        Keys are all existing values of attribute ``key`` from ``parameters``.
        Values are lists of :class:`.DesignSpaceParameter` with ``key``
        attribute equaling the dict key.

    """
    dict_by_key = defaultdict(list)
    for parameter in parameters:
        dict_by_key[str(getattr(parameter, key))].append(parameter)
    return dict_by_key


def _parameters_to_dict(
    parameters: list[DesignSpaceParameter], to_get: Sequence[str]
) -> list[dict]:
    """Convert several design space parameters to dict.

    We use the ``prepend_parameter_name`` argument to prepend the name of each
    ``parameter.name`` to the name of the values ``to_get``. This way, we avoid
    dictionaries sharing the same keys in the output list.

    Parameters
    ----------
    parameters :
        Where ``to_get`` will be looked for.
    to_get :
        Values to get.

    Returns
    -------
        Contains ``to_get`` values in dictionaries for every parameter.

    """
    return [
        parameter.to_dict(*to_get, prepend_parameter_name=True)
        for parameter in parameters
    ]


def _merge(dicts: list[dict]) -> dict:
    """Merge a list of dicts in a single dict."""
    return {key: value for dic in dicts for key, value in dic.items()}


@overload
def _from_file(
    parameter_class: type[Variable],
    filepath: Path,
    elements_names: Sequence[str],
    parameters_names: Sequence[str],
    delimiter: str = ",",
) -> list[Variable]: ...


@overload
def _from_file(
    parameter_class: type[Constraint],
    filepath: Path,
    elements_names: Sequence[str],
    parameters_names: Sequence[str],
    delimiter: str = ",",
) -> list[Constraint]: ...


def _from_file(
    parameter_class: type[Constraint] | type[Variable],
    filepath: Path,
    elements_names: Sequence[str],
    parameters_names: Sequence[str],
    delimiter: str = ",",
) -> list[Variable] | list[Constraint]:
    """Generate list of variables or constraints from a given ``CSV``.

    .. todo::
        Add support for when all element do not have the same
        variables/constraints.

    Parameters
    ----------
    parameter_class :
        Object which ``from_pd_series`` method will be called.
    filepath :
        Path to the ``CSV``.
    elements_names :
        Name of the elements.
    parameters_names :
        Name of the parameters.
    delimiter :
        Delimiter in the ``CSV``.

    Returns
    -------
        List of variables or constraints.

    """
    assert hasattr(parameter_class, "from_pd_series")
    as_df = pd.read_csv(filepath, index_col="element_name", sep=delimiter)
    parameters = [
        parameter_class.from_pd_series(
            parameter_name, element_name, as_df.loc[element_name]
        )
        for parameter_name in parameters_names
        for element_name in elements_names
    ]
    return parameters
