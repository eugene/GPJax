# Copyright 2022 The JaxLinOp Contributors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


from dataclasses import dataclass

from beartype.typing import (
    Any,
    Union,
)
import jax.numpy as jnp
from jaxtyping import Float

from gpjax.base import static_field
from gpjax.linops.diagonal_linear_operator import DiagonalLinearOperator
from gpjax.linops.linear_operator import LinearOperator
from gpjax.typing import (
    Array,
    ScalarFloat,
)


def _check_args(value: Any, size: Any) -> None:
    if not isinstance(size, int):
        raise ValueError(f"`length` must be an integer, but `length = {size}`.")

    if value.ndim != 1:
        raise ValueError(
            "`value` must be one dimensional scalar, but `value.shape ="
            f" {value.shape}`."
        )


@dataclass
class ConstantDiagonalLinearOperator(DiagonalLinearOperator):
    value: Float[Array, "1"]
    size: int = static_field()

    def __init__(
        self, value: Float[Array, "1"], size: int, dtype: jnp.dtype = None
    ) -> None:
        """Initialize the constant diagonal linear operator.

        Args:
            value (Float[Array, "1"]): Constant value of the diagonal.
            size (int): Size of the diagonal.
        """
        _check_args(value, size)

        if dtype is not None:
            value = value.astype(dtype)

        self.value = value
        self.size = size
        self.shape = (size, size)
        self.dtype = value.dtype

    def __add__(
        self, other: Union[Float[Array, "N N"], LinearOperator]
    ) -> LinearOperator:
        if isinstance(other, ConstantDiagonalLinearOperator):
            if other.size == self.size:
                return ConstantDiagonalLinearOperator(
                    value=self.value + other.value, size=self.size
                )

            raise ValueError(
                f"`length` must be the same, but `length = {self.size}` and `length ="
                f" {other.size}`."
            )

        else:
            return super().__add__(other)

    def __mul__(self, other: Union[ScalarFloat, Float[Array, "1"]]) -> LinearOperator:
        """Multiply covariance operator by scalar.

        Args:
            other (LinearOperator): Scalar.

        Returns
        -------
            LinearOperator: Covariance operator multiplied by a scalar.
        """
        return ConstantDiagonalLinearOperator(value=self.value * other, size=self.size)

    def _add_diagonal(self, other: DiagonalLinearOperator) -> LinearOperator:
        """Add diagonal to the covariance operator,  useful for computing, Kxx + Io².

        Args:
            other (DiagonalLinearOperator): Diagonal covariance operator to add to the covariance operator.

        Returns
        -------
            LinearOperator: Covariance operator with the diagonal added.
        """
        if isinstance(other, ConstantDiagonalLinearOperator):
            if other.size == self.size:
                return ConstantDiagonalLinearOperator(
                    value=self.value + other.value, size=self.size
                )

            raise ValueError(
                f"`length` must be the same, but `length = {self.size}` and `length ="
                f" {other.size}`."
            )

        else:
            return super()._add_diagonal(other)

    def diagonal(self) -> Float[Array, " N"]:
        """Diagonal of the covariance operator."""
        return self.value * jnp.ones(self.size)

    def to_root(self) -> "ConstantDiagonalLinearOperator":
        """
        Lower triangular.

        Returns
        -------
            Float[Array, "N N"]: Lower triangular matrix.
        """
        return ConstantDiagonalLinearOperator(
            value=jnp.sqrt(self.value), size=self.size
        )

    def log_det(self) -> ScalarFloat:
        """Log determinant.

        Returns
        -------
            ScalarFloat: Log determinant of the covariance matrix.
        """
        return 2.0 * self.size * jnp.log(self.value.squeeze())

    def inverse(self) -> "ConstantDiagonalLinearOperator":
        """Inverse of the covariance operator.

        Returns
        -------
            DiagonalLinearOperator: Inverse of the covariance operator.
        """
        return ConstantDiagonalLinearOperator(value=1.0 / self.value, size=self.size)

    def solve(self, rhs: Float[Array, "... M"]) -> Float[Array, "... M"]:
        """Solve linear system.

        Args:
            rhs (Float[Array, "N M"]): Right hand side of the linear system.

        Returns
        -------
            Float[Array, "N M"]: Solution of the linear system.
        """
        return rhs / self.value

    @classmethod
    def from_dense(cls, dense: Float[Array, "N N"]) -> "ConstantDiagonalLinearOperator":
        """Construct covariance operator from dense matrix.

        Args:
            dense (Float[Array, "N N"]): Dense matrix.

        Returns
        -------
            DiagonalLinearOperator: Covariance operator.
        """
        return ConstantDiagonalLinearOperator(
            value=jnp.atleast_1d(dense[0, 0]), size=dense.shape[0]
        )

    @classmethod
    def from_root(
        cls, root: "ConstantDiagonalLinearOperator"
    ) -> "ConstantDiagonalLinearOperator":
        """Construct covariance operator from root.

        Args:
            root (ConstantDiagonalLinearOperator): Root of the covariance operator.

        Returns
        -------
            ConstantDiagonalLinearOperator: Covariance operator.
        """
        return ConstantDiagonalLinearOperator(value=root.value**2, size=root.size)


__all__ = [
    "ConstantDiagonalLinearOperator",
]
