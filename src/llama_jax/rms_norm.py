"""Normalization."""

from typing import NamedTuple

from jax import Array
import jax.numpy as jnp
from jax.typing import ArrayLike

from llama_jax.checkpoint import ModelConfig, ModelParameters

__all__ = [
    "RMSNorm",
    "create",
    "forward",
]


class RMSNorm(NamedTuple):
    """RMS Normalization state."""

    weight: Array

    eps: float


def create(config: ModelConfig, params: ModelParameters, path: str) -> RMSNorm:
    """Load Llama3 RMSNorm."""
    return RMSNorm(weight=params[f"{path}.weight"], eps=config.rms_norm_eps)


def forward(state: RMSNorm, x: ArrayLike) -> Array:
    """Normalize x using RMS Normalization.

    See https://doi.org/10.48550/arXiv.1910.07467
    """
    return state.weight * x / jnp.sqrt(jnp.mean(x**2) + state.eps)