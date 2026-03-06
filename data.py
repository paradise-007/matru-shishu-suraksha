import json

# Load the original QA dataset
with open('chatbot_qa_dataset.json', 'r') as qa_file:
    qa_data = json.load(qa_file)

# Load the dialogue dataset
with open('chatbot_dialogue_dataset.json', 'r') as dialogue_file:
    dialogue_data = json.load(dialogue_file)

# Function to convert QA pairs to conversational format
def convert_qa_to_conversations(qa_data):
    conversations = []
    for item in qa_data['data']:
        for paragraph in item['paragraphs']:
            for qa in paragraph['qas']:
                question = qa['question']
                answer = qa['answers'][0]['text']  # Take the first answer
                conversations.append({
                    "messages": [
                        {"role": "user", "content": question},
                        {"role": "bot", "content": answer}
                    ]
                })
    return conversations

# Convert QA dataset
qa_conversations = convert_qa_to_conversations(qa_data)

# Combine with dialogue dataset
combined_conversations = qa_conversations + dialogue_data['conversations']

# Save the combined dataset
with open('combined_conversations.json', 'w') as combined_file:
    json.dump({"conversations": combined_conversations}, combined_file, indent=2)

print(f"Combined dataset saved with {len(combined_conversations)} conversations.")