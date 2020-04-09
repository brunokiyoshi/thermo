# -*- coding: utf-8 -*-
'''Chemical Engineering Design Library (ChEDL). Utilities for process modeling.
Copyright (C) 2019, Caleb Bell <Caleb.Andrew.Bell@gmail.com>

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
from fluids.numerics import derivative, assert_close, jacobian, hessian

from thermo.chemical_package import ChemicalConstantsPackage, PropertyCorrelationPackage
from thermo import Chemical, Mixture
from math import *
from thermo.phases import *
from thermo.eos_mix import *
from thermo.eos import *
from thermo.vapor_pressure import VaporPressure
from thermo.volume import *
from thermo.viscosity import *
from thermo.thermal_conductivity import *
from thermo.heat_capacity import *
from thermo.phase_change import *
from thermo.unifac import UNIFAC, UFSG, UFIP
from thermo.coolprop import PropsSI


def test_GibbbsExcessLiquid_VaporPressure():
    # Binary ethanol-water
    VaporPressures = [VaporPressure(best_fit=(159.11, 514.7, [-2.3617526481119e-19, 7.318686894378096e-16, -9.835941684445551e-13, 7.518263303343784e-10, -3.598426432676194e-07, 0.00011171481063640762, -0.022458952185007635, 2.802615041941912, -166.43524219017118])),
                      VaporPressure(best_fit=(273.17, 647.086, [-2.8478502840358144e-21, 1.7295186670575222e-17, -4.034229148562168e-14, 5.0588958391215855e-11, -3.861625996277003e-08, 1.886271475957639e-05, -0.005928371869421494, 1.1494956887882308, -96.74302379151317]))]
    T = 300.0
    P = 1e5
    zs = [.4, .6]
    liquid = GibbsExcessLiquid(VaporPressures=VaporPressures).to_TP_zs(T, P, zs)
    
    # Ingredients
    Psats_expect = [8778.910843769489, 3537.075987237396]
    assert_allclose(liquid.Psats(), Psats_expect, rtol=1e-12)
    assert_allclose(liquid.Psats_at(T), Psats_expect, rtol=1e-12)
    assert_allclose(liquid.Psats_at(310.0), [15187.108461608485, 6231.649608160113], rtol=1e-12)
    
    gammas_expect = [1.0, 1.0]
    assert liquid.gammas() == gammas_expect
    
    Poyntings_expect = [1.0, 1.0]
    assert liquid.Poyntings() == Poyntings_expect
    
    dPoyntings_dT_expect = [0.0, 0.0]
    assert liquid.dPoyntings_dT() == dPoyntings_dT_expect
    
    dPoyntings_dP_expect = [0.0, 0.0]
    assert liquid.dPoyntings_dP() == dPoyntings_dP_expect
    
    phis_sat_expect = [1.0, 1.0]
    assert liquid.phis_sat() == phis_sat_expect
    
    # Fugacities and friends
    phis_expect = [0.0877891084376949, 0.035370759872373966]
    assert_allclose(liquid.phis(), phis_expect, rtol=1e-12)
    
    lnphis_expect = [-2.432817835720433, -3.3418697924678376]
    assert_allclose(liquid.lnphis(), lnphis_expect, rtol=1e-12)
    
    fugacities_expect = [3511.564337507796, 2122.245592342438]
    assert_allclose(liquid.fugacities(), fugacities_expect, rtol=1e-12)
    
    # Temperature derivatives
    dlnphis_dT_expect = [0.05691421137269392, 0.058786419948670225]
    assert_allclose(liquid.dlnphis_dT(), dlnphis_dT_expect, rtol=1e-12)
    
    dphis_dT_expect = [0.004996447873843315, 0.0020793203437609493]
    assert_allclose(liquid.dphis_dT(), dphis_dT_expect, rtol=1e-12)
    
    dfugacities_dT_expect = [199.8579149537326, 124.75922062565697]
    assert_allclose(liquid.dfugacities_dT(), dfugacities_dT_expect, rtol=1e-12)
    
    # Pressure derivatives
    dlnphis_dP_expect = [-1e-05, -1e-05]
    assert_allclose(liquid.dlnphis_dP(), dlnphis_dP_expect, rtol=1e-12)
    
    dphis_dP_expect = [-8.778910843769491e-07, -3.537075987237397e-07]
    assert_allclose(liquid.dphis_dP(), dphis_dP_expect, rtol=1e-12)
    
    dfugacities_dP_expect = [0, 0]
    assert_allclose(liquid.dfugacities_dP(), dfugacities_dP_expect, atol=1e-15)


def test_GibbbsExcessLiquid_VolumeLiquids():
    # Binary ethanol-water
    T = 230.0
    P = 1e5
    zs = [.4, .6]
    
    MWs = [18.01528, 46.06844]
    Tcs = [647.14, 514.0]
    Pcs = [22048320.0, 6137000.0]
    Vcs = [5.6e-05, 0.000168]
    Zcs = [0.22947273972184645, 0.24125043269792068]
    omegas = [0.344, 0.635]
    
    eoss = [PR(Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0], T=T, P=P),
            PR(Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1], T=T, P=P)]
    
    # m = Mixture(['water', 'ethanol'], zs=zs, T=T, P=P)
    
    VaporPressures = [VaporPressure(best_fit=(159.11, 514.7, [-2.3617526481119e-19, 7.318686894378096e-16, -9.835941684445551e-13, 7.518263303343784e-10, -3.598426432676194e-07, 0.00011171481063640762, -0.022458952185007635, 2.802615041941912, -166.43524219017118])),
                      VaporPressure(best_fit=(273.17, 647.086, [-2.8478502840358144e-21, 1.7295186670575222e-17, -4.034229148562168e-14, 5.0588958391215855e-11, -3.861625996277003e-08, 1.886271475957639e-05, -0.005928371869421494, 1.1494956887882308, -96.74302379151317]))]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                       HeatCapacityGas(best_fit=(50.0, 1000.0, [-1.162767978165682e-20, 5.4975285700787494e-17, -1.0861242757337942e-13, 1.1582703354362728e-10, -7.160627710867427e-08, 2.5392014654765875e-05, -0.004732593693568646, 0.5072291035198603, 20.037826650765965]))]
    # HBT Pressure dependence needs Psats, Tc, Pc, omegas
    VolumeLiquids = [VolumeLiquid(best_fit=(273.17, 637.096, [9.00307261049824e-24, -3.097008950027417e-20, 4.608271228765265e-17, -3.8726692841874345e-14, 2.0099220218891486e-11, -6.596204729785676e-09, 1.3368112879131157e-06, -0.00015298762503607717, 0.007589247005014652]),
                                  Psat=VaporPressures[0], Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0]),
                     VolumeLiquid(best_fit=(159.11, 504.71000000000004, [5.388587987308587e-23, -1.331077476340645e-19, 1.4083880805283782e-16, -8.327187308842775e-14, 3.006387047487587e-11, -6.781931902982022e-09, 9.331209920256822e-07, -7.153268618320437e-05, 0.0023871634205665524]),
                                  Psat=VaporPressures[1], Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1])]
    
    EnthalpyVaporizations = [EnthalpyVaporization(best_fit=(273.17, 647.095, 647.14, [0.010220675607316746, 0.5442323619614213, 11.013674729940819, 110.72478547661254, 591.3170172192005, 1716.4863395285283, 4063.5975524922624, 17960.502354189244, 53916.28280689388])),
                              EnthalpyVaporization(best_fit=(159.11, 513.9999486, 514.0, [-0.002197958699297133, -0.1583773493009195, -4.716256555877727, -74.79765793302774, -675.8449382004112, -3387.5058752252276, -7531.327682252346, 5111.75264050548, 50774.16034043739]))]
    
    liquid = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               EnthalpyVaporizations=EnthalpyVaporizations,
                               use_phis_sat=False, eos_pure_instances=eoss).to_TP_zs(T, P, zs)
    
    Vms_expect = [1.7835985614552184e-05, 5.44799706327522e-05]
    Vms_calc = liquid.Vms_sat()
    assert_allclose(Vms_expect, Vms_calc, rtol=1e-12)
    
    dVms_sat_dT_expect = [3.855990979785858e-09, 5.14342987163643e-08]
    dVms_sat_dT_calc = liquid.dVms_sat_dT()
    assert_allclose(dVms_sat_dT_expect, dVms_sat_dT_calc, rtol=1e-12)
    
    V_calc = liquid.V()
    assert_allclose(V_calc, 3.982237662547219e-05)
    
    liq2 = liquid.to_TP_zs(400, 1e6, zs)
    assert_allclose(liq2.V(), 4.8251068646661126e-05)
    
#    assert_allclose(liquid.H(), -49557.51889261903, rtol=1e-10) # poyntings?
    assert_allclose(liquid.Hvaps(), [46687.6343559442, 45719.87039687816])

def test_GibbbsExcessLiquid_MiscIdeal():
    # Binary ethanol-water
    T = 230.0
    P = 1e5
    zs = [.4, .6]
    
    MWs = [18.01528, 46.06844]
    Tcs = [647.14, 514.0]
    Pcs = [22048320.0, 6137000.0]
    Vcs = [5.6e-05, 0.000168]
    Zcs = [0.22947273972184645, 0.24125043269792068]
    omegas = [0.344, 0.635]
    
    eoss = [PR(Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0], T=T, P=P),
            PR(Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1], T=T, P=P)]
    
    VaporPressures = [VaporPressure(best_fit=(159.11, 514.7, [-2.3617526481119e-19, 7.318686894378096e-16, -9.835941684445551e-13, 7.518263303343784e-10, -3.598426432676194e-07, 0.00011171481063640762, -0.022458952185007635, 2.802615041941912, -166.43524219017118])),
                      VaporPressure(best_fit=(273.17, 647.086, [-2.8478502840358144e-21, 1.7295186670575222e-17, -4.034229148562168e-14, 5.0588958391215855e-11, -3.861625996277003e-08, 1.886271475957639e-05, -0.005928371869421494, 1.1494956887882308, -96.74302379151317]))]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                       HeatCapacityGas(best_fit=(50.0, 1000.0, [-1.162767978165682e-20, 5.4975285700787494e-17, -1.0861242757337942e-13, 1.1582703354362728e-10, -7.160627710867427e-08, 2.5392014654765875e-05, -0.004732593693568646, 0.5072291035198603, 20.037826650765965]))]
    # HBT Pressure dependence needs Psats, Tc, Pc, omegas
    VolumeLiquids = [VolumeLiquid(best_fit=(273.17, 637.096, [9.00307261049824e-24, -3.097008950027417e-20, 4.608271228765265e-17, -3.8726692841874345e-14, 2.0099220218891486e-11, -6.596204729785676e-09, 1.3368112879131157e-06, -0.00015298762503607717, 0.007589247005014652]),
                                  Psat=VaporPressures[0], Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0]),
                     VolumeLiquid(best_fit=(159.11, 504.71000000000004, [5.388587987308587e-23, -1.331077476340645e-19, 1.4083880805283782e-16, -8.327187308842775e-14, 3.006387047487587e-11, -6.781931902982022e-09, 9.331209920256822e-07, -7.153268618320437e-05, 0.0023871634205665524]),
                                  Psat=VaporPressures[1], Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1])]
    
    EnthalpyVaporizations = [EnthalpyVaporization(best_fit=(273.17, 647.095, 647.14, [0.010220675607316746, 0.5442323619614213, 11.013674729940819, 110.72478547661254, 591.3170172192005, 1716.4863395285283, 4063.5975524922624, 17960.502354189244, 53916.28280689388])),
                              EnthalpyVaporization(best_fit=(159.11, 513.9999486, 514.0, [-0.002197958699297133, -0.1583773493009195, -4.716256555877727, -74.79765793302774, -675.8449382004112, -3387.5058752252276, -7531.327682252346, 5111.75264050548, 50774.16034043739]))]
    
    liquid = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               EnthalpyVaporizations=EnthalpyVaporizations,
                               use_phis_sat=False, eos_pure_instances=eoss).to_TP_zs(T, P, zs)
    
    dV_dT = liquid.dV_dT()
    dV_dT_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).V(), T, dx=T*1e-5, order=3)
    assert_close(dV_dT, dV_dT_num)
    assert_close(dV_dT, 3.240297562173293e-08)
    
    assert liquid.dV_dP() == INCOMPRESSIBLE_CONST
    assert liquid.d2P_dV2() == INCOMPRESSIBLE_CONST
    assert 0 == liquid.d2V_dP2() #  # derivative of a constant is zero
    assert_close(liquid.dP_dT(), -3.240297562173293e-38)
    d2P_dTdV = liquid.d2P_dTdV()
    assert 0 == d2P_dTdV # derivative of a constant is zero
    d2P_dTdV_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).dP_dV(), T, dx=T*1e-5)
    assert_close(d2P_dTdV, d2P_dTdV_num, atol=1e-14)
    
    d2P_dT2_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).dP_dT(), T, dx=T*1e-5)
    assert_close(liquid.d2P_dT2(), d2P_dT2_num)
    
    assert_allclose(liquid.gammas(), [1.0, 1.0], rtol=1e-12)
    assert_allclose(liquid.phis_sat(), [1.0, 1.0], rtol=1e-12)
    assert_allclose(liquid.Poyntings(), [1.0, 1.0], rtol=1e-12)
    assert_allclose(liquid.phis(), [0.0004035893669389571, 0.000136992723615756], rtol=1e-12)
    
    dphis_dT = liquid.dphis_dT()
    dphis_dT_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).phis(), [T], scalar=False, perturbation=1e-8)
    dphis_dT_num = [i[0] for i in dphis_dT_num]
    assert_allclose(dphis_dT, dphis_dT_num, rtol=1e-6)
    
    dphis_dP = liquid.dphis_dP()
    dphis_dP_num = jacobian(lambda P: liquid.to(P=P[0], T=T, zs=zs).phis(), [P], scalar=False, perturbation=1e-8)
    dphis_dP_num = [i[0] for i in dphis_dP_num]
    assert_allclose(dphis_dP, dphis_dP_num, rtol=1e-8)
    
    # TODO dphis_dxs
    dphis_dxs_expect = [[0.0, 0.0], [0.0, 0.0]]
    dphis_dxs_num = jacobian(lambda zs: liquid.to(P=P, T=T, zs=zs).phis(), zs, scalar=False, perturbation=1e-8)
    assert_allclose(dphis_dxs_num, dphis_dxs_expect)
    
    # none of these are passing
    liquid.S_phi_consistency()
    liquid.H_phi_consistency()
    liquid.V_phi_consistency()
    liquid.G_phi_consistency()
    
    dPsats_dT = liquid.dPsats_dT()
    dPsats_dT_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).Psats(), [T], scalar=False, perturbation=2e-9)
    dPsats_dT_num = [i[0] for i in dPsats_dT_num]
    assert_allclose(dPsats_dT, dPsats_dT_num, rtol=2e-7)
    assert_allclose(dPsats_dT, [4.158045781849272, 1.4571835115958096], rtol=1e-12)
    
    d2Psats_dT2 = liquid.d2Psats_dT2()
    d2Psats_dT2_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).dPsats_dT(), [T], scalar=False, perturbation=10e-9)
    d2Psats_dT2_num = [i[0] for i in d2Psats_dT2_num]
    assert_allclose(d2Psats_dT2, d2Psats_dT2_num, rtol=5e-7)
    assert_allclose(d2Psats_dT2, [0.38889016337503146, 0.1410925971754788], rtol=1e-12)
    
    
    dVms_sat_dT = liquid.dVms_sat_dT()
    dVms_sat_dT_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).Vms_sat(), [T],
                               scalar=False, perturbation=1e-6)
    dVms_sat_dT_num = [i[0] for i in dVms_sat_dT_num]
    assert_allclose(dVms_sat_dT, dVms_sat_dT_num, rtol=1e-6)
    assert_allclose(dVms_sat_dT, [3.855990979785858e-09, 5.14342987163643e-08], rtol=1e-12)
    
    
    d2Vms_sat_dT2 = liquid.d2Vms_sat_dT2()
    d2Vms_sat_dT2_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).dVms_sat_dT(), 
                                 [T], scalar=False, perturbation=1e-7)
    d2Vms_sat_dT2_num = [i[0] for i in d2Vms_sat_dT2_num]
    assert_allclose(d2Vms_sat_dT2, d2Vms_sat_dT2_num, rtol=1e-6)
    assert_allclose(d2Vms_sat_dT2, [1.676517817298199e-11, 5.457718437885466e-10], rtol=1e-12)
    
    # Do a comple more points near the second derivative
    for T in [159.11+.1, 159.11-.1, 159.11+1e-5, 159.11-1e-5]:
        liquid = liquid.to(T=T, P=P, zs=zs)
    
        dPsats_dT = liquid.dPsats_dT()
        dPsats_dT_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).Psats(), [liquid.T], scalar=False, perturbation=10e-9)
        dPsats_dT_num = [i[0] for i in dPsats_dT_num]
        assert_allclose(dPsats_dT, dPsats_dT_num, rtol=5e-7)
    
        d2Psats_dT2 = liquid.d2Psats_dT2()
        d2Psats_dT2_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).dPsats_dT(), [liquid.T], scalar=False, perturbation=10e-9)
        d2Psats_dT2_num = [i[0] for i in d2Psats_dT2_num]
        assert_allclose(d2Psats_dT2, d2Psats_dT2_num, rtol=5e-7)
    
    T_min = liquid.VaporPressures[0].best_fit_Tmin
    liquid_under = liquid.to(T=T_min-1e-12, P=P,zs=zs)
    liquid_over = liquid.to(T=T_min+1e-12, P=P,zs=zs)
    d2Psats_dT2_under = liquid_under.d2Psats_dT2()
    d2Psats_dT2_over = liquid_over.d2Psats_dT2()
    assert_allclose(d2Psats_dT2_under, d2Psats_dT2_over)
    
    dPsats_dT_under = liquid_under.dPsats_dT()
    dPsats_dT_over = liquid_over.dPsats_dT()
    assert_allclose(dPsats_dT_under, dPsats_dT_over)
    
    Psats_under = liquid_under.Psats()
    Psats_over = liquid_over.Psats()
    assert_allclose(Psats_under, Psats_over)
    
    # Not always true at this point
    # d2Vms_sat_dT2_under = liquid_under.d2Vms_sat_dT2()
    # d2Vms_sat_dT2_over = liquid_over.d2Vms_sat_dT2()
    # assert_allclose(d2Vms_sat_dT2_under, d2Vms_sat_dT2_over)
    dVms_sat_dT_under = liquid_under.dVms_sat_dT()
    dVms_sat_dT_over = liquid_over.dVms_sat_dT()
    assert_allclose(dVms_sat_dT_under, dVms_sat_dT_over)
    
    Vms_sat_under = liquid_under.Vms_sat()
    Vms_sat_over = liquid_over.Vms_sat()
    assert_allclose(Vms_sat_under, Vms_sat_over)

            
    
def test_GibbbsExcessLiquid_PoyntingWorking():
    # Binary ethanol-water
    T = 230.0
    P = 1e5
    zs = [.4, .6]
    
    MWs = [18.01528, 46.06844]
    Tcs = [647.14, 514.0]
    Pcs = [22048320.0, 6137000.0]
    Vcs = [5.6e-05, 0.000168]
    omegas = [0.344, 0.635]
    
    VaporPressures = [VaporPressure(best_fit=(273.17, 647.086, [-2.8478502840358144e-21, 1.7295186670575222e-17, -4.034229148562168e-14, 5.0588958391215855e-11, -3.861625996277003e-08, 1.886271475957639e-05, -0.005928371869421494, 1.1494956887882308, -96.74302379151317])),
                      VaporPressure(best_fit=(159.11, 514.7, [-2.3617526481119e-19, 7.318686894378096e-16, -9.835941684445551e-13, 7.518263303343784e-10, -3.598426432676194e-07, 0.00011171481063640762, -0.022458952185007635, 2.802615041941912, -166.43524219017118])),]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                       HeatCapacityGas(best_fit=(50.0, 1000.0, [-1.162767978165682e-20, 5.4975285700787494e-17, -1.0861242757337942e-13, 1.1582703354362728e-10, -7.160627710867427e-08, 2.5392014654765875e-05, -0.004732593693568646, 0.5072291035198603, 20.037826650765965]))]
    # HBT Pressure dependence needs Psats, Tc, Pc, omegas
    VolumeLiquids = [VolumeLiquid(best_fit=(273.17, 637.096, [9.00307261049824e-24, -3.097008950027417e-20, 4.608271228765265e-17, -3.8726692841874345e-14, 2.0099220218891486e-11, -6.596204729785676e-09, 1.3368112879131157e-06, -0.00015298762503607717, 0.007589247005014652]),
                                  Psat=VaporPressures[0], Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0]),
                     VolumeLiquid(best_fit=(159.11, 504.71000000000004, [5.388587987308587e-23, -1.331077476340645e-19, 1.4083880805283782e-16, -8.327187308842775e-14, 3.006387047487587e-11, -6.781931902982022e-09, 9.331209920256822e-07, -7.153268618320437e-05, 0.0023871634205665524]),
                                  Psat=VaporPressures[1], Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1])]
    
    liquid = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               use_Poynting=True, # Makes V_from_phi consistent
                               use_phis_sat=False).to_TP_zs(T, P, zs)
    
    assert_close(liquid.S_phi_consistency(), 0, atol=1e-13)
    assert_close(liquid.H_phi_consistency(), 0, atol=1e-13)
    assert_close(liquid.G_phi_consistency(), 0, atol=1e-13)
    assert_close(liquid.V_phi_consistency(), 0, atol=1e-13)
    assert_close(liquid.V_from_phi(), liquid.V(), rtol=1e-13)
    
    
    assert_close(liquid.H(), -49263.45037352884)
    assert_close(liquid.S(), -138.07941956364567)
    assert_close(liquid.G(), -17505.183873890335)
    
    assert_allclose(liquid.phis(), [0.0001371205367872173, 0.0004047403204229314])
    
    dphis_dT = liquid.dphis_dT()
    dphis_dT_num = jacobian(lambda T: liquid.to(T=T[0], P=P, zs=zs).phis(), [T], scalar=False, perturbation=1e-8)
    dphis_dT_num = [i[0] for i in dphis_dT_num]
    assert_allclose(dphis_dT, dphis_dT_num, rtol=1e-6)
    
    dphis_dP = liquid.dphis_dP()
    dphis_dP_num = jacobian(lambda P: liquid.to(P=P[0], T=T, zs=zs).phis(), [P], scalar=False, perturbation=1e-8)
    dphis_dP_num = [i[0] for i in dphis_dP_num]
    assert_allclose(dphis_dP, dphis_dP_num, rtol=1e-7)
    
    # point under Psats - check the consistencies are still there
    liq2 = liquid.to(T=400, P=1e5, zs=zs)
    assert_close(liq2.S_phi_consistency(), 0, atol=1e-13)
    assert_close(liq2.H_phi_consistency(), 0, atol=1e-13)
    assert_close(liq2.G_phi_consistency(), 0, atol=1e-13)
    assert_close(liq2.V_phi_consistency(), 0, atol=1e-13)
    assert_close(liq2.V_from_phi(), liq2.V(), rtol=1e-13)
    
    
    dH_dP_num = derivative(lambda P: liquid.to(T=T, P=P, zs=zs).H(), P, dx=P*1e-5)
    dH_dP = liquid.dH_dP()
    assert_close(dH_dP, 3.236969223247362e-05, rtol=1e-11)
    assert_close(dH_dP, dH_dP_num, rtol=1e-6)
    
    dS_dP_num = derivative(lambda P: liquid.to(T=T, P=P, zs=zs).S(), P, dx=P*1e-5)
    dS_dP = liquid.dS_dP()
    assert_close(dS_dP, dS_dP_num, rtol=1e-6)
    assert_close(dS_dP, -3.240297562173293e-08, rtol=1e-11)
    
    dH_dT_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).H(), T, dx=T*1e-7)
    dH_dT = liquid.dH_dT()
    assert_close(dH_dT, dH_dT_num, rtol=1e-7)
    assert_close(dH_dT, 84.15894725560165, rtol=1e-11)
    
    dS_dT_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).S(), T, dx=T*1e-7)
    dS_dT = liquid.dS_dT()
    assert_close(dS_dT, dS_dT_num, rtol=1e-7)
    assert_close(dS_dT, 0.3659084663286978, rtol=1e-11)

    dPoyntings_dT = liquid.dPoyntings_dT()
    dPoyntings_dT_num = jacobian(lambda T: liquid.to(P=P, T=T[0], zs=zs).Poyntings(), [T], scalar=False, perturbation=5e-7)
    dPoyntings_dT_num = [i[0] for i in dPoyntings_dT_num]
    assert_allclose(dPoyntings_dT, dPoyntings_dT_num, rtol=1e-6)
    assert_allclose(dPoyntings_dT, [-3.870184881396542e-06, -9.839359563363645e-06], rtol=1e-10)
    
    d2Poyntings_dT2 = liquid.d2Poyntings_dT2()
    d2Poyntings_d2T_num = jacobian(lambda T: liquid.to(P=P, T=T[0], zs=zs).dPoyntings_dT(), [T], scalar=False, perturbation=5e-7)
    d2Poyntings_d2T_num = [i[0] for i in d2Poyntings_d2T_num]
    assert_allclose(d2Poyntings_dT2, d2Poyntings_d2T_num, rtol=1e-6)
    assert_allclose(d2Poyntings_dT2, [3.3223074340239076e-08, 1.0293076880888814e-07], rtol=1e-10)

    d2Poyntings_dPdT = liquid.d2Poyntings_dPdT()
    d2Poyntings_dPdT_num = jacobian(lambda P: liquid.to(P=P[0], T=T, zs=zs).dPoyntings_dT(), [P], scalar=False, perturbation=5e-7)
    d2Poyntings_dPdT_num = [i[0] for i in d2Poyntings_dPdT_num]
    assert_allclose(d2Poyntings_dPdT, d2Poyntings_dPdT_num, rtol=1e-6)
    assert_allclose(d2Poyntings_dPdT, [-3.860719326165776e-11, -9.752519722895721e-11], rtol=1e-10)

def test_GibbbsExcessLiquid_NoPoyNoGammaNoPhi():
    # Binary ethanol-water
    T = 230.0
    P = 1e5
    zs = [.4, .6]
    
    MWs = [18.01528, 46.06844]
    Tcs = [647.14, 514.0]
    Pcs = [22048320.0, 6137000.0]
    Vcs = [5.6e-05, 0.000168]
    omegas = [0.344, 0.635]
    
    VaporPressures = [VaporPressure(best_fit=(273.17, 647.086, [-2.8478502840358144e-21, 1.7295186670575222e-17, -4.034229148562168e-14, 5.0588958391215855e-11, -3.861625996277003e-08, 1.886271475957639e-05, -0.005928371869421494, 1.1494956887882308, -96.74302379151317])),
                      VaporPressure(best_fit=(159.11, 514.7, [-2.3617526481119e-19, 7.318686894378096e-16, -9.835941684445551e-13, 7.518263303343784e-10, -3.598426432676194e-07, 0.00011171481063640762, -0.022458952185007635, 2.802615041941912, -166.43524219017118])),]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                       HeatCapacityGas(best_fit=(50.0, 1000.0, [-1.162767978165682e-20, 5.4975285700787494e-17, -1.0861242757337942e-13, 1.1582703354362728e-10, -7.160627710867427e-08, 2.5392014654765875e-05, -0.004732593693568646, 0.5072291035198603, 20.037826650765965]))]
    # HBT Pressure dependence needs Psats, Tc, Pc, omegas
    VolumeLiquids = [VolumeLiquid(best_fit=(273.17, 637.096, [9.00307261049824e-24, -3.097008950027417e-20, 4.608271228765265e-17, -3.8726692841874345e-14, 2.0099220218891486e-11, -6.596204729785676e-09, 1.3368112879131157e-06, -0.00015298762503607717, 0.007589247005014652]),
                                  Psat=VaporPressures[0], Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0]),
                     VolumeLiquid(best_fit=(159.11, 504.71000000000004, [5.388587987308587e-23, -1.331077476340645e-19, 1.4083880805283782e-16, -8.327187308842775e-14, 3.006387047487587e-11, -6.781931902982022e-09, 9.331209920256822e-07, -7.153268618320437e-05, 0.0023871634205665524]),
                                  Psat=VaporPressures[1], Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1])]
    
    liquid = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               use_Poynting=False,
                               use_phis_sat=False).to_TP_zs(T, P, zs)
    dH_dP_num = derivative(lambda P: liquid.to(T=T, P=P, zs=zs).H(), P, dx=P*1e-5)
    dH_dP = liquid.dH_dP()
    assert_close(dH_dP, 0, atol=1e-11)
    assert_close(dH_dP, dH_dP_num)


def test_GibbsExcessLiquid_H_S_settings():
    # water-ethanol
    T = 400.0
    P = 1e6
    zs = [.4, .6]

    MWs = [18.01528, 46.06844]
    Tcs = [647.14, 514.0]
    Pcs = [22048320.0, 6137000.0]
    Vcs = [5.6e-05, 0.000168]
    Zcs = [0.22947273972184645, 0.24125043269792068]
    omegas = [0.344, 0.635]
    
    eoss = [PR(Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0], T=T, P=P),
            PR(Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1], T=T, P=P)]
    
    GE = UNIFAC.from_subgroups(T, zs, chemgroups=[{16: 1}, {1: 1, 2: 1, 14: 1}], subgroups=UFSG,
                           interaction_data=UFIP, version=0)
        
    VaporPressures = [VaporPressure(best_fit=(159.11, 514.7, [-2.3617526481119e-19, 7.318686894378096e-16, -9.835941684445551e-13, 7.518263303343784e-10, -3.598426432676194e-07, 0.00011171481063640762, -0.022458952185007635, 2.802615041941912, -166.43524219017118])),
                      VaporPressure(best_fit=(273.17, 647.086, [-2.8478502840358144e-21, 1.7295186670575222e-17, -4.034229148562168e-14, 5.0588958391215855e-11, -3.861625996277003e-08, 1.886271475957639e-05, -0.005928371869421494, 1.1494956887882308, -96.74302379151317]))]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                       HeatCapacityGas(best_fit=(50.0, 1000.0, [-1.162767978165682e-20, 5.4975285700787494e-17, -1.0861242757337942e-13, 1.1582703354362728e-10, -7.160627710867427e-08, 2.5392014654765875e-05, -0.004732593693568646, 0.5072291035198603, 20.037826650765965]))]
    VolumeLiquids = [VolumeLiquid(best_fit=(273.17, 637.096, [9.00307261049824e-24, -3.097008950027417e-20, 4.608271228765265e-17, -3.8726692841874345e-14, 2.0099220218891486e-11, -6.596204729785676e-09, 1.3368112879131157e-06, -0.00015298762503607717, 0.007589247005014652]),
                                  Psat=VaporPressures[0], Tc=Tcs[0], Pc=Pcs[0], omega=omegas[0]),
                     VolumeLiquid(best_fit=(159.11, 504.71000000000004, [5.388587987308587e-23, -1.331077476340645e-19, 1.4083880805283782e-16, -8.327187308842775e-14, 3.006387047487587e-11, -6.781931902982022e-09, 9.331209920256822e-07, -7.153268618320437e-05, 0.0023871634205665524]),
                                  Psat=VaporPressures[1], Tc=Tcs[1], Pc=Pcs[1], omega=omegas[1])]
    
    liquid_base = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               use_Poynting=False,
                               use_phis_sat=False, eos_pure_instances=eoss, T=T, P=P, zs=zs)
    
    liquid_poy = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               use_Poynting=True,
                               use_phis_sat=False, eos_pure_instances=eoss, T=T, P=P, zs=zs)
    
    liquid_phi = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               use_Poynting=False,
                               use_phis_sat=True, eos_pure_instances=eoss, T=T, P=P, zs=zs)
    
    liquid_phi_poy = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               use_Poynting=True,
                               use_phis_sat=True, eos_pure_instances=eoss, T=T, P=P, zs=zs)
    
    liquid_phi_poy_gamma = GibbsExcessLiquid(VaporPressures=VaporPressures,HeatCapacityGases=HeatCapacityGases,
                               VolumeLiquids=VolumeLiquids,
                               GibbsExcessModel=GE,
                               use_Poynting=True,
                               use_phis_sat=True, eos_pure_instances=eoss, T=T, P=P, zs=zs)
    
    Hs_sympy = [-33955.85490517719, -33782.17641365815, -32392.64972459377, -32218.97123307472, -32231.87689500188]
    Ss_sympy = [-86.99253060781912, -86.643966007413, -82.62865124423134, -82.28008664382519, -84.6099271604735]
    
    liquids = [liquid_base, liquid_poy, liquid_phi, liquid_phi_poy, liquid_phi_poy_gamma]
    for i, liquid in enumerate(liquids):
        assert_close(liquid.H(), Hs_sympy[i], rtol=1e-7)
        assert_close(liquid.S(), Ss_sympy[i], rtol=1e-7)
        assert liquid.H_phi_consistency() < 1e-12
        assert liquid.G_phi_consistency() < 1e-12
        assert liquid.S_phi_consistency() < 1e-12
        
    Hs_sympy_25 = [-65338.10590845912, -65302.94609111096, -65338.10590845621, -65302.946091108046, -66674.23856545633]
    Ss_sympy_25 = [-301.96338548883887, -301.9678046815029, -301.96338548872274, -301.9678046813865, -314.04477767859197]
    for i, liquid in enumerate(liquids):
        liquid = liquid.to(T=25.0, P=P, zs=zs)
        assert_close(liquid.H(), Hs_sympy_25[i], rtol=1e-7)
        assert_close(liquid.S(), Ss_sympy_25[i], rtol=1e-7)
        assert liquid.H_phi_consistency() < 1e-12
        assert liquid.G_phi_consistency() < 1e-12
        assert liquid.S_phi_consistency() < 1e-12
    
    Hs_sympy_100 = [-59946.52795254455, -59912.196733820856, -59946.52795254455, -59912.196733820856, -61013.95021615358]
    Ss_sympy_100 = [-203.4071522317269, -203.42482900238204, -203.4071522317269, -203.42482900238204, -211.71645847200244]    
    for i, liquid in enumerate(liquids):
        liquid = liquid.to(T=100.0, P=P, zs=zs)
        assert_close(liquid.H(), Hs_sympy_100[i], rtol=1e-7)
        assert_close(liquid.S(), Ss_sympy_100[i], rtol=1e-7)
        assert liquid.H_phi_consistency() < 1e-12
        assert liquid.G_phi_consistency() < 1e-12
        assert liquid.S_phi_consistency() < 1e-12
    
    
    Hs_sympy_513_99 = [-24370.789969661833, -20892.60843773296, -16638.418485822214, -13160.23695389335, -12983.67776053422]
    Ss_sympy_513_99 = [-65.67919656626539, -58.49338700743429, -48.01112147345394, -40.825311914622844, -42.73731658374935]
    for i, liquid in enumerate(liquids):
        liquid = liquid.to(T=513.99, P=P, zs=zs)
        assert_close(liquid.H(), Hs_sympy_513_99[i], rtol=1e-7)
        assert_close(liquid.S(), Ss_sympy_513_99[i], rtol=1e-7)
        assert liquid.H_phi_consistency() < 1e-12
        assert liquid.G_phi_consistency() < 1e-12
        assert liquid.S_phi_consistency() < 1e-12

def test_GibbsExcessLiquid_lnPsats():
    T, P, zs = 100.0, 1e5, [1.0]
    constants = ChemicalConstantsPackage(Tms=[179.2], Tbs=[383.75], Tcs=[591.75], Pcs=[4108000.0], omegas=[0.257], MWs=[92.13842], CASs=['108-88-3'], names=[u'toluene'])
    VaporPressures = [VaporPressure(best_fit=(178.01, 591.74, [-8.638045111752356e-20, 2.995512203611858e-16, -4.5148088801006036e-13, 3.8761537879200513e-10, -2.0856828984716705e-07, 7.279010846673517e-05, -0.01641020023565049, 2.2758331029405516, -146.04484159879843]))]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [-9.48396765770823e-21, 4.444060985512694e-17, -8.628480671647472e-14, 8.883982004570444e-11, -5.0893293251198045e-08, 1.4947108372371731e-05, -0.0015271248410402886, 0.19186172941013854, 30.797883940134057]))]
    VolumeLiquids = [VolumeLiquid(best_fit=(178.01, 581.75, [2.2801490297347937e-23, -6.411956871696508e-20, 7.723152902379232e-17, -5.197203733189603e-14, 2.1348482785660093e-11, -5.476649499770259e-09, 8.564670053875876e-07, -7.455178589434267e-05, 0.0028545812080104068]))]
    correlations = PropertyCorrelationPackage(constants, VolumeLiquids=VolumeLiquids, VaporPressures=VaporPressures, HeatCapacityGases=HeatCapacityGases, skip_missing=True)
    liquid_AB = GibbsExcessLiquid(VaporPressures=correlations.VaporPressures, 
                               HeatCapacityGases=correlations.HeatCapacityGases,
                               VolumeLiquids=correlations.VolumeLiquids,
                               use_phis_sat=False, use_Poynting=True, T=T, P=P, zs=zs, Psat_extrpolation='AB')
    liquid_ABC = GibbsExcessLiquid(VaporPressures=correlations.VaporPressures, 
                               HeatCapacityGases=correlations.HeatCapacityGases,
                               VolumeLiquids=correlations.VolumeLiquids,
                               use_phis_sat=False, use_Poynting=True, T=T, P=P, zs=zs, Psat_extrpolation='ABC')
    
    for liquid in (liquid_AB, liquid_ABC):
        for T in (1, 5, 20, 100, 400, 591.74-1e-4, 591.74, 591.74+1e-10, 1000):
            liquid = liquid.to(T=T, P=P, zs=zs)
            assert_close(liquid.Psats()[0], exp(liquid.lnPsats()[0]), rtol=1e-12)
        
            dlnPsats_dT = liquid.dlnPsats_dT()[0]
            dlnPsats_dT_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).lnPsats()[0], T, dx=T*1e-7)
            assert_close(dlnPsats_dT, dlnPsats_dT_num, rtol=5e-6)
            
            # Lack of second derivative continuity means this doesn't work
            if T < 591.73 or liquid is liquid_ABC:
                d2lnPsats_dT2 = liquid.d2lnPsats_dT2()[0]
                d2lnPsats_dT2_num = derivative(lambda T: liquid.to(T=T, P=P, zs=zs).dlnPsats_dT()[0], T, dx=T*1e-7)
                assert_close(d2lnPsats_dT2, d2lnPsats_dT2_num, rtol=5e-6)
    
    # Points which do not matter which high model is used
    liquid = liquid_ABC
    
    liquid = liquid.to(T=300, P=P, zs=zs)
    assert_close(liquid.dPsats_dT_over_Psats()[0], 0.05097707819215502, rtol=1e-12)
    liquid = liquid.to(T=100, P=P, zs=zs)
    assert_close(liquid.dPsats_dT_over_Psats()[0], .6014857645090779, rtol=1e-12)
    
    # Point where cannot calculate normally, need special math
    liquid = liquid.to(T=5, P=P, zs=zs)
    assert_close(liquid.dPsats_dT_over_Psats(), 268.3252967590297, rtol=1e-12)
    
    # High temp - avoid checking a value
    liquid = liquid.to(T=1000, P=P, zs=zs)
    assert_close(liquid.dPsats_dT_over_Psats()[0], liquid.dPsats_dT()[0]/liquid.Psats()[0], rtol=1e-12)
    
    # High temp- check value with both
    assert_close(liquid_AB.to(T=600, P=P, zs=zs).Psats()[0], 4557099.181299873)

    assert_close(liquid_ABC.to(T=600, P=P, zs=zs).Psats()[0], 4559674.018096333)
    
    

def test_GibbsExcessLiquid_dHS_dT_low():
    T, P, zs = 100.0, 1e5, [1.0]
    constants = ChemicalConstantsPackage(Tms=[179.2], Tbs=[383.75], Tcs=[591.75], Pcs=[4108000.0], omegas=[0.257], MWs=[92.13842], CASs=['108-88-3'], names=[u'toluene'])
    VaporPressures = [VaporPressure(best_fit=(178.01, 591.74, [-8.638045111752356e-20, 2.995512203611858e-16, -4.5148088801006036e-13, 3.8761537879200513e-10, -2.0856828984716705e-07, 7.279010846673517e-05, -0.01641020023565049, 2.2758331029405516, -146.04484159879843]))]
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [-9.48396765770823e-21, 4.444060985512694e-17, -8.628480671647472e-14, 8.883982004570444e-11, -5.0893293251198045e-08, 1.4947108372371731e-05, -0.0015271248410402886, 0.19186172941013854, 30.797883940134057]))]
    VolumeLiquids = [VolumeLiquid(best_fit=(178.01, 581.75, [2.2801490297347937e-23, -6.411956871696508e-20, 7.723152902379232e-17, -5.197203733189603e-14, 2.1348482785660093e-11, -5.476649499770259e-09, 8.564670053875876e-07, -7.455178589434267e-05, 0.0028545812080104068]))]
    correlations = PropertyCorrelationPackage(constants, VolumeLiquids=VolumeLiquids, VaporPressures=VaporPressures, HeatCapacityGases=HeatCapacityGases, skip_missing=True)
    liquid = GibbsExcessLiquid(VaporPressures=correlations.VaporPressures, 
                               HeatCapacityGases=correlations.HeatCapacityGases,
                               VolumeLiquids=correlations.VolumeLiquids,
                               use_phis_sat=False, use_Poynting=True, T=T, P=P, zs=zs)
    liquid = liquid.to(T=10.0, P=P, zs=zs)
    assert_close(liquid.Psats()[0], 1.8250740791522587e-269)
    assert_close(liquid.S(), -463.15806679753285, rtol=1e-12)
    assert_close(liquid.dS_dT(), 9.368833868082978, rtol=1e-12)
    assert_close(liquid.H(), -73061.5146569193, rtol=1e-12)
    assert_close(liquid.dH_dT(), 93.68833868183933, rtol=1e-12)
    
    liquid = liquid.to(T=8.0, P=P, zs=zs)
    assert_close(liquid.S(), -484.0343032579679, rtol=1e-12)
    assert_close(liquid.dS_dT(), 11.67894683998161, rtol=1e-12)
    assert_close(liquid.H(), -73248.63457031998, rtol=1e-12)
    assert_allclose(liquid.dH_dT(), 93.43157471985432, rtol=1e-12)
    assert liquid.Psats()[0] == 0.0
    
    # used to return inf but not error - now check for infinity
    liquid = liquid.to(T=8.7, P=P, zs=zs)
    assert_close(liquid.S(), -476.1934077017887, rtol=1e-12)
    assert_close(liquid.dS_dT(), 10.749591046689055, rtol=1e-12)
    assert_close(liquid.H(), -73183.20101443084, rtol=1e-12)
    assert_allclose(liquid.dH_dT(), 93.52144210619554, rtol=1e-12) # used to be nan
    
    # Point where vapor pressure was so low the calculation was not erroring
    # but was failing for floating point errors
    liquid = liquid.to(T=16.010610610610595, P=P, zs=zs)
    assert_allclose(liquid.dS_dT(), 5.899836993871634, rtol=1e-12)
    assert_allclose(liquid.dH_dT(), 94.45999277445732, rtol=1e-12)



def test_EOSGas_phis():
    # Acetone, chloroform, methanol
    T = 331.42
    P = 90923
    zs = [0.229, 0.175, 0.596]
    
    eos_kwargs = {'Pcs': [4700000.0, 5330000.0, 8084000.0],
     'Tcs': [508.1, 536.2, 512.5],
     'omegas': [0.309, 0.21600000000000003, 0.5589999999999999],
     'kijs': [[0, 0.038, 0.08], [0.038, 0, 0.021], [0.08, 0.021, 0]],
    }
    
    HeatCapacityGases = [HeatCapacityGas(best_fit=(200.0, 1000.0, [-1.3320002425347943e-21, 6.4063345232664645e-18, -1.251025808150141e-14, 1.2265314167534311e-11, -5.535306305509636e-09, -4.32538332013644e-08, 0.0010438724775716248, -0.19650919978971002, 63.84239495676709])),
     HeatCapacityGas(best_fit=(200.0, 1000.0, [1.5389278550737367e-21, -8.289631533963465e-18, 1.9149760160518977e-14, -2.470836671137373e-11, 1.9355882067011222e-08, -9.265600540761629e-06, 0.0024825718663005762, -0.21617464276832307, 48.149539665907696])),
     HeatCapacityGas(best_fit=(50.0, 1000.0, [2.3511458696647882e-21, -9.223721411371584e-18, 1.3574178156001128e-14, -8.311274917169928e-12, 4.601738891380102e-10, 1.78316202142183e-06, -0.0007052056417063217, 0.13263597297874355, 28.44324970462924]))]
    
    gas = EOSGas(PRMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    
    lnphis_expect = [-0.02360432649642419, -0.024402271514780954, -0.016769813943198587]
    assert_allclose(gas.lnphis(), lnphis_expect, rtol=1e-12)
    
    phis_expect = [0.9766720765776962, 0.9758930568084294, 0.9833700166511827]
    assert_allclose(gas.phis(), phis_expect, rtol=1e-12)
    
    fugacities_expect = [20335.64774507632, 15527.946770733744, 53288.92740628939]
    assert_allclose(gas.fugacities(), fugacities_expect, rtol=1e-12)
    
    dlnphis_dT_expect = [0.0001969437889400412, 0.0001955309568834383, 0.00014847122768410804]
    assert_allclose(gas.dlnphis_dT(), dlnphis_dT_expect, rtol=1e-12)
    
    dphis_dT_expect = [0.00019234949931314953, 0.00019081730321365582, 0.00014600215363994287]
    assert_allclose(gas.dphis_dT(), dphis_dT_expect, rtol=1e-12)
    
    dfugacities_dT_expect = [4.004979517465334, 3.036194290516665, 7.911872473981097]
    assert_allclose(gas.dfugacities_dT(), dfugacities_dT_expect, rtol=1e-12)
    
    dlnphis_dP_expect = [-2.6201216188562436e-07, -2.709988856769895e-07, -1.857038475967749e-07]
    assert_allclose(gas.dlnphis_dP(), dlnphis_dP_expect, rtol=1e-12)
    
    dphis_dP_expect = [-2.558999622374442e-07, -2.644659309349954e-07, -1.8261559570342924e-07]
    assert_allclose(gas.dphis_dP(), dphis_dP_expect, rtol=1e-12)
    
    dfugacities_dP_expect = [0.21832971850726046, 0.16657322866975469, 0.5761925710704517]
    assert_allclose(gas.dfugacities_dP(), dfugacities_dP_expect, rtol=1e-12)

    assert_allclose(gas.H(), 1725.7273210879043, rtol=1e-12)
    assert_allclose(gas.S(), 14.480694885134456, rtol=1e-12)
    assert_allclose(gas.Cp(), 58.748474752042945, rtol=1e-12)
    assert_allclose(gas.dH_dT(), gas.Cp(), rtol=1e-12)
    assert_allclose(gas.dH_dP(), -0.0017158255316092434, rtol=1e-12)
    assert_allclose(gas.dS_dT(), 0.17726291337892383, rtol=1e-12)
    assert_allclose(gas.dS_dP(), -9.480886482495667e-05, rtol=1e-12)
    
    dH_dzs_expect = [2227.672637816117, 1886.132133010868, 1210.163163133309]
    assert_allclose(gas.dH_dzs(), dH_dzs_expect, rtol=1e-12)
    dS_dzs_expect = [11.452747620043832, 12.611417881165302, 0.2036373977480378]
    assert_allclose(gas.dS_dzs(), dS_dzs_expect, rtol=1e-12)
    
    # Volumetric properties - should be implemented in the model only
    assert_allclose(gas.V(), 0.029705728448677898, rtol=1e-12)
    assert_allclose(gas.dP_dT(), 284.342003076555, rtol=1e-12)
    assert_allclose(gas.dP_dV(), -2999107.769105018, rtol=1e-12)
    assert_allclose(gas.d2P_dT2(), -0.009887846156943235, rtol=1e-12)
    assert_allclose(gas.d2P_dV2(), 197784608.40171462, rtol=1e-12)
    assert_allclose(gas.d2P_dTdV(), -9721.251806049266, rtol=1e-12)
    
    # Volumetric properties - base class
    assert_allclose(gas.Z(), 0.9801692315172096, rtol=1e-12)
    assert_allclose(gas.rho(), 33.66354074527018, rtol=1e-12)
    assert_allclose(gas.dT_dP(), 0.0035168915924488455, rtol=1e-12)
    assert_allclose(gas.dV_dT(), 9.480886482495666e-05, rtol=1e-12)
    assert_allclose(gas.dV_dP(), -3.334324995925092e-07, rtol=1e-12)
    assert_allclose(gas.dT_dV(), 10547.536898013452, rtol=1e-12)
    assert_allclose(gas.d2V_dP2(), 7.331895665172319e-12, rtol=1e-12)
    assert_allclose(gas.d2T_dP2(), 4.301091137792481e-10, rtol=1e-12)
    assert_allclose(gas.d2T_dV2(), 29492.455975795572, rtol=1e-12)
    assert_allclose(gas.d2V_dT2(), -2.513377829277684e-08, rtol=1e-12)
    assert_allclose(gas.d2V_dPdT(), -1.003984034506695e-09, rtol=1e-12)
    assert_allclose(gas.d2T_dPdV(), 0.12152750389888099, rtol=1e-12)
    # aliases
    assert_allclose(gas.d2V_dTdP(), gas.d2V_dPdT())
    assert_allclose(gas.d2T_dPdV(), gas.d2T_dVdP())
    assert_allclose(gas.d2P_dVdT(), gas.d2P_dTdV())
    # Compressibility factor
    assert_allclose(gas.dZ_dT(), 0.00017082651132311415, rtol=1e-12)
    assert_allclose(gas.dZ_dP(), -2.2171553318823896e-07, rtol=1e-12)
    
    # Derived properties
    assert_allclose(gas.PIP(), 0.9434309912868786, rtol=1e-12)
    assert_allclose(gas.kappa(), 1.1224518535829717e-05, rtol=1e-12)
    assert_allclose(gas.beta(), 0.0031916020840477414, rtol=1e-12)
    assert_allclose(gas.Joule_Thomson(), 2.9206299207786268e-05, rtol=1e-12)
    assert_allclose(gas.speed_of_sound(), 55.867443841933685, rtol=1e-12)
    assert_allclose(gas.speed_of_sound(), (gas.dP_drho_S())**0.5, rtol=1e-11)
    
    # Molar density
    assert_allclose(gas.dP_drho(), 2646.5035764210666, rtol=1e-12)
    assert_allclose(gas.drho_dP(), 0.00037785703707694405, rtol=1e-12)
    assert_allclose(gas.d2P_drho2(), -3.2210736519363414, rtol=1e-12)
    assert_allclose(gas.d2rho_dP2(), 1.737733604711968e-10, rtol=1e-12)
    assert_allclose(gas.dT_drho(), -9.30746617730105, rtol=1e-12)
    assert_allclose(gas.d2T_drho2(), 0.5759354067635106, rtol=1e-12)
    assert_allclose(gas.drho_dT(), -0.10744062679903038, rtol=1e-12)
    assert_allclose(gas.d2rho_dT2(), 0.0007142979083006338, rtol=1e-12)
    assert_allclose(gas.d2P_dTdrho(), 8.578327173510202, rtol=1e-12)
    assert_allclose(gas.d2T_dPdrho(), -0.00010723955204780491, rtol=1e-12)
    assert_allclose(gas.d2rho_dPdT(), -1.274189795242708e-06, rtol=1e-12)
    
    # ideal gas heat capacity functions
    # Special speed-heavy functions are implemented, so tests are good.
    Ts = [25, 75, 200, 500, 1000, 2000]
    Cps_expect = [[40.07347056476225, 33.29375955093512, 31.648314772557875],
     [45.85126998195463, 39.28949465629621, 35.173569709777134],
     [60.29576852493555, 54.27883241969893, 39.860887753971014],
     [107.85718893790086, 80.57497980236016, 59.60897906926993],
     [162.03590079225324, 95.5180597032743, 89.53718866129503],
     [235.64700575314473, 111.94330438696761, 133.75492691926814]]
    
    integrals_expect = [[-15359.743127401309, -13549.348836281308, -10504.31342159649],
     [-13211.624613733387, -11734.767481100524, -8829.670918204232],
     [-6577.434707052751, -5886.747038850828, -4113.998603256549],
     [18460.582821423024, 14891.995003616028, 10416.929377837709],
     [87563.90176282992, 59654.61279312357, 48496.162006301776],
     [286405.35503552883, 163385.2948382445, 160142.21979658338]]
    integrals_over_T_expect = [[-124.11377728159405, -107.78348964807205, -89.75780643024278],
     [-77.48455137296759, -68.50431529726663, -53.31873830843409],
     [-26.568337973571715, -23.79988041589195, -16.67690619528966],
     [46.53789612349661, 37.80485397009687, 26.33993249405455],
     [140.16601782591798, 99.2695080821947, 77.9324862384278],
     [275.0685207089067, 170.51771449925985, 153.56327376798978]]
    
    dCps_expect = [[0.11555598834384742, 0.11991470210722174, 0.07548394100635737], [0.11555598834384742, 0.11991470210722174, 0.056589692276255196], [0.1155559883438474, 0.11991470210722148, 0.0349394761861727], [0.15194986052287612, 0.05385782617451507, 0.08087587202769089], [0.07361110496090048, 0.016425244683690856, 0.044217738257974225], [0.07361110496089149, 0.016425244683693302, 0.04421773825797312]]
    
    
    integrals_calc = []
    integrals_over_T_calc = []
    Cps_calc = []
    dCps_dT_calc = []
    for i, T in enumerate(Ts):
        gas2 = gas.to_TP_zs(T=T, P=P, zs=zs)
        assert gas2.Cpgs_locked
        Cps_calc.append(gas2.Cpigs_pure())
        integrals_calc.append(gas2.Cpig_integrals_pure())
        integrals_over_T_calc.append(gas2.Cpig_integrals_over_T_pure())
        dCps_dT_calc.append(gas2.dCpigs_dT_pure())
    
    assert_allclose(Cps_expect, Cps_calc)
    assert_allclose(integrals_expect, integrals_calc)
    assert_allclose(integrals_over_T_expect, integrals_over_T_calc)
    assert_allclose(dCps_expect, dCps_dT_calc)
    
    assert_close(gas.S_phi_consistency(), 0, atol=1e-13)
    assert_close(gas.H_phi_consistency(), 0, atol=1e-13)
    assert_close(gas.G_phi_consistency(), 0, atol=1e-13)
    assert_close(gas.V_phi_consistency(), 0, atol=1e-13)
    assert_close(gas.V_from_phi(), gas.V(), rtol=1e-13)

def test_chemical_potential():
    T, P = 200.0, 1e5
    zs = [0.229, 0.175, 0.596]
    
    eos_kwargs = {'Pcs': [4700000.0, 5330000.0, 8084000.0],
     'Tcs': [508.1, 536.2, 512.5],
     'omegas': [0.309, 0.21600000000000003, 0.5589999999999999],
    }
    
    HeatCapacityGases = [HeatCapacityGas(best_fit=(200.0, 1000.0, [-1.3320002425347943e-21, 6.4063345232664645e-18, -1.251025808150141e-14, 1.2265314167534311e-11, -5.535306305509636e-09, -4.32538332013644e-08, 0.0010438724775716248, -0.19650919978971002, 63.84239495676709])),
     HeatCapacityGas(best_fit=(200.0, 1000.0, [1.5389278550737367e-21, -8.289631533963465e-18, 1.9149760160518977e-14, -2.470836671137373e-11, 1.9355882067011222e-08, -9.265600540761629e-06, 0.0024825718663005762, -0.21617464276832307, 48.149539665907696])),
     HeatCapacityGas(best_fit=(50.0, 1000.0, [2.3511458696647882e-21, -9.223721411371584e-18, 1.3574178156001128e-14, -8.311274917169928e-12, 4.601738891380102e-10, 1.78316202142183e-06, -0.0007052056417063217, 0.13263597297874355, 28.44324970462924]))]
    
    Hfs = [-216070.0, -103510.0, -200700.0]
    Sfs = [-216.5, -110.0, -129.8]
    Gfs = [-151520.525, -70713.5, -162000.13]
    
    liquid = EOSLiquid(PRMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, Hfs=Hfs,
                       Sfs=Sfs, Gfs=Gfs, T=T, P=P, zs=zs)
    mu_r_exp = [-188705.73988392908, -97907.9761772734, -193308.17514525697]
    mu_r_calc = liquid.chemical_potential()
    assert_allclose(mu_r_exp, mu_r_calc, rtol=1e-9)
    '''#Derived with:
    from sympy import *
    T = symbols('T')
    zs = z0, z1, z2 = symbols('z0, z1, z2')
    Hb = symbols('Hbase', cls=Function)
    Hbase = Hb(z0, z1, z2)
    Hfs = Hf0, Hf1, Hf2 = symbols('Hf0, Hf1, Hf2')
    for zi, Hf in zip(zs, Hfs):
        Hbase += zi*Hf
    Sb = symbols('Sbase', cls=Function)
    Sbase = Sb(z0, z1, z2)
    Sfs = Sf0, Sf1, Sf2 = symbols('Sf0, Sf1, Sf2')
    for zi, Sf in zip(zs, Sfs):
        Sbase += zi*Sf
    
    G = Hbase - T*Sbase
    diff(G, z0)
    '''
    
    
    
    # Random gamma example
    gammas_expect = [1.8877873731435573, 1.52276935445383, 1.5173639948878495]
    assert_allclose(liquid.gammas(), gammas_expect, rtol=1e-12)
    
    gammas_parent = super(EOSLiquid, liquid).gammas()
    assert_allclose(gammas_parent, gammas_expect, rtol=1e-12)
    
    
def test_EOSGas_volume_HSGUA_derivatives():
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [2.3511458696647882e-21, -9.223721411371584e-18, 1.3574178156001128e-14, -8.311274917169928e-12, 
                                                                  4.601738891380102e-10, 1.78316202142183e-06, -0.0007052056417063217, 0.13263597297874355, 28.44324970462924])), ]
    kwargs = dict(eos_kwargs=dict(Tcs=[512.5], Pcs=[8084000.0], omegas=[.559]),
                 HeatCapacityGases=HeatCapacityGases)
    gas = EOSGas(PRMIX, T=330, P=1e5, zs=[1], **kwargs)
    
    dH_dT_V_num = derivative(lambda T: gas.to(V=gas.V(), T=T, zs=gas.zs).H(), gas.T, dx=gas.T*1e-6)
    assert_allclose(dH_dT_V_num, gas.dH_dT_V(), rtol=1e-8)
    
    dH_dP_V_num = derivative(lambda P: gas.to(V=gas.V(), P=P, zs=gas.zs).H(), gas.P, dx=gas.P*1e-7)
    assert_allclose(dH_dP_V_num, gas.dH_dP_V(), rtol=1e-8)
    
    dH_dV_T_num = derivative(lambda V: gas.to(V=V, T=gas.T, zs=gas.zs).H(), gas.V(), dx=gas.V()*2e-7)
    assert_allclose(dH_dV_T_num, gas.dH_dV_T(), rtol=1e-8)
    
    dH_dV_P_num = derivative(lambda V: gas.to(V=V, P=gas.P, zs=gas.zs).H(), gas.V(), dx=gas.V()*1e-7)
    assert_allclose(dH_dV_P_num, gas.dH_dV_P(), rtol=1e-8)    
    
    
    dS_dT_V_num = derivative(lambda T: gas.to(V=gas.V(), T=T, zs=gas.zs).S(), gas.T, dx=gas.T*1e-8)
    assert_allclose(gas.dS_dT_V(), dS_dT_V_num, rtol=1e-7)
    
    dS_dP_V_num = derivative(lambda P: gas.to(V=gas.V(), P=P, zs=gas.zs).S(), gas.P, dx=gas.P*1e-7)
    assert_allclose(gas.dS_dP_V(), dS_dP_V_num, rtol=1e-7)
    
    dS_dV_T_num = derivative(lambda V: gas.to(V=V, T=gas.T, zs=gas.zs).S(), gas.V(), dx=gas.V()*1e-7)
    assert_allclose(gas.dS_dV_T(), dS_dV_T_num, rtol=1e-7)
    
    dS_dV_P_num = derivative(lambda V: gas.to(V=V, P=gas.P, zs=gas.zs).S(), gas.V(), dx=gas.V()*1e-7)
    assert_allclose(gas.dS_dV_P(), dS_dV_P_num, rtol=1e-7)
    

    dG_dT_V_num = derivative(lambda T: gas.to(V=gas.V(), T=T, zs=gas.zs).G(), gas.T, dx=gas.T*1e-8)
    assert_allclose(gas.dG_dT_V(), dG_dT_V_num, rtol=1e-7)
    
    dG_dP_V_num = derivative(lambda P: gas.to(V=gas.V(), P=P, zs=gas.zs).G(), gas.P, dx=gas.P*1e-6)
    assert_allclose(gas.dG_dP_V(), dG_dP_V_num, rtol=1e-7)
    
    dG_dV_T_num = derivative(lambda V: gas.to(V=V, T=gas.T, zs=gas.zs).G(), gas.V(), dx=gas.V()*1e-6)
    assert_allclose(gas.dG_dV_T(), dG_dV_T_num, rtol=1e-7)
    
    dG_dV_P_num = derivative(lambda V: gas.to(V=V, P=gas.P, zs=gas.zs).G(), gas.V(), dx=gas.V()*1e-6)
    assert_allclose(gas.dG_dV_P(), dG_dV_P_num, rtol=1e-7)
    
    dU_dT_V_num = derivative(lambda T: gas.to(V=gas.V(), T=T, zs=gas.zs).U(), gas.T, dx=gas.T*1e-8)
    assert_allclose(gas.dU_dT_V(), dU_dT_V_num)
    
    dU_dP_V_num = derivative(lambda P: gas.to(V=gas.V(), P=P, zs=gas.zs).U(), gas.P, dx=gas.P*1e-8)
    assert_allclose(gas.dU_dP_V(), dU_dP_V_num)
    
    dU_dV_T_num = derivative(lambda V: gas.to(V=V, T=gas.T, zs=gas.zs).U(), gas.V(), dx=gas.V()*1e-8)
    assert_allclose(gas.dU_dV_T(), dU_dV_T_num)
    
    dU_dV_P_num = derivative(lambda V: gas.to(V=V, P=gas.P, zs=gas.zs).U(), gas.V(), dx=gas.V()*1e-8)
    assert_allclose(gas.dU_dV_P(), dU_dV_P_num)
    
    dA_dT_V_num = derivative(lambda T: gas.to(V=gas.V(), T=T, zs=gas.zs).A(), gas.T, dx=gas.T*1e-8)
    assert_allclose(gas.dA_dT_V(), dA_dT_V_num)
    
    dA_dP_V_num = derivative(lambda P: gas.to(V=gas.V(), P=P, zs=gas.zs).A(), gas.P, dx=gas.P*1e-7)
    assert_allclose(gas.dA_dP_V(), dA_dP_V_num)
    
    dA_dV_T_num = derivative(lambda V: gas.to(V=V, T=gas.T, zs=gas.zs).A(), gas.V(), dx=gas.V()*1e-8)
    assert_allclose(gas.dA_dV_T(), dA_dV_T_num)
    
    dA_dV_P_num = derivative(lambda V: gas.to(V=V, P=gas.P, zs=gas.zs).A(), gas.V(), dx=gas.V()*1e-8)
    assert_allclose(gas.dA_dV_P(), dA_dV_P_num)
    
    
def test_CoolPropPhase_PR_pure():
    T, P = 299.0, 1e5
    CPP = CoolPropPhase('PR', 'nHexane', T=T, P=P)
    # Make a duplicate fluid using the parameters from CoolProp
    Tc, Pc, omega = CPP.AS.T_critical(), CPP.AS.p_critical(), CPP.AS.acentric_factor()

    # These have been tested by varing the PRMIX coefficients - they are correct,
    # and can get much closer as well when that is the case
    eos = PRMIX(Tcs=[Tc], Pcs=[Pc], omegas=[omega], T=T, P=P, zs=[1])
    assert_allclose(CPP.V(), eos.V_l, rtol=1e-4)
    assert_allclose(CPP.dP_dT(), eos.dP_dT_l, rtol=3e-4)
    assert_allclose(CPP.dP_dV(), eos.dP_dV_l, rtol=5e-4)
    assert_allclose(CPP.d2P_dT2(), eos.d2P_dT2_l, rtol=2e-4)
    assert_allclose(CPP.d2P_dV2(), eos.d2P_dV2_l, rtol=4e-4)
    assert_allclose(CPP.d2P_dTdV(), eos.d2P_dTdV_l, rtol=5e-4)


def test_CoolPropPhase_Water():
    T, P = 299.0, 1e5
    CPP = CoolPropPhase('HEOS', 'water', T=T, P=P)
    
    # Test the initialization methods
    CPP_TV = CPP.to(T=T, V=CPP.V(), zs=[1.0])
    assert_allclose(CPP_TV.P, P, rtol=1e-8)
    
    CPP_PV = CPP.to(P=P, V=CPP.V(), zs=[1.0])
    assert_allclose(CPP_PV.T, T, rtol=1e-8)
    
    assert_allclose(CPP.H(), 1954.1678289799822)
    assert_allclose(CPP.S(), 6.829644373073796)
    assert_allclose(CPP.G(), CPP.AS.gibbsmolar(), rtol=1e-11)
    assert_allclose(CPP.U(), CPP.AS.umolar(), rtol=1e-11)
    assert_allclose(CPP.A(), CPP.AS.helmholtzmolar(), rtol=1e-9) # This one cannot go lower prec oddly
    
    dH_dT_num = derivative(lambda T: CPP.to(T=T, P=P, zs=[1]).H(), T, dx=.01)
    assert_allclose(CPP.dH_dT(), dH_dT_num)
    
    dH_dP_num = derivative(lambda P: CPP.to(T=T, P=P, zs=[1]).H(), P, dx=P*2e-5, order=7)
    assert_allclose(CPP.dH_dP(), dH_dP_num, rtol=5e-6)
    
    d2H_dT2_num = derivative(lambda T: CPP.to(T=T, P=P, zs=[1]).dH_dT(), T, dx=T*1e-5, n=1)
    assert_allclose(CPP.d2H_dT2(), d2H_dT2_num)
    
    d2H_dP2_num = derivative(lambda P: CPP.to(T=T, P=P, zs=[1]).dH_dP(), P, dx=P*1e-3, n=1, order=5)
    assert_allclose(CPP.d2H_dP2(), d2H_dP2_num, rtol=5e-6)
    
    d2H_dTdP_num = derivative(lambda T: CPP.to(T=T, P=P, zs=[1]).dH_dP(), T, dx=T*1e-5, n=1)
    assert_allclose(CPP.d2H_dTdP(), d2H_dTdP_num)
    
    dH_dT_V_num = derivative(lambda T: CPP.to(T=T, V=CPP.V(), zs=[1]).H(), T, dx=.001)
    assert_allclose(CPP.dH_dT_V(), dH_dT_V_num)
    
    dH_dP_V_num = derivative(lambda P: CPP.to(P=P, V=CPP.V(), zs=[1]).H(), P, dx=P*3e-5)
    assert_allclose(CPP.dH_dP_V(), dH_dP_V_num, rtol=5e-6)
    
    dH_dV_T_num = derivative(lambda V: CPP.to(T=T, V=V, zs=[1]).H(), CPP.V(), dx=CPP.V()*1e-5)
    assert_allclose(CPP.dH_dV_T(), dH_dV_T_num)
    
    dH_dV_P_num = derivative(lambda V: CPP.to(P=P, V=V, zs=[1]).H(), CPP.V(), dx=CPP.V()*1e-6)
    assert_allclose(CPP.dH_dV_P(), dH_dV_P_num)
    
    dS_dT_num = derivative(lambda T: CPP.to(T=T, P=P, zs=[1]).S(), T, dx=.01)
    assert_allclose(CPP.dS_dT(), dS_dT_num)
    
    dS_dP_num = derivative(lambda P: CPP.to(T=T, P=P, zs=[1]).S(), P, dx=P*2e-4, order=7)
    assert_allclose(CPP.dS_dP(), dS_dP_num, rtol=5e-5)
    
    d2S_dT2_num = derivative(lambda T: CPP.to(T=T, P=P, zs=[1]).dS_dT(), T, dx=T*1e-5, n=1)
    assert_allclose(CPP.d2S_dT2(), d2S_dT2_num)
    
    d2S_dP2_num = derivative(lambda P: CPP.to(T=T, P=P, zs=[1]).dS_dP(), P, dx=P*1e-3, n=1, order=5)
    assert_allclose(CPP.d2S_dP2(), d2S_dP2_num, rtol=5e-6)
    
    d2S_dTdP_num = derivative(lambda T: CPP.to(T=T, P=P, zs=[1]).dS_dP(), T, dx=T*1e-5, n=1)
    assert_allclose(CPP.d2S_dTdP(), d2S_dTdP_num)
    
    dS_dT_V_num = derivative(lambda T: CPP.to(T=T, V=CPP.V(), zs=[1]).S(), T, dx=.001)
    assert_allclose(CPP.dS_dT_V(), dS_dT_V_num)
    
    dS_dP_V_num = derivative(lambda P: CPP.to(P=P, V=CPP.V(), zs=[1]).S(), P, dx=P*3e-5)
    assert_allclose(CPP.dS_dP_V(), dS_dP_V_num, rtol=5e-6)
    
    dS_dV_T_num = derivative(lambda V: CPP.to(T=T, V=V, zs=[1]).S(), CPP.V(), dx=CPP.V()*1e-5)
    assert_allclose(CPP.dS_dV_T(), dS_dV_T_num)
    
    dS_dV_P_num = derivative(lambda V: CPP.to(P=P, V=V, zs=[1]).S(), CPP.V(), dx=CPP.V()*1e-6)
    assert_allclose(CPP.dS_dV_P(), dS_dV_P_num)
    
def test_CoolPropPhase_Transport():
    liq = CoolPropLiquid('HEOS', 'water', T=300, P=1e5, zs=[1.0])
    assert_close(liq.mu(), PropsSI("VISCOSITY", "T", 300, "P", 1e5, "Water"), rtol=1e-12)
    
    gas = CoolPropGas('HEOS', 'water', T=400, P=1e5, zs=[1.0])
    assert_close(gas.mu(), PropsSI("VISCOSITY", "T", 400, "P", 1e5, "Water"), rtol=1e-12)
    
def test_model_hash():
    zs = [0.95, 0.05]
    T, P = 400.0, 1325753.6447835972*.96
    
    constants = ChemicalConstantsPackage(Tcs=[647.14, 615.0], Pcs=[22048320.0, 5100000.0], omegas=[0.344, 0.1869], MWs=[18.01528, 94.19904], CASs=['7732-18-5', '624-92-0'])

    properties = PropertyCorrelationPackage(constants=constants, HeatCapacityGases=[HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                                                                        HeatCapacityGas(best_fit=(273, 1000, [-1.575967061488898e-21, 8.453271073419098e-18, -1.921448640274908e-14, 2.3921686769873392e-11, -1.7525253961492494e-08, 7.512525679465744e-06, -0.0018211688612260338, 0.3869010410224839, 35.590034427486614])),],)
    properties2 = PropertyCorrelationPackage(constants=constants, HeatCapacityGases=[HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                                                                        HeatCapacityGas(best_fit=(273, 1000, [-1.575967061488898e-21, 8.453271073419098e-18, -1.921448640274908e-14, 2.3921686769873392e-11, -1.7525253961492494e-08, 7.512525679465744e-06, -0.0018211688612260338, 0.3869010410224839, 35.590034427486614])),],)
    HeatCapacityGases = properties.HeatCapacityGases
    
    eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas': constants.omegas}
    gas = EOSGas(PRMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    liq = EOSLiquid(PRMIX, dict(eos_kwargs), HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    liq2 = EOSLiquid(PRMIX, eos_kwargs, HeatCapacityGases=properties2.HeatCapacityGases, T=T, P=P, zs=zs)
    liq3 = EOSLiquid(SRKMIX, eos_kwargs, HeatCapacityGases=properties2.HeatCapacityGases, T=T, P=P, zs=zs)
    assert gas.model_hash() != liq.model_hash()
    assert liq2.model_hash() == liq.model_hash()
    assert liq3.model_hash() != liq.model_hash()


def test_dlnfugacities_SRK():
    T = 115.0
    P = 1e6
    zs = [0.4, 0.6]
    
    dlnfugacities_dns_expect = [[1.4378058197970829, -0.9585372131980551],
     [-0.958537213198055, 0.6390248087987035]]
    
    dlnfugacities_dns_l_expect = [[1.1560067098003597, -0.7706711398669063],
     [-0.7706711398669062, 0.5137807599112717]]
    
    HeatCapacityGases = [HeatCapacityGas(best_fit=(50.0, 1000.0, [5.543665000518528e-22, -2.403756749600872e-18, 4.2166477594350336e-15, -3.7965208514613565e-12, 1.823547122838406e-09, -4.3747690853614695e-07, 5.437938301211039e-05, -0.003220061088723078, 33.32731489750759])),
                         HeatCapacityGas(best_fit=(273, 1000, [-1.575967061488898e-21, 8.453271073419098e-18, -1.921448640274908e-14, 2.3921686769873392e-11, -1.7525253961492494e-08, 7.512525679465744e-06, -0.0018211688612260338, 0.3869010410224839, 35.590034427486614])),]
    
    eos_kwargs = {'Pcs': [33.94E5, 46.04E5], 'Tcs': [126.1, 190.6], 'omegas': [0.04, 0.011]}
    gas = EOSGas(SRKMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    liq = EOSLiquid(SRKMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    assert_allclose(gas.dlnfugacities_dns(), dlnfugacities_dns_expect, rtol=1e-9)
    assert_allclose(liq.dlnfugacities_dns(), dlnfugacities_dns_l_expect, rtol=1e-9)
    
    
def test_viscosity_thermal_conductivity():
    constants = ChemicalConstantsPackage(Tcs=[508.1, 536.2, 512.5], Pcs=[4700000.0, 5330000.0, 8084000.0], omegas=[0.309, 0.21600000000000003, 0.5589999999999999],
                                         MWs=[58.07914, 119.37764000000001, 32.04186], CASs=['67-64-1', '67-66-3', '67-56-1'], names=['acetone', 'chloroform', 'methanol'])
    
    HeatCapacityGases = [HeatCapacityGas(best_fit=(200.0, 1000.0, [-1.3320002425347943e-21, 6.4063345232664645e-18, -1.251025808150141e-14, 1.2265314167534311e-11, -5.535306305509636e-09, -4.32538332013644e-08, 0.0010438724775716248, -0.19650919978971002, 63.84239495676709])),
     HeatCapacityGas(best_fit=(200.0, 1000.0, [1.5389278550737367e-21, -8.289631533963465e-18, 1.9149760160518977e-14, -2.470836671137373e-11, 1.9355882067011222e-08, -9.265600540761629e-06, 0.0024825718663005762, -0.21617464276832307, 48.149539665907696])),
     HeatCapacityGas(best_fit=(50.0, 1000.0, [2.3511458696647882e-21, -9.223721411371584e-18, 1.3574178156001128e-14, -8.311274917169928e-12, 4.601738891380102e-10, 1.78316202142183e-06, -0.0007052056417063217, 0.13263597297874355, 28.44324970462924]))]
    
    ViscosityLiquids = [ViscosityLiquid(best_fit=(178.51, 508.09000000000003, [2.8593746556294576e-20, -8.831809032695423e-17, 1.192862144552288e-13, -9.238748704721018e-11, 4.5178055121691235e-08, -1.4450830676420802e-05, 0.0030188274322848108, -0.39502805194488444, 17.918505535499264])),
                        ViscosityLiquid(best_fit=(209.63, 353.2, [1.1006657452874283e-19, -2.78693273821854e-16, 3.121817433044988e-13, -2.0302355776141153e-10, 8.44634485674659e-08, -2.3304265452286684e-05, 0.00426076556873685, -0.49578199836449677, 22.277694951054546])),
                        ViscosityLiquid(best_fit=(175.7, 512.49, [-1.5594529993966785e-18, 3.998467862455612e-15, -4.381896401904306e-12, 2.6713893418127396e-09, -9.85912718968894e-07, 0.00022366768366845858, -0.029947978392505514, 2.0636070644367552, -53.665250988554575])),]
    
    ViscosityGases = [ViscosityGas(best_fit=(329.23, 508.1, [1.8941828276365244e-29, -7.105137785617246e-26, 1.1774297154042727e-22, -1.1282479132608084e-19, 6.840473685242011e-17, -2.656366990949586e-14, 5.678131240835556e-12, 2.58920890679614e-08, -3.7362058625420564e-07])),
                      ViscosityGas(best_fit=(209.63, 1000.0, [1.4755596910272421e-29, -7.947738623851205e-26, 1.832820128910847e-22, -2.349864903550044e-19, 1.8011389200128507e-16, -7.865457394747658e-14, 8.6601377565636e-12, 3.86699451992744e-08, -9.379663436673728e-07])),
                      ViscosityGas(best_fit=(337.63, 500.0, [6.176223694341085e-25, -2.0830721232131668e-21, 3.059975750040745e-18, -2.556041767358262e-15, 1.3272271669202934e-12, -4.3839521826127676e-10, 8.988216138863085e-08, -1.0412854594353523e-05, 0.0005255880487418567]))]
    
    ThermalConductivityGases = [ThermalConductivityGas(best_fit=(329.23, 508.1, [1.374856029316929e-26, -5.504343742972516e-23, 9.996390406875445e-20, -1.0998045210773463e-16, 8.419820230735209e-14, -5.3325177485697514e-11, 1.326338442408566e-07, 1.5412252071649057e-06, -3.752556677217439e-05])),
                                ThermalConductivityGas(best_fit=(334.33, 1000.0, [1.7882799581639057e-27, -1.1580200426336988e-23, 3.3960825823193976e-20, -6.093231538633042e-17, 7.841997808572439e-14, -8.474210717531882e-11, 8.915485885801078e-08, 3.243447514310259e-06, -0.00011076142350832305])),
                                ThermalConductivityGas(best_fit=(337.63, 500.0, [8.987814291965324e-22, -3.1782557641667015e-18, 4.909844083600474e-15, -4.3276628557996325e-12, 2.3804692092103243e-09, -8.369334280151882e-07, 0.00018389977868277303, -0.02305052995889577, 1.2683162659290514])),]
    
    ThermalConductivityLiquids = [ThermalConductivityLiquid(best_fit=(329.23, 508.1, [-2.169902030409515e-31, 6.491435516132496e-28, -8.318195033349147e-25, 5.928645244512013e-22, -2.5469451994770507e-19, 6.645718987018692e-17, -9.961965445286596e-15, -0.00042699999927586345, 0.28779999998602923])),
                                  ThermalConductivityLiquid(best_fit=(209.63, 400.0, [-6.590556798622678e-32, 1.1052627373562177e-28, -6.1836669727271e-26, 2.744732053083117e-24, 1.2240098450807603e-20, -6.135150640499972e-18, 1.3892919737126464e-15, -0.00020230000015730222, 0.17780000000721982])),
                                 ThermalConductivityLiquid(best_fit=(175.61, 460.0, [-2.0427137654192538e-21, 5.397904343028161e-18, -6.3763077367349095e-15, 4.417686780434988e-12, -1.9632755240328655e-09, 5.709120910380979e-07, -0.00010549847813202652, 0.011071902367193028, -0.2719858296092696])),]
    
    VolumeLiquids = [VolumeLiquid(best_fit=(178.51, 498.1, [6.564241965071999e-23, -1.6568522275506375e-19, 1.800261692081815e-16, -1.0988731296761538e-13, 4.118691518070104e-11, -9.701938804617744e-09, 1.4022905458596618e-06, -0.00011362923883050033, 0.0040109650220160956])),
                    VolumeLiquid(best_fit=(209.63, 509.5799999999999, [2.034047306563089e-23, -5.45567626310959e-20, 6.331811062990084e-17, -4.149759318710192e-14, 1.6788970104955462e-11, -4.291900093120011e-09, 6.769385838271721e-07, -6.0166473220815445e-05, 0.0023740769479069054])),
                    VolumeLiquid(best_fit=(175.7, 502.5, [3.5725079384600736e-23, -9.031033742820083e-20, 9.819637959370411e-17, -5.993173551565636e-14, 2.2442465416964825e-11, -5.27776114586072e-09, 7.610461006178106e-07, -6.148574498547711e-05, 0.00216398089328537])),]
    
    VaporPressures = [VaporPressure(best_fit=(178.51, 508.09000000000003, [-1.3233111115238975e-19, 4.2217134794609376e-16, -5.861832547132719e-13, 4.6488594950801467e-10, -2.3199079844570237e-07, 7.548290741523459e-05, -0.015966705328994194, 2.093003523977292, -125.39006100979816])),
                      VaporPressure(best_fit=(207.15, 536.4, [-8.714046553871422e-20, 2.910491615051279e-16, -4.2588796020294357e-13, 3.580003116042944e-10, -1.902612144361103e-07, 6.614096470077095e-05, -0.01494801055978542, 2.079082613726621, -130.24643185169472])),
                      VaporPressure(best_fit=(175.7, 512.49, [-1.446088049406911e-19, 4.565038519454878e-16, -6.278051259204248e-13, 4.935674274379539e-10, -2.443464113936029e-07, 7.893819658700523e-05, -0.016615779444332356, 2.1842496316772264, -134.19766175812708]))]
    
    ViscosityGasMixtureObj = ViscosityGasMixture(ViscosityGases=ViscosityGases)
    ViscosityGasMixtureObj.set_user_method('Simple', forced=True)
    ViscosityLiquidMixtureObj = ViscosityLiquidMixture(ViscosityLiquids=ViscosityLiquids, correct_pressure_pure=False)
    ViscosityLiquidMixtureObj.set_user_method('Simple', forced=True)
    
    ThermalConductivityLiquidMixtureObj = ThermalConductivityLiquidMixture(ThermalConductivityLiquids=ThermalConductivityLiquids)
    ThermalConductivityLiquidMixtureObj.set_user_method('Simple', forced=True)
    
    ThermalConductivityGasMixtureObj = ThermalConductivityGasMixture(ThermalConductivityGases=ThermalConductivityGases)
    ThermalConductivityGasMixtureObj.set_user_method('Simple', forced=True)
    
    correlations = PropertyCorrelationPackage(constants=constants, skip_missing=True, HeatCapacityGases=HeatCapacityGases,
                               ViscosityLiquids=ViscosityLiquids, ViscosityGases=ViscosityGases, 
                               ThermalConductivityGases=ThermalConductivityGases, ThermalConductivityLiquids=ThermalConductivityLiquids,
                               VolumeLiquids=VolumeLiquids, VaporPressures=VaporPressures,
                                ViscosityGasMixtureObj=ViscosityGasMixtureObj, 
                                ViscosityLiquidMixtureObj=ViscosityLiquidMixtureObj,
                              ThermalConductivityGasMixtureObj=ThermalConductivityGasMixtureObj,
                              ThermalConductivityLiquidMixtureObj=ThermalConductivityLiquidMixtureObj)
    
    T, P = 350.0, 1e6
    zs = [0.2, 0.3, 0.5]
    # Simple mixing rule always
    eos_kwargs = {'Pcs': constants.Pcs, 'Tcs': constants.Tcs, 'omegas':constants.omegas}#  'kijs': [[0, 0.038, 0.08], [0.038, 0, 0.021], [0.08, 0.021, 0]]}
    
    # gas point
    phase = EOSGas(PRMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    phase.constants = constants
    phase.correlations = correlations
    assert_close(phase.mu(), 1.1006640924847626e-05, rtol=1e-7)
    assert_close(phase.k(), 0.01591594304085816, rtol=1e-7)
    
    # Gas phase but becomes a liquid property as volume root is liquid
    phase = phase.to(T=T, P=1e7, zs=zs)
    phase.constants = constants
    phase.correlations = correlations
    assert_close(phase.mu(), 0.00028727346628185633, rtol=1e-7)
    assert_close(phase.k(), 0.15487898658770405, rtol=1e-7)
    
    # Liquid point
    phase = EOSLiquid(PRMIX, eos_kwargs, HeatCapacityGases=HeatCapacityGases, T=T, P=P, zs=zs)
    phase.constants = constants
    phase.correlations = correlations
    assert_close(phase.mu(), 0.00028727346628185633, rtol=1e-7)
    assert_close(phase.k(), 0.15487898658770405, rtol=1e-7)
    
    # Liquid point but becomes a gas as volume root is gas
    # Have to increase temperature to make it happen
    phase = phase.to(T=480, P=1e5, zs=zs)
    phase.constants = constants
    phase.correlations = correlations
    assert_close(phase.rho_mass(), 1.602260139151343, rtol=1e-7)
    assert_close(phase.mu(), 1.52014008290963e-05, rtol=1e-7)
    assert_close(phase.k(), 0.028032831809820278, rtol=1e-7)
    
    # Check we can back, phase transition - and the liquid viscosity is higher
    p2 = phase.to(T=480, P=1e7, zs=zs)
    p2.constants = constants
    p2.correlations = correlations
    assert_close(p2.rho_mass(), 675.2127753434202)
    assert phase.mu() < p2.mu()
    # Test the extrapolated liquid thermal conductivity
    # Might break if extrpolation method changes
    assert_close(p2.k(), 0.12412669592158972, rtol=1e-7)
    
    # Ideal gas
    phase = IdealGas(T=T, P=P, zs=zs, HeatCapacityGases=HeatCapacityGases)
    phase.constants = constants
    phase.correlations = correlations
    assert_close(phase.mu(), 1.1006640924847626e-05, rtol=1e-7)
    assert_close(phase.k(), 0.01591594304085816, rtol=1e-7)
    
    # Gibbs excess liquid
    phase = GibbsExcessLiquid(VaporPressures=VaporPressures, VolumeLiquids=VolumeLiquids, 
                     HeatCapacityGases=HeatCapacityGases, use_Poynting=True,
                     use_phis_sat=False,
                     T=T, P=P, zs=zs)
    phase.constants = constants
    phase.correlations = correlations
    assert_close(phase.mu(), 0.00028727346628185633, rtol=1e-7)
    assert_close(phase.k(), 0.15487898658770405, rtol=1e-7)