#   Copyright 2024 The PyMC Labs Developers
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Adstock transformations for MMM.

Each of these transformations is a subclass of
:class:`pymc_marketing.mmm.components.adstock.AdstockTransformation`
and defines a function that takes a time series and returns the adstocked
version of it. The parameters of the function are the parameters
of the adstock transformation.

Examples
--------
Create a new adstock transformation:

.. code-block:: python

    from pymc_marketing.mmm import AdstockTransformation

    class MyAdstock(AdstockTransformation):
        def function(self, x, alpha):
            return x * alpha

        default_priors = {"alpha": {"dist": "HalfNormal", "kwargs": {"sigma": 1}}}

Plot the default priors for an adstock transformation:

.. code-block:: python

    from pymc_marketing.mmm import GeometricAdstock

    import matplotlib.pyplot as plt

    adstock = GeometricAdstock(l_max=15)
    prior = adstock.sample_prior()
    curve = adstock.sample_curve(prior)
    adstock.plot_curve(curve)
    plt.show()

"""

import warnings

import numpy as np
import xarray as xr

from pymc_marketing.mmm.components.base import Transformation
from pymc_marketing.mmm.transformers import (
    ConvMode,
    WeibullType,
    delayed_adstock,
    geometric_adstock,
    weibull_adstock,
)


class AdstockTransformation(Transformation):
    """Subclass for all adstock functions.

    In order to use a custom saturation function, inherit from this class and define:

    - `function`: a function that takes x to adstock x
    - `default_priors`: dictionary with priors for every parameter in function

    Consider the predefined subclasses as examples.

    """

    prefix: str = "adstock"
    lookup_name: str

    def __init__(
        self,
        l_max: int,
        normalize: bool = True,
        mode: ConvMode = ConvMode.After,
        priors: dict | None = None,
        prefix: str | None = None,
    ) -> None:
        self.l_max = l_max
        self.normalize = normalize
        self.mode = mode

        super().__init__(priors=priors, prefix=prefix)

    def sample_curve(
        self,
        parameters: xr.Dataset,
        amount: float = 1.0,
    ) -> xr.DataArray:
        """Sample the adstock transformation given parameters.

        Parameters
        ----------
        parameters : xr.Dataset
            Dataset with parameter values.
        amount : float, optional
            Amount to apply the adstock transformation to, by default 1.0.

        Returns
        -------
        xr.DataArray
            Adstocked version of the amount.

        """

        time_since = np.arange(0, self.l_max)
        coords = {
            "time since exposure": time_since,
        }
        x = np.zeros(self.l_max)
        x[0] = amount

        return self._sample_curve(
            var_name="adstock",
            parameters=parameters,
            x=x,
            coords=coords,
        )


class GeometricAdstock(AdstockTransformation):
    """Wrapper around geometric adstock function.

    For more information, see :func:`pymc_marketing.mmm.transformers.geometric_adstock`.

    .. plot::
        :context: close-figs

        import matplotlib.pyplot as plt
        import numpy as np
        from pymc_marketing.mmm import GeometricAdstock

        rng = np.random.default_rng(0)

        adstock = GeometricAdstock(l_max=10)
        prior = adstock.sample_prior(random_seed=rng)
        curve = adstock.sample_curve(prior)
        adstock.plot_curve(curve, sample_kwargs={"rng": rng})
        plt.show()

    """

    lookup_name = "geometric"

    def function(self, x, alpha):
        return geometric_adstock(
            x, alpha=alpha, l_max=self.l_max, normalize=self.normalize, mode=self.mode
        )

    default_priors = {"alpha": {"dist": "Beta", "kwargs": {"alpha": 1, "beta": 3}}}


class DelayedAdstock(AdstockTransformation):
    """Wrapper around delayed adstock function.

    For more information, see :func:`pymc_marketing.mmm.transformers.delayed_adstock`.

    .. plot::
        :context: close-figs

        import matplotlib.pyplot as plt
        import numpy as np
        from pymc_marketing.mmm import DelayedAdstock

        rng = np.random.default_rng(0)

        adstock = DelayedAdstock(l_max=10)
        prior = adstock.sample_prior(random_seed=rng)
        curve = adstock.sample_curve(prior)
        adstock.plot_curve(curve, sample_kwargs={"rng": rng})
        plt.show()

    """

    lookup_name = "delayed"

    def function(self, x, alpha, theta):
        return delayed_adstock(
            x,
            alpha=alpha,
            theta=theta,
            l_max=self.l_max,
            normalize=self.normalize,
            mode=self.mode,
        )

    default_priors = {
        "alpha": {"dist": "Beta", "kwargs": {"alpha": 1, "beta": 3}},
        "theta": {"dist": "HalfNormal", "kwargs": {"sigma": 1}},
    }


class WeibullAdstock(AdstockTransformation):
    """Wrapper around weibull adstock function.

    For more information, see :func:`pymc_marketing.mmm.transformers.weibull_adstock`.

    .. plot::
        :context: close-figs

        import matplotlib.pyplot as plt
        import numpy as np
        from pymc_marketing.mmm import WeibullAdstock

        rng = np.random.default_rng(0)

        adstock = WeibullAdstock(l_max=10, kind="CDF")
        prior = adstock.sample_prior(random_seed=rng)
        curve = adstock.sample_curve(prior)
        adstock.plot_curve(curve, sample_kwargs={"rng": rng})
        plt.show()

    """

    lookup_name = "weibull"

    def __init__(
        self,
        l_max: int,
        normalize: bool = True,
        kind=WeibullType.PDF,
        mode: ConvMode = ConvMode.After,
        priors: dict | None = None,
        prefix: str | None = None,
    ) -> None:
        self.kind = kind

        super().__init__(
            l_max=l_max, normalize=normalize, mode=mode, priors=priors, prefix=prefix
        )

    def function(self, x, lam, k):
        return weibull_adstock(
            x=x,
            lam=lam,
            k=k,
            l_max=self.l_max,
            mode=self.mode,
            type=self.kind,
        )

    default_priors = {
        "lam": {"dist": "HalfNormal", "kwargs": {"sigma": 1}},
        "k": {"dist": "HalfNormal", "kwargs": {"sigma": 1}},
    }


ADSTOCK_TRANSFORMATIONS: dict[str, type[AdstockTransformation]] = {
    cls.lookup_name: cls  # type: ignore
    for cls in [GeometricAdstock, DelayedAdstock, WeibullAdstock]
}


def _get_adstock_function(
    function: str | AdstockTransformation,
    **kwargs,
) -> AdstockTransformation:
    """Helper for use in the MMM to get an adstock function."""
    if isinstance(function, AdstockTransformation):
        return function

    if function not in ADSTOCK_TRANSFORMATIONS:
        raise ValueError(
            f"Unknown adstock function: {function}. Choose from {list(ADSTOCK_TRANSFORMATIONS.keys())}"
        )

    if kwargs:
        warnings.warn(
            "The preferred method of initializing a lagging function is to use the class directly.",
            DeprecationWarning,
            stacklevel=1,
        )

    return ADSTOCK_TRANSFORMATIONS[function](**kwargs)
