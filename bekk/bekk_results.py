#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BEKK results
============

"""
from __future__ import print_function, division

import numpy as np
import scipy.linalg as scl

from .utils import format_time

__all__ = ['BEKKResults']


class BEKKResults(object):

    """Estimation results.

    Attributes
    ----------
    innov
        Return innovations
    hvar
        Filtered variance matrices
    var_target
        Estimated varinace target
    param_start
        Starting parameters
    param_final
        Estimated parameters
    model
        Specific model to estimate
    restriction
        Restriction on parameters
    use_target
        Variance targeting flag
    method
        Optimization method. See scipy.optimize.minimize
    cython
        Whether to use Cython optimizations (True) or not (False)

    Methods
    -------

    """

    def __init__(self, innov=None, hvar=None, var_target=None, model=None,
                 use_target=None, restriction=None, cfree=None,
                 method=None, cython=None, time_delta=None,
                 param_start=None, param_final=None, opt_out=None):
        """Initialize the class.

        Parameters
        ----------
        innov : (nobs, nstocks) array
            Return innovations
        hvar : (nobs, nstocks, nstocks) array
            Filtered variance matrices
        var_target : (nstocks, nstocks) array
            Estimated varinace target
        param_start : BEKKParams instance
            Starting parameters
        param_final : BEKKParams instance
            Estimated parameters
        model : str
            Specific model to estimate.

            Must be
                - 'standard'
                - 'spatial'

        restriction : str
            Restriction on parameters.

            Must be
                - 'full'
                - 'diagonal'
                - 'scalar'

        use_target : bool
            Whether to use variance targeting (True) or not (False)
        cfree : bool
            Whether to leave C matrix free (True) or not (False)
        method : str
            Optimization method. See scipy.optimize.minimize
        cython : bool
            Whether to use Cython optimizations (True) or not (False)
        opt_out : OptimizeResult instance
            Optimization results from scipy.optimize.minimize

        """
        self.innov = innov
        self.hvar = hvar
        self.param_start = param_start
        self.param_final = param_final
        self.time_delta = time_delta
        self.opt_out = opt_out
        self.var_target = var_target
        self.model = model
        self.restriction = restriction
        self.use_target = use_target
        self.cfree = cfree
        self.method = method

    def __str__(self):
        """String representation.

        """
        width = 60
        show = '=' * width
        show += '\nModel: ' + self.model
        show += '\nRestriction: ' + self.restriction
        show += '\nUse target: ' + str(self.use_target)
        show += '\nMatrix C is free: ' + str(self.cfree)
        show += '\nNumber of parameters: ' + str(len(self.opt_out.x))
        try:
            show += '\nIterations = ' + str(self.opt_out.nit)
        except:
            show += '\nIterations = NA'
        show += '\nOptimization method = %s' % self.method
        show += '\nOptimization time = %s' % format_time(self.time_delta)
        show += '\n\nFinal parameters:'
        show += str(self.param_final)
        show += '\nVariance target:\n'
        show += str(self.var_target) + '\n'
        show += '\nFinal log-likelihood (with penalty) = %.2f' \
            % (-self.opt_out.fun) + '\n'
        show += 'Final log-likelihood = %.2f' \
            % (-self.opt_out.fun + self.param_final.penalty()) + '\n'
        show += '=' * width
        return show

    def __repr__(self):
        """String representation.

        """
        return self.__str__()

    def weights_equal(self):
        """Equal weights.

        Returns
        -------
        (nobs, nstocks) array

        """
        return np.ones_like(self.innov) / self.innov.shape[1]

    def weights_minvar(self):
        """Minimum variance weights.

        Returns
        -------
        (nobs, nstocks) array

        """
        nstocks = self.innov.shape[1]
        out = []
        for hvari in self.hvar:
            inv_hvar = np.linalg.solve(hvari, np.ones(nstocks))
            out.append(inv_hvar / inv_hvar.sum())
        return np.array(out)

    def weights(self, kind='equal'):
        """Portfolio weights.

        Parameters
        ----------
        weight : str
            Either 'equal' or 'minvar' (minimum variance).

        Returns
        -------
        (nobs, nstocks) array

        """
        if kind == 'equal':
            return self.weights_equal()
        elif kind == 'minvar':
            return self.weights_minvar()
        else:
            raise ValueError('Weight choice is not supported!')

    def portf_rvar(self, kind='equal'):
        """Portfolio predicted variance.

        Parameters
        ----------
        kind : str
            Either 'equal' or 'minvar' (minimum variance).

        Returns
        -------
        (nobs, ) array

        """
        weights = self.weights(kind=kind)
        return (self.innov * weights).sum(1)

    def portf_evar(self, kind='equal'):
        """Portfolio predicted variance.

        Parameters
        ----------
        kind : str
            Either 'equal' or 'minvar' (minimum variance).

        Returns
        -------
        (nobs, ) array

        """
        weights = self.weights(kind=kind)
        return ((self.hvar.T * weights.T).sum(0) * weights.T).sum(0)

    def portf_mvar(self, kind='equal'):
        """Portfolio mean variance.

        Parameters
        ----------
        kind : str
            Either 'equal' or 'minvar' (minimum variance).

        Returns
        -------
        float

        """
        return self.portf_evar(kind=kind).mean()

    def loss_var_ratio(self, kind='equal'):
        """Ratio of realized and predicted variance.

        Parameters
        ----------
        kind : str
            Either 'equal' or 'minvar' (minimum variance).

        Returns
        -------
        (nobs, ) array

        """
        return self.portf_rvar(kind=kind) / self.portf_evar(kind=kind) - 1
