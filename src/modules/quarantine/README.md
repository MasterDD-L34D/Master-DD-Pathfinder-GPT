Cartella di servizio dove finiscono i salvataggi dell'Hub che non superano `hub_storage.validation`.
I file qui richiedono revisione manuale prima di essere rimessi nel flusso normale: non vengono caricati
automaticamente dal runtime e non dovrebbero essere consumati da altri moduli senza prima verificarne
l'integrità.
