/* Sample summation program for benchmarking, takes in parameter n and finds the summation. Supports serial or parallel versions.
*  Note: In order to be properly processed by the python program, the print statements must follow the same convention as below. */

#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

long long compute_sum(int rank, int size, long long n);  // Computation for each process

int main(int argc, char** argv) {
    // Validate the input arguments
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <number>\n", argv[0]);  // Print to standard error
        return 1;
    }

    long long n = atoll(argv[1]);  // The number up that we want to sum (converted to a long long int)

    // Initialize MPI and relevant variables
    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    long long localSum = 0, totalSum = 0;

    // Start timing for benchmarking purposes
    double startTime = MPI_Wtime();

    // If the size is 1, we can run an optimized serial version
    if(size == 1){
        for(long long i = 1; i <= n; i++){
            localSum += i;
        }
        printf("Serial Run Time (seconds): %f\n", MPI_Wtime() - startTime);
        printf("Summation from 1 to %lld: %lld\n", n, localSum);
    }
    // Else, run in parallel using MPI
    else{
        // Each process computes its sum
        localSum = compute_sum(rank, size, n);

        // Reduce all local sums from all processes to the total sum
        MPI_Reduce(&localSum, &totalSum, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

        // Each process prints its runtime
        double endTime = MPI_Wtime();  // End timing
        printf("MPI run time for rank %d (seconds): %f\n", rank, endTime - startTime);
        
        // Barrier before printing final result for formatting
        MPI_Barrier(MPI_COMM_WORLD);

        // Root process prints the final result
        if (rank == 0) {
            printf("Summation from 1 to %lld is: %lld\n", n, totalSum);
        }
    }

    MPI_Finalize();  // Finalize MPI
    return 0;
}

/* Each process computes it's share of the total sum */
long long compute_sum(int rank, int size, long long n) {
    // Determine the range of numbers this process will sum
    long long base = n / size;  // Number of elements per process
    long long remainder = n % size;  // Remainder to distribute
    long long start = base * rank + (rank < remainder ? rank : remainder) + 1;  // Adjust start index to evenly distribute remainder
    long long count = base + (rank < remainder ? 1 : 0);  // Start index
    long long end = start + count - 1;  // End index

    // Compute local sum
    long long localSum = 0;
    for (long long i = start; i <= end; i++) {
        localSum += i;
    }

    return localSum;
}