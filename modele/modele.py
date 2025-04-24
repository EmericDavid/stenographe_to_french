import pandas as pd
from torch.utils.data import Dataset, DataLoader
import sentencepiece as spm



if __name__ == '__main__':
    vocab = (pd.read_csv('../data/train.steno.txt', sep=" :: ", header=None))[:][0]

    train = pd.read_csv('../data/translated_phrases.csv', sep=',', quotechar='"')

    tmp = train[int(len(train)*0.9):]
    train = train[:int(len(train)*0.9)]
    val, test = tmp[int(len(tmp)*0.5):], tmp[:int(len(tmp)*0.5)]

    train_x, train_y = train[:]['phrase_steno'], train[:]['phrase_fr']
    valid_x, valid_y = val[:]['phrase_steno'], val[:]['phrase_fr']
    test_x , test_y  = test[:]['phrase_steno'], test[:]['phrase_fr']

    spm.SentencePieceTrainer.Train(input='../data/translated_phrases.csv',model_prefix="steno",vocab_size=2500,model_type="bpe",shuffle_input_sentence=True)
    sp=spm.SentencePieceProcessor()
    sp.load('steno.model')

    valid_x = valid_x.apply(lambda x: sp.EncodeAsPieces(x))
    print(valid_x[:10])