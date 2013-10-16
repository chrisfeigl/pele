#include "_lbfgs_cpp.h"
#include <vector>
#include <math.h>
#include <algorithm>

using namespace LBFGS_ns;
using std::vector;

double vecdot(std::vector<double> const v1, std::vector<double> const v2,
    size_t N)
{
  size_t i;
  double dot = 0.;
  for (i=0; i<N; ++i) {
    dot += v1[i] * v2[i];
  }
  return dot;
}

double vecnorm(std::vector<double> const v, size_t N)
{
  return sqrt(vecdot(v, v, N));
}

LBFGS::LBFGS(double const * x0, int N, int M)
{
    M_ = M;
    N_ = N;
    // these should be passed
    maxiter_ = 1000;
    H0_ = 0.1;
    tol_ = 1e-4;
    maxstep_ = 0.2;
    max_f_rise_ = 1e-4;

    // initialize parameters
    k_ = 0;
    nfev_ = 0;

    for (int j2 = 0; j2 < N_; ++j2){ 
      x_[j2] = x0[j2];
    }
    compute_func_gradient(x_, f_, g_);
    rms_ = vecnorm(g_, N_) / sqrt(N_);

    // allocate arrays
    x_ = std::vector<double>(N_);
    g_ = std::vector<double>(N_);

    y_ = std::vector<vector<double> >(M_, vector<double>(N_));
    s_ = std::vector<vector<double> >(M_, vector<double>(N_));
    rho_ = std::vector<double>(M_);
    alpha_ = std::vector<double>(M_);
}

LBFGS::~LBFGS()
{
}

void LBFGS::one_iteration()
{
  std::vector<double> x_old = x_;
  std::vector<double> g_old = g_;

  compute_lbfgs_step();

  backtracking_linesearch();

  update_memory(x_old, g_old, x_, g_);
}

void LBFGS::run()
{
  int iter = 0;
  for (iter = 0; iter < maxiter_; ++iter)
  {
    if (stop_criterion_satisfied()){
      break;
    }
    one_iteration();
  }
}

void LBFGS::update_memory(
          std::vector<double> & xold,
          std::vector<double> & gold,
          std::vector<double> & xnew,
          std::vector<double> & gnew
          )
{
  int klocal = k_ % M_;
  for (int j2 = 0; j2 < N_; ++j2){ 
    s_[klocal][j2] = gnew[j2] - gold[j2];
    y_[klocal][j2] = xnew[j2] - xold[j2];
  }

  double ys = vecdot(y_[klocal], s_[klocal], N_);
  if (ys == 0.) {
    // should print a warning here
    ys = 1.;
  }

  rho_[klocal] = 1. / ys;

  double yy = vecdot(y_[klocal], y_[klocal], N_);
  if (yy == 0.) {
    // should print a warning here
    yy = 1.;
  }
  H0_ = ys / yy;

  k_ += 1;
  
}

void LBFGS::compute_lbfgs_step()
{
  if (k_ == 0){ 
    double gnorm = vecnorm(g_, N_);
    if (gnorm > 1.) gnorm = 1. / gnorm;
    for (int i = 0; i < N_; ++i){
      step_[i] = - gnorm * H0_ * g_[i];
    }
    return;
  } 

  step_ = g_;

  int jmin = std::max(0, k_ - M_);
  int jmax = std::max(M_, k_);
  int i;
  double beta;

  // loop backwards through the memory
  for (int j = jmax - 1; j >= jmin; --j){
    i = j % M_;
    alpha_[i] = rho_[i] * vecdot(s_[i], step_, N_);
    for (int j2 = 0; j2 < N_; ++j2){
      step_[j2] -= alpha_[i] * y_[i][j2];
    }
  }

  // scale the step size by H0
  for (int j2 = 0; j2 < N_; ++j2){
    step_[j2] *= H0_;
  }

  // loop forwards through the memory
  for (int j = jmin; j < jmin; ++j){
    i = j % M_;
    beta = rho_[i] * vecdot(y_[i], step_, N_);
    for (int j2 = 0; j2 < N_; ++j2){
      step_[j2] -=  s_[i][j2] * (alpha_[i] - beta);
    }
  }

  // invert the step to point downhill
  for (int j2 = 0; j2 < N_; ++j2){
    step_[j2] *= -1;
  }

}

void LBFGS::backtracking_linesearch()
{
  vector<double> xnew(N_);
  vector<double> gnew(N_);
  double fnew;

  // if the step is pointing uphill, invert it
  if (vecdot(step_, g_, N_) < 0.){
    for (int j2 = 0; j2 < N_; ++j2){
      step_[j2] = -1;
    }
  }

  double f = 1.;
  double stepsize = vecnorm(step_, N_);

  // make sure the step is no larger than maxstep_
  if (f * stepsize > maxstep_){
    f = maxstep_ / stepsize;
  }

  int nred;
  int nred_max = 10;
  for (nred = 0; nred < nred_max; ++nred){
    for (int j2 = 0; j2 < N_; ++j2){
      xnew[j2] = x_[j2] + f * step_[j2];
    }
    compute_func_gradient(xnew, fnew, gnew);

    double df = fnew - f;
    if (df < max_f_rise_){
      break;
    } else {
      f /= 10.;
    }
  }

  if (nred >= nred_max){
    // possibly raise an error here
  }

  x_ = xnew;
  g_ = gnew;
  f_ = fnew;
  rms_ = vecnorm(gnew, N_) / sqrt(N_);
}

int LBFGS::stop_criterion_satisfied()
{
  return rms_ <= tol_;
}

void LBFGS::compute_func_gradient(std::vector<double> & x, double & func,
      std::vector<double> & gradient)
{
  nfev_ += 1;
}