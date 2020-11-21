# -*- coding: utf-8 -*-
r'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2020 Caleb Bell <Caleb.Andrew.Bell@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This file contains a number of overflow methods for EOSs which for various
reasons are better implemented as functions.
Documentation is not provided for this file and no methods are intended to be
used outside this library.


.. contents:: :local:
'''
# TODO: put methods like "_fast_init_specific" in here so numba can accelerate them.
from fluids.constants import R
from math import sqrt, log
from thermo.eos_volume import volume_solutions_halley

R2 = R*R
R_inv = 1.0/R
R2_inv = R_inv*R_inv
root_two = sqrt(2.)
root_two_m1 = root_two - 1.0
root_two_p1 = root_two + 1.0

def a_alpha_aijs_composition_independent(a_alphas, kijs):
    N = len(a_alphas)
    cmps = range(N)

    a_alpha_ijs = [[0.0]*N for _ in cmps]
    a_alpha_i_roots = [a_alpha_i**0.5 for a_alpha_i in a_alphas]
#    a_alpha_i_roots_inv = [1.0/i for i in a_alpha_i_roots] # Storing this to avoid divisions was not faster when tested
    # Tried optimization - skip the divisions - can just store the inverses of a_alpha_i_roots and do another multiplication
    # Store the inverses of a_alpha_ij_roots
    a_alpha_ij_roots_inv = [[0.0]*N for _ in cmps]

    for i in cmps:
        kijs_i = kijs[i]
        a_alpha_i = a_alphas[i]
        a_alpha_ijs_is = a_alpha_ijs[i]
        a_alpha_ij_roots_i_inv = a_alpha_ij_roots_inv[i]
        # Using range like this saves 20% of the comp time for 44 components!
        a_alpha_i_root_i = a_alpha_i_roots[i]
        for j in range(i, N):
#        for j in cmps:
#            # TODo range
#            if j < i:
#                continue
            term = a_alpha_i_root_i*a_alpha_i_roots[j]
#            a_alpha_ij_roots_i_inv[j] = a_alpha_i_roots_inv[i]*a_alpha_i_roots_inv[j]#1.0/term
            a_alpha_ij_roots_i_inv[j] = 1.0/term
            a_alpha_ijs_is[j] = a_alpha_ijs[j][i] = (1. - kijs_i[j])*term
    return a_alpha_ijs, a_alpha_i_roots, a_alpha_ij_roots_inv


def a_alpha_aijs_composition_independent_support_zeros(a_alphas, kijs):
    # Same as the above but works when there are zeros
    N = len(a_alphas)
    cmps = range(N)

    a_alpha_ijs = [[0.0] * N for _ in cmps]
    a_alpha_i_roots = [a_alpha_i ** 0.5 for a_alpha_i in a_alphas]
    a_alpha_ij_roots_inv = [[0.0] * N for _ in cmps]

    for i in cmps:
        kijs_i = kijs[i]
        a_alpha_i = a_alphas[i]
        a_alpha_ijs_is = a_alpha_ijs[i]
        a_alpha_ij_roots_i_inv = a_alpha_ij_roots_inv[i]
        a_alpha_i_root_i = a_alpha_i_roots[i]
        for j in range(i, N):
            term = a_alpha_i_root_i * a_alpha_i_roots[j]
            try:
                a_alpha_ij_roots_i_inv[j] = 1.0/term
            except ZeroDivisionError:
                a_alpha_ij_roots_i_inv[j] = 1e100
            a_alpha_ijs_is[j] = a_alpha_ijs[j][i] = (1. - kijs_i[j]) * term
    return a_alpha_ijs, a_alpha_i_roots, a_alpha_ij_roots_inv


def a_alpha_and_derivatives(a_alphas, T, zs, kijs, a_alpha_ijs=None,
                            a_alpha_i_roots=None, a_alpha_ij_roots_inv=None):
    N = len(a_alphas)
    da_alpha_dT, d2a_alpha_dT2 = 0.0, 0.0

    if a_alpha_ijs is None or a_alpha_i_roots is None or a_alpha_ij_roots_inv is None:
        a_alpha_ijs, a_alpha_i_roots, a_alpha_ij_roots_inv = a_alpha_aijs_composition_independent(a_alphas, kijs)

    a_alpha = 0.0
    for i in range(N):
        a_alpha_ijs_i = a_alpha_ijs[i]
        zi = zs[i]
        for j in range(i+1, N):
            term = a_alpha_ijs_i[j]*zi*zs[j]
            a_alpha += term + term

        a_alpha += a_alpha_ijs_i[i]*zi*zi

    return a_alpha, None, a_alpha_ijs


def a_alpha_and_derivatives_full(a_alphas, da_alpha_dTs, d2a_alpha_dT2s, T, zs,
                                 kijs, a_alpha_ijs=None, a_alpha_i_roots=None,
                                 a_alpha_ij_roots_inv=None,
                                 second_derivative=False):
    # For 44 components, takes 150 us in PyPy.

    N = len(a_alphas)
    cmps = range(N)
    da_alpha_dT, d2a_alpha_dT2 = 0.0, 0.0

    if a_alpha_ijs is None or a_alpha_i_roots is None or a_alpha_ij_roots_inv is None:
        a_alpha_ijs, a_alpha_i_roots, a_alpha_ij_roots_inv = a_alpha_aijs_composition_independent(a_alphas, kijs)

    z_products = [[zs[i]*zs[j] for j in cmps] for i in cmps]

    a_alpha = 0.0
    for i in cmps:
        a_alpha_ijs_i = a_alpha_ijs[i]
        z_products_i = z_products[i]
        for j in range(i):
            term = a_alpha_ijs_i[j]*z_products_i[j]
            a_alpha += term + term
        a_alpha += a_alpha_ijs_i[i]*z_products_i[i]

    da_alpha_dT_ijs = [[0.0]*N for _ in cmps]
    if second_derivative:
        d2a_alpha_dT2_ijs = [[0.0]*N for _ in cmps]

    d2a_alpha_dT2_ij = 0.0

    for i in cmps:
        kijs_i = kijs[i]
        a_alphai = a_alphas[i]
        z_products_i = z_products[i]
        da_alpha_dT_i = da_alpha_dTs[i]
        d2a_alpha_dT2_i = d2a_alpha_dT2s[i]
        a_alpha_ij_roots_inv_i = a_alpha_ij_roots_inv[i]
        da_alpha_dT_ijs_i = da_alpha_dT_ijs[i]

        for j in cmps:
#        for j in range(0, i+1):
            if j < i:
#                # skip the duplicates
                continue
            a_alphaj = a_alphas[j]
            x0_05_inv = a_alpha_ij_roots_inv_i[j]
            zi_zj = z_products_i[j]
            da_alpha_dT_j = da_alpha_dTs[j]

            x1 = a_alphai*da_alpha_dT_j
            x2 = a_alphaj*da_alpha_dT_i
            x1_x2 = x1 + x2
            x3 = x1_x2 + x1_x2

            kij_m1 = kijs_i[j] - 1.0

            da_alpha_dT_ij = -0.5*kij_m1*x1_x2*x0_05_inv
            # For temperature derivatives of fugacities
            da_alpha_dT_ijs_i[j] = da_alpha_dT_ijs[j][i] = da_alpha_dT_ij

            da_alpha_dT_ij *= zi_zj


            x0 = a_alphai*a_alphaj

            d2a_alpha_dT2_ij = kij_m1*(  (x0*(
            -0.5*(a_alphai*d2a_alpha_dT2s[j] + a_alphaj*d2a_alpha_dT2_i)
            - da_alpha_dT_i*da_alpha_dT_j) +.25*x1_x2*x1_x2)/(x0_05_inv*x0*x0))
            if second_derivative:
                d2a_alpha_dT2_ijs[i][j] = d2a_alpha_dT2_ijs[j][i] = d2a_alpha_dT2_ij

            d2a_alpha_dT2_ij *= zi_zj

            if i != j:
                da_alpha_dT += da_alpha_dT_ij + da_alpha_dT_ij
                d2a_alpha_dT2 += d2a_alpha_dT2_ij + d2a_alpha_dT2_ij
            else:
                da_alpha_dT += da_alpha_dT_ij
                d2a_alpha_dT2 += d2a_alpha_dT2_ij

    if second_derivative:
        return a_alpha, da_alpha_dT, d2a_alpha_dT2, d2a_alpha_dT2_ijs, da_alpha_dT_ijs, a_alpha_ijs
    return a_alpha, da_alpha_dT, d2a_alpha_dT2, da_alpha_dT_ijs, a_alpha_ijs


def a_alpha_quadratic_terms(a_alphas, a_alpha_i_roots, T, zs, kijs):
    r'''Calculates the `a_alpha` term for an equation of state along with the
    vector quantities needed to compute the fugacities of the mixture. This
    routine is efficient in both numba and PyPy.

    .. math::
        a \alpha = \sum_i \sum_j z_i z_j {(a\alpha)}_{ij}

    .. math::
        (a\alpha)_{ij} = (1-k_{ij})\sqrt{(a\alpha)_{i}(a\alpha)_{j}}

    The secondary values are as follows:

    .. math::
        \sum_i y_i(a\alpha)_{ij}

    Parameters
    ----------
    a_alphas : list[float]
        EOS attractive terms, [J^2/mol^2/Pa]]
    a_alpha_i_roots : list[float]
        Square roots of `a_alphas` [J/mol/Pa^0.5]
    T : float
        Temperature, not used, [K]
    zs : list[float]
        Mole fractions of each species
    kijs : list[list[float]]
        Constant kijs, [-]

    Returns
    -------
    a_alpha : float
        EOS attractive term, [J^2/mol^2/Pa]
    a_alpha_j_rows : list[float]
        EOS attractive term row sums, [J^2/mol^2/Pa]

    Notes
    -----
    Tried moving the i=j loop out, no difference in speed, maybe got a bit slower
    in PyPy.

    '''
    # This is faster in PyPy and can be made even faster optimizing a_alpha!
#    N = len(a_alphas)
#    a_alpha_j_rows = [0.0]*N
#    a_alpha = 0.0
#    for i in range(N):
#        kijs_i = kijs[i]
#        a_alpha_i_root_i = a_alpha_i_roots[i]
#        for j in range(i):
#            a_alpha_ijs_ij = (1. - kijs_i[j])*a_alpha_i_root_i*a_alpha_i_roots[j]
#            t200 = a_alpha_ijs_ij*zs[i]
#            a_alpha_j_rows[j] += t200
#            a_alpha_j_rows[i] += zs[j]*a_alpha_ijs_ij
#            t200 *= zs[j]
#            a_alpha += t200 + t200
#
#        t200 = (1. - kijs_i[i])*a_alphas[i]*zs[i]
#        a_alpha += t200*zs[i]
#        a_alpha_j_rows[i] += t200
#
#    return a_alpha, a_alpha_j_rows

    N = len(a_alphas)
    a_alpha_j_rows = [0.0]*N
    things0 = [0.0]*N
    for i in range(N):
        things0[i] = a_alpha_i_roots[i]*zs[i]

    a_alpha = 0.0
    i = 0
    while i < N:
        kijs_i = kijs[i]
        j = 0
        while j < i:
            # Numba appears to be better with this split into two loops.
            # PyPy has 1.5x speed reduction when so.
            a_alpha_j_rows[j] += (1. - kijs_i[j])*things0[i]
            a_alpha_j_rows[i] += (1. - kijs_i[j])*things0[j]
            j += 1
        i += 1

    for i in range(N):
        a_alpha_j_rows[i] *= a_alpha_i_roots[i]
        a_alpha_j_rows[i] += (1. -  kijs[i][i])*a_alphas[i]*zs[i]
        a_alpha += a_alpha_j_rows[i]*zs[i]

    return a_alpha, a_alpha_j_rows


def a_alpha_and_derivatives_quadratic_terms(a_alphas, a_alpha_i_roots,
                                            da_alpha_dTs, d2a_alpha_dT2s, T, zs, kijs):
    N = len(a_alphas)
    a_alpha = da_alpha_dT = d2a_alpha_dT2 = 0.0

#     da_alpha_dT_off = d2a_alpha_dT2_off = 0.0
#     a_alpha_j_rows = np.zeros(N)
    a_alpha_j_rows = [0.0]*N
#     da_alpha_dT_j_rows = np.zeros(N)
    da_alpha_dT_j_rows = [0.0]*N

    # If d2a_alpha_dT2s were all halved, could save one more multiply
    for i in range(N):
        kijs_i = kijs[i]
        a_alpha_i_root_i = a_alpha_i_roots[i]

        # delete these references?
        a_alphai = a_alphas[i]
        da_alpha_dT_i = da_alpha_dTs[i]
        d2a_alpha_dT2_i = d2a_alpha_dT2s[i]
        workingd1 = workings2 = 0.0

        for j in range(i):
            # TODO: optimize this, compute a_alpha after
            v0 = a_alpha_i_root_i*a_alpha_i_roots[j]
            a_alpha_ijs_ij = (1. - kijs_i[j])*v0
            t200 = a_alpha_ijs_ij*zs[i]
            a_alpha_j_rows[j] += t200
            a_alpha_j_rows[i] += zs[j]*a_alpha_ijs_ij
            t200 *= zs[j]
            a_alpha += t200 + t200

            a_alphaj = a_alphas[j]
            da_alpha_dT_j = da_alpha_dTs[j]
            zi_zj = zs[i]*zs[j]

            x1 = a_alphai*da_alpha_dT_j
            x2 = a_alphaj*da_alpha_dT_i
            x1_x2 = x1 + x2

            kij_m1 = kijs_i[j] - 1.0

            v0_inv = 1.0/v0
            v1 = kij_m1*v0_inv
            da_alpha_dT_ij = x1_x2*v1
#             da_alpha_dT_ij = -0.5*x1_x2*v1 # Factor the -0.5 out, apply at end
            da_alpha_dT_j_rows[j] += zs[i]*da_alpha_dT_ij
            da_alpha_dT_j_rows[i] += zs[j]*da_alpha_dT_ij

            da_alpha_dT_ij *= zi_zj

            x0 = a_alphai*a_alphaj

            # Technically could use a second list of double a_alphas, probably not used
            d2a_alpha_dT2_ij =  v0_inv*v0_inv*v1*(  (x0*(
                              -0.5*(a_alphai*d2a_alpha_dT2s[j] + a_alphaj*d2a_alpha_dT2_i)
                              - da_alpha_dT_i*da_alpha_dT_j) +.25*x1_x2*x1_x2))

            d2a_alpha_dT2_ij *= zi_zj
            workingd1 += da_alpha_dT_ij
            workings2 += d2a_alpha_dT2_ij
            # 23 multiplies, 1 divide in this loop


        # Simplifications for j=i, kij is always 0 by definition.
        t200 = a_alphas[i]*zs[i]
        a_alpha_j_rows[i] += t200
        a_alpha += t200*zs[i]
        zi_zj = zs[i]*zs[i]
        da_alpha_dT_ij = -da_alpha_dT_i - da_alpha_dT_i#da_alpha_dT_i*-2.0
        da_alpha_dT_j_rows[i] += zs[i]*da_alpha_dT_ij
        da_alpha_dT_ij *= zi_zj
        da_alpha_dT -= 0.5*(da_alpha_dT_ij + (workingd1 + workingd1))
        d2a_alpha_dT2 += d2a_alpha_dT2_i*zi_zj + (workings2 + workings2)
    for i in range(N):
        da_alpha_dT_j_rows[i] *= -0.5

    return a_alpha, da_alpha_dT, d2a_alpha_dT2, a_alpha_j_rows, da_alpha_dT_j_rows


def PR_lnphis(T, P, Z, b, a_alpha, zs, bs, a_alpha_j_rows):
    N = len(zs)
    T_inv = 1.0/T
    P_T = P*T_inv

    A = a_alpha*P_T*R2_inv*T_inv
    B = b*P_T*R_inv
    x0 = log(Z - B)
    root_two_B = B*root_two
    two_root_two_B = root_two_B + root_two_B
    ZB = Z + B
    x4 = A*log((ZB + root_two_B)/(ZB - root_two_B))
    t50 = (x4 + x4)/(a_alpha*two_root_two_B)
    t51 = (x4 + (Z - 1.0)*two_root_two_B)/(b*two_root_two_B)
    lnphis = [0.0]*N
    for i in range(N):
        lnphis[i] = bs[i]*t51 - x0 - t50*a_alpha_j_rows[i]
    return lnphis


def PR_lnphis_fastest(zs, T, P, kijs, l, g, ais, bs, a_alphas, a_alpha_i_roots, kappas):
    # Uses precomputed values
    # Only creates its own arrays for a_alpha_j_rows and PR_lnphis
    N = len(bs)
    b = 0.0
    for i in range(N):
        b += bs[i]*zs[i]
    delta = 2.0*b
    epsilon = -b*b

    a_alpha, a_alpha_j_rows = a_alpha_quadratic_terms(a_alphas, a_alpha_i_roots, T, zs, kijs)
    V0, V1, V2 = volume_solutions_halley(T, P, b, delta, epsilon, a_alpha)
    if l:
        # Prefer liquid, ensure V0 is the smalest root
        if V1 != 0.0:
            if V0 > V1 and V1 > b:
                V0 = V1
            if V0 > V2 and V2 > b:
                V0 = V2
    elif g:
        if V1 != 0.0:
            if V0 < V1 and V1 > b:
                V0 = V1
            if V0 < V2 and V2 > b:
                V0 = V2
    else:
        raise ValueError("Root must be specified")
    Z = Z = P*V0/(R*T)
    return PR_lnphis(T, P, Z, b, a_alpha, zs, bs, a_alpha_j_rows)