import numpy as np

from settings import settings
from src.motion.gaits.gait import Gait
from src.motion.gaits.gait_spec import GaitSpec, LegSpec, compile_spec
from src.motion.gaits import trajectories as T


class Trot(Gait):
    """Diagonal trot: pairs {0,2} and {1,3} move a half-cycle out of phase, no
    lateral motion. Expressed declaratively via GaitSpec (see
    docs/plans/2026-05-30-001-refactor-gait-core-phasing-plan.md)."""

    def build_steps(self):
        self.steps = compile_spec(self._spec())

    def _spec(self) -> GaitSpec:
        num = self.num_steps
        stride, clearance = int(self.stride), self.clearance

        def x(_n):
            return np.hstack([
                T.stride_forward(num), T.stride_home(num), T.stride_back(num * 2),
            ]) * stride

        def z(_n):
            return np.hstack([T.downupdown(num), T.zero(num * 3)]) * (-clearance)

        a = LegSpec(x=x, z=z, phase_offset=0.0)   # legs 0, 2
        b = LegSpec(x=x, z=z, phase_offset=0.5)   # legs 1, 3 (diagonal half-cycle)
        return GaitSpec(period=num * 4, duty_factor=0.75, legs=[a, b, a, b])


if __name__ == "__main__":
    gait = Trot(
        p0=settings.position_ready,
        stride=50,
        clearance=50,
        step_size=1
    )

    gait.plotit()
