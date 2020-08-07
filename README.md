# RealNVP
Author: [Mandolini Giorgio Maria](https://www.linkedin.com/in/giorgio-maria-mandolini-a2a1b71b4/), [Sanna Daniele](https://www.linkedin.com/in/daniele-sanna-338629bb/), [Zannini Quirini Giorgio](https://www.linkedin.com/in/giorgio-zannini-quirini-16ab181a0/)

The aim of this work consists in mapping a simple distribution - which is easy to sample
and whose density is simple to estimate - to a more complex one learned from the data;
these kind of generative models is also knowm as "normalizing flows".

In order to obtain the aforementioned result the model is trained by means of the maximum
likelihood principle, resorting to the "change of variable formula".

An affine coupling layer function is built. It is created such that its inverse and the determinant
of the jacobian is easy to obtain (more details in the referenced paper).

References:
[Density estimation using Real NVP](https://arxiv.org/pdf/1605.08803.pdf)
