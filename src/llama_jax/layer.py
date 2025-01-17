"""Decoder layer."""

from typing import NamedTuple

from jax import Array

import llama_jax as ll
from llama_jax.attention import Attention
from llama_jax.checkpoint import ModelConfig, ModelParameters
from llama_jax.ffn import FFN
from llama_jax.kv_cache import LayerKVCache
from llama_jax.rope import Rope

__all__ = [
    "Layer",
    "create",
    "forward",
]


class Layer(NamedTuple):
    """Decoder layer state."""

    attention: Attention

    ffn: FFN


def create(config: ModelConfig, params: ModelParameters, path: str) -> Layer:
    """Load Llama3 Layer."""
    # Attention
    attention = ll.attention.create(config, params, f"{path}.attention")

    # FFN
    ffn = ll.ffn.create(config, params, f"{path}.feed_forward")

    return Layer(attention=attention, ffn=ffn)


def forward(
    config: ModelConfig,
    state: Layer,
    rope: Rope,
    mask: Array,
    x: Array,
    kv_cache: LayerKVCache,
) -> tuple[Array, LayerKVCache]:
    """Transform x using attention and feedforward network."""
    # Sanity check
    assert x.ndim == 3

    # Attention
    x, kv_cache = ll.attention.forward(config, state.attention, rope, mask, x, kv_cache)

    # FFN
    x = ll.ffn.forward(config, state.ffn, x)

    return x, kv_cache
