from transformers import pipeline

generator = pipeline("text2text-generation", model="google/flan-t5-base")
