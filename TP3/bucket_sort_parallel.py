from mpi4py import MPI
import numpy as np

def bucket_sort_parallel():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    nbp = comm.Get_size()  # Nombre total de processus (nbp)

    # Taille totale du tableau
    N = 100  

    # Création du fichier de sortie spécifique à chaque processus
    filename = f"Output{rank:03d}.txt"
    out = open(filename, mode='w')

    # Répartition équilibrée des éléments entre les processus
    reste = N % nbp
    NLoc = N // nbp + (1 if reste > rank else 0)
    out.write(f"Process {rank} - Nombre de valeurs locales : {NLoc}\n")

    # Chaque processus génère aléatoirement ses propres données
    values = np.random.randint(-32768, 32768, size=NLoc, dtype=np.int64)
    out.write(f"Process {rank} - Valeurs initiales : {values}\n")

    # Tri local des valeurs
    values.sort()
    out.write(f"Process {rank} - Valeurs triées localement : {values}\n")

    # Calcul des quantiles locaux
    local_quantiles = np.quantile(values, np.linspace(0, 1, nbp + 1))
    out.write(f"Process {rank} - Quantiles locaux : {local_quantiles}\n")

    # Tous les processus partagent leurs quantiles avec `allgather`
    all_quantiles = np.array(comm.allgather(local_quantiles)).flatten()

    # Fusion et tri des quantiles globaux
    merged_quantiles = np.sort(all_quantiles)
    final_quantiles = merged_quantiles[np.round(np.linspace(0, len(merged_quantiles) - 1, nbp + 1)).astype(int)]

    out.write(f"Process {rank} - Quantiles globaux après fusion : {final_quantiles}\n")

    # Chaque processus crée un bucket pour chaque autre processus
    buckets = {i: [] for i in range(nbp)}

    for val in values:
        for i in range(nbp):
            if final_quantiles[i] <= val < final_quantiles[i + 1]:
                buckets[i].append(val)
                break
    
    # Écriture des buckets avant envoi
    for i in range(nbp):
        out.write(f"Process {rank} - Bucket pour Process {i} : {buckets[i]}\n")

    # Préparer les données pour l'envoi avec alltoallv
    send_counts = np.array([len(buckets[i]) for i in range(nbp)], dtype=np.int64)
    send_displs = np.insert(np.cumsum(send_counts), 0, 0)[:-1]
    send_data = np.concatenate([buckets[i] for i in range(nbp)])

    # Allouer un buffer de réception
    recv_counts = np.zeros(nbp, dtype=np.int64)
    comm.Alltoall(send_counts, recv_counts)

    recv_displs = np.insert(np.cumsum(recv_counts), 0, 0)[:-1]
    recv_data = np.empty(sum(recv_counts), dtype=np.int64)

    # Échange des buckets entre les processus
    comm.Alltoallv([send_data, send_counts, send_displs, MPI.INT64_T],
                   [recv_data, recv_counts, recv_displs, MPI.INT64_T])

    out.write(f"Process {rank} - Données reçues : {recv_data}\n")

    # Tri final des données reçues
    recv_data.sort()
    out.write(f"Process {rank} - Données triées finales : {recv_data}\n")

    # Rassemblement des données triées
    gathered_data = comm.gather(recv_data, root=0)

    if rank == 0:
        sorted_data = np.concatenate(gathered_data)
        out.write(f"Process 0 - Données triées finales : {sorted_data}\n")
        print(f"Processus 0 - Données triées : {sorted_data}")

    # Fermer le fichier
    out.close()

if __name__ == "__main__":
    bucket_sort_parallel()