import numpy as np
from bfgs import lineSearch, BFGS

class LBFGS(BFGS):
    def __init__(self, X, G, pot, maxstep = 0.1, M=10):
        self.X = X
        self.G = G
        self.pot = pot
        self.maxstep = maxstep
        self.funcalls = 0
    
        self.N = len(X)
        self.M = M 
        N = self.N
        M = self.M
        
        self.s = np.zeros([M,N])  #position updates
        self.y = np.zeros([M,N])  #gradient updates
        self.a = np.zeros(M)  #approximation for the inverse hessian
        #self.beta = np.zeros(M) #working space
        
        self.q = np.zeros(N)  #working space
        self.z = np.zeros(N)  #working space
        
        self.H0 = np.ones(M) * 1. #initial guess for the hessian
        self.rho = np.zeros(M)
        self.k = -1
        
        self.s[0,:] = X
        self.y[0,:] = G
        self.rho[0] = 0. #1. / np.dot(X,G)
        
        self.stp = np.zeros(N)

        self.Xold = np.zeros(N)
        self.Gold = np.zeros(N)
    
    def step(self, X, G):
        s = self.s
        y = self.y
        a = self.a
        q = self.q
        z = self.z
        rho = self.rho
        M = self.M
        
        k = self.k
        ki = k % M #the index corresponding to k
        
        
        #we have a new X and G, save in s and y
        if k >= 0:
            s[ki,:] = X - self.Xold
            y[ki,:] = G - self.Gold
            rho[ki] = 1. / np.dot(s[ki,:], y[ki,:])
        self.Xold[:] = X[:]
        self.Gold[:] = G[:]
        
        
        q[:] = G[:]
        myrange = [ i % M for i in range(max([0,k-M]), k, 1) ]
        print "myrange", myrange, ki, k
        for i in reversed(myrange):
            #i = i1 % M
            #print i, len(a), len(rho), np.shape(s)
            a[i] = rho[i] * np.dot( s[i,:], q )
            q -= a[i] * y[i,:]
        
        z[:] = self.H0[ki] * q[:]
        for i in myrange:
            #i = i1 % M
            #print i
            beta = rho[i] * np.dot( y[i,:], z )
            z += s[i,:] * (a[i] - beta)
        
        self.stp[:] = -z[:]
        
        #we now have the step direction.  now take the step
        self.takeStep(X, self.stp)
        #print "step size", np.linalg.norm(self.stp)
        
        self.k += 1
        return X

        

def test():
    import bfgs
    natoms = 10
    tol = 1e-5
    
    from potentials.lj import LJ
    pot = LJ()
    
    X = bfgs.getInitialCoords(natoms, pot)
    X += np.random.uniform(-1,1,[3*natoms]) * 0.3
    
    
    Xinit = np.copy(X)
    e, g = pot.getEnergyGradient(X)
    print "energy", e
    
    lbfgs = LBFGS(X, g, pot, maxstep = 0.1)
    
    ret = lbfgs.run(1000, tol = tol, iprint=1)
    print "done", ret[1], ret[2], ret[3], ret[5]
    
    print "now do the same with old lbfgs"
    from optimize.quench import quench
    ret = quench(Xinit, pot.getEnergyGradient, tol = tol)
    print ret[1], ret[2], ret[3]    
    
    print "now do the same with old bfgs"
    from optimize.quench import bfgs as oldbfgs
    ret = oldbfgs(Xinit, pot.getEnergyGradient, tol = tol)
    print ret[1], ret[2], ret[3]    
    
    if False:
        print "now do the same with old gradient + linesearch"
        gpl = bfgs.GradientPlusLinesearch(Xinit, pot, maxstep = 0.1)  
        ret = gpl.run(100, tol = 1e-6)
        print ret[1], ret[2], ret[3]    
            
    
    
        
if __name__ == "__main__":
    test()
    











