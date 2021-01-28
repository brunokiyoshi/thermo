# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2016, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

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
SOFTWARE.'''

from numpy.testing import assert_allclose
import pytest
from fluids.numerics import assert_close, assert_close1d
from fluids.constants import R
from thermo.thermal_conductivity import *
from thermo.mixture import Mixture
from thermo.thermal_conductivity import MAGOMEDOV, DIPPR_9H, FILIPPOV, SIMPLE, ThermalConductivityLiquidMixture
from thermo.thermal_conductivity import (GHARAGHEIZI_G, CHUNG, ELI_HANLEY, VDI_PPDS,
                                        ELI_HANLEY_DENSE, CHUNG_DENSE,
                                        EUCKEN_MOD, EUCKEN, BAHADORI_G,
                                        STIEL_THODOS_DENSE, DIPPR_9B, COOLPROP,
                                        DIPPR_PERRY_8E, VDI_TABULAR, GHARAGHEIZI_L,
                                       SATO_RIEDEL, NICOLA, NICOLA_ORIGINAL,
                                       SHEFFY_JOHNSON, BAHADORI_L,
                                       LAKSHMI_PRASAD, DIPPR_9G, MISSENARD)



@pytest.mark.meta_T_dept
def test_ThermalConductivityLiquid():
    EtOH = ThermalConductivityLiquid(CASRN='64-17-5', MW=46.06844, Tm=159.05, Tb=351.39, Tc=514.0, Pc=6137000.0, omega=0.635, Hfus=4931.0)

    EtOH.T_dependent_property(305.)
    all_methods = EtOH.all_methods
    methods = list(all_methods)
    methods.remove(VDI_TABULAR)
    kl_calcs = []
    for i in methods:
        EtOH.method = i
        kl_calcs.append(EtOH.T_dependent_property(305.))

    kl_exp = [0.162183005823234, 0.16627999999999998, 0.166302, 0.20068212675966418, 0.18526367184633258, 0.18846433785041306, 0.16837295487233528, 0.16883011582627103, 0.09330268101157643, 0.028604363267557775]
    assert_close1d(sorted(kl_calcs), sorted(kl_exp))

    assert_close(EtOH.calculate(305., VDI_TABULAR), 0.17417420086033197, rtol=1E-4)


    # Test that methods return None
    EtOH.extrapolation = None
    kl_calcs = []
    for i in all_methods:
        EtOH.method = i
        kl_calcs.append(EtOH.T_dependent_property(5000))

    assert [None]*11 == kl_calcs

    EtOH.method = VDI_TABULAR
    EtOH.extrapolation = 'interp1d'
    assert_close(EtOH.T_dependent_property(600.), 0.040117737789202995)
    EtOH.extrapolation = None
    assert None == EtOH.T_dependent_property(600.)

    with pytest.raises(Exception):
        EtOH.test_method_validity(300, 'BADMETHOD')


    # Ethanol compressed
    assert [False, True] == [EtOH.test_method_validity_P(300, P, COOLPROP) for P in (1E3, 1E5)]
    assert [True, True] == [EtOH.test_method_validity_P(300, P, DIPPR_9G) for P in (1E3, 1E5)]
    assert [True, True, False] == [EtOH.test_method_validity_P(300, P, MISSENARD) for P in (1E3, 1E5, 1E10)]

    EtOH = ThermalConductivityLiquid(CASRN='64-17-5', MW=46.06844, Tm=159.05, Tb=351.39, Tc=514.0, Pc=6137000.0, omega=0.635, Hfus=4931.0)
    assert_close(EtOH.calculate_P(298.15, 1E6, COOLPROP), 0.1639626989794703)
    assert_close(EtOH.calculate_P(298.15, 1E6, DIPPR_9G), 0.1606146938795702)
    assert_close(EtOH.calculate_P(298.15, 1E6, MISSENARD), 0.1641582259181843)


    # Ethanol data, calculated from CoolProp
    Ts = [275, 300, 350]
    Ps = [1E5, 5E5, 1E6]
    TP_data = [[0.16848555706973622, 0.16313525757474362, 0.15458068887966378], [0.16868861153075654, 0.163343255114212, 0.1548036152853355], [0.16894182645698885, 0.1636025336196736, 0.15508116339039268]]
    EtOH.add_tabular_data_P(Ts, Ps, TP_data, name='CPdata')
    recalc_pts = [[EtOH.TP_dependent_property(T, P) for T in Ts] for P in Ps]
    assert_close1d(TP_data, recalc_pts)

    EtOH.forced_P = True
    assert_allclose(EtOH.TP_dependent_property(274, 9E4), 0.16848555706973622)
    EtOH.tabular_extrapolation_permitted = False
    assert None == EtOH.TP_dependent_property(300, 9E4)

    with pytest.raises(Exception):
        EtOH.test_method_validity_P(300, 1E5, 'BADMETHOD')

    assert False == EtOH.test_method_validity_P(-10, 1E5, DIPPR_9G)


@pytest.mark.meta_T_dept
def test_ThermalConductivityGas():
    EtOH = ThermalConductivityGas(MW=46.06844, Tb=351.39, Tc=514.0, Pc=6137000.0, Vc=0.000168, Zc=0.2412, omega=0.635, dipole=1.44, Vmg=0.02357, Cpgm=56.98+R, mug=7.903e-6, CASRN='64-17-5')
    all_methods = list(EtOH.all_methods)

    EtOH.method = EUCKEN_MOD
    assert_close(EtOH.T_dependent_property(305), 0.015427445804245578)
    EtOH.method = EUCKEN
    assert_close(EtOH.T_dependent_property(305), 0.012984130473277289)
    EtOH.method = VDI_PPDS
    assert_close(EtOH.T_dependent_property(305), 0.015661846372995)
    EtOH.method = BAHADORI_G
    assert_close(EtOH.T_dependent_property(305), 0.018297587287579457)
    EtOH.method = GHARAGHEIZI_G
    assert_close(EtOH.T_dependent_property(305), 0.016862968023145547)
    EtOH.method = COOLPROP
    assert_close(EtOH.T_dependent_property(305), 0.015870725750339945)
    EtOH.method = DIPPR_9B
    assert_close(EtOH.T_dependent_property(305), 0.014372770946906635)
    EtOH.method = ELI_HANLEY
    assert_close(EtOH.T_dependent_property(305), 0.011684946002735508)
    EtOH.method = VDI_TABULAR
    assert_close(EtOH.T_dependent_property(305), 0.015509857659914554)
    EtOH.method = CHUNG
    assert_close(EtOH.T_dependent_property(305), 0.011710616856383785)
    EtOH.method = DIPPR_PERRY_8E
    assert_close(EtOH.T_dependent_property(305), 0.015836254853225484)


    EtOH.extrapolation = None

    kg_calcs = []
    for i in [COOLPROP, DIPPR_PERRY_8E, VDI_TABULAR, GHARAGHEIZI_G, ELI_HANLEY, BAHADORI_G, VDI_PPDS]:
        EtOH.method = i
        kg_calcs.append(EtOH.T_dependent_property(5E20))
    assert [None]*7 == kg_calcs

    # Test tabular limits/extrapolation
    EtOH.method = VDI_TABULAR
    EtOH.extrapolation = 'interp1d'
    assert_close(EtOH.T_dependent_property(600.), 0.05755089974293061)

    EtOH.extrapolation = None
    assert None == EtOH.T_dependent_property(600.)

    with pytest.raises(Exception):
        EtOH.test_method_validity(300, 'BADMETHOD')


    # Ethanol compressed

    assert [True, False] == [EtOH.test_method_validity_P(300, P, COOLPROP) for P in (1E3, 1E5)]
    assert [True, False] == [EtOH.test_method_validity_P(300, P, ELI_HANLEY_DENSE) for P in (1E5, -1E5)]
    assert [True, False] == [EtOH.test_method_validity_P(300, P, CHUNG_DENSE) for P in (1E5, -1E5)]
    assert [True, False] == [EtOH.test_method_validity_P(300, P, STIEL_THODOS_DENSE) for P in (1E5, -1E5)]


    EtOH = ThermalConductivityGas(MW=46.06844, Tb=351.39, Tc=514.0, Pc=6137000.0, Vc=0.000168, Zc=0.2412, omega=0.635, dipole=1.44, Vmg=0.02357, Cpgm=56.98+R, mug=7.903e-6, CASRN='64-17-5')
    assert_close(EtOH.calculate_P(298.15, 1E2, COOLPROP), 0.015207849649231962)
    assert_close(EtOH.calculate_P(298.15, 1E6, ELI_HANLEY_DENSE), 0.011210125242396791)
    assert_close(EtOH.calculate_P(298.15, 1E6, CHUNG_DENSE), 0.011770368783141446)
    assert_close(EtOH.calculate_P(298.15, 1E6, STIEL_THODOS_DENSE), 0.015447836685420897)


      # Ethanol data, calculated from CoolProp
    Ts = [400, 500, 600]
    Ps = [1E4, 1E5, 2E5]
    TP_data = [[0.025825794817543015, 0.037905383602635095, 0.05080124980338535], [0.02601702567554805, 0.03806794452306919, 0.050946301396380594], [0.026243171168075605, 0.03825284803978187, 0.05110925652065333]]
    EtOH.add_tabular_data_P(Ts, Ps, TP_data, name='CPdata')
    recalc_pts = [[EtOH.TP_dependent_property(T, P) for T in Ts] for P in Ps]
    assert_allclose(TP_data, recalc_pts)

    EtOH.forced_P = True
    EtOH.tabular_extrapolation_permitted = True
    assert_close(EtOH.TP_dependent_property(399, 9E3), 0.025825794817543015)
    EtOH.tabular_extrapolation_permitted = False
    assert None == EtOH.TP_dependent_property(399, 9E3)

    with pytest.raises(Exception):
        EtOH.test_method_validity_P(300, 1E5, 'BADMETHOD')

    assert False == EtOH.test_method_validity_P(100, 1E5, COOLPROP)


def test_ThermalConductivityGasMixture():
    from thermo.thermal_conductivity import ThermalConductivityGasMixture, LINDSAY_BROMLEY, SIMPLE

    m2 = Mixture(['nitrogen', 'argon', 'oxygen'], ws=[0.7557, 0.0127, 0.2316])
    ThermalConductivityGases = [i.ThermalConductivityGas for i in m2.Chemicals]
    ViscosityGases = [i.ViscosityGas for i in m2.Chemicals]

    kg_mix = ThermalConductivityGasMixture(MWs=m2.MWs, Tbs=m2.Tbs, CASs=m2.CASs,
                                      ThermalConductivityGases=ThermalConductivityGases,
                                      ViscosityGases=ViscosityGases)

    k = kg_mix.mixture_property(m2.T, m2.P, m2.zs, m2.ws)
    assert_close(k, 0.025864474514829254) # test LINDSAY_BROMLEY and mixture property
    # Do it twice to test the stored method
    k = kg_mix.mixture_property(m2.T, m2.P, m2.zs, m2.ws)
    assert_close(k, 0.025864474514829254) # test LINDSAY_BROMLEY and mixture property

    k =  kg_mix.calculate(m2.T, m2.P, m2.zs, m2.ws, SIMPLE) # Test calculate, and simple
    assert_close(k, 0.02586655464213776)

    dT1 = kg_mix.calculate_derivative_T(m2.T, m2.P, m2.zs, m2.ws, LINDSAY_BROMLEY)
    dT2 = kg_mix.property_derivative_T(m2.T, m2.P, m2.zs, m2.ws)
    assert_close1d([dT1, dT2], [7.3391064059347144e-05]*2)

    dP1 = kg_mix.calculate_derivative_P(m2.P, m2.T, m2.zs, m2.ws, LINDSAY_BROMLEY)
    dP2 = kg_mix.property_derivative_P(m2.T, m2.P, m2.zs, m2.ws)

    assert_close1d([dP1, dP2], [3.5325319058809868e-10]*2, rtol=1E-4)

    # Test other methods

    assert kg_mix.all_methods == {LINDSAY_BROMLEY, SIMPLE}
    assert kg_mix.ranked_methods == [LINDSAY_BROMLEY, SIMPLE]

    # set a method
    kg_mix.method = SIMPLE
    k = kg_mix.mixture_property(m2.T, m2.P, m2.zs, m2.ws)
    assert_close(k, 0.02586655464213776)

    # Unhappy paths
    with pytest.raises(Exception):
        kg_mix.calculate(m2.T, m2.P, m2.zs, m2.ws, 'BADMETHOD')

    with pytest.raises(Exception):
        kg_mix.test_method_validity(m2.T, m2.P, m2.zs, m2.ws, 'BADMETHOD')



def test_ThermalConductivityLiquidMixture():
    from thermo.thermal_conductivity import MAGOMEDOV, DIPPR_9H, FILIPPOV, SIMPLE, ThermalConductivityLiquidMixture

    m = Mixture(['ethanol', 'pentanol'], ws=[0.258, 0.742], T=298.15)
    ThermalConductivityLiquids = [i.ThermalConductivityLiquid for i in m.Chemicals]

    kl_mix = ThermalConductivityLiquidMixture(CASs=m.CASs, ThermalConductivityLiquids=ThermalConductivityLiquids, MWs=m.MWs)
    k = kl_mix.mixture_property(m.T, m.P, m.zs, m.ws)
    assert_close(k, 0.15300152782218343)

    k = kl_mix.calculate(m.T, m.P, m.zs, m.ws, FILIPPOV)
    assert_close(k, 0.15522139770330717)

    k = kl_mix.calculate(m.T, m.P, m.zs, m.ws, SIMPLE)
    assert_close(k, 0.1552717795028546)

    # Test electrolytes
    m = Mixture(['water', 'sulfuric acid'], ws=[.5, .5], T=298.15)
    ThermalConductivityLiquids = [i.ThermalConductivityLiquid for i in m.Chemicals]
    kl_mix = ThermalConductivityLiquidMixture(CASs=m.CASs, ThermalConductivityLiquids=ThermalConductivityLiquids, MWs=m.MWs)
    assert kl_mix.method == MAGOMEDOV
    k = kl_mix.mixture_property(m.T, m.P, m.zs, m.ws)
    assert_close(k, 0.4677453168207703)


    # Unhappy paths
    with pytest.raises(Exception):
        kl_mix.calculate(m.T, m.P, m.zs, m.ws, 'BADMETHOD')

    with pytest.raises(Exception):
        kl_mix.test_method_validity(m.T, m.P, m.zs, m.ws, 'BADMETHOD')
