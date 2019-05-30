"""
Incompressible SPH
"""
import numpy
from numpy import sqrt
from compyle.api import declare
from pysph.sph.scheme import Scheme, add_bool_argument
from pysph.base.utils import get_particle_array
from pysph.sph.integrator import Integrator
from pysph.sph.integrator_step import IntegratorStep
from pysph.sph.equation import Equation, Group, MultiStageEquations


def get_particle_array_isph(constants=None, **props):
    isph_props = [
        'u0', 'v0', 'w0', 'x0', 'y0', 'z0', 'rho0', 'diag', 'odiag',
        'pk', 'rhs', 'pdiff', 'wg', 'vf', 'vg', 'ug', 'wij', 'wf', 'uf',
        'V', 'au', 'av', 'aw', 'dt_force', 'dt_cfl', 'vmag',
        'auhat', 'avhat', 'awhat', 'p0', 'uhat', 'vhat', 'what',
        'uhat0', 'vhat0', 'what0'
    ]

    pa = get_particle_array(
        additional_props=isph_props, constants=constants, **props
    )

    pa.add_output_arrays(['p', 'V', 'vmag', 'p0'])
    return pa


class PECIntegrator(Integrator):
    def one_timestep(self, t, dt):
        self.initialize()

        self.compute_accelerations(0)

        self.stage1()

        self.update_domain()

        self.do_post_stage(0.5*dt, 1)

        self.compute_accelerations(1)

        self.stage2()

        self.update_domain()

        self.do_post_stage(dt, 2)

    def initial_acceleration(self, t, dt):
        pass


class ISPHStep(IntegratorStep):
    def initialize(self, d_idx, d_x, d_y, d_z, d_x0, d_y0, d_z0, d_u, d_v,
                   d_w, d_u0, d_v0, d_w0, dt):
        d_x0[d_idx] = d_x[d_idx]
        d_y0[d_idx] = d_y[d_idx]
        d_z0[d_idx] = d_z[d_idx]

        d_u0[d_idx] = d_u[d_idx]
        d_v0[d_idx] = d_v[d_idx]
        d_w0[d_idx] = d_w[d_idx]

    def stage1(self, d_idx, d_x, d_y, d_z, d_u, d_v, d_w, d_au, d_av,
               d_aw, dt):
        d_x[d_idx] += dt*d_u[d_idx]
        d_y[d_idx] += dt*d_v[d_idx]
        d_z[d_idx] += dt*d_w[d_idx]

        d_u[d_idx] += dt*d_au[d_idx]
        d_v[d_idx] += dt*d_av[d_idx]
        d_w[d_idx] += dt*d_aw[d_idx]

    def stage2(self, d_idx, d_x, d_y, d_z, d_u, d_v, d_w, d_u0, d_v0, d_w0,
               d_x0, d_y0, d_z0, d_au, d_av, d_aw, d_vmag, d_dt_cfl,
               d_dt_force, dt):
        d_u[d_idx] += dt*d_au[d_idx]
        d_v[d_idx] += dt*d_av[d_idx]
        d_w[d_idx] += dt*d_aw[d_idx]

        d_x[d_idx] = d_x0[d_idx] + 0.5*dt * (d_u[d_idx] + d_u0[d_idx])
        d_y[d_idx] = d_y0[d_idx] + 0.5*dt * (d_v[d_idx] + d_v0[d_idx])
        d_z[d_idx] = d_z0[d_idx] + 0.5*dt * (d_w[d_idx] + d_w0[d_idx])

        d_vmag[d_idx] = sqrt(d_u[d_idx]*d_u[d_idx] + d_v[d_idx]*d_v[d_idx] +
                             d_w[d_idx]*d_w[d_idx])

        d_dt_cfl[d_idx] = 2.0*d_vmag[d_idx]

        au = (d_u[d_idx] - d_u0[d_idx])/dt
        av = (d_v[d_idx] - d_v0[d_idx])/dt
        aw = (d_w[d_idx] - d_w0[d_idx])/dt

        d_dt_force[d_idx] = 2*(au*au + av*av + aw*aw)


class ISPHDIStep(ISPHStep):
    def stage1(self, d_idx, d_x, d_y, d_z, d_u, d_v, d_w, d_au, d_av,
               d_aw, dt):
        d_u[d_idx] += dt*d_au[d_idx]
        d_v[d_idx] += dt*d_av[d_idx]
        d_w[d_idx] += dt*d_aw[d_idx]

        d_x[d_idx] += dt*d_u[d_idx]
        d_y[d_idx] += dt*d_v[d_idx]
        d_z[d_idx] += dt*d_w[d_idx]


class ISPHGTVFStep(IntegratorStep):
    def initialize(self, d_idx, d_x, d_y, d_z, d_x0, d_y0, d_z0, d_u, d_v,
                   d_w, d_u0, d_v0, d_w0, d_uhat, d_vhat, d_what, d_uhat0,
                   d_vhat0, d_what0):
        d_x0[d_idx] = d_x[d_idx]
        d_y0[d_idx] = d_y[d_idx]
        d_z0[d_idx] = d_z[d_idx]

        d_u0[d_idx] = d_u[d_idx]
        d_v0[d_idx] = d_v[d_idx]
        d_w0[d_idx] = d_w[d_idx]

        d_uhat0[d_idx] = d_uhat[d_idx]
        d_vhat0[d_idx] = d_vhat[d_idx]
        d_what0[d_idx] = d_what[d_idx]

    def stage1(self, d_idx, d_x, d_y, d_z, d_u, d_v, d_w, d_au, d_av,
               d_aw, d_uhat, d_vhat, d_what, dt):
        d_x[d_idx] += dt*d_uhat[d_idx]
        d_y[d_idx] += dt*d_vhat[d_idx]
        d_z[d_idx] += dt*d_what[d_idx]

        d_u[d_idx] += dt*d_au[d_idx]
        d_v[d_idx] += dt*d_av[d_idx]
        d_w[d_idx] += dt*d_aw[d_idx]

    def stage2(self, d_idx, d_x, d_y, d_z, d_u, d_v, d_w, d_x0, d_y0, d_z0,
               d_au, d_av, d_aw, d_uhat, d_vhat, d_what, d_auhat, d_avhat,
               d_awhat, d_uhat0, d_vhat0, d_what0, d_vmag, d_dt_cfl, dt):
        d_u[d_idx] += dt*d_au[d_idx]
        d_v[d_idx] += dt*d_av[d_idx]
        d_w[d_idx] += dt*d_aw[d_idx]

        d_vmag[d_idx] = sqrt(d_u[d_idx]*d_u[d_idx] + d_v[d_idx]*d_v[d_idx] +
                             d_w[d_idx]*d_w[d_idx])
        d_dt_cfl[d_idx] = 2.0*d_vmag[d_idx]

        d_uhat[d_idx] = d_u[d_idx] + dt*d_auhat[d_idx]
        d_vhat[d_idx] = d_v[d_idx] + dt*d_avhat[d_idx]
        d_what[d_idx] = d_w[d_idx] + dt*d_awhat[d_idx]

        d_x[d_idx] = d_x0[d_idx] + 0.5*dt * (d_uhat[d_idx] + d_uhat0[d_idx])
        d_y[d_idx] = d_y0[d_idx] + 0.5*dt * (d_vhat[d_idx] + d_vhat0[d_idx])
        d_z[d_idx] = d_z0[d_idx] + 0.5*dt * (d_what[d_idx] + d_what0[d_idx])


class MomentumEquationBodyForce(Equation):
    def __init__(self, dest, sources, gx=0.0, gy=0.0, gz=0.0):
        self.gx = gx
        self.gy = gy
        self.gz = gz
        super(MomentumEquationBodyForce, self).__init__(dest, sources)

    def post_loop(self, d_idx, d_au, d_av, d_aw):
        d_au[d_idx] += self.gx
        d_av[d_idx] += self.gy
        d_aw[d_idx] += self.gz


class VelocityDivergence(Equation):
    def initialize(self, d_idx, d_rhs, d_pk, d_p):
        d_rhs[d_idx] = 0.0
        d_pk[d_idx] = d_p[d_idx]

    def loop(self, d_idx, s_idx, s_m, s_rho, d_rhs, dt, VIJ, DWIJ):
        Vj = s_m[s_idx] / s_rho[s_idx]
        vdotdwij = VIJ[0]*DWIJ[0] + VIJ[1]*DWIJ[1] + VIJ[2]*DWIJ[2]
        d_rhs[d_idx] += -Vj * vdotdwij / dt


class VelocityDivergenceSolid(Equation):
    def loop(self, d_idx, s_idx, s_m, s_rho, d_rhs, dt, d_u, d_v, d_w, s_ug,
             s_vg, s_wg, DWIJ):
        Vj = s_m[s_idx] / s_rho[s_idx]
        uij = d_u[d_idx] - s_ug[s_idx]
        vij = d_v[d_idx] - s_vg[s_idx]
        wij = d_w[d_idx] - s_wg[s_idx]
        vdotdwij = uij*DWIJ[0] + vij*DWIJ[1] + wij*DWIJ[2]
        d_rhs[d_idx] += -Vj * vdotdwij / dt


class DensityInvariance(Equation):
    def __init__(self, dest, sources, rho0):
        self.rho0 = rho0
        super(DensityInvariance, self).__init__(dest, sources)

    def post_loop(self, d_idx, d_rho, d_rhs, dt):
        rho0 = self.rho0
        d_rhs[d_idx] = (rho0 - d_rho[d_idx]) / (dt*dt*rho0)


class PressureCoeffMatrixIterative(Equation):
    def initialize(self, d_idx, d_diag, d_odiag):
        d_diag[d_idx] = 0.0
        d_odiag[d_idx] = 0.0

    def loop(self, d_idx, s_idx, s_m, d_rho, s_rho, d_diag, d_odiag, s_pk, XIJ,
             DWIJ, R2IJ, EPS):
        rhoij = (s_rho[s_idx] + d_rho[d_idx])
        rhoij2_1 = 1.0/(rhoij*rhoij)

        xdotdwij = XIJ[0]*DWIJ[0] + XIJ[1]*DWIJ[1] + XIJ[2]*DWIJ[2]

        fac = 8.0 * s_m[s_idx] * rhoij2_1 * xdotdwij / (R2IJ + EPS)

        d_diag[d_idx] += fac
        d_odiag[d_idx] += -fac * s_pk[s_idx]


class PPESolve(Equation):
    def __init__(self, dest, sources, rho0, rho_cutoff=0.8, omega=0.5,
                 tolerance=0.05):
        self.rho0 = rho0
        self.rho_cutoff = rho_cutoff
        self.conv = 0.0
        self.omega = omega
        self.tolerance = tolerance
        super(PPESolve, self).__init__(dest, sources)

    def post_loop(self, d_idx, d_p, d_pk, d_rhs, d_odiag, d_diag, d_pdiff, d_V,
                  d_m):
        omega = self.omega
        rho = d_V[d_idx] * d_m[d_idx] / self.rho0
        if rho < self.rho_cutoff:
            p = 0.0
        else:
            pnew = (d_rhs[d_idx] - d_odiag[d_idx]) / d_diag[d_idx]
            p = omega * pnew + (1.0 - omega) * d_pk[d_idx]

        d_pdiff[d_idx] = abs(p - d_pk[d_idx])
        d_p[d_idx] = p
        d_pk[d_idx] = p

    def reduce(self, dst, t, dt):
        pdiff = dst.pdiff.mean()
        pmean = numpy.abs(dst.p).mean()
        conv = pdiff/abs(pmean)
        self.conv = 1 if conv < self.tolerance else -1

    def converged(self):
        return self.conv


class UpdateGhostPressure(Equation):
    def initialize(self, d_idx, d_tag, d_gid, d_p, d_pk):
        idx = declare('int')
        if d_tag[d_idx] == 2:
            idx = d_gid[d_idx]
            d_pk[d_idx] = d_pk[idx]
            d_p[d_idx] = d_p[idx]


class MomentumEquationPressureGradient(Equation):
    def initialize(self, d_idx, d_au, d_av, d_aw):
        d_au[d_idx] = 0.0
        d_av[d_idx] = 0.0
        d_aw[d_idx] = 0.0

    def loop(self, d_idx, s_idx, s_m, d_p, s_p, d_rho, s_rho, d_au,
             d_av, d_aw, DWIJ):
        Vj = s_m[s_idx] / s_rho[s_idx]
        pji = (s_p[s_idx] - d_p[d_idx])
        fac = -Vj * pji / d_rho[d_idx]

        d_au[d_idx] += fac * DWIJ[0]
        d_av[d_idx] += fac * DWIJ[1]
        d_aw[d_idx] += fac * DWIJ[2]


class MomentumEquationPressureGradientSymmetric(Equation):
    def initialize(self, d_idx, d_au, d_av, d_aw):
        d_au[d_idx] = 0.0
        d_av[d_idx] = 0.0
        d_aw[d_idx] = 0.0

    def loop(self, d_idx, s_idx, s_m, d_p, s_p, d_rho, s_rho, d_au, d_av, d_aw,
             DWIJ):
        rhoi2 = d_rho[d_idx]*d_rho[d_idx]
        rhoj2 = s_rho[s_idx]*s_rho[s_idx]
        pij = d_p[d_idx]/rhoi2 + s_p[s_idx]/rhoj2
        fac = -s_m[s_idx] * pij

        d_au[d_idx] += fac * DWIJ[0]
        d_av[d_idx] += fac * DWIJ[1]
        d_aw[d_idx] += fac * DWIJ[2]


class EvaluateNumberDensity(Equation):
    def initialize(self, d_idx, d_wij):
        d_wij[d_idx] = 0.0

    def loop(self, d_idx, d_wij, WIJ):
        d_wij[d_idx] += WIJ


class VolumeSummationBand(Equation):
    def initialize(self, d_idx, d_rhoband):
        d_rhoband[d_idx] = 0.0

    def loop(self, d_idx, d_rhoband, d_m, WIJ):
        d_rhoband[d_idx] += WIJ * d_m[d_idx]


class SetPressureSolid(Equation):
    def __init__(self, dest, sources, gx=0.0, gy=0.0, gz=0.0,
                 hg_correction=True):
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.hg_correction = hg_correction
        super(SetPressureSolid, self).__init__(dest, sources)

    def initialize(self, d_idx, d_p):
        d_p[d_idx] = 0.0

    def loop(self, d_idx, s_idx, d_p, s_p, s_rho,
             d_au, d_av, d_aw, WIJ, XIJ):

        # numerator of Eq. (27) ax, ay and az are the prescribed wall
        # accelerations which must be defined for the wall boundary
        # particle
        gdotxij = (self.gx - d_au[d_idx])*XIJ[0] + \
            (self.gy - d_av[d_idx])*XIJ[1] + \
            (self.gz - d_aw[d_idx])*XIJ[2]

        d_p[d_idx] += s_p[s_idx]*WIJ + s_rho[s_idx]*gdotxij*WIJ

    def post_loop(self, d_idx, d_wij, d_p, d_rho, d_pk):
        # extrapolated pressure at the ghost particle
        if d_wij[d_idx] > 1e-14:
            d_p[d_idx] /= d_wij[d_idx]
        if self.hg_correction:
            d_p[d_idx] = max(0.0, d_p[d_idx])
        d_pk[d_idx] = d_p[d_idx]


class GTVFAcceleration(Equation):
    def __init__(self, dest, sources, pref, hij_fac=0.5):
        self.hij_fac = hij_fac
        self.pref = pref
        assert self.pref is not None, "pref should not be None"
        super(GTVFAcceleration, self).__init__(dest, sources)

    def initialize(self, d_idx, d_auhat, d_avhat, d_awhat, d_p0, d_p):
        d_auhat[d_idx] = 0.0
        d_avhat[d_idx] = 0.0
        d_awhat[d_idx] = 0.0

        d_p0[d_idx] = min(10*abs(d_p[d_idx]), self.pref)

    def loop(self, d_p0, s_m, s_idx, d_rho, d_idx, d_auhat, d_avhat,
             d_awhat, XIJ, RIJ, SPH_KERNEL,
             HIJ):
        rhoi2 = d_rho[d_idx]*d_rho[d_idx]
        tmp = -d_p0[d_idx] * s_m[s_idx]/rhoi2

        dwijhat = declare('matrix(3)')
        SPH_KERNEL.gradient(XIJ, RIJ, self.hij_fac*HIJ, dwijhat)

        d_auhat[d_idx] += tmp * dwijhat[0]
        d_avhat[d_idx] += tmp * dwijhat[1]
        d_awhat[d_idx] += tmp * dwijhat[2]


class ISPHScheme(Scheme):
    def __init__(self, fluids, solids, dim, nu, rho0, c0, alpha=0.0, beta=0.0,
                 gx=0.0, gy=0.0, gz=0.0, variant="CR", tolerance=0.05,
                 omega=0.5, hg_correction=True, has_ghosts=False,
                 inviscid_solids=None, inlet_outlet_manager=None, pref=None,
                 gtvf=False, symmetric=False, rho_cutoff=0.8, hij_fac=0.5):
        self.fluids = fluids
        self.solids = solids
        self.solver = None
        self.dim = dim
        self.nu = nu
        self.gx = gx
        self.gy = gy
        self.gz = gz
        self.c0 = c0
        self.alpha = alpha
        self.beta = beta
        self.variant = variant
        self.rho0 = rho0
        self.rho_cutoff = rho_cutoff
        self.tolerance = tolerance
        self.omega = omega
        self.hg_correction = hg_correction
        self.has_ghosts = has_ghosts
        self.inviscid_solids = [] if inviscid_solids is None else\
            inviscid_solids
        self.inlet_outlet_manager = None if inlet_outlet_manager is None\
            else inlet_outlet_manager
        self.fluid_with_io = self.fluids.copy()
        self.pref = pref
        self.gtvf = gtvf
        self.symmetric = symmetric
        self.hij_fac = hij_fac

    def add_user_options(self, group):
        group.add_argument(
            "--variant", action="store", dest="variant",
            type=str, choices=['DF', 'DI', 'DFDI'],
            help="ISPH variant (defaults to \"CR\" Cummins and Rudmann)."
        )
        group.add_argument(
            "--tol", action="store", dest="tolerance",
            type=float,
            help="Tolerance for convergence."
        )
        group.add_argument(
            "--omega", action="store", dest="omega",
            type=float,
            help="Omega for convergence."
        )
        group.add_argument(
            '--alpha', action='store', type=float, dest='alpha',
            default=None,
            help='Artificial viscosity.'
        )
        add_bool_argument(
            group, 'gtvf', dest='gtvf', default=None,
            help='Use GTVF.'
        )
        add_bool_argument(
            group, 'symmetric', dest='symmetric', default=None,
            help='Use symmetric form of pressure gradient.'
        )

    def consume_user_options(self, options):
        _vars = ['variant', 'tolerance', 'omega', 'alpha', 'gtvf', 'symmetric']
        data = dict((var, self._smart_getattr(options, var))
                    for var in _vars)
        self.configure(**data)

    def configure_solver(self, kernel=None, integrator_cls=None,
                         extra_steppers=None, **kw):
        import pysph.base.kernels as kern
        if kernel is None:
            kernel = kern.QuinticSpline(dim=self.dim)
        steppers = {}
        if extra_steppers is not None:
            steppers.update(extra_steppers)

        step_cls = ISPHStep
        if self.variant == "DI":
            step_cls = ISPHDIStep
        if self.gtvf:
            step_cls = ISPHGTVFStep

        for fluid in self.fluids:
            if fluid not in steppers:
                steppers[fluid] = step_cls()

        if integrator_cls is not None:
            cls = integrator_cls
        else:
            cls = PECIntegrator

        iom = self.inlet_outlet_manager
        if iom is not None:
            iom_stepper = iom.get_stepper(self, cls)
            for name in iom_stepper:
                steppers[name] = iom_stepper[name]

        integrator = cls(**steppers)

        from pysph.solver.solver import Solver
        self.solver = Solver(
            dim=self.dim, integrator=integrator, kernel=kernel, **kw
        )

        if iom is not None:
            iom.setup_iom(dim=self.dim, kernel=kernel)

    def _get_velocity_bc(self):
        from pysph.sph.wc.transport_velocity import SetWallVelocity
        from pysph.sph.wc.edac import NoSlipVelocityExtrapolation

        eqs = [SetWallVelocity(dest=s, sources=self.fluid_with_io)
               for s in self.solids]

        for solids in self.inviscid_solids:
            eqs.append(
                NoSlipVelocityExtrapolation(
                    dest=solids, sources=self.fluid_with_io
                )
            )

        return Group(equations=eqs)

    def _get_pressure_bc(self):
        eqs = []
        all_solids = self.solids + self.inviscid_solids
        for solid in all_solids:
            eqs.append(
                EvaluateNumberDensity(
                    dest=solid, sources=self.fluid_with_io
                )
            )
            eqs.append(
                SetPressureSolid(
                    dest=solid, sources=self.fluid_with_io,
                    gx=self.gx, gy=self.gy, gz=self.gz,
                    hg_correction=self.hg_correction
                )
            )

        return Group(equations=eqs) if eqs else None

    def _get_viscous_eqns(self, variant):
        from pysph.sph.wc.transport_velocity import (
            MomentumEquationViscosity, MomentumEquationArtificialViscosity,
            SummationDensity, SolidWallNoSlipBC)
        from pysph.sph.wc.viscosity import LaminarViscosity
        from pysph.sph.wc.gtvf import MomentumEquationArtificialStress

        iom = self.inlet_outlet_manager
        if iom is not None:
            self.fluid_with_io = self.fluids + iom.get_io_names()
        all = self.fluid_with_io + self.solids + self.inviscid_solids

        eq, stg = [], []
        if variant.endswith('DI'):
            for fluid in self.fluids:
                eq.append(SummationDensity(dest=fluid, sources=all))
            stg.append(Group(equations=eq, real=False))

        eq = []
        for fluid in self.fluids:
            if variant.endswith('DI'):
                eq.append(
                    MomentumEquationViscosity(fluid, sources=all, nu=self.nu)
                )
            else:
                eq.append(
                    LaminarViscosity(fluid, sources=self.fluids, nu=self.nu)
                )
            if self.alpha > 0.0:
                eq.append(
                    # FIXME: All sources?
                    MomentumEquationArtificialViscosity(
                        dest=fluid, sources=self.fluids, c0=self.c0,
                        alpha=self.alpha
                    )
                )
            if self.gx != 0.0 or self.gy != 0.0 or self.gz != 0.0:
                eq.append(
                    MomentumEquationBodyForce(
                        fluid, sources=None, gx=self.gx, gy=self.gy,
                        gz=self.gz)
                )
            if self.gtvf:
                eq.append(
                    MomentumEquationArtificialStress(
                        dest=fluid, sources=self.fluids, dim=self.dim)
                )
            if self.solids and self.nu > 0.0:
                eq.append(
                    SolidWallNoSlipBC(
                        dest=fluid, sources=self.solids, nu=self.nu
                    )
                )
        stg.append(Group(equations=eq))
        return stg

    def _get_ppe(self, variant):
        from pysph.sph.wc.transport_velocity import (SummationDensity,
                                                     VolumeSummation)

        iom = self.inlet_outlet_manager
        if iom is not None:
            self.fluid_with_io = self.fluids + iom.get_io_names()
        all = self.fluid_with_io + self.solids + self.inviscid_solids
        all_solids = self.solids + self.inviscid_solids

        eq, stg = [], []
        if self.variant.endswith('DI'):
            for fluid in self.fluid_with_io:
                eq.append(SummationDensity(dest=fluid, sources=all))
            stg.append(Group(equations=eq, real=False))

        eq2 = []
        for fluid in self.fluid_with_io:
            if self.variant == 'DI':
                eq2.append(
                    DensityInvariance(dest=fluid, sources=None, rho0=self.rho0)
                )
            else:
                eq2.append(VolumeSummation(dest=fluid, sources=all))
                eq2.append(VelocityDivergence(dest=fluid,
                           sources=self.fluid_with_io))
                if self.solids:
                    eq2.append(
                        VelocityDivergenceSolid(fluid, sources=self.solids)
                    )
        stg.append(Group(equations=eq2))

        solver_eqns = []
        if self.has_ghosts:
            ghost_eqns = Group(
                equations=[UpdateGhostPressure(dest=fluid, sources=None)
                           for fluid in self.fluid_with_io],
                real=False
            )
            solver_eqns = [ghost_eqns]

        iom = self.inlet_outlet_manager
        if iom is not None:
            io_eqs = iom.get_equations(self)
            for grp in io_eqs:
                solver_eqns.append(grp)

        if all_solids:
            g3 = self._get_pressure_bc()
            solver_eqns.append(g3)

        eq3 = []
        for fluid in self.fluids:
            eq3.append(PressureCoeffMatrixIterative(dest=fluid, sources=all))
            eq3.append(
                PPESolve(
                    dest=fluid, sources=all, rho0=self.rho0,
                    rho_cutoff=self.rho_cutoff, tolerance=self.tolerance,
                    omega=self.omega
                )
            )
        eq3 = Group(equations=eq3)

        solver_eqns.append(eq3)

        stg.append(
            Group(
                equations=solver_eqns, iterate=True, max_iterations=100,
                min_iterations=2
            )
        )

        if self.has_ghosts:
            ghost_eqns = Group(
                equations=[UpdateGhostPressure(dest=fluid, sources=None)
                           for fluid in self.fluid_with_io],
                real=False
            )
            stg.append(ghost_eqns)
        return stg

    def get_equations(self):
        iom = self.inlet_outlet_manager
        if iom is not None:
            self.fluid_with_io = self.fluids + iom.get_io_names()
        all = self.fluid_with_io + self.solids + self.inviscid_solids
        all_solids = self.solids + self.inviscid_solids

        stg1 = []
        if all_solids:
            g0 = self._get_velocity_bc()
            stg1.append(g0)

        if iom is not None:
            io_eqs = iom.get_equations(self)
            for grp in io_eqs:
                stg1.append(grp)

        stg1.extend(self._get_viscous_eqns(self.variant))

        stg2 = []
        if all_solids:
            g0 = self._get_velocity_bc()
            stg2.append(g0)

        stg2.extend(self._get_ppe(self.variant))

        if iom is not None:
            io_eqs = iom.get_equations(self)
            stg2.extend(io_eqs)

        if all_solids:
            g3 = self._get_pressure_bc()
            stg2.append(g3)

        if all_solids:
            g0 = self._get_velocity_bc()
            stg2.append(g0)

        eq4 = []
        for fluid in self.fluids:
            if self.symmetric:
                eq4.append(
                    MomentumEquationPressureGradientSymmetric(fluid, all)
                )
            else:
                eq4.append(
                    MomentumEquationPressureGradient(fluid, sources=all)
                )
            if self.gtvf:
                eq4.append(
                    GTVFAcceleration(dest=fluid, sources=all, pref=self.pref,
                                     hij_fac=self.hij_fac)
                )
        stg2.append(Group(equations=eq4))
        return MultiStageEquations([stg1, stg2])

    def setup_properties(self, particles, clean=True):
        particle_arrays = dict([(p.name, p) for p in particles])
        dummy = get_particle_array_isph(name='junk',
                                        gid=particle_arrays['fluid'].gid)
        props = list(dummy.properties.keys())
        props += [dict(name=x, stride=v) for x, v in dummy.stride.items()]
        constants = [dict(name=x, data=v) for x, v in dummy.constants.items()]
        output_props = dummy.output_property_arrays
        iom = self.inlet_outlet_manager
        for fluid in self.fluid_with_io:
            pa = particle_arrays[fluid]
            self._ensure_properties(pa, props, clean)
            pa.set_output_arrays(output_props)
            for const in constants:
                pa.add_constant(**const)
            if iom is not None:
                iom.add_io_properties(pa, self)

        solid_props = ['wij', 'ug', 'vg', 'wg', 'uf', 'vf', 'wf', 'pk', 'V']
        all_solids = self.solids + self.inviscid_solids
        for solid in all_solids:
            pa = particle_arrays[solid]
            for prop in solid_props:
                pa.add_property(prop)
            pa.add_output_arrays(['p'])
