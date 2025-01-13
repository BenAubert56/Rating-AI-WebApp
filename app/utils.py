from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Charger le modèle linguistique et le tokenizer
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def predict_comment_rating(comment):
    print("----------------------------------------------------")
    print(comment)
    inputs = tokenizer(comment, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    scores = outputs.logits
    print(scores)
    predicted_rating = torch.argmax(scores, dim=1).item() + 1  # Ajouter +1 car les notes sont indexées de 0 à 4
    print(predicted_rating)
    return predicted_rating