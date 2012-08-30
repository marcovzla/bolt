#!/usr/bin/env python

from __future__ import division
import numpy as np
import scipy.optimize

def logistic(z):
    return 1.0 / (1.0 + np.exp(-z))

def predict(w, X):
    return (logistic(np.dot(X,w)) > 0.5)*2-1

def log_likelihood(X, Y, instance_weights, w, C=0.1):
    return np.sum(instance_weights*np.log(logistic(Y * np.dot(X, w)))) - C/2 * np.dot(w, w)

def log_likelihood_grad(X, Y, instance_weights, w, C=0.1):
    K = len(w)
    N = len(X)
    s = np.zeros(K)

    for i in range(N):
        s += instance_weights[i] * Y[i] * X[i] * logistic(-Y[i] * np.dot(X[i], w))

    s -= C * w

    return s

def grad_num(X, Y, instance_weights, w, f, eps=0.00001):
    K = len(w)
    ident = np.identity(K)
    g = np.zeros(K)

    for i in range(K):
        g[i] += f(X, Y, instance_weights, w + eps * ident[i])
        g[i] -= f(X, Y, instance_weights, w - eps * ident[i])
        g[i] /= 2 * eps

    return g

def test_log_likelihood_grad(X, Y, instance_weights):
    n_attr = X.shape[1]
    w = np.array([1.0 / n_attr] * n_attr)

    print "with regularization"
    print log_likelihood_grad(X, Y, instance_weights, w)
    print grad_num(X, Y, instance_weights, w, log_likelihood)

    print "without regularization"
    print log_likelihood_grad(X, Y, instance_weights, w, C=0)
    print grad_num(X, Y, instance_weights, w, lambda X,Y,instance_weights,w: log_likelihood(X,Y, instance_weights,w,C=0))

def train_w(X, Y, instance_weights, C=0.1):
    def f(w):
        return -log_likelihood(X, Y, instance_weights, w, C)

    def fprime(w):
        return -log_likelihood_grad(X, Y, instance_weights, w, C)

    K = X.shape[1]
    initial_guess = np.zeros(K)

    return scipy.optimize.fmin_bfgs(f, initial_guess, fprime, disp=False)

def accuracy(X, Y, instance_weights, w):
    unweighted = sum((predict(w,X) == Y) ) / len(X)
    weighted = sum((predict(w,X) == Y)*instance_weights ) / sum(instance_weights)
    return unweighted, weighted

def read_data(filename, sep=",", filt=int):

    def split_line(line):
        return line.split(sep)

    def apply_filt(values):
        return map(filt, values)

    def process_line(line):
        return apply_filt(split_line(line))

    f = open(filename)
    lines = map(process_line, f.readlines())
    # "[1]" below corresponds to x0
    X = np.array([[1] + l[1:] for l in lines])
    # "or -1" converts 0 values to -1
    Y = np.array([l[0] or -1 for l in lines])
    f.close()

    return X, Y

def test():
    X_train, Y_train = read_data("SPECT.train")

    print 'Testing unweighted'
    instance_weights = np.ones(Y_train.shape)


    w = train_w(X_train, Y_train, instance_weights)
    print "w was", w
    print "accuracy was", accuracy(X_train, Y_train, instance_weights, w)

    print 'Testing weighted'
    instance_weights = Y_train + 2

    # Uncomment the line below to check the gradient calculations
    # test_log_likelihood_grad(X_train, Y_train, instance_weights); exit()

    w = train_w(X_train, Y_train, instance_weights)
    print "w was", w
    print "accuracy was", accuracy(X_train, Y_train, instance_weights, w)

if __name__ == "__main__": test()