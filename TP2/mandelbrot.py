# Calcul de l'ensemble de Mandelbrot en python
import numpy as np
from dataclasses import dataclass
from PIL import Image
from math import log
from time import time
import matplotlib.cm
from mpi4py import MPI

@dataclass
class MandelbrotSet:
    max_iterations: int
    escape_radius:  float = 2.0

    def __contains__(self, c: complex) -> bool:
        return self.stability(c) == 1

    def convergence(self, c: complex, smooth=False, clamp=True) -> float:
        value = self.count_iterations(c, smooth)/self.max_iterations
        return max(0.0, min(value, 1.0)) if clamp else value

    def count_iterations(self, c: complex,  smooth=False) -> int | float:
        z:    complex
        iter: int

        # On vérifie dans un premier temps si le complexe
        # n'appartient pas à une zone de convergence connue :   
        #   1. Appartenance aux disques  C0{(0,0),1/4} et C1{(-1,0),1/4}
        if c.real*c.real+c.imag*c.imag < 0.0625:
            return self.max_iterations
        if (c.real+1)*(c.real+1)+c.imag*c.imag < 0.0625:
            return self.max_iterations
        #  2.  Appartenance à la cardioïde {(1/4,0),1/2(1-cos(theta))}
        if (c.real > -0.75) and (c.real < 0.5):
            ct = c.real-0.25 + 1.j * c.imag
            ctnrm2 = abs(ct)
            if ctnrm2 < 0.5*(1-ct.real/max(ctnrm2, 1.E-14)):
                return self.max_iterations
        # Sinon on itère
        z = 0
        for iter in range(self.max_iterations):
            z = z*z + c
            if abs(z) > self.escape_radius:
                if smooth:
                    return iter + 1 - log(log(abs(z)))/log(2)
                return iter
        return self.max_iterations

#Initialization du MPI  (mpi collective operations)
N : int = 360
comGlobal = MPI.COMM_WORLD.Dup()
rank      = comGlobal.rank
size       = comGlobal.size

# On peut changer les paramètres des deux prochaines lignes
mandelbrot_set = MandelbrotSet(max_iterations=50, escape_radius=10)
width, height = 1024, 1024

scaleX = 3./width
scaleY = 2.25/height
## convergence = np.empty((width, height), dtype=np.double)

# Partition équitable des lignes entre les processus -- 1a
columns_per_proc = width // size 
start_x = rank * columns_per_proc
end_x = width if rank == size - 1 else (rank + 1) * columns_per_proc

# Calcul local
local_convergence = np.empty((end_x - start_x, height), dtype=np.double)
deb = time()
for x in range(start_x, end_x):
    for y in range(width):
        c = complex(-2.0 + scaleX * x, -1.125 + scaleY * y)
        local_convergence[x - start_x, y] = mandelbrot_set.convergence(c, smooth=True)
fin = time()
local_time = fin - deb

# Rassemblement des résultats sur le processus 0
if rank == 0:
    full_convergence = np.empty((width, height), dtype=np.double)
else:
    full_convergence = None

comGlobal.Gather(local_convergence, full_convergence, root=0)  #estou pegando todos os locals e unindo em uma mesma imagem no 0


# Calcul de l'ensemble de mandelbrot :
deb = time()
for y in range(height):
    for x in range(width):
        c = complex(-2. + scaleX*x, -1.125 + scaleY * y)
        full_convergence[x, y] = mandelbrot_set.convergence(c, smooth=True)
fin = time()
print(f"Temps du calcul de l'ensemble de Mandelbrot : {fin-deb}")


# Constitution de l'image résultante :
deb = time()
if rank == 0:
    image = Image.fromarray(np.uint8(matplotlib.cm.plasma(full_convergence.T) * 255))
    image.save("mandelbrot.png")
    fin = time()
    print(f"Temps total du calcul : {fin - deb}")

