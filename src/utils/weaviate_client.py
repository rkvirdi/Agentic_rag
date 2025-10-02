import weaviate

WEAVIATE_URL = "http://localhost:8080"

client = weaviate.connect_to_local(skip_init_checks=True)
