# -*- coding: utf-8 -*-
# Copyright 2018-2021 the orix developers
#
# This file is part of orix.
#
# orix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# orix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with orix.  If not, see <http://www.gnu.org/licenses/>.

from diffpy.structure import Lattice, Structure
import numpy as np
import pytest

from orix.crystal_map import Phase
from orix.quaternion import Orientation
from orix.vector import Miller
from orix.vector.miller import _round_indices, _uvw2UVTW, _UVTW2uvw


TETRAGONAL_LATTICE = Lattice(0.5, 0.5, 1, 90, 90, 90)
TETRAGONAL_PHASE = Phase(
    point_group="4", structure=Structure(lattice=TETRAGONAL_LATTICE)
)
TRIGONAL_PHASE = Phase(
    point_group="321", structure=Structure(lattice=Lattice(4.9, 4.9, 5.4, 90, 90, 120))
)
CUBIC_PHASE = Phase(point_group="m-3m")


class TestMiller:
    def test_init_raises(self):
        with pytest.raises(ValueError, match="Either *"):
            _ = Miller(phase=Phase(point_group="m-3m"))

    def test_repr(self):
        m = Miller(hkil=[1, 1, -2, 0], phase=TRIGONAL_PHASE)
        assert repr(m) == ("Miller (1,), point group 321, hkil\n" "[[ 1.  1. -2.  0.]]")

    def test_coordinate_format_raises(self):
        m = Miller(hkl=[1, 1, 1], phase=TETRAGONAL_PHASE)
        with pytest.raises(ValueError, match="Available coordinate formats are "):
            m.coordinate_format = "abc"

    def test_set_coordinates(self):
        m = Miller(xyz=[1, 2, 0], phase=TETRAGONAL_PHASE)
        assert np.allclose(m.data, m.coordinates)

    def test_set_hkl_hkil(self):
        m1 = Miller(hkl=[[1, 1, 1], [2, 0, 0]], phase=TETRAGONAL_PHASE)
        assert np.allclose(m1.data, [[2, 2, 1], [4, 0, 0]])
        assert np.allclose([m1.h, m1.k, m1.l], [[1, 2], [1, 0], [1, 0]])
        m1.hkl = [[1, 2, 0], [1, 1, 0]]
        assert np.allclose(m1.data, [[2, 4, 0], [2, 2, 0]])
        assert np.allclose([m1.h, m1.k, m1.l], [[1, 1], [2, 1], [0, 0]])

        m2 = Miller(hkil=[[1, 1, -2, 1], [2, 0, -2, 0]], phase=TRIGONAL_PHASE)
        assert np.allclose(m2.data, [[0.20, 0.35, 0.19], [0.41, 0.24, 0]], atol=0.01)
        assert np.allclose([m2.h, m2.k, m2.i, m2.l], [[1, 2], [1, 0], [-2, -2], [1, 0]])
        m2.hkil = [[1, 2, -3, 1], [2, 1, -3, 1]]
        assert np.allclose(m2.data, [[0.20, 0.59, 0.19], [0.41, 0.47, 0.19]], atol=0.01)
        assert np.allclose([m2.h, m2.k, m2.i, m2.l], [[1, 2], [2, 1], [-3, -3], [1, 1]])

    def test_set_uvw_UVTW(self):
        m1 = Miller(uvw=[[1, 1, 1], [2, 0, 0]], phase=TETRAGONAL_PHASE)
        assert np.allclose(m1.data, [[0.5, 0.5, 1], [1, 0, 0]])
        assert np.allclose([m1.u, m1.v, m1.w], [[1, 2], [1, 0], [1, 0]])
        m1.uvw = [[1, 2, 0], [1, 1, 0]]
        assert np.allclose(m1.data, [[0.5, 1, 0], [0.5, 0.5, 0]])
        assert np.allclose([m1.u, m1.v, m1.w], [[1, 1], [2, 1], [0, 0]])

        m2 = Miller(UVTW=[[1, 1, -2, 1], [2, 0, -2, 0]], phase=TRIGONAL_PHASE)
        assert np.allclose(m2.data, [[7.35, 12.73, 5.4], [14.7, 8.49, 0]], atol=0.01)
        assert np.allclose([m2.U, m2.V, m2.T, m2.W], [[1, 2], [1, 0], [-2, -2], [1, 0]])
        m2.UVTW = [[1, 2, -3, 1], [2, 1, -3, 1]]
        assert np.allclose(m2.data, [[7.35, 21.22, 5.4], [14.7, 16.97, 5.4]], atol=0.01)
        assert np.allclose([m2.U, m2.V, m2.T, m2.W], [[1, 2], [2, 1], [-3, -3], [1, 1]])

    def test_length(self):
        # Direct lattice vectors
        m1 = Miller(uvw=[0, -0.5, 0.5], phase=TETRAGONAL_PHASE)
        assert np.allclose(m1.length, 0.559, atol=1e-3)

        # Reciprocal lattice vectors
        m2 = Miller(hkl=[[1, 2, 0], [3, 1, 1]], phase=TETRAGONAL_PHASE)
        assert np.allclose(m2.length, [4.472, 6.403], atol=1e-3)
        assert np.allclose(1 / m2.length, [0.224, 0.156], atol=1e-3)

        # Vectors
        m3 = Miller(xyz=[[1, 0, 0], [0, 1, 0], [0, 0, 1]], phase=TETRAGONAL_PHASE)
        assert np.allclose(m3.length, [1, 1, 1])

    def test_init_from_highest_indices(self):
        m1 = Miller.from_highest_indices(phase=TETRAGONAL_PHASE, hkl=[3, 2, 1])
        assert np.allclose(np.max(m1.hkl, axis=0), [3, 2, 1])
        m2 = Miller.from_highest_indices(phase=TETRAGONAL_PHASE, uvw=[1, 2, 3])
        assert np.allclose(np.max(m2.uvw, axis=0), [1, 2, 3])

        with pytest.raises(ValueError, match="Either highest `hkl` or `uvw` indices "):
            _ = Miller.from_highest_indices(phase=TETRAGONAL_PHASE)

        with pytest.raises(ValueError, match="All indices*"):
            _ = Miller.from_highest_indices(phase=TETRAGONAL_PHASE, hkl=[3, 2, -1])

    def test_init_from_min_dspacing(self):
        # Tested against EMsoft v5.0
        m1 = Miller.from_min_dspacing(phase=TETRAGONAL_PHASE, min_dspacing=0.05)
        assert m1.coordinate_format == "hkl"
        assert m1.size == 14078
        assert np.allclose(np.max(m1.hkl, axis=0), [9, 9, 19])
        assert np.allclose(np.min(1 / m1.length), 0.0315, atol=1e-4)
        m2 = Miller.from_min_dspacing(phase=TRIGONAL_PHASE, min_dspacing=0.5)
        assert m2.size == 6068
        assert np.allclose(np.max(m2.hkl, axis=0), [8, 8, 10])
        assert np.allclose(np.min(1 / m2.length), 0.2664, atol=1e-4)

    def test_deepcopy(self):
        m = Miller(hkl=[1, 1, 0], phase=TETRAGONAL_PHASE)
        m2 = m.deepcopy()
        m2.coordinate_format = "uvw"
        assert m2.coordinate_format == "uvw"
        assert m.coordinate_format == "hkl"

    def test_get_nearest(self):
        assert (
            Miller(uvw=[1, 0, 0], phase=TETRAGONAL_PHASE).get_nearest()
            == NotImplemented
        )

    def test_mean(self):
        # Tested against MTEX v5.6.0
        m1 = Miller(hkl=[[1, 2, 0], [3, 1, 1]], phase=TETRAGONAL_PHASE)
        m1_mean = m1.mean()
        assert isinstance(m1_mean, Miller)
        assert m1_mean.coordinate_format == "hkl"
        assert np.allclose(m1_mean.hkl, [2, 1.5, 0.5])

        m2 = Miller(UVTW=[[1, 2, -3, 0], [3, 1, -4, 1]], phase=TRIGONAL_PHASE)
        m2_mean = m2.mean()
        assert m2_mean.coordinate_format == "UVTW"
        assert np.allclose(m2_mean.UVTW, [2, 1.5, -3.5, 0.5])

        assert m2.mean(use_symmetry=True) == NotImplemented

    def test_round(self):
        # Tested against MTEX v5.6.0
        m1 = Miller(uvw=[[1, 1, 0], [1, 1, 1]], phase=TETRAGONAL_PHASE)
        m1perp = m1[0].cross(m1[1])
        m1round = m1perp.round()
        assert isinstance(m1round, Miller)
        assert m1round.coordinate_format == "hkl"
        assert np.allclose(m1round.hkl, [1, -1, 0])

        m2 = Miller(hkil=[1, 1, -2, 3], phase=TRIGONAL_PHASE)
        m2.coordinate_format = "UVTW"
        m2round = m2.round()
        assert np.allclose(m2round.UVTW, [3, 3, -6, 11])

        m3 = Miller(xyz=[[0.1, 0.2, 0.3], [1, 0.5, 1]], phase=TRIGONAL_PHASE)
        assert m3.coordinate_format == "xyz"
        m3round = m3.round()
        assert np.allclose(m3.data, m3round.data)
        assert not np.may_share_memory(m3.data, m3round.data)

    def test_symmetrise_raises(self):
        m = Miller(uvw=[1, 0, 0], phase=TETRAGONAL_PHASE)
        with pytest.raises(ValueError, match="`unique` must be True when"):
            _ = m.symmetrise(return_multiplicity=True)
        with pytest.raises(ValueError, match="`unique` must be True when"):
            _ = m.symmetrise(return_index=True)

    def test_symmetrise(self):
        # Also thoroughly tested in the TestMillerPointGroup* classes

        # Test from MTEX' v5.6.0 documentation
        m = Miller(UVTW=[1, -2, 1, 3], phase=TRIGONAL_PHASE)
        _, l = m.symmetrise(return_multiplicity=True, unique=True)
        assert l == 6

        m2 = Miller(uvw=[[1, 0, 0], [1, 1, 0], [1, 1, 1]], phase=CUBIC_PHASE)
        _, idx = m2.symmetrise(unique=True, return_index=True)
        assert np.allclose(idx, np.array([0] * 6 + [1] * 12 + [2] * 8))

        _, l3, _ = m2.symmetrise(
            unique=True, return_multiplicity=True, return_index=True
        )
        assert np.allclose(l3, [6, 12, 8])

    def test_unique(self):
        # From the "Crystal geometry" notebook
        diamond = Phase(space_group=227)
        m = Miller.from_highest_indices(phase=diamond, uvw=[10, 10, 10])
        assert m.size == 9260
        m2 = m.unique(use_symmetry=True)
        assert m2.size == 450
        m3, idx = m2.unit.unique(return_index=True)
        assert m3.size == 345
        assert isinstance(m3, Miller)
        assert np.allclose(idx[:10], [74, 448, 434, 409, 374, 330, 278, 447, 412, 432])

    def test_multiply_orientation(self):
        o = Orientation.from_euler(np.deg2rad([45, 0, 0]))
        o = o.set_symmetry(CUBIC_PHASE.point_group)
        m = Miller(hkl=[[1, 1, 1], [2, 0, 0]], phase=CUBIC_PHASE)
        m2 = o * m
        assert isinstance(m2, Miller)
        assert m2.coordinate_format == "hkl"
        assert np.allclose(m2.data, [[np.sqrt(2), 0, 1], [np.sqrt(2), -np.sqrt(2), 0]])


class TestMillerBravais:
    def test_uvw2UVTW(self):
        """Indices taken from Table 1.1 in 'Introduction to Conventional
        Transmission Electron Microscopy (DeGraef, 2003)'.
        """
        # fmt: off
        uvw = [
            [ 1, 0, 0],
            [ 1, 1, 0],
            [ 0, 0, 1],
            [ 0, 1, 1],
            [ 2, 1, 0],
            [ 2, 1, 1],
            [ 0, 1, 0],
            [-1, 1, 0],
            [ 1, 0, 1],
            [ 1, 1, 1],
            [ 1, 2, 0],
            [ 1, 1, 2],
        ]
        UVTW = [
            [ 2, -1, -1, 0],
            [ 1,  1, -2, 0],
            [ 0,  0,  0, 1],
            [-1,  2, -1, 3],
            [ 1,  0, -1, 0],
            [ 1,  0, -1, 1],
            [-1,  2, -1, 0],
            [-1,  1,  0, 0],
            [ 2, -1, -1, 3],
            [ 1,  1, -2, 3],
            [ 0,  1, -1, 0],
            [ 1,  1, -2, 6],
        ]
        # fmt: on

        assert np.allclose(_round_indices(_uvw2UVTW(uvw)), UVTW)
        assert np.allclose(_round_indices(_UVTW2uvw(UVTW)), uvw)
        assert np.allclose(_round_indices(_uvw2UVTW(_UVTW2uvw(UVTW))), UVTW)
        assert np.allclose(_round_indices(_UVTW2uvw(_uvw2UVTW(uvw))), uvw)

        m1 = Miller(uvw=uvw, phase=TETRAGONAL_PHASE)
        assert np.allclose(m1.uvw, uvw)
        m2 = Miller(UVTW=UVTW, phase=TETRAGONAL_PHASE)
        assert np.allclose(m2.UVTW, UVTW)
        assert np.allclose(m1.unit.data, m2.unit.data)

        # MTEX convention
        assert np.allclose(_uvw2UVTW(uvw, convention="mtex") / 3, _uvw2UVTW(uvw))
        assert np.allclose(_UVTW2uvw(UVTW, convention="mtex") * 3, _UVTW2uvw(UVTW))

    def test_mtex_convention(self):
        # Same result without convention="mtex" because of rounding...
        UVTW = [2, 1, -3, 1]
        uvw = _UVTW2uvw(UVTW, convention="mtex")
        assert np.allclose(_round_indices(uvw), [5, 4, 1])

    def test_trigonal_crystal(self):
        # Examples from MTEX' documentation:
        # https://mtex-toolbox.github.io/CrystalDirections.html
        m = Miller(UVTW=[2, 1, -3, 1], phase=TRIGONAL_PHASE)
        assert np.allclose(m.U + m.V + m.T, 0)
        n = Miller(hkil=[1, 1, -2, 3], phase=TRIGONAL_PHASE)
        assert np.allclose(n.h + n.k + n.i, 0)

        m.coordinate_format = "uvw"
        mround = m.round()
        assert np.allclose(mround.uvw, [5, 4, 1])
        assert np.allclose([mround.u[0], mround.v[0], mround.w[0]], [5, 4, 1])

        n.coordinate_format = "UVTW"
        nround = n.round()
        assert np.allclose(nround.UVTW, [3, 3, -6, 11])
        assert np.allclose(
            [nround.U[0], nround.V[0], nround.T[0], nround.W[0]], [3, 3, -6, 11]
        )

        # Examples from MTEX' documentation:
        # https://mtex-toolbox.github.io/CrystalOperations.html
        m1 = Miller(hkil=[1, -1, 0, 0], phase=TRIGONAL_PHASE)
        m2 = Miller(hkil=[1, 0, -1, 0], phase=TRIGONAL_PHASE)
        assert np.allclose(m1.cross(m2).round().UVTW, [0, 0, 0, 1])

        m3 = Miller(UVTW=[0, 0, 0, 1], phase=TRIGONAL_PHASE)
        m4 = Miller(UVTW=[1, -2, 1, 3], phase=TRIGONAL_PHASE)
        assert np.allclose(m3.cross(m4).round().hkil, [1, 0, -1, 0])

        m5 = m4.symmetrise(unique=True)
        assert m5.size == 6
        # fmt: off
        assert np.allclose(
            m5.coordinates,
            [
                [ 1, -2,  1,  3],
                [ 1,  1, -2,  3],
                [-2,  1,  1,  3],
                [ 1,  1, -2, -3],
                [-2,  1,  1, -3],
                [ 1, -2,  1, -3],
            ]
        )
        # fmt: on

        m6 = Miller(hkil=[1, 1, -2, 0], phase=TRIGONAL_PHASE)
        m7 = Miller(hkil=[-1, -1, 2, 0], phase=TRIGONAL_PHASE)

        assert np.allclose(np.rad2deg(m6.angle_with(m7).data[0]), 180)
        assert np.allclose(np.rad2deg(m6.angle_with(m7, use_symmetry=True).data[0]), 60)

    def test_convention_not_met(self):
        with pytest.raises(ValueError, match="The Miller-Bravais indices convention"):
            _ = Miller(hkil=[1, 1, -1, 0], phase=TETRAGONAL_PHASE)
        with pytest.raises(ValueError, match="The Miller-Bravais indices convention"):
            _ = Miller(UVTW=[1, 1, -1, 0], phase=TETRAGONAL_PHASE)


class TestDeGraefExamples:
    # Tests from examples in chapter 1 in Introduction to Conventional
    # Transmission Electron Microscopy (DeGraef, 2003)
    def test_tetragonal_crystal(self):
        # a = b = 0.5 nm, c = 1 nm
        lattice = TETRAGONAL_LATTICE

        # Example 1.1: Direct metric tensor
        assert np.allclose(lattice.metrics, [[0.25, 0, 0], [0, 0.25, 0], [0, 0, 1]])

        # Example 1.2: Distance between two points (length of a vector)
        answer = np.sqrt(5) / 4  # nm
        p1 = np.array([0.5, 0, 0.5])
        p2 = np.array([0.5, 0.5, 0])
        assert np.allclose(lattice.dist(p1, p2), answer)
        m1 = Miller(uvw=p1 - p2, phase=TETRAGONAL_PHASE)
        assert np.allclose(m1.length, answer)

        # Example 1.3, 1.4: Dot product and angle between two directions
        m2 = Miller(uvw=[1, 2, 0], phase=TETRAGONAL_PHASE)
        m3 = Miller(uvw=[3, 1, 1], phase=TETRAGONAL_PHASE)
        assert np.allclose(m2.dot(m3).data, 5 / 4)  # nm^2
        assert np.allclose(np.rad2deg(m2.angle_with(m3).data[0]), 53.30, atol=0.01)

        # Example 1.5: Reciprocal metric tensor
        lattice_recip = lattice.reciprocal()
        assert np.allclose(lattice_recip.metrics, [[4, 0, 0], [0, 4, 0], [0, 0, 1]])

        # Example 1.6, 1.7: Angle between two plane normals
        m4 = Miller(hkl=[1, 2, 0], phase=TETRAGONAL_PHASE)
        m5 = Miller(hkl=[3, 1, 1], phase=TETRAGONAL_PHASE)
        assert np.allclose(np.rad2deg(m4.angle_with(m5).data[0]), 45.7, atol=0.1)

        # Example 1.8: Reciprocal components of a lattice vector
        m6 = Miller(uvw=[1, 1, 4], phase=TETRAGONAL_PHASE)
        assert np.allclose(m6.hkl, [0.25, 0.25, 4])
        m7 = Miller(hkl=m6.hkl, phase=TETRAGONAL_PHASE)
        assert np.allclose(m7.round().hkl, [1, 1, 16])

        # Example 1.9: Reciprocal lattice parameters
        assert np.allclose(lattice_recip.abcABG(), [2, 2, 1, 90, 90, 90])

        # Example 1.10, 1.11: Cross product of two directions
        m8 = Miller(uvw=[1, 1, 0], phase=TETRAGONAL_PHASE)
        m9 = Miller(uvw=[1, 1, 1], phase=TETRAGONAL_PHASE)
        m10 = m8.cross(m9)
        assert m10.coordinate_format == "hkl"
        assert np.allclose(m10.coordinates, [0.25, -0.25, 0])
        assert np.allclose(m10.uvw, [1, -1, 0])
        assert np.allclose(m10.round().coordinates, [1, -1, 0])

        # Example 1.12: Cross product of two reciprocal lattice vectors
        m11 = Miller(hkl=[1, 1, 0], phase=TETRAGONAL_PHASE)
        m12 = Miller(hkl=[1, 1, 1], phase=TETRAGONAL_PHASE)
        m13 = m11.cross(m12)
        assert m13.coordinate_format == "uvw"
        assert np.allclose(m13.coordinates, [4, -4, 0])
        assert np.allclose(m13.hkl, [1, -1, 0])
        assert np.allclose(m13.round().coordinates, [1, -1, 0])


# Run tests for all systems: $ pytest -k TestMillerPointGroups
# Run tests for one system:  $ pytest -k TestMillerPointGroupsMonoclinic


class TestMillerPointGroups:
    hkl = [[0, 0, 1], [0, 1, 1], [1, 1, 1]]
    phase = Phase(structure=Structure(lattice=Lattice(1, 1, 1, 90, 90, 90)))


class TestMillerPointGroupsTriclinic(TestMillerPointGroups):
    # Triclinic: 1, -1
    def test_group_1(self):
        self.phase.point_group = "1"
        m = Miller(hkl=self.hkl, phase=self.phase)

        assert np.allclose(m.symmetrise(unique=False).hkl, self.hkl)
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(m_unique.hkl, self.hkl)

        mult = m.multiplicity
        assert np.allclose(mult, [1, 1, 1])
        assert np.sum(mult) == m_unique.size

    def test_group_bar1(self):
        self.phase.point_group = "-1"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1, -1],

                [ 1,  1,  1],
                [-1, -1, -1],
            ],
        )

        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1, -1],

                [ 1,  1,  1],
                [-1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 2, 2])
        assert np.sum(mult) == m_unique.size


class TestMillerPointGroupsMonoclinic(TestMillerPointGroups):
    # Monoclinic: 2 (121), m (1m1), 2/m
    def test_group_121(self):
        self.phase.point_group = "121"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1,  1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 2, 2])
        assert np.sum(mult) == m_unique.size

    def test_group_1m1(self):
        self.phase.point_group = "1m1"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],

                [ 0,  1,  1],
                [ 0, -1,  1],

                [ 1,  1,  1],
                [ 1, -1,  1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],

                [ 0,  1,  1],
                [ 0, -1,  1],

                [ 1,  1,  1],
                [ 1, -1,  1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 2, 2])
        assert np.sum(mult) == m_unique.size

    def test_group_2overm(self):
        self.phase.point_group = "2/m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0,  1, -1],
                [ 0, -1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1,  1, -1],
                [-1, -1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0,  1, -1],
                [ 0, -1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1,  1, -1],
                [-1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 4, 4])
        assert np.sum(mult) == m_unique.size


class TestMillerPointGroupsOrthorhombic(TestMillerPointGroups):
    # Orthorhombic: 222, mm2, 2/m 2/m 2/m (mmm)
    def test_group_222(self):
        self.phase.point_group = "222"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 4, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_mm2(self):
        self.phase.point_group = "mm2"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0,  1],

                [ 0,  1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [ 0, -1,  1],

                [ 1,  1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [ 1, -1,  1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [ 0, -1,  1],

                [ 1,  1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [ 1, -1,  1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 4, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_2overm_2overm_2overm(self):
        self.phase.point_group = "mmm"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0,  1, -1],
                [ 0,  1,  1],
                [ 0,  1, -1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0, -1,  1],
                [ 0, -1, -1],

                [ 1,  1,  1],
                [ 1,  1, -1],
                [-1,  1,  1],
                [-1,  1, -1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [-1, -1,  1],
                [-1, -1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0,  1, -1],
                [ 0, -1,  1],
                [ 0, -1, -1],

                [ 1,  1,  1],
                [ 1,  1, -1],
                [-1,  1,  1],
                [-1,  1, -1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [-1, -1,  1],
                [-1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 4, 8])
        assert np.sum(mult) == m_unique.size


class TestMillerPointGroupsTetragonal(TestMillerPointGroups):
    # Tetragonal: 4, -4, 4/m, 422, 4mm, -42m, 4/m 2/m 2/m
    def test_group_4(self):
        self.phase.point_group = "4"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 4, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_bar4(self):
        self.phase.point_group = "-4"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [-1, -1, -1],
                [ 1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [-1, -1, -1],
                [ 1,  1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 4, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_4overm(self):
        self.phase.point_group = "4/m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 8, 8])
        assert np.sum(mult) == m_unique.size

    def test_group_422(self):
        self.phase.point_group = "422"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 8, 8])
        assert np.sum(mult) == m_unique.size

    def test_group_4mm(self):
        self.phase.point_group = "4mm"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1,  1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 4, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_bar42m(self):
        self.phase.point_group = "-42m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [ 1,  0,  1],
                [-1,  0,  1],
                [ 1,  0, -1],
                [-1,  0, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [ 1,  0,  1],
                [-1,  0,  1],
                [ 1,  0, -1],
                [-1,  0, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 8, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_4overm_2overm_2overm(self):
        self.phase.point_group = "4/mmm"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 8, 8])
        assert np.sum(mult) == m_unique.size


class TestMillerPointGroupsTrigonal(TestMillerPointGroups):
    # Trigonal: 3, -3, 32, 3m, -3 2/m
    def test_group_3(self):
        self.phase.point_group = "3"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 3, 3])
        assert np.sum(mult) == m_unique.size

    def test_group_bar3(self):
        self.phase.point_group = "-3"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 6, 6])
        assert np.sum(mult) == m_unique.size

    def test_group_32(self):
        self.phase.point_group = "32"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 6, 6])
        assert np.sum(mult) == m_unique.size

    def test_group_3m(self):
        self.phase.point_group = "3m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],
                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
                [-1    ,  1    , 1],
                [-0.366, -1.366, 1],
                [ 1.366,  0.366, 1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
                [-1    ,  1    , 1],
                [-0.366, -1.366, 1],
                [ 1.366,  0.366, 1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 3, 6])
        assert np.sum(mult) == m_unique.size

    def test_group_bar3_2overm(self):
        self.phase.point_group = "-3m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],
                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
                [-1    ,  1    ,  1],
                [-0.366, -1.366,  1],
                [ 1.366,  0.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
                [-1    ,  1    ,  1],
                [-0.366, -1.366,  1],
                [ 1.366,  0.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 6, 12])
        assert np.sum(mult) == m_unique.size


class TestMillerPointGroupsHexagonal(TestMillerPointGroups):
    # Hexagonal: 6, -6, 6/m, 622, 6mm, -6m2, 6/m 2/m 2/m (6/mmm)
    def test_group_6(self):
        self.phase.point_group = "6"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],
                [ 0    , -1    , 1],
                [ 0.866,  0.5  , 1],
                [-0.866,  0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
                [-1    , -1    , 1],
                [ 1.366, -0.366, 1],
                [-0.366,  1.366, 1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],
                [ 0    , -1    , 1],
                [ 0.866,  0.5  , 1],
                [-0.866,  0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
                [-1    , -1    , 1],
                [ 1.366, -0.366, 1],
                [-0.366,  1.366, 1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 6, 6])
        assert np.sum(mult) == m_unique.size

    def test_group_bar6(self):
        self.phase.point_group = "-6"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 6, 6])
        assert np.sum(mult) == m_unique.size

    def test_group_6overm(self):
        self.phase.point_group = "6/m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    ,  1],
                [ 1.366, -0.366,  1],
                [-0.366,  1.366,  1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    ,  1],
                [ 1.366, -0.366,  1],
                [-0.366,  1.366,  1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 12, 12])
        assert np.sum(mult) == m_unique.size

    def test_group_622(self):
        self.phase.point_group = "622"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    ,  1],
                [ 1.366, -0.366,  1],
                [-0.366,  1.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
                [-1    ,  1    , -1],
                [-0.366, -1.366, -1],
                [ 1.366,  0.366, -1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    ,  1],
                [ 1.366, -0.366,  1],
                [-0.366,  1.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
                [-1    ,  1    , -1],
                [-0.366, -1.366, -1],
                [ 1.366,  0.366, -1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 12, 12])
        assert np.sum(mult) == m_unique.size

    def test_group_6mm(self):
        self.phase.point_group = "6mm"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],
                [ 0    , -1    , 1],
                [ 0.866,  0.5  , 1],
                [-0.866,  0.5  , 1],
                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],
                [ 0    , -1    , 1],
                [ 0.866,  0.5  , 1],
                [-0.866,  0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
                [-1    , -1    , 1],
                [ 1.366, -0.366, 1],
                [-0.366,  1.366, 1],
                [-1    ,  1    , 1],
                [-0.366, -1.366, 1],
                [ 1.366,  0.366, 1],
                [ 1    , -1    , 1],
                [ 0.366,  1.366, 1],
                [-1.366, -0.366, 1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    , 1],

                [ 0    ,  1    , 1],
                [-0.866, -0.5  , 1],
                [ 0.866, -0.5  , 1],
                [ 0    , -1    , 1],
                [ 0.866,  0.5  , 1],
                [-0.866,  0.5  , 1],

                [ 1    ,  1    , 1],
                [-1.366,  0.366, 1],
                [ 0.366, -1.366, 1],
                [-1    , -1    , 1],
                [ 1.366, -0.366, 1],
                [-0.366,  1.366, 1],
                [-1    ,  1    , 1],
                [-0.366, -1.366, 1],
                [ 1.366,  0.366, 1],
                [ 1    , -1    , 1],
                [ 0.366,  1.366, 1],
                [-1.366, -0.366, 1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [1, 6, 12])
        assert np.sum(mult) == m_unique.size

    def test_group_bar6m2(self):
        self.phase.point_group = "-6m2"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],
                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    ,  1    , -1],
                [-0.366, -1.366, -1],
                [ 1.366,  0.366, -1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
                [-1    ,  1    ,  1],
                [-0.366, -1.366,  1],
                [ 1.366,  0.366,  1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    ,  1    , -1],
                [-0.366, -1.366, -1],
                [ 1.366,  0.366, -1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
                [-1    ,  1    ,  1],
                [-0.366, -1.366,  1],
                [ 1.366,  0.366,  1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 6, 12])
        assert np.sum(mult) == m_unique.size

    def test_group_6overm_2overm_2overm(self):
        self.phase.point_group = "6/mmm"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    , -1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],
                [ 0    ,  0    ,  1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    ,  1],
                [ 1.366, -0.366,  1],
                [-0.366,  1.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
                [-1    ,  1    , -1],
                [-0.366, -1.366, -1],
                [ 1.366,  0.366, -1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
                [ 1    , -1    ,  1],
                [ 0.366,  1.366,  1],
                [-1.366, -0.366,  1],
                [-1    ,  1    ,  1],
                [-0.366, -1.366,  1],
                [ 1.366,  0.366,  1],
            ],
            atol=1e-3
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0    ,  0    ,  1],
                [ 0    ,  0    , -1],

                [ 0    ,  1    ,  1],
                [-0.866, -0.5  ,  1],
                [ 0.866, -0.5  ,  1],
                [ 0    , -1    ,  1],
                [ 0.866,  0.5  ,  1],
                [-0.866,  0.5  ,  1],
                [ 0    , -1    , -1],
                [ 0.866,  0.5  , -1],
                [-0.866,  0.5  , -1],
                [ 0    ,  1    , -1],
                [-0.866, -0.5  , -1],
                [ 0.866, -0.5  , -1],

                [ 1    ,  1    ,  1],
                [-1.366,  0.366,  1],
                [ 0.366, -1.366,  1],
                [-1    , -1    ,  1],
                [ 1.366, -0.366,  1],
                [-0.366,  1.366,  1],
                [ 1    , -1    , -1],
                [ 0.366,  1.366, -1],
                [-1.366, -0.366, -1],
                [-1    ,  1    , -1],
                [-0.366, -1.366, -1],
                [ 1.366,  0.366, -1],
                [ 1    ,  1    , -1],
                [-1.366,  0.366, -1],
                [ 0.366, -1.366, -1],
                [-1    , -1    , -1],
                [ 1.366, -0.366, -1],
                [-0.366,  1.366, -1],
                [ 1    , -1    ,  1],
                [ 0.366,  1.366,  1],
                [-1.366, -0.366,  1],
                [-1    ,  1    ,  1],
                [-0.366, -1.366,  1],
                [ 1.366,  0.366,  1],
            ],
            atol=1e-3
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [2, 12, 24])
        assert np.sum(mult) == m_unique.size


class TestMillerPointGroupsCubic(TestMillerPointGroups):
    # Cubic: 23, 2/m -3, 432, -43m, 4/m -3 2/m (m-3m)
    def test_group_23(self):
        self.phase.point_group = "23"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 0,  1,  0],
                [ 0, -1,  0],
                [ 0, -1,  0],
                [ 0,  1,  0],
                [ 0,  0, -1],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [-1,  0,  1],
                [ 1,  0, -1],
                [-1,  0, -1],
                [ 1,  1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [-1,  1,  0],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [ 1,  1,  1],

                [-1, -1,  1],
                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [ 1, -1, -1],
                [-1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 0,  1,  0],
                [ 0, -1,  0],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [-1,  0,  1],
                [ 1,  0, -1],
                [-1,  0, -1],
                [ 1,  1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [-1,  1,  0],
                [ 0, -1, -1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [6, 12, 4])
        assert np.sum(mult) == m_unique.size

    def test_group_2overm_bar3(self):
        self.phase.point_group = "m-3"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 0,  1,  0],
                [ 0, -1,  0],
                [ 0, -1,  0],
                [ 0,  1,  0],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [-1,  0,  0],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 1,  0,  0],
                [ 0, -1,  0],
                [ 0,  1,  0],
                [ 0,  1,  0],
                [ 0, -1,  0],
                [ 0,  0,  1],
                [ 0,  0,  1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [-1,  0,  1],
                [ 1,  0, -1],
                [-1,  0, -1],
                [ 1,  1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [-1,  1,  0],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [ 0, -1, -1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 1,  0, -1],
                [-1,  0,  1],
                [ 1,  0,  1],
                [-1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [ 1, -1,  0],
                [ 0,  1,  1],
                [ 0, -1,  1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1,  1, -1],
                [-1, -1, -1],
                [ 1,  1, -1],
                [-1,  1,  1],
                [ 1, -1,  1],
                [-1, -1, -1],
                [ 1,  1, -1],
                [-1,  1,  1],
                [ 1, -1,  1],
                [-1,  1,  1],
                [ 1, -1,  1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 1,  0,  0],
                [-1,  0,  0],
                [ 0,  1,  0],
                [ 0, -1,  0],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [-1,  0,  1],
                [ 1,  0, -1],
                [-1,  0, -1],
                [ 1,  1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [-1,  1,  0],
                [ 0, -1, -1],
                [ 0,  1, -1],

                [ 1,  1,  1],
                [-1, -1,  1],
                [ 1, -1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1,  1, -1],
                [-1,  1,  1],
                [ 1, -1,  1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [6, 12, 8])
        assert np.sum(mult) == m_unique.size

    def test_group_432(self):
        self.phase.point_group = "432"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 1,  0,  1],
                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [-1, -1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [-1, -1,  0],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [6, 12, 8])
        assert np.sum(mult) == m_unique.size

    def test_group_4overm_bar3_2overm(self):
        self.phase.point_group = "m-3m"
        m = Miller(hkl=self.hkl, phase=self.phase)

        # fmt: off
        assert np.allclose(
            m.symmetrise(unique=False).hkl,
            [
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [ 0,  0, -1],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 0,  0,  1],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 1,  0,  1],
                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [-1, -1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [-1,  0, -1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 1,  0,  1],
                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [-1,  1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [-1, -1,  0],
                [ 1, -1,  0],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [ 1, -1,  1],
                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [-1,  1, -1],
                [-1, -1, -1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
            ],
        )
        m_unique = m.symmetrise(unique=True)
        assert np.allclose(
            m_unique.hkl,
            [
                [ 0,  0,  1],
                [ 1,  0,  0],
                [ 0,  1,  0],
                [-1,  0,  0],
                [ 0, -1,  0],
                [ 0,  0, -1],

                [ 0,  1,  1],
                [-1,  0,  1],
                [ 0, -1,  1],
                [ 1,  0,  1],
                [ 0, -1, -1],
                [ 1,  0, -1],
                [ 0,  1, -1],
                [-1,  0, -1],
                [ 1, -1,  0],
                [ 1,  1,  0],
                [-1,  1,  0],
                [-1, -1,  0],

                [ 1,  1,  1],
                [-1,  1,  1],
                [-1, -1,  1],
                [ 1, -1,  1],
                [ 1, -1, -1],
                [ 1,  1, -1],
                [-1,  1, -1],
                [-1, -1, -1],
            ],
        )
        # fmt: on

        mult = m.multiplicity
        assert np.allclose(mult, [6, 12, 8])
        assert np.sum(mult) == m_unique.size
