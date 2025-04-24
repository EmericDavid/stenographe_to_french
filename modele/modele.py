import pandas as pd
from torch.utils.data import Dataset, DataLoader
import sentencepiece as spm
import argparse
import os
import time

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.optim as optim
from torch.nn.utils import clip_grad_norm
import torchtext.data as data


if __name__ == '__main__':
    

    train = pd.read_csv('../data/translated_phrases.csv', sep=',', quotechar='"')

    tmp = train[int(len(train)*0.9):]
    train = train[:int(len(train)*0.9)]
    val, test = tmp[int(len(tmp)*0.5):], tmp[:int(len(tmp)*0.5)]

    train_x, train_y = train[:]['phrase_steno'], train[:]['phrase_fr']
    valid_x, valid_y = val[:]['phrase_steno'], val[:]['phrase_fr']
    test_x , test_y  = test[:]['phrase_steno'], test[:]['phrase_fr']
    #spm.SentencePieceTrainer.Train(input='../data/translated_phrases.csv',model_prefix="steno",vocab_size=2500,model_type="bpe",shuffle_input_sentence=True)
    sp=spm.SentencePieceProcessor()
    sp.load('steno.model')

    valid_x = valid_x.apply(lambda x: sp.EncodeAsPieces(x))
    valid_y = valid_y.apply(lambda x: sp.EncodeAsPieces(x))
    train_x = train_x.apply(lambda x: sp.EncodeAsPieces(x))
    train_y = train_y.apply(lambda x: sp.EncodeAsPieces(x))
    test_x = test_x.apply(lambda x: sp.EncodeAsPieces(x))
    test_y = test_y.apply(lambda x: sp.EncodeAsPieces(x))

    class StenoDataset(Dataset):
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __len__(self):
            return len(self.x)

        def __getitem__(self, idx):
            return self.x[idx], self.y[idx]

train_dataset = StenoDataset(train_x, train_y)
val_dataset = StenoDataset(valid_x, valid_y)
test_dataset = StenoDataset(test_x, test_y)
BATCH_SIZE = 32
train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

