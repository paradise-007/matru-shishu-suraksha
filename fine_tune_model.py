from datasets import load_dataset
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np

# Load the dataset
dataset = load_dataset('json', data_files={'train': 'health_queries.jsonl'})

# Define labels
labels = list(set(dataset['train']['label']))
label2id = {label: idx for idx, label in enumerate(labels)}
id2label = {idx: label for label, idx in label2id.items()}

# Tokenize the dataset
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

def preprocess_function(examples):
    # Tokenize the text
    encodings = tokenizer(examples['text'], truncation=True, padding='max_length', max_length=128)
    # Map string labels to integer IDs
    encodings['labels'] = [label2id[label] for label in examples['label']]
    return encodings

# Apply preprocessing
encoded_dataset = dataset.map(preprocess_function, batched=True)

# Ensure the dataset has the correct format for PyTorch
encoded_dataset.set_format(type='torch', columns=['input_ids', 'attention_mask', 'labels'])

# Split the dataset into train and validation sets (80% train, 20% validation)
train_test_split = encoded_dataset['train'].train_test_split(test_size=0.2, seed=42)
train_dataset = train_test_split['train']
eval_dataset = train_test_split['test']

# Debug: Print a sample to verify the data
print("Sample from train dataset:", train_dataset[0])

# Load the model
model = DistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    num_labels=len(labels),
    id2label=id2label,
    label2id=label2id
)

# Define a function to compute metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# Define training arguments with optimized hyperparameters
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=100,
    weight_decay=0.05,
    logging_dir='./logs',
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    learning_rate=2e-5,
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
)

# Fine-tune the model
trainer.train()

# Save the model and tokenizer
model.save_pretrained('./fine_tuned_model')
tokenizer.save_pretrained('./fine_tuned_model')

# Evaluate the model on the validation set
eval_results = trainer.evaluate()
print("Evaluation Results:", eval_results)