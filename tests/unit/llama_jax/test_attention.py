import jax
from jax import Array
from jax import numpy as jnp

import llama_jax as ll
from llama_jax.checkpoint import ModelConfig, ModelParameters
from llama_jax.kv_cache import LayerKVCache, MutableKVCache
from llama_jax.rope import Rope

from tests.fixtures.jax_fixtures import assert_similar_arrays


def test_factory():
    #
    # Givens
    #

    # I loaded config and parameters for 3.2 3B checkpoint
    config = ll.checkpoint.load_config("Llama3.2-3B")
    params = ll.checkpoint.load_parameters(config)

    #
    # Whens
    #

    # I create Attention for layers.0.attention
    attention = ll.attention.create(config, params, "layers.0.attention")

    #
    # Thens
    #

    # attention should be populated
    assert attention.queries.shape == (config.d_model, config.n_heads * config.d_head)
    assert attention.queries.dtype == config.dtype

    assert attention.keys.shape == (config.d_model, config.n_kv_heads * config.d_head)
    assert attention.keys.dtype == config.dtype

    assert attention.values.shape == (config.d_model, config.n_kv_heads * config.d_head)
    assert attention.values.dtype == config.dtype

    assert attention.output.shape == (config.d_model, config.d_model)
    assert attention.output.dtype == config.dtype


def test_masked_attention_bias(n: int):
    #
    # Givens
    #

    #
    # Whens
    #

    # I generate masked attention bias term M
    m = ll.attention.attention_mask(n, jax.dtypes.bfloat16)

    #
    # Thens
    #

    # m is (n, n) array with zeros below the diagonal, -inf above the diagonal
    for i in range(n):
        for j in range(n):
            if j > i:
                assert m[i, j] == -jnp.inf
            else:
                assert m[i, j] == 0


def test_attention_heads(config: ModelConfig, bs: int, n: int, token_embeddings: Array):
    #
    # Givens
    #

    # Sample embeddings
    x = token_embeddings

    #
    # Whens
    #

    # I split attention heads
    y = ll.attention.split_heads(x, config.n_heads)

    #
    # Thens
    #

    # shape should be bs x n_heads x n x d_head
    assert y.shape == (bs, config.n_heads, n, config.d_head)

    #
    # Whens
    #

    # I combine attention heads
    y = ll.attention.combine_heads(y)

    #
    # Thens
    #

    # shape should be restored
    assert y.shape == x.shape

    # y should equal x
    assert (y == x).all()


def test_forward_0(
    config: ModelConfig,
    params: ModelParameters,
    rope: Rope,
    mask: Array,
    bs: int,
    n: int,
    token_embeddings: Array,
    attention_0: Array,
):
    #
    # Givens
    #

    # I created Attention for layers.0.attention
    attention = ll.attention.create(config, params, "layers.0.attention")

    # I created a key/value cache
    kv_cache = LayerKVCache()

    # Sample embeddings
    x = token_embeddings

    #
    # Whens
    #

    # I transform x w/ attention
    x, kv_cache = ll.attention.forward(config, attention, rope, mask, kv_cache, x)

    #
    # Thens
    #

    # x should match expected output
    assert_similar_arrays(x, attention_0)


def test_forward_n(
    config: ModelConfig,
    params: ModelParameters,
    rope: Rope,
    mask: Array,
    bs: int,
    n: int,
    token_embeddings: Array,
    attention_n: Array,
):
    #
    # Givens
    #

    # I created model
    model = ll.model.create(config, params)

    # I created a key/value cache
    kv_cache = ll.kv_cache.create(config)
    kv_cache = MutableKVCache(kv_cache)

    # Sample embeddings
    x = token_embeddings

    #
    # Whens
    #

    # I transform x w/ n layers
    for i, layer in enumerate(model.layers):
        # Attention
        x, kv_cache[i] = ll.attention.forward(config, layer.attention, rope, mask, kv_cache[i], x)

        # Bail on last layer
        if i == config.n_layers - 1:
            break

        # FFN
        x = ll.ffn.forward(config, layer.ffn, x)

    #
    # Thens
    #

    # x should match expected output
    assert_similar_arrays(x, attention_n)
