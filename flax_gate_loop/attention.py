import math
from flax import linen as nn
import jax.numpy as jnp

import jax.numpy as jnp
from jax.nn import softmax
from flax import linen as nn
import math


def scaled_dot_product(q, k, v, mask=None):
    d_k = q.shape[-1]
    attn_logits = jnp.matmul(q, jnp.swapaxes(k, -2, -1))
    attn_logits = attn_logits / math.sqrt(d_k)
    if mask is not None:
        attn_logits = jnp.where(mask == 0, float('-inf'), attn_logits)
    attention_weights = softmax(attn_logits, axis=-1)
    output = jnp.matmul(attention_weights, v)
    return output


class MultiHeadSelfAttention(nn.Module):
    d_h: int
    n_head: int
    use_causal_mask: bool

    def setup(self):
        self.qkv_proj = nn.Dense(3 * self.d_h,
                                 kernel_init=nn.initializers.xavier_uniform(),
                                 bias_init=nn.initializers.zeros
                                 )

    def __call__(self, x, mask=None):
        batch_size, seq_len, d_model = x.shape

        qkv = self.qkv_proj(x)
        qkv = qkv.reshape(batch_size, seq_len, self.n_head, 3 * d_model // self.n_head)
        qkv = qkv.transpose(0, 2, 1, 3)  # [Batch, Head, SeqLen, Dims]
        q, k, v = jnp.split(qkv, 3, axis=-1)

        combined_mask = None
        if self.use_causal_mask:
            causal_mask = jnp.tril(jnp.ones((seq_len, seq_len), dtype=jnp.float32)).reshape((1, 1, seq_len, seq_len))
            combined_mask = causal_mask
        if mask is not None:
            mask = mask.reshape((1, 1, seq_len, seq_len))  # Adjust shape to be broadcastable
            combined_mask = mask if combined_mask is None else jnp.logical_and(combined_mask, mask)

        output = scaled_dot_product(q, k, v, mask=combined_mask)
        output = output.transpose(0, 2, 1, 3)  # [Batch, SeqLen, Head, Dims]
        output = output.reshape(batch_size, seq_len, -1)
        return output




