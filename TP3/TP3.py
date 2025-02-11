from mpi4py import MPI
import numpy as np

def bucket_sort_parallel():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # Génération des données sur le processus 0
    if rank == 0:
        data_size = 100  # Taille du tableau à trier
        data = np.random.randint(0, 100, data_size)
        print(f"Données initiales : {data}")
    else:
        data = None

    # Distribution des données
    data = comm.bcast(data, root=0)

    # Calcul des buckets locaux
    local_bucket = []
    for num in data:
        bucket_id = num // (100 // size)  # Assigner chaque valeur à un bucket
        if bucket_id >= size:  # Gérer les cas où num == 100
            bucket_id = size - 1
        if rank == bucket_id:
            local_bucket.append(num)

    # Tri local
    local_bucket.sort()

    # Rassemblement des résultats
    gathered_data = comm.gather(local_bucket, root=0)

    # Fusion des résultats sur le processus 0
    if rank == 0:
        sorted_data = []
        for bucket in gathered_data:
            sorted_data.extend(bucket)
        print(f"Données triées : {sorted_data}")

if __name__ == "__main__":
    bucket_sort_parallel()