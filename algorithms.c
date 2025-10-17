/* C Implementations of necessary algorithms - Speedup, Efficiency, Ahmdahl's Law */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

/* Returns the speedup as a double 
    Parameters:
        T1: Execution time on one processor
        Tp: Execution time on p processors
*/
double getSpeedup(double T1, double Tp) {
    if (Tp == 0) {
        fprintf(stderr, "Error: Tp cannot be zero.\n");
        return 0;
    }
    return (double)(T1 / Tp);
}

/* Returns the efficiency as a double
    Parameters:
        S: Speedup
        p: Number of processors
*/
double getEfficiency(double S, int p) {
    if (p == 0) {
        fprintf(stderr, "Error: Number of processors cannot be zero.\n");
        return 0;
    }
    return (double)(S / p);
}

/* Returns the maximum speedup according to Amdahl's Law
    Parameters:
        f: Fraction of the program that is serial (0 <= f <= 1)
        p: Number of processors
*/
double getAmdahlsLaw(double f, int p) {
    if (p <= 0) {
        fprintf(stderr, "Error: Number of processors must be greater than zero.\n");
        return 0;
    }
    if (f < 0 || f > 1) {
        fprintf(stderr, "Error: Fraction f must be between 0 and 1.\n");
        return 0;
    }
    // Return the result of the formula
    return (double)(1 / ((1 - f) / (f / p)));
}

/* Returns the fraction of the program that is serial using Amdah's Law 
    Parameters:
        T1: Execution time on one processor
        Tp: Execution time on p processors
        p: Number of processors
*/
double getFractionParallelizable(double T1, double Tp, int p) {
    // Avoid division by zero
    if (T1 == 0.0) {
        fprintf(stderr, "Error: T1 cannot be zero.\n");
        return 0.0;
    }
    // Serial case
    if (p <= 1) {
        fprintf(stderr, "Error: Number of processors must be greater than one.\n");
        return 0.0;
    }
    // Get the speedup
    double S = getSpeedup(T1, Tp);
    // Apply Amdahl's Law rearranged to solve for f
    double fp = (p * (S - 1)) / ((p - 1) * S);
    return fp;
}