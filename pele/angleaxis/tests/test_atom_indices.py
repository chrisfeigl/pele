import unittest

import numpy as np

from pele.angleaxis._otp_cluster import make_otp, OTPCluster
from pele.angleaxis import RBTopology
from pele.angleaxis._cpp_aa import RBPotentialWrapper as cppRBPotentialWrapper
from pele.angleaxis.rigidbody import RBPotentialWrapper as pythonRBPotentialWrapper
from pele.potentials import LJ
from pele.potentials.tests._base_test import assert_arrays_almost_equal

class TestAtomIndices(unittest.TestCase):
    def setUp(self):
        self.nrigid = 3


    def make_normal_cpp_topology(self):
        sites = [make_otp() for _ in xrange(self.nrigid)]
        normal_topology = RBTopology()
        normal_topology.add_sites(sites)
        normal_topology.finalize_setup()
        return normal_topology

    def make_normal_python_topology(self):
        normal_topology = self.make_normal_cpp_topology()
        normal_topology.cpp_topology = None
        return normal_topology

    def make_atom_indices_cpp_topology(self):
        sites = [make_otp() for _ in xrange(self.nrigid)]
        atom_indices = np.array(range(self.nrigid*3), dtype=int)
        np.random.shuffle(atom_indices)
        i = 0
        for site in sites:
            site.atom_indices = atom_indices[i:i+site.get_natoms()].copy()
            i += site.get_natoms()
        
        topology = RBTopology()
        topology.add_sites(sites)
        topology.finalize_setup(use_cpp=False)
        return topology, atom_indices

    def make_atom_indices_python_topology(self):
        topology, atom_indices = self.make_atom_indices_cpp_topology()
        topology.cpp_topology = None
        return topology, atom_indices
    
    def get_random_rbcoords(self):
        otp = OTPCluster(self.nrigid)
        ret = otp.get_random_minimized_configuration(tol=100.)
        return ret.coords

    def test_to_atomistic(self):
        tai, atom_indices = self.make_atom_indices_python_topology()
        tnorm = self.make_normal_python_topology()
        
        coords = self.get_random_rbcoords()
        
        a1 = tai.to_atomistic(coords.copy())
        a2 = tnorm.to_atomistic(coords)
        
        a1perm = a1[atom_indices]
        assert_arrays_almost_equal(self, a1perm, a2)
    
    def test_transform_gradient(self):
        tai, atom_indices = self.make_atom_indices_python_topology()
        tnorm = self.make_normal_python_topology()
        
        coords = self.get_random_rbcoords()

        aai = tai.to_atomistic(coords.copy())
        anorm = tnorm.to_atomistic(coords.copy())

        
        lj = LJ()
#        atomistic_coords = np.random.uniform(-1, 1, 3*len(atom_indices))
#        e, atomistic_grad = lj.getEnergyGradient(atomistic_coords)
        
        e1, gai = lj.getEnergyGradient(aai.ravel())
        e2, gnorm = lj.getEnergyGradient(anorm.ravel())
        self.assertAlmostEqual(e1, e2)
        assert_arrays_almost_equal(self, gai.reshape(-1,3)[atom_indices], gnorm.reshape(-1,3))

        
        
        rb_gai = tai.transform_gradient(coords.copy(), gai)
        rb_gnorm = tnorm.transform_gradient(coords.copy(), gnorm)
        
        assert_arrays_almost_equal(self, rb_gai, rb_gnorm)

    def test_atom_indices(self):
        topology, atom_indices = self.make_atom_indices_python_topology()
        
        
        normal_topology = self.make_normal_python_topology()

        
        lj = LJ()
        
        pot = pythonRBPotentialWrapper(topology, lj)
        pot_normal = pythonRBPotentialWrapper(normal_topology, lj)
        
        coords = self.get_random_rbcoords()

        energy_atom_indices = pot.getEnergy(coords.copy())
        energy_normal = pot_normal.getEnergy(coords.copy())
        self.assertAlmostEqual(energy_atom_indices, energy_normal)

        e1, gei = pot.getEnergyGradient(coords.copy())
        e2, gnorm = pot_normal.getEnergyGradient(coords.copy())
        assert_arrays_almost_equal(self, gei, gnorm)
        
            

if __name__ == "__main__":
#    subset = unittest.TestSuite()
#    subset.addTest(TestAtomIndices())
#    unittest.TextTestResult().run(subset)
    unittest.main()

