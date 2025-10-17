/* Sample summation program for benchmarking, takes in parameter n and  */

#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <time.h>

long long compute_sum(int rank, int size, long long n);  // Computation for each process

int main(int argc, char** argv) {
    // Validate the input arguments
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <number>\n", argv[0]);  // Print as an error
        return 1;
    }

    long long n = atoll(argv[1]);  // The number up to which we want to sum (converted to a long long int)

    // Initialize MPI and relevant variables
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    int rank, size;
    long long localSum = 0, totalSum = 0;

    // Start timing
    double startTime = MPI_Wtime();

    // If the size is 1, we can run an optimized serial version
    if(size == 1){
        for(long long i = 1; i <= n; i++){
            localSum += i;
        }
        printf("Total Sum from 1 to %lld: %lld\n", n, localSum);
        printf("Serial Run Time (seconds): %f\n", MPI_Wtime() - startTime);
    }
    // Else, run in parallel using MPI
    else{
        // Each process computes its sum
        localSum = compute_sum(rank, size, n);

        // Reduce all local sums from all processes to the total sum
        MPI_Reduce(&localSum, &totalSum, 1, MPI_LONG_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

        // Each process prints its runtime
        double endTime = MPI_Wtime();  // End timing
        printf("MPI run time for rank %d: %f seconds\n", rank, endTime - startTime);
        
        // Root process prints the final result
        if (rank == 0) {
            printf("Summation from 1 to %lld is: %lld\n", n, totalSum);
        }

        MPI_Finalize();  // Finalize MPI
        return 0;
    }
}

/* Each process computes it's share of the total sum */
long long compute_sum(int rank, int size, long long n) {
    long long locaNum = n / size;  // Number of elements per process
    long long start = rank * localNum + 1;  // Start index for this process
    long long end = (rank + 1) * localNum;  // End index for this process

    // Handle the case where n is not perfectly divisible by size
    if (rank == size - 1) {
        end = n;
    }

    long long localSum = 0;
    for (long long i = start; i <= end; i++) {
        localSum += i;
    }

    return localSum;
}