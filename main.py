# -*- coding: utf-8 -*-
"""CLIP-1st8

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AzxT9WnIi_3aWBKyqHsP4ToTEcpIcLBq
"""

# importing libraries
#!pip install kaggle
from google.colab import files
import numpy as np
import pandas as pd
import os

import requests
from PIL import Image
from io import BytesIO

import torch
import torch.nn as nn
from torchvision import transforms
import torch.nn.functional as F
import torch.optim as optim


import matplotlib.pyplot as plt

#Bringing the dataset
from google.colab import drive
drive.mount('/content/drive')
#! mkdir ~/.kaggle
os.environ['KAGGLE_USERNAME'] = "hanviksuruboyina"
os.environ['KAGGLE_KEY'] = "b8f48ef46400e2f5a559ada21f2cc402"
!cp /content/drive/MyDrive/ML/kaggle.json ~/.kaggle/kaggle.json
! chmod 600 ~/.kaggle/kaggle.json
! kaggle datasets download vitaliykinakh/guie-laion5b-dataset
! unzip guie-laion5b-dataset.zip

#json to csv
data_json = pd.read_json('GUIE_laion5b_dataset_en.json')
data_json.to_csv('data.csv', index=False)
data = pd.read_csv('data.csv')
print(data.head(5))

# to find the names of categories
def categories(category):
  column_values = data[category]
  unique_values = column_values.unique()
  unique_column_names = [col.split(':')[0] for col in unique_values]
  #print(unique_column_names)
  #print(len(unique_column_names))
  return unique_column_names

print(categories('category'))
print(categories('prompt'))

def number_rows_category(word, category):
  matching_rows = data[data[category].str.contains(word, case=False)]
  num_rows = matching_rows.shape[0]
  print(num_rows)


for i in range (0,9):
  number_rows_category(categories('category')[i], 'category')
print(categories('category'))

data = data.drop('id', axis=1) # to remove the id column as it is not useful
data = data.drop('caption', axis=1) # to remove the caption column as it is not useful
data = data.drop('caption_en', axis=1)
data = data.drop('similarity', axis=1)


df = pd.DataFrame()

for i in range (len(categories('category'))):
  print(i)
  items_with_specific_label = data[data['category'] == categories('category')[i]]
  items_with_specific_label = items_with_specific_label.sample(frac=1, random_state=42)
  items_with_specific_label = items_with_specific_label.head(10)
  df = df.append(items_with_specific_label)
df = df.reset_index(drop=True)



size = df.shape[0]
image_array = np.zeros((size,), dtype=object)  # Use object dtype to store arrays of varying sizes
image_array.shape

count = 0
for i in range(size):
    urls = df.loc[i, 'url']

    try:
        print(i)
        response = requests.get(urls)
        response.raise_for_status()  # Check for any HTTP request errors

        # Read the image data from the response content
        image_data = response.content

        # Create a PIL image object from the image data
        image = Image.open(BytesIO(image_data))
        image = image.resize((224, 224))

        # Convert the PIL image to a NumPy array
        image_np = np.array(image)

        # Assign the NumPy array to the appropriate index in image_array
        image_array[count] = image_np
        count = count + 1

    except requests.exceptions.RequestException as err:
        df = df.drop(i)
        print(f"Error occurred for URL {urls}: {err}")

    except (IOError, ValueError) as err:
        df = df.drop(i)
        print(f"Error occurred while processing image {i}: {err}")

df = df.reset_index(drop=True)
image_array = image_array[:count]
df['image_array'] = image_array


num_rows = df.shape[0]

import matplotlib.pyplot as plt
plt.imshow(image_array[3], cmap='viridis')
#plt.colorbar()

# Display the plot
plt.show()



#TOKENIZER


token_words = ['this', 'is', 'a', 'picture', 'of', 'a']
len_token = len(token_words)

def tokenizer(words):
    unique_tokens = set(words)
    return list(unique_tokens)

for k in range (0, num_rows):
  prompt = df.loc[k, 'prompt']
  prompt = prompt.lower()
  #print(prompt)
  x = prompt.split()
  token_words.extend(x)
  #token_words.append(prompt)
  token_words = tokenizer(token_words)

for k in range (0, num_rows):
  prompt = df.loc[k, 'category']
  prompt = prompt.lower()
  #print(prompt)
  x = prompt.split()
  token_words.extend(x)
  #token_words.append(prompt)
  token_words = tokenizer(token_words)

print(token_words)




len(token_words)

values = []
for i in range (1, len(token_words)+1):
  values.append(i)



def token(i):
  prompt = df.loc[i, 'prompt']
  prompt = prompt.lower()
  x = prompt.split()
  token_words.extend(x)
  return tokenizer(token_words)

text_paths = df['prompt'].head(10).tolist()


text_paths = [word.lower() for word in text_paths]

dataset = text_paths





# Example vocabulary mapping with "<PAD>" token
vocab = {}
for i in range(len(token_words)):
    key = token_words[i]
    value = values[i]
    vocab[key] = value

# Add the "<PAD>" token to the vocab
vocab["<PAD>"] = 0

sentences_list = text_paths

# Initialize an empty list to store tokenized sentences
tokenized_sentences = []
max_sentence_length = 20
tokenized_sentences_with_padding = []

# Loop through each sentence in the sentences_list
for sentence in sentences_list:
    # Split the sentence into words
    words = sentence.split()
    # Initialize an empty list to store tokens for this sentence
    tokenized_sentence = []
    # Loop through each word in the words list
    for word in words:
        # Convert the word to lowercase
        lowercase_word = word.lower()
        # Check if the lowercase word exists in the vocab dictionary
        if lowercase_word in vocab:
            # If it exists, append its corresponding token to the tokenized_sentence list
            tokenized_sentence.append(vocab[lowercase_word])
    # Add padding to the tokenized_sentence to make its length 25
    tokenized_sentence += [vocab['<PAD>']] * (max_sentence_length - len(tokenized_sentence))
    # Truncate the sentence to the maximum length (in case it's longer than 25)
    tokenized_sentence = tokenized_sentence[:max_sentence_length]
    # Append the tokenized_sentence list to the tokenized_sentences_with_padding list
    tokenized_sentences_with_padding.append(tokenized_sentence)

print(tokenized_sentences_with_padding)
input_tensor = torch.tensor(tokenized_sentences_with_padding, dtype=torch.long)
print(input_tensor.shape)


# Add any missing words from the dataset to the vocab
#for sentence in text_paths:
#    for word in sentence:
#        if word not in vocab:
#            vocab[word] = len(vocab)

# Now convert the dataset to numerical_dataset
#numerical_dataset = [[vocab[word] for word in sentence] for sentence in dataset]

#max_sequence_length = max(len(sentence) for sentence in numerical_dataset)
#padded_numerical_dataset = [sentence + [vocab["<PAD>"]] * (max_sequence_length - len(sentence)) for sentence in numerical_dataset]

#input_tensor = torch.tensor(padded_numerical_dataset, dtype=torch.long)
#print(input_tensor.shape)

mask = (input_tensor != vocab["<PAD>"]).unsqueeze(1).unsqueeze(2)
print(mask.shape)

mask = mask.float()



import torch
import torch.nn as nn


class SelfAttention(nn.Module):
    def __init__(self, embed_size, heads):
        super(SelfAttention, self).__init__()
        self.embed_size = embed_size
        self.heads = heads
        self.head_dim = embed_size // heads

        assert (
            self.head_dim * heads == embed_size
        ), "Embedding size needs to be divisible by heads"

        self.values = nn.Linear(embed_size, embed_size)
        self.keys = nn.Linear(embed_size, embed_size)
        self.queries = nn.Linear(embed_size, embed_size)
        self.fc_out = nn.Linear(embed_size, embed_size)

    def forward(self, values, keys, query, mask):
        # Get number of training examples
        N = query.shape[0]

        value_len, key_len, query_len = values.shape[1], keys.shape[1], query.shape[1]

        values = self.values(values)  # (N, value_len, embed_size)
        keys = self.keys(keys)  # (N, key_len, embed_size)
        queries = self.queries(query)  # (N, query_len, embed_size)

        # Split the embedding into self.heads different pieces
        values = values.reshape(N, value_len, self.heads, self.head_dim)
        keys = keys.reshape(N, key_len, self.heads, self.head_dim)
        queries = queries.reshape(N, query_len, self.heads, self.head_dim)

        energy = torch.einsum("nqhd,nkhd->nhqk", [queries, keys])
        # queries shape: (N, query_len, heads, heads_dim),
        # keys shape: (N, key_len, heads, heads_dim)
        # energy: (N, heads, query_len, key_len)

        if mask is not None:
            energy = energy.masked_fill(mask == 0, float("-1e20"))

        attention = torch.softmax(energy / (self.embed_size ** (1 / 2)), dim=3)
        # attention shape: (N, heads, query_len, key_len)

        out = torch.einsum("nhql,nlhd->nqhd", [attention, values]).reshape(
            N, query_len, self.heads * self.head_dim
        )

        out = self.fc_out(out)


        return out


class TransformerBlock(nn.Module):
    def __init__(self, embed_size, heads, dropout, forward_expansion):
        super(TransformerBlock, self).__init__()
        self.attention = SelfAttention(embed_size, heads)
        self.norm1 = nn.LayerNorm(embed_size)
        self.norm2 = nn.LayerNorm(embed_size)

        self.feed_forward = nn.Sequential(
            nn.Linear(embed_size, forward_expansion * embed_size),
            nn.ReLU(),
            nn.Linear(forward_expansion * embed_size, embed_size),
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, value, key, query, mask):
        attention = self.attention(value, key, query, mask)

        # Add skip connection, run through normalization and finally dropout
        x = self.dropout(self.norm1(attention + query))
        forward = self.feed_forward(x)
        out = self.dropout(self.norm2(forward + x))
        return out


class Encoder(nn.Module):
    def __init__(
        self,
        src_vocab_size,
        embed_size,
        num_layers,
        heads,
        device,
        forward_expansion,
        dropout,
        max_length,
    ):

        super(Encoder, self).__init__()
        self.embed_size = embed_size
        self.device = device
        self.word_embedding = nn.Embedding(src_vocab_size, embed_size)
        self.position_embedding = nn.Embedding(max_length, embed_size)

        self.layers = nn.ModuleList(
            [
                TransformerBlock(
                    embed_size,
                    heads,
                    dropout=dropout,
                    forward_expansion=forward_expansion,
                )
                for _ in range(num_layers)
            ]
        )

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask):
        N, seq_length = x.shape
        positions = torch.arange(0, seq_length).expand(N, seq_length).to(self.device)
        out = self.dropout(
            (self.word_embedding(x) + self.position_embedding(positions))
        )

        # In the Encoder the query, key, value are all the same, it's in the
        # decoder this will change. This might look a bit odd in this case.
        for layer in self.layers:
            out = layer(out, out, out, mask)

        return out





src_vocab_size = 1000  # Assuming there are 10,000 unique words in the source vocabulary
#embed_size = 128        # Dimension of word embeddings is 256
embed_size = 196*2
num_layers = 6          # Using 6 Transformer blocks (layers)
heads = 8               # 8 attention heads
forward_expansion = 4   # Factor by which the hidden dimension is expanded in the feed-forward network is 4
dropout = 0.1           # Dropout rate of 0.1 (10%)
max_length = 150
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Use GPU if available

#encoder = Encoder(src_vocab_size, embed_size, num_layers, heads, device, forward_expansion, dropout, max_length)

encoder = Encoder(src_vocab_size, embed_size, num_layers, heads, device, forward_expansion, dropout, max_length)

text_output_tensor = encoder(input_tensor, mask)


import torch
import torch.nn as nn

class PatchEmbedding(nn.Module):
    def __init__(self, img_size, patch_size, in_channels, embed_size):
        super(PatchEmbedding, self).__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.in_channels = in_channels
        self.embed_size = embed_size
        self.num_patches = (img_size // patch_size) ** 2

        self.projection = nn.Conv2d(in_channels, embed_size, kernel_size=patch_size, stride=patch_size)

    def forward(self, x):
        x = self.projection(x)  # (batch_size, embed_size, num_patches, num_patches)
        x = x.flatten(2).transpose(1, 2)  # (batch_size, num_patches*num_patches, embed_size)
        return x


class VisionTransformer(nn.Module):
    def __init__(
        self,
        img_size,
        patch_size,
        in_channels,
        embed_size,
        num_layers,
        heads,
        device,
        forward_expansion,
        dropout,
        num_classes,
        max_length,
    ):
        super(VisionTransformer, self).__init__()
        self.patch_embedding = PatchEmbedding(img_size, patch_size, in_channels, embed_size)
        self.position_embedding = nn.Embedding(max_length, embed_size)

        self.layers = nn.ModuleList(
            [
                TransformerBlock(
                    embed_size,
                    heads,
                    dropout=dropout,
                    forward_expansion=forward_expansion,
                )
                for _ in range(num_layers)
            ]
        )

        self.classification_head = nn.Linear(embed_size, num_classes)
        self.dropout = nn.Dropout(dropout)
        self.device = device

    def forward(self, x, mask=None):
        x = self.patch_embedding(x)
        N, num_patches, _ = x.shape

        positions = torch.arange(0, num_patches).expand(N, num_patches).to(self.device)
        x += self.position_embedding(positions)

        for layer in self.layers:
            x = layer(x, x, x, mask)
        #print(x.shape)
        #print(x[:, 0].shape)
        # Take only the first token (CLS token) and pass it through the classification head
        #cls_token = x[:, 0]
        cls_token = x
        cls_token = self.dropout(cls_token)
        logits = self.classification_head(cls_token)

        return logits

dftemp = df.head(10)

image_paths = dftemp['image_array'].tolist()

preprocess = transforms.Compose([
    #transforms.Resize((256, 256)),  # Resize images to a fixed size (e.g., 256x256)
    transforms.ToTensor(),          # Convert images to tensors
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize the tensor
])
i = 0
preprocessed_images = []
for image_path in image_paths:
    img = image_paths[i]
    img = preprocess(img)
    preprocessed_images.append(img)
    i = i+1


stacked_images_tensor = torch.stack(preprocessed_images)


import torch
import torch.nn as nn

# Example input image size and patch size
img_size = 224
patch_size = 16
in_channels = 3  # Assuming RGB images

# Vision Transformer parameters
embed_size = 256
num_layers = 6
heads = 8
dropout = 0.1
num_classes = 40  # Replace this with the number of classes in your classification task
#num_classes = 142*128
max_length = (img_size // patch_size) ** 2 + 1  # +1 for the CLS token

# Create 10 random input images as a batch (batch_size=10)
batch_size = 10
input_images = stacked_images_tensor

# Create the VisionTransformer model
model = VisionTransformer(
    img_size=img_size,
    patch_size=patch_size,
    in_channels=in_channels,
    embed_size=embed_size,
    num_layers=num_layers,
    heads=heads,
    device='cuda' if torch.cuda.is_available() else 'cpu',
    forward_expansion=4,  # You can adjust this value if needed
    dropout=dropout,
    num_classes=num_classes,
    max_length=max_length,
)


# Move the model to the appropriate device (CPU or GPU)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# Forward pass to get the output tensor
with torch.no_grad():
    model.eval()
    input_images = input_images.to(device)
    image_output_tensor = model(input_images)

print(image_output_tensor.shape)



def image_tens():
    # Move the model to the appropriate device (CPU or GPU)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    # Forward pass to get the output tensor
    with torch.no_grad():
        model.eval()  # Set the model to evaluation mode (important for dropout layers)
        input_images = input_images.to(device)
        image_output_tensor = model(input_images)

    #print(image_output_tensor.shape)  # Output should be torch.Size([10, 10, 256])
    return(image_output_tensor)

"""* For text = text_output_tensor


* For images = image_output_tensor
"""

def resize_tensor(text_output_tensor):
  x_size = text_output_tensor.size(1)
  y_size = text_output_tensor.size(2)

  z_size = x_size * y_size

  text_output_tensor = text_output_tensor.view(10, z_size)
  return text_output_tensor

print(text_output_tensor.shape)
print(image_output_tensor.shape)

temp = 7840
text_output_tensor1 = text_output_tensor.view(10, temp)
image_output_tensor1 = image_output_tensor.view(10, temp)
#image_output_tensor = image_output_tensor.transpose(0, 1)

print(text_output_tensor1.shape)
print(image_output_tensor1.shape)


import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

# Assuming you have a custom image and text encoder models
# Replace these with your actual models
#image_encoder = model
#text_encoder = encoder

class CLIPModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.image_encoder = model
        self.text_encoder = encoder

    def forward(self, input_images, input_tensor, mask):
        # Getting Image and Text Features
        image_features = self.image_encoder(input_images)
        text_features = self.text_encoder(input_tensor, mask)

        batch_size = input_images.size(0)
        temp = 7840
        text_features_flat = text_features.view(batch_size, temp)
        image_features_flat = image_features.view(batch_size, temp)

        # to trnspose
        image_features_flat = image_features_flat.transpose(0, 1)

        # Matrix multiplication
        #predicted_matrix = torch.matmul(text_features_flat, image_features_flat)
        #print(predicted_matrix.shape)
        #return predicted_matrix
        return text_features_flat, image_features_flat



def pred_matrix(text_features_flat, image_features_flat):
  predicted_matrix = torch.matmul(text_features_flat, image_features_flat)
  #print(predicted_matrix)
  return predicted_matrix

my_model = CLIPModel().to(device)
#predicted_matrix = my_model(input_images, input_tensor, mask)

#criterion = nn.CrossEntropyLoss()
criterion = nn.MSELoss(size_average=None, reduce=None, reduction='mean')
optimizer = optim.Adam(my_model.parameters(), lr=0.01)

epochs = 15

batch_size

targets = 1000*torch.eye(batch_size)

targets

my_data = (input_images, input_tensor, mask)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

import torch
import torch.nn as nn
import torch.optim as optim


# Define your cross_entropy function
def cross_entropy(preds, targets, reduction='mean'):
    log_softmax = nn.LogSoftmax(dim=-1)
    loss = (-targets * log_softmax(preds)).sum(1)
    if reduction == "mean":
        return loss.mean()
    elif reduction == "sum":
        return loss.sum()
    else:
        return loss

criterion = nn.MSELoss()

# Assuming you have a training loop
epochs = 5
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
my_model.to(device)

for epoch in range(epochs):
        #my_model.train()  # Set the model to training mode
    #for batch_idx, (input_images, input_tensor, mask, targets) in enumerate(train_loader):
        # Move data to the device
        input_images = input_images.to(device)
        input_tensor = input_tensor.to(device)
        mask = mask.to(device)
        targets = targets.to(device)

        # Forward pass to get predictions
        a, b = my_model(input_images, input_tensor, mask)
        print(a,b)
        scores = pred_matrix(a, b)

        ground_truth_matrix = 1000*torch.eye(10)  # Identity matrix of size (10, 10)

        # Calculate the mean squared error loss
        #loss = F.mse_loss(scores, ground_truth_matrix)
        # Compute the cross-entropy loss
        loss = cross_entropy(scores, targets, reduction='mean')
        #loss = criterion(scores, targets)
        #print(loss.item())  # Print the loss for each batch


        # Perform backpropagation and update model parameters
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        print('Epoch:', epoch)
        #print(scores)
        my_model.train()

# After training, you can switch the model to evaluation mode before making predictions.
my_model.eval()

print(scores)

def cross_entropy(preds, targets, reduction='none'):
    log_softmax = nn.LogSoftmax(dim=-1)
    loss = (-targets * log_softmax(preds)).sum(1)
    if reduction == "none":
        return loss
    elif reduction == "mean":
        return loss.mean()

mask.shape

a, b = my_model(input_images, input_tensor, mask)

first_batch = input_images[:1, :, :, :]

x = model(input_images)















































len(input_tensor)

c, d = my_model(input_images, input_tensor, mask)





import torch
import torchvision.models as models

#model =my_model
def are_params_unfrozen(model):
    for name, param in model.named_parameters():
        if param.requires_grad:
            print(f"Parameter '{name}' is unfrozen.")
        else:
            print(f"Parameter '{name}' is frozen.")

are_params_unfrozen(model)

