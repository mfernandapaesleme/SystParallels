#include <algorithm>
#include <cassert>
#include <iostream>
#include <thread>
#if defined(_OPENMP)
#include <omp.h>
#endif
#include "ProdMatMat.hpp"

namespace {
void prodSubBlocks(int iRowBlkA, int iColBlkB, int iColBlkA, int szBlock,
                   const Matrix& A, const Matrix& B, Matrix& C) {
  #pragma omp parallel for 
  for (int j = iColBlkB; j < std::min(B.nbCols, iColBlkB + szBlock); j++)
    for (int k = iColBlkA; k < std::min(A.nbCols, iColBlkA + szBlock); k++)
      for (int i = iRowBlkA; i < std::min(A.nbRows, iRowBlkA + szBlock); ++i)
        C(i, j) += A(i, k) * B(k, j);
}
const int szBlock = 512;
}  // namespace

namespace {
void prodBlocks(int szBlock, const Matrix& A, const Matrix& B, Matrix& C){
  int dim = std::max({A.nbRows, B.nbCols, A.nbCols});
  #pragma omp parallel for 
  for (int n = 0; n < dim; n+=szBlock)
        for (int m = 0; m < dim; m+=szBlock)
          for (int j = n; j < n+szBlock; j++)
            for (int k = 0; k < dim; k++)
              for (int i = m; i < m+szBlock; i++)
                C(i, j) += A(i, k) * B(k, j);
  }
}

Matrix operator*(const Matrix& A, const Matrix& B) {
  Matrix C(A.nbRows, B.nbCols, 0.0);
  // prodSubBlocks(0, 0, 0, std::max({A.nbRows, B.nbCols, A.nbCols}), A, B, C);  // without blocking
  prodBlocks(512, A, B, C);
  return C;
}