from jax import random
import pytest

import llama_jax as ll


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

    # I create FFN for layers.0.feed_forward
    ffn = ll.ffn.create(config, params, "layers.0.feed_forward")

    #
    # Thens
    #

    # ffn should be populated
    assert ffn.input.shape == (config.d_model, config.d_ffn)
    assert ffn.gate.shape == (config.d_model, config.d_ffn)
    assert ffn.output.shape == (config.d_ffn, config.d_model)


@pytest.mark.parametrize("input_shape", [(10, 3072), (2, 10, 3072)])
def test_forward(input_shape: tuple):
    #
    # Givens
    #

    # rng
    key = random.key(42)

    # I loaded config and parameters for 3.2 3B checkpoint
    config = ll.checkpoint.load_config("Llama3.2-3B")
    params = ll.checkpoint.load_parameters(config)

    # I created FFN for layers.0.feed_forward
    ffn = ll.ffn.create(config, params, "layers.0.feed_forward")

    # I generated sample embeddings
    key, subkey = random.split(key)
    x = random.normal(subkey, input_shape)

    #
    # Whens
    #

    # I transform x w/ ffn
    y = ll.ffn.forward(config, ffn, x)

    #
    # Thens
    #

    # y.shape didn't change
    assert y.shape == x.shape
